#!/usr/bin/env python3
"""
CSV to JSON Migration Tool
Imports all historical data from rx_data.csv into river_data.json
Run this ONCE to populate your JSON file with existing data
"""

import csv
import json
from datetime import datetime
import sys

def migrate_csv_to_json(csv_path, json_path):
    """
    Read all data from CSV and create the initial JSON file.
    """
    print(f"Reading data from {csv_path}...")
    
    readings = []
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse the data
                    iso_time = row['iso_time']
                    river_stage = float(row['riverstage'])
                    
                    # Convert to timestamp
                    dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
                    
                    reading = {
                        'timestamp': dt.isoformat(),
                        'riverstage': round(river_stage, 3),
                        'date_display': dt.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    readings.append(reading)
                    
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid row: {e}")
                    continue
        
        print(f"Successfully read {len(readings)} readings")
        
    except FileNotFoundError:
        print(f"ERROR: CSV file not found at {csv_path}")
        return False
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return False
    
    # Create the JSON structure
    data = {
        'site_name': 'Wabash River at Hutsonville Bridge',
        'units': 'feet',
        'flood_stages': {
            'action': 12,
            'flood': 16,
            'moderate': 24,
            'major': 28,
            'near_record': 29
        },
        'last_updated': datetime.now().isoformat(),
        'readings': readings
    }
    
    # Save to JSON
    try:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully wrote data to {json_path}")
        print(f"Total readings: {len(readings)}")
        
        if readings:
            print(f"First reading: {readings[0]['date_display']} - {readings[0]['riverstage']} ft")
            print(f"Last reading: {readings[-1]['date_display']} - {readings[-1]['riverstage']} ft")
        
        return True
        
    except Exception as e:
        print(f"ERROR writing JSON: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python3 migrate_csv_to_json.py <csv_file> <json_output>")
        print("\nExample:")
        print("  python3 migrate_csv_to_json.py /path/to/rx_data.csv data/river_data.json")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    json_path = sys.argv[2]
    
    print(f"\n{'='*60}")
    print("CSV to JSON Migration Tool")
    print(f"{'='*60}\n")
    
    success = migrate_csv_to_json(csv_path, json_path)
    
    if success:
        print(f"\n{'='*60}")
        print("Migration completed successfully!")
        print(f"{'='*60}\n")
    else:
        print("\nMigration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
