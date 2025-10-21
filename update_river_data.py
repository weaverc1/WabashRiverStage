#!/usr/bin/env python3
"""
River Stage Data Updater for Wabash River at Hutsonville Bridge
Updates river stage data from local CSV and pushes to GitHub Pages
Run this script every 15 minutes via cron/Task Scheduler
"""

import csv
import json
import os
from datetime import datetime
import subprocess
import sys

# Configuration
CSV_FILE_PATH = "/home/storm3receiver/storm/logs/rx_data.csv"
REPO_PATH = "/home/storm3receiver/WabashRiverStage"
DATA_FILE = "data/river_data.json"

def read_latest_river_stage(csv_path):
    """
    Read the most recent river stage reading from the CSV file.
    Returns a dict with timestamp and river stage value.
    """
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                print("ERROR: CSV file is empty")
                return None
            
            # Get the last row (most recent reading)
            latest = rows[-1]
            
            # Parse the data
            iso_time = latest['iso_time']
            river_stage = float(latest['riverstage'])
            
            # Convert to timestamp for easier handling
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            
            return {
                'timestamp': dt.isoformat(),
                'riverstage': round(river_stage, 3),
                'date_display': dt.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    except FileNotFoundError:
        print(f"ERROR: CSV file not found at {csv_path}")
        return None
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return None

def load_existing_data(data_file_path):
    """Load existing river data from JSON file."""
    try:
        with open(data_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # File doesn't exist yet, return empty structure
        return {
            'site_name': 'Wabash River at Hutsonville Bridge',
            'units': 'feet',
            'flood_stages': {
                'action': 12,
                'flood': 16,
                'moderate': 24,
                'major': 28,
                'near_record': 29
            },
            'last_updated': None,
            'readings': []
        }
    except Exception as e:
        print(f"ERROR loading existing data: {e}")
        return None

def update_data(existing_data, new_reading):
    """Add new reading to existing data, avoiding duplicates."""
    if new_reading is None:
        return existing_data
    
    # Check if this reading already exists (based on timestamp)
    existing_timestamps = [r['timestamp'] for r in existing_data['readings']]
    
    if new_reading['timestamp'] not in existing_timestamps:
        existing_data['readings'].append(new_reading)
        existing_data['last_updated'] = datetime.now().isoformat()
        print(f"Added new reading: {new_reading['date_display']} - {new_reading['riverstage']} ft")
    else:
        print(f"Reading already exists for {new_reading['date_display']}, skipping")
    
    return existing_data

def save_data(data, data_file_path):
    """Save updated data to JSON file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
        
        with open(data_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {data_file_path}")
        return True
    except Exception as e:
        print(f"ERROR saving data: {e}")
        return False

def git_commit_and_push(repo_path, data_file):
    """Commit changes and push to GitHub."""
    try:
        # Change to repo directory
        os.chdir(repo_path)
        
        # Add the data file
        subprocess.run(['git', 'add', data_file], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("No changes to commit")
            return True
        
        # Commit with timestamp and [skip ci] to avoid triggering GitHub Pages rebuild
        commit_msg = f"Update river stage data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [skip ci]"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Push to GitHub
        subprocess.run(['git', 'push'], check=True)
        
        print("Successfully pushed to GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR with git operation: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function to update river stage data."""
    print(f"\n{'='*60}")
    print(f"River Stage Data Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Read the latest reading
    print("Reading latest data from CSV...")
    new_reading = read_latest_river_stage(CSV_FILE_PATH)
    
    if new_reading is None:
        print("Failed to read new data. Exiting.")
        sys.exit(1)
    
    # Load existing data
    data_file_path = os.path.join(REPO_PATH, DATA_FILE)
    print(f"Loading existing data from {data_file_path}...")
    existing_data = load_existing_data(data_file_path)
    
    if existing_data is None:
        print("Failed to load existing data. Exiting.")
        sys.exit(1)
    
    # Update with new reading
    print("Updating data...")
    updated_data = update_data(existing_data, new_reading)
    
    # Save to file
    print("Saving updated data...")
    if not save_data(updated_data, data_file_path):
        print("Failed to save data. Exiting.")
        sys.exit(1)
    
    # Commit and push to GitHub
    print("Pushing to GitHub...")
    if not git_commit_and_push(REPO_PATH, DATA_FILE):
        print("Failed to push to GitHub. Exiting.")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("Update completed successfully!")
    print(f"Current river stage: {new_reading['riverstage']} ft")
    print(f"Total readings: {len(updated_data['readings'])}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
