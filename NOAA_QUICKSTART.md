# NOAA Forecast Integration - Quick Start

## Quick Start (5 minutes)

### 1. Verify Dependencies
```bash
python3 -c "import requests" && echo "✓ Ready to go!" || echo "✗ Need to: pip install requests"
```

### 2. Run the Script
```bash
cd /home/user/WabashRiverStage
python3 fetch_noaa_forecasts.py
```

### 3. Check the Output
```bash
cat data/noaa_forecasts.json | head -30
```

### 4. Setup Automatic Updates (Optional)
```bash
# Edit crontab
crontab -e

# Add this line (runs every 30 minutes):
*/30 * * * * cd /home/user/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1

# Create log directory
mkdir -p logs
```

## What You Get

✓ **TERI3** (Terre Haute - Upstream) forecast data
✓ **RVTI3** (Riverton - Downstream) forecast data
✓ Current observed stage and flow
✓ Forecast stage and timing
✓ Flood category (no flooding, minor, moderate, major)
✓ Flood stage thresholds
✓ Long-range flood outlook with probabilities
✓ Historic crests for context

## Output File

**Location:** `/home/user/WabashRiverStage/data/noaa_forecasts.json`

**Key Data Points:**
```json
{
  "last_updated": "2025-11-05T16:31:22.729211",
  "gauges": {
    "TERI3": {
      "observed": {
        "stage": 3.72,
        "timestamp": "2025-11-05T15:30:00Z"
      },
      "forecast": {
        "stage": 4.6,
        "timestamp": "2025-11-08T12:00:00Z",
        "flood_category": "no_flooding"
      },
      "flood_stages": {
        "action": 11.5,
        "minor": 16.5,
        "moderate": 24.5,
        "major": 30
      }
    },
    "RVTI3": { /* similar structure */ }
  }
}
```

## Common Commands

```bash
# Run manually
python3 fetch_noaa_forecasts.py

# Test API connectivity
curl -s "https://api.water.noaa.gov/nwps/v1/gauges/TERI3" | head

# Check when file was last updated
stat data/noaa_forecasts.json

# Pretty print the JSON
cat data/noaa_forecasts.json | python3 -m json.tool | less

# Check for flooding forecast
python3 -c "import json; data=json.load(open('data/noaa_forecasts.json')); print('Flooding:', any(g['forecast']['flood_category'] != 'no_flooding' for g in data['gauges'].values() if g))"
```

## Integration Options

### Option 1: Standalone (Recommended)
Run as separate cron job from river data updates.

### Option 2: Import in update_river_data.py
```python
import fetch_noaa_forecasts

# After river data update
gauge_data = fetch_noaa_forecasts.fetch_all_gauges()
fetch_noaa_forecasts.save_forecast_data(gauge_data, "data/noaa_forecasts.json")
```

### Option 3: Shell Script Wrapper
```bash
#!/bin/bash
cd /home/user/WabashRiverStage
python3 update_river_data.py
python3 fetch_noaa_forecasts.py
```

## Troubleshooting

**Problem:** Script fails
**Solution:** Check logs, verify internet connection, test API with curl

**Problem:** Old data in JSON
**Solution:** Check cron is running, check file permissions

**Problem:** `requests` not found
**Solution:** `pip install requests`

## Need More Details?

See `NOAA_INTEGRATION_GUIDE.md` for comprehensive documentation.

## Quick Test

```bash
# One-liner to test everything
cd /home/user/WabashRiverStage && python3 fetch_noaa_forecasts.py && echo "✓ Script works!" && cat data/noaa_forecasts.json | python3 -m json.tool | head -20
```
