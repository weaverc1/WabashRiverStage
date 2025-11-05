#!/usr/bin/env python3
"""
NOAA NWPS Forecast Data Fetcher for Wabash River Gauges
Fetches forecast data from NOAA National Water Prediction Service API
for upstream (TERI3) and downstream (RVTI3) gauges.

Run this script every 15-60 minutes to keep forecast data current.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Optional, List
import logging

# Attempt to import requests, provide helpful error if missing
try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Configuration
NOAA_API_BASE = "https://api.water.noaa.gov/nwps/v1/gauges"
GAUGES = {
    "TERI3": {
        "name": "Wabash River at Terre Haute",
        "location": "Upstream",
        "description": "US Hwy 150 Eastbound"
    },
    "RVTI3": {
        "name": "Wabash River at Riverton",
        "location": "Downstream",
        "description": "Below Hutsonville"
    }
}

# Output configuration
OUTPUT_FILE = "data/noaa_forecasts.json"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

# API request configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_gauge_data(gauge_id: str, retry_count: int = 0) -> Optional[Dict]:
    """
    Fetch data for a specific gauge from NOAA API with retry logic.

    Args:
        gauge_id: The gauge identifier (e.g., 'TERI3')
        retry_count: Current retry attempt (internal use)

    Returns:
        Dictionary containing gauge data, or None if fetch failed
    """
    url = f"{NOAA_API_BASE}/{gauge_id}"

    try:
        logger.info(f"Fetching data for gauge {gauge_id} (attempt {retry_count + 1}/{MAX_RETRIES})...")

        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Successfully fetched data for {gauge_id}")
        return data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {gauge_id}")
        if retry_count < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return fetch_gauge_data(gauge_id, retry_count + 1)
        return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {gauge_id}: {e}")
        if retry_count < MAX_RETRIES - 1 and e.response.status_code >= 500:
            # Retry on server errors (5xx)
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return fetch_gauge_data(gauge_id, retry_count + 1)
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {gauge_id}: {e}")
        if retry_count < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return fetch_gauge_data(gauge_id, retry_count + 1)
        return None

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response for {gauge_id}: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error fetching {gauge_id}: {e}")
        return None


def parse_gauge_data(raw_data: Dict, gauge_id: str) -> Optional[Dict]:
    """
    Parse and extract relevant information from raw NOAA API response.

    Args:
        raw_data: Raw JSON response from NOAA API
        gauge_id: The gauge identifier

    Returns:
        Parsed dictionary with relevant forecast data
    """
    try:
        # Extract observed data
        observed = raw_data.get('status', {}).get('observed', {})
        observed_data = {
            'stage': observed.get('primary'),
            'stage_unit': observed.get('primaryUnit', 'ft'),
            'flow': observed.get('secondary'),
            'flow_unit': observed.get('secondaryUnit'),
            'flood_category': observed.get('floodCategory', 'unknown'),
            'timestamp': observed.get('validTime'),
            'time_display': format_timestamp(observed.get('validTime'))
        }

        # Extract forecast data
        forecast = raw_data.get('status', {}).get('forecast', {})
        forecast_data = {
            'stage': forecast.get('primary'),
            'stage_unit': forecast.get('primaryUnit', 'ft'),
            'flow': forecast.get('secondary'),
            'flow_unit': forecast.get('secondaryUnit'),
            'flood_category': forecast.get('floodCategory', 'unknown'),
            'timestamp': forecast.get('validTime'),
            'time_display': format_timestamp(forecast.get('validTime'))
        }

        # Extract flood stage thresholds
        flood_info = raw_data.get('flood', {})
        categories = flood_info.get('categories', {})
        flood_stages = {
            'action': categories.get('action', {}).get('stage'),
            'minor': categories.get('minor', {}).get('stage'),
            'moderate': categories.get('moderate', {}).get('stage'),
            'major': categories.get('major', {}).get('stage'),
            'units': flood_info.get('stageUnits', 'ft')
        }

        # Extract long-range outlook (LRO)
        lro = flood_info.get('lro', {})
        long_range_outlook = {
            'minor_flood_chance': lro.get('minorCS', 'N/A'),
            'moderate_flood_chance': lro.get('moderateCS', 'N/A'),
            'major_flood_chance': lro.get('majorCS', 'N/A'),
            'produced_time': lro.get('producedTime'),
            'interval': lro.get('interval', 'N/A'),  # e.g., "NDJ" = Nov-Dec-Jan
            'interval_display': format_lro_interval(lro.get('interval'))
        }

        # Extract location information
        location = {
            'name': raw_data.get('name', ''),
            'state': raw_data.get('state', {}).get('abbreviation', ''),
            'county': raw_data.get('county', ''),
            'latitude': raw_data.get('latitude'),
            'longitude': raw_data.get('longitude'),
            'timezone': raw_data.get('timeZone', ''),
            'rfc': raw_data.get('rfc', {}).get('name', ''),
            'rfc_abbrev': raw_data.get('rfc', {}).get('abbreviation', '')
        }

        # Extract recent historic crests (top 5)
        crests = flood_info.get('crests', {}).get('historic', [])
        historic_crests = []
        for crest in crests[:5]:
            historic_crests.append({
                'date': crest.get('occurredTime'),
                'date_display': format_timestamp(crest.get('occurredTime'), date_only=True),
                'stage': crest.get('stage'),
                'flow': crest.get('flow') if crest.get('flow', 0) > 0 else None
            })

        # Compile final data structure
        parsed = {
            'gauge_id': gauge_id,
            'location': location,
            'observed': observed_data,
            'forecast': forecast_data,
            'flood_stages': flood_stages,
            'long_range_outlook': long_range_outlook,
            'historic_crests': historic_crests,
            'forecast_reliability': raw_data.get('forecastReliability', 'N/A'),
            'in_service': raw_data.get('inService', {}).get('enabled', True),
            'service_message': raw_data.get('inService', {}).get('message', '')
        }

        return parsed

    except Exception as e:
        logger.error(f"Error parsing data for {gauge_id}: {e}")
        return None


def format_timestamp(timestamp: Optional[str], date_only: bool = False) -> str:
    """
    Format ISO timestamp to human-readable format.

    Args:
        timestamp: ISO format timestamp string
        date_only: If True, return only date (YYYY-MM-DD)

    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if date_only:
            return dt.strftime('%Y-%m-%d')
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return timestamp


def format_lro_interval(interval: Optional[str]) -> str:
    """
    Convert LRO interval code to human-readable format.

    Args:
        interval: Interval code (e.g., "NDJ", "DJF", "JFM")

    Returns:
        Human-readable interval string
    """
    if not interval:
        return "N/A"

    month_map = {
        'J': 'Jan', 'F': 'Feb', 'M': 'Mar', 'A': 'Apr',
        'M': 'May', 'J': 'Jun', 'J': 'Jul', 'A': 'Aug',
        'S': 'Sep', 'O': 'Oct', 'N': 'Nov', 'D': 'Dec'
    }

    # Handle standard 3-letter codes
    if len(interval) == 3:
        try:
            months = [month_map.get(c, c) for c in interval]
            return f"{months[0]}-{months[1]}-{months[2]}"
        except Exception:
            return interval

    return interval


def get_flood_category_display(category: str) -> str:
    """
    Convert flood category code to display text.

    Args:
        category: Category code (e.g., 'no_flooding', 'minor', 'moderate', 'major')

    Returns:
        Display text for category
    """
    category_map = {
        'no_flooding': 'No Flooding',
        'minor': 'Minor Flooding',
        'moderate': 'Moderate Flooding',
        'major': 'Major Flooding',
        'action': 'Action Stage',
        'unknown': 'Unknown'
    }
    return category_map.get(category, category.replace('_', ' ').title())


def fetch_all_gauges() -> Dict[str, Optional[Dict]]:
    """
    Fetch and parse data for all configured gauges.

    Returns:
        Dictionary mapping gauge IDs to parsed data
    """
    results = {}

    for gauge_id, gauge_info in GAUGES.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {gauge_info['name']} ({gauge_id})")
        logger.info(f"{'='*60}")

        # Fetch raw data
        raw_data = fetch_gauge_data(gauge_id)

        if raw_data is None:
            logger.warning(f"Failed to fetch data for {gauge_id}")
            results[gauge_id] = None
            continue

        # Parse data
        parsed_data = parse_gauge_data(raw_data, gauge_id)

        if parsed_data is None:
            logger.warning(f"Failed to parse data for {gauge_id}")
            results[gauge_id] = None
            continue

        # Add metadata from configuration
        parsed_data['metadata'] = gauge_info
        results[gauge_id] = parsed_data

        # Log summary
        obs = parsed_data.get('observed', {})
        fcst = parsed_data.get('forecast', {})
        logger.info(f"  Observed: {obs.get('stage')} {obs.get('stage_unit')} at {obs.get('time_display')}")
        logger.info(f"  Forecast: {fcst.get('stage')} {fcst.get('stage_unit')} at {fcst.get('time_display')}")
        logger.info(f"  Flood Category: {get_flood_category_display(fcst.get('flood_category', 'unknown'))}")

    return results


def save_forecast_data(data: Dict[str, Optional[Dict]], output_path: str) -> bool:
    """
    Save forecast data to JSON file.

    Args:
        data: Dictionary of parsed gauge data
        output_path: Path to output JSON file

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Create output structure
        output = {
            'last_updated': datetime.now().isoformat(),
            'last_updated_display': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'NOAA National Water Prediction Service',
            'api_base': NOAA_API_BASE,
            'gauges': data,
            'fetch_status': {
                'total_gauges': len(GAUGES),
                'successful': sum(1 for v in data.values() if v is not None),
                'failed': sum(1 for v in data.values() if v is None)
            }
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to file with pretty formatting
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"\nData saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {e}")
        return False


def main():
    """Main function to fetch and save NOAA forecast data."""
    logger.info(f"\n{'='*60}")
    logger.info(f"NOAA NWPS Forecast Data Fetch - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}\n")

    # Fetch data for all gauges
    gauge_data = fetch_all_gauges()

    # Check if we got any data
    if all(v is None for v in gauge_data.values()):
        logger.error("\nFailed to fetch data for all gauges. Exiting.")
        sys.exit(1)

    # Save to file
    output_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    if not save_forecast_data(gauge_data, output_path):
        logger.error("Failed to save forecast data. Exiting.")
        sys.exit(1)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("Fetch completed successfully!")
    logger.info(f"Gauges processed: {len(GAUGES)}")
    logger.info(f"Successful: {sum(1 for v in gauge_data.values() if v is not None)}")
    logger.info(f"Failed: {sum(1 for v in gauge_data.values() if v is None)}")
    logger.info(f"Output file: {output_path}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
