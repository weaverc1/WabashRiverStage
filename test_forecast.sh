#!/bin/bash
# Quick test script to verify forecast is working

echo "============================================================"
echo "Testing Hutsonville Forecast System"
echo "============================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "1. Fetching NOAA forecasts..."
python3 fetch_noaa_forecasts.py
echo ""

echo "2. Generating Hutsonville forecast..."
python3 generate_hutsonville_forecast.py
echo ""

echo "3. Checking forecast in data file..."
python3 << 'PYEOF'
import json
from datetime import datetime

with open('data/river_data.json', 'r') as f:
    data = json.load(f)

forecast = data.get('forecast', [])
if forecast:
    print(f"✓ Found {len(forecast)} forecast points:")
    for i, point in enumerate(forecast, 1):
        print(f"  Day {i}: {point['date_display']} → {point['riverstage']} ft")
    print(f"\n✓ Forecast generated: {data.get('forecast_generated', 'Unknown')}")
    print(f"✓ Method: {data.get('forecast_method', 'Unknown')}")
else:
    print("✗ No forecast data found")
PYEOF

echo ""
echo "============================================================"
echo "Test complete! Check your website - forecast should appear"
echo "as an orange dashed line continuing from the observed data."
echo "============================================================"
