#!/usr/bin/env python3
"""
Generate Hutsonville River Stage Forecast
Uses upstream (TERI3) and downstream (RVTI3) NOAA forecasts to estimate
Hutsonville forecast with time lag adjustment.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# Configuration
NOAA_FORECAST_FILE = "data/noaa_forecasts.json"
RIVER_DATA_FILE = "data/river_data.json"
OUTPUT_FILE = "data/river_data.json"

# Timing parameters
TERI3_TO_HUTSONVILLE_LAG_HOURS = 18  # ~75 miles, estimate 18 hour lag
HUTSONVILLE_TO_RVTI3_LAG_HOURS = 6   # ~15 miles, estimate 6 hour lag

# Stage scaling factor - Hutsonville tends to be slightly lower than RVTI3
# Based on relative flood stages and geography
STAGE_SCALING = 0.98


def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON file safely."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}")
        return None


def save_json_file(filepath: str, data: Dict) -> bool:
    """Save data to JSON file with formatting."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


def estimate_hutsonville_stage(teri3_stage: float, rvti3_stage: float,
                                position_weight: float = 0.85) -> float:
    """
    Estimate Hutsonville stage based on upstream (TERI3) and downstream (RVTI3).

    Args:
        teri3_stage: Upstream stage in feet
        rvti3_stage: Downstream stage in feet
        position_weight: Weight towards downstream (0=all upstream, 1=all downstream)
                        Default 0.85 accounts for Hutsonville being closer to RVTI3

    Returns:
        Estimated Hutsonville stage in feet
    """
    # Weighted average favoring downstream gauge (Hutsonville is closer to RVTI3)
    interpolated = (1 - position_weight) * teri3_stage + position_weight * rvti3_stage

    # Apply scaling factor
    hutsonville_stage = interpolated * STAGE_SCALING

    return round(hutsonville_stage, 2)


def generate_forecast_points(noaa_data: Dict, current_time: datetime,
                             current_hutsonville_stage: float,
                             num_hours: int = 120) -> List[Dict]:
    """
    Generate forecast data points for Hutsonville.

    Args:
        noaa_data: NOAA forecast data from noaa_forecasts.json
        current_time: Current timestamp
        current_hutsonville_stage: Current observed Hutsonville stage
        num_hours: Number of hours to forecast (default 120 = 5 days)

    Returns:
        List of forecast point dictionaries
    """
    forecasts = []

    # Get NOAA forecasts
    gauges = noaa_data.get('gauges', {})
    teri3 = gauges.get('TERI3', {})
    rvti3 = gauges.get('RVTI3', {})

    if not teri3 or not rvti3:
        print("Warning: NOAA forecast data incomplete")
        return []

    # Get current observed stages
    teri3_current = teri3.get('observed', {}).get('stage')
    rvti3_current = rvti3.get('observed', {}).get('stage')

    # Get forecast stages
    teri3_forecast = teri3.get('forecast', {}).get('stage')
    rvti3_forecast = rvti3.get('forecast', {}).get('stage')

    # Get forecast timestamps
    teri3_forecast_time_str = teri3.get('forecast', {}).get('timestamp')
    rvti3_forecast_time_str = rvti3.get('forecast', {}).get('timestamp')

    if not all([teri3_current, rvti3_current, teri3_forecast, rvti3_forecast]):
        print("Warning: Missing required forecast data")
        return []

    # Parse forecast times
    teri3_forecast_time = datetime.fromisoformat(teri3_forecast_time_str.replace('Z', '+00:00'))
    rvti3_forecast_time = datetime.fromisoformat(rvti3_forecast_time_str.replace('Z', '+00:00'))

    # Adjust forecast times for Hutsonville's position
    # Hutsonville is between the two gauges
    hutsonville_peak_time = teri3_forecast_time + timedelta(hours=TERI3_TO_HUTSONVILLE_LAG_HOURS)

    # Estimate peak Hutsonville stage based on upstream/downstream forecasts
    peak_stage = estimate_hutsonville_stage(teri3_forecast, rvti3_forecast)

    print(f"   Forecasted peak: {peak_stage} ft at {hutsonville_peak_time.strftime('%Y-%m-%d %H:%M')}")

    # Add initial forecast point at current time for seamless transition
    # This eliminates visual gap on chart
    current_time_naive = current_time.replace(tzinfo=None)
    forecasts.append({
        'timestamp': current_time_naive.isoformat(),
        'riverstage': current_hutsonville_stage,
        'date_display': current_time_naive.strftime('%Y-%m-%d %H:%M:%S'),
        'is_forecast': True
    })

    # Generate forecast points every 6 hours for better continuity
    for hours in range(6, num_hours + 1, 6):
        forecast_time = current_time + timedelta(hours=hours)

        # Calculate stage based on position in forecast timeline
        if forecast_time < hutsonville_peak_time:
            # Rising stage - interpolate from CURRENT OBSERVED to peak
            time_to_peak = (hutsonville_peak_time - current_time).total_seconds()
            time_elapsed = (forecast_time - current_time).total_seconds()
            progress = min(1.0, time_elapsed / time_to_peak) if time_to_peak > 0 else 1.0

            # Interpolate from current observed stage to forecasted peak
            forecast_stage = current_hutsonville_stage + (peak_stage - current_hutsonville_stage) * progress
        else:
            # At or past peak - use peak or slight decline
            # Apply slight recession after peak
            hours_after_peak = (forecast_time - hutsonville_peak_time).total_seconds() / 3600
            recession_factor = 0.99 ** (hours_after_peak / 6)  # ~1% decline per 6 hours
            forecast_stage = peak_stage * recession_factor

        # Remove timezone info for consistency with observed data
        forecast_time_naive = forecast_time.replace(tzinfo=None)

        forecasts.append({
            'timestamp': forecast_time_naive.isoformat(),
            'riverstage': round(forecast_stage, 2),
            'date_display': forecast_time_naive.strftime('%Y-%m-%d %H:%M:%S'),
            'is_forecast': True
        })

    return forecasts


def main():
    """Main function to generate and save Hutsonville forecast."""
    print("=" * 60)
    print("Hutsonville River Stage Forecast Generator")
    print("=" * 60)

    # Load NOAA forecast data
    print("\n1. Loading NOAA forecast data...")
    noaa_data = load_json_file(NOAA_FORECAST_FILE)
    if not noaa_data:
        print("Error: Could not load NOAA forecast data")
        return 1

    print(f"   ✓ Loaded NOAA forecasts (updated: {noaa_data.get('last_updated_display', 'unknown')})")

    # Load current river data
    print("\n2. Loading Hutsonville observed data...")
    river_data = load_json_file(RIVER_DATA_FILE)
    if not river_data:
        print("Error: Could not load river data")
        return 1

    num_readings = len(river_data.get('readings', []))
    print(f"   ✓ Loaded {num_readings} observed readings")

    # Get current time from latest reading
    latest_reading = river_data['readings'][-1] if river_data.get('readings') else None
    if not latest_reading:
        print("Error: No observed readings found")
        return 1

    current_time = datetime.fromisoformat(latest_reading['timestamp'])
    # Make timezone-aware if not already
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    current_stage = latest_reading['riverstage']
    print(f"   ✓ Latest reading: {latest_reading['date_display']} ({current_stage} ft)")

    # Generate forecast
    print("\n3. Generating Hutsonville forecast...")
    print(f"   Starting from current stage: {current_stage} ft")
    forecast_points = generate_forecast_points(noaa_data, current_time, current_stage, num_hours=120)

    if not forecast_points:
        print("Error: Could not generate forecast")
        return 1

    print(f"   ✓ Generated {len(forecast_points)} forecast points")

    # Display forecast summary
    print("\n4. Forecast Summary:")
    for i, point in enumerate(forecast_points[:8], 1):  # Show first 8 points (2 days)
        print(f"   +{i*6}hrs: {point['date_display']} → {point['riverstage']} ft")

    # Add forecast to river data
    river_data['forecast'] = forecast_points
    river_data['forecast_generated'] = datetime.now().isoformat()
    river_data['forecast_method'] = 'Interpolation from TERI3/RVTI3 NOAA forecasts'

    # Save updated data
    print(f"\n5. Saving forecast to {OUTPUT_FILE}...")
    if save_json_file(OUTPUT_FILE, river_data):
        print("   ✓ Forecast saved successfully")
    else:
        print("   ✗ Error saving forecast")
        return 1

    print("\n" + "=" * 60)
    print("Forecast generation complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
