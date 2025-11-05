# NOAA NWPS API Integration Guide

## Overview

This guide provides complete documentation for the `fetch_noaa_forecasts.py` script, which fetches river forecast data from the NOAA National Water Prediction Service (NWPS) API for upstream and downstream gauges on the Wabash River.

## Files

- **`fetch_noaa_forecasts.py`** - Main Python script to fetch forecast data
- **`data/noaa_forecasts.json`** - Output file containing latest forecast data

## Features

- Fetches forecast data for TERI3 (Terre Haute - Upstream) and RVTI3 (Riverton - Downstream)
- Extracts comprehensive information:
  - Current observed stage and flow
  - Forecast stage and flow with timestamps
  - Flood category (current and forecast)
  - Flood stage thresholds (action, minor, moderate, major)
  - Long-range outlook (LRO) with flood probabilities
  - Top 5 historic crests for reference
- Robust error handling with automatic retry logic
- Detailed logging for troubleshooting
- Production-ready code following PEP 8 style guidelines

## Dependencies

The script requires Python 3.x and the `requests` library:

```bash
# Check if requests is installed
python3 -c "import requests; print('requests is installed')"

# Install if needed
pip install requests
# or
pip3 install requests
```

## Usage

### Basic Usage

Run the script manually:

```bash
# From the repository root
cd /home/user/WabashRiverStage/
python3 fetch_noaa_forecasts.py
```

Or make it executable and run directly:

```bash
chmod +x fetch_noaa_forecasts.py
./fetch_noaa_forecasts.py
```

### Expected Output

The script will:
1. Fetch data from NOAA API for both gauges (TERI3 and RVTI3)
2. Parse and format the data
3. Save to `data/noaa_forecasts.json`
4. Display summary information in the console

Example console output:
```
============================================================
NOAA NWPS Forecast Data Fetch - 2025-11-05 16:31:21
============================================================

============================================================
Processing Wabash River at Terre Haute (TERI3)
============================================================
Fetching data for gauge TERI3 (attempt 1/3)...
Successfully fetched data for TERI3
  Observed: 3.72 ft at 2025-11-05 15:30:00 UTC
  Forecast: 4.6 ft at 2025-11-08 12:00:00 UTC
  Flood Category: No Flooding

[... similar output for RVTI3 ...]

Data saved to /home/user/WabashRiverStage/data/noaa_forecasts.json

============================================================
Fetch completed successfully!
Gauges processed: 2
Successful: 2
Failed: 0
Output file: /home/user/WabashRiverStage/data/noaa_forecasts.json
============================================================
```

## Output JSON Structure

The `data/noaa_forecasts.json` file contains:

```json
{
  "last_updated": "ISO timestamp",
  "last_updated_display": "Human-readable timestamp",
  "source": "NOAA National Water Prediction Service",
  "api_base": "API URL",
  "gauges": {
    "TERI3": {
      "gauge_id": "TERI3",
      "location": {
        "name": "Gauge name",
        "state": "State code",
        "county": "County name",
        "latitude": float,
        "longitude": float,
        "timezone": "Timezone",
        "rfc": "River Forecast Center name",
        "rfc_abbrev": "RFC abbreviation"
      },
      "observed": {
        "stage": float,
        "stage_unit": "ft",
        "flow": float,
        "flow_unit": "kcfs",
        "flood_category": "no_flooding|minor|moderate|major",
        "timestamp": "ISO timestamp",
        "time_display": "Human-readable timestamp"
      },
      "forecast": {
        "stage": float,
        "stage_unit": "ft",
        "flow": float,
        "flow_unit": "kcfs",
        "flood_category": "no_flooding|minor|moderate|major",
        "timestamp": "ISO timestamp",
        "time_display": "Human-readable timestamp"
      },
      "flood_stages": {
        "action": float,
        "minor": float,
        "moderate": float,
        "major": float,
        "units": "ft"
      },
      "long_range_outlook": {
        "minor_flood_chance": "Probability (0-1 or text)",
        "moderate_flood_chance": "Probability (0-1 or text)",
        "major_flood_chance": "Probability (0-1 or text)",
        "produced_time": "ISO timestamp",
        "interval": "Code (e.g., NDJ)",
        "interval_display": "Human-readable (e.g., Nov-Dec-Jan)"
      },
      "historic_crests": [
        {
          "date": "ISO timestamp",
          "date_display": "YYYY-MM-DD",
          "stage": float,
          "flow": float or null
        }
      ],
      "forecast_reliability": "Description text",
      "in_service": true/false,
      "service_message": "Message if gauge is offline",
      "metadata": {
        "name": "Short name",
        "location": "Upstream|Downstream",
        "description": "Description"
      }
    },
    "RVTI3": { /* Same structure as TERI3 */ }
  },
  "fetch_status": {
    "total_gauges": 2,
    "successful": 2,
    "failed": 0
  }
}
```

## Scheduling

### Recommended Schedule

- **Production:** Run every 30-60 minutes
- **During flood events:** Run every 15-30 minutes
- **Off-season:** Run every 60 minutes

NOAA updates forecasts regularly, but not continuously. Running more frequently than every 15 minutes provides minimal benefit.

### Linux Cron Setup

Edit crontab:
```bash
crontab -e
```

Add one of these entries:

```bash
# Run every 30 minutes
*/30 * * * * cd /home/user/WabashRiverStage && /usr/bin/python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1

# Run every hour at 5 minutes past
5 * * * * cd /home/user/WabashRiverStage && /usr/bin/python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1

# Run every 15 minutes (flood season)
*/15 * * * * cd /home/user/WabashRiverStage && /usr/bin/python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

Create log directory:
```bash
mkdir -p /home/user/WabashRiverStage/logs
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "Daily" then repeat every 30 minutes)
4. Action: Start a program
   - Program: `C:\Python39\python.exe` (adjust path)
   - Arguments: `fetch_noaa_forecasts.py`
   - Start in: `C:\path\to\WabashRiverStage`

## Integration with Existing Update Script

### Option 1: Import and Call as Module

Add to `update_river_data.py`:

```python
# At the top of update_river_data.py
import fetch_noaa_forecasts

# In main() function, after saving river data:
try:
    print("\nFetching NOAA forecast data...")
    gauge_data = fetch_noaa_forecasts.fetch_all_gauges()
    output_path = os.path.join(REPO_PATH, "data/noaa_forecasts.json")
    fetch_noaa_forecasts.save_forecast_data(gauge_data, output_path)
    print("NOAA forecast data updated successfully")
except Exception as e:
    print(f"Warning: Failed to update NOAA forecasts: {e}")
    # Continue anyway - don't fail the entire update
```

### Option 2: Run as Separate Process

Add to `update_river_data.py`:

```python
import subprocess

# In main() function, after git push:
try:
    print("\nFetching NOAA forecast data...")
    result = subprocess.run(
        ['python3', 'fetch_noaa_forecasts.py'],
        cwd=REPO_PATH,
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode == 0:
        print("NOAA forecast data updated successfully")
    else:
        print(f"Warning: NOAA fetch failed: {result.stderr}")
except Exception as e:
    print(f"Warning: Error running NOAA fetch: {e}")
```

### Option 3: Separate Cron Jobs (Recommended)

Keep them as separate cron jobs with different schedules:

```bash
# River stage data - every 15 minutes
*/15 * * * * cd /home/user/WabashRiverStage && python3 update_river_data.py >> logs/update.log 2>&1

# NOAA forecasts - every 30 minutes
*/30 * * * * cd /home/user/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

**Advantages of separate jobs:**
- Independent failure handling
- Different update frequencies
- Easier to debug
- Less risk of one failure blocking the other

## Configuration

Edit configuration variables at the top of `fetch_noaa_forecasts.py`:

```python
# API Configuration
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

# Output Configuration
OUTPUT_FILE = "data/noaa_forecasts.json"

# Request Configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries
```

### Adding Additional Gauges

To monitor additional gauges, add them to the `GAUGES` dictionary:

```python
GAUGES = {
    "TERI3": { ... },
    "RVTI3": { ... },
    "NEWID": {
        "name": "Gauge Name",
        "location": "Description",
        "description": "Additional details"
    }
}
```

Find gauge IDs at: https://water.noaa.gov/

## Error Handling

The script includes comprehensive error handling:

1. **Network Errors:** Automatic retry with exponential backoff (up to 3 attempts)
2. **Timeout:** 30-second timeout per request
3. **HTTP Errors:** Logged with details, retries on 5xx server errors
4. **Invalid JSON:** Caught and logged
5. **Partial Failures:** If one gauge fails, the other is still saved

### Common Issues

**Issue:** `requests` module not found
```
Solution: pip install requests
```

**Issue:** Permission denied
```
Solution: chmod +x fetch_noaa_forecasts.py
```

**Issue:** API timeout
```
Solution: Script automatically retries. Check network connection.
```

**Issue:** All gauges failed
```
Solution: Check if NOAA API is operational: curl https://api.water.noaa.gov/nwps/v1/gauges/TERI3
```

## API Rate Limiting

The NOAA NWPS API does not have strict published rate limits, but best practices:
- Wait at least 5 seconds between requests (script does this automatically)
- Don't exceed 1 request per minute per gauge
- Use reasonable retry delays (5 seconds)

The script fetches 2 gauges per run, which completes in ~1-2 seconds total.

## Monitoring and Logging

### Log Levels

The script uses Python's `logging` module with INFO level by default. To see more details:

```python
# In fetch_noaa_forecasts.py, change:
logging.basicConfig(level=logging.DEBUG)  # For verbose output
```

### Monitor for Failures

Check if data is being updated:

```bash
# Check last update time
stat data/noaa_forecasts.json

# Check file contents
head -20 data/noaa_forecasts.json

# Monitor logs (if using cron with log file)
tail -f logs/noaa_fetch.log
```

### Alert on Failures

Create a wrapper script `run_noaa_fetch.sh`:

```bash
#!/bin/bash
cd /home/user/WabashRiverStage

# Run the script
python3 fetch_noaa_forecasts.py

# Check exit code
if [ $? -ne 0 ]; then
    echo "NOAA fetch failed at $(date)" | mail -s "NOAA Fetch Failure" admin@example.com
fi
```

## Testing

### Test API Connectivity

```bash
# Test TERI3 gauge
curl -s "https://api.water.noaa.gov/nwps/v1/gauges/TERI3" | python3 -m json.tool | head

# Test RVTI3 gauge
curl -s "https://api.water.noaa.gov/nwps/v1/gauges/RVTI3" | python3 -m json.tool | head
```

### Test Script

```bash
# Dry run with verbose output
python3 fetch_noaa_forecasts.py

# Check output file
cat data/noaa_forecasts.json | python3 -m json.tool

# Validate JSON
python3 -m json.tool data/noaa_forecasts.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## Frontend Integration

The JSON output is designed for easy frontend consumption. Example JavaScript:

```javascript
// Fetch the forecast data
fetch('data/noaa_forecasts.json')
  .then(response => response.json())
  .then(data => {
    // Get TERI3 (upstream) forecast
    const teri3 = data.gauges.TERI3;
    console.log(`Upstream forecast: ${teri3.forecast.stage} ${teri3.forecast.stage_unit}`);
    console.log(`Flood category: ${teri3.forecast.flood_category}`);

    // Get RVTI3 (downstream) forecast
    const rvti3 = data.gauges.RVTI3;
    console.log(`Downstream forecast: ${rvti3.forecast.stage} ${rvti3.forecast.stage_unit}`);

    // Check if flooding expected
    if (teri3.forecast.flood_category !== 'no_flooding') {
      alert('Flooding forecast at upstream gauge!');
    }

    // Display long-range outlook
    const lro = teri3.long_range_outlook;
    console.log(`Minor flood chance (${lro.interval_display}): ${lro.minor_flood_chance}`);
  });
```

## Support and Resources

- **NOAA API Documentation:** https://api.water.noaa.gov/nwps/v1/docs/
- **NOAA Water Prediction Service:** https://water.noaa.gov/
- **TERI3 Gauge Page:** https://water.noaa.gov/gauges/TERI3
- **RVTI3 Gauge Page:** https://water.noaa.gov/gauges/RVTI3
- **Ohio River Forecast Center:** https://www.weather.gov/ohrfc/

## Changelog

### Version 1.0 (2025-11-05)
- Initial release
- Support for TERI3 and RVTI3 gauges
- Comprehensive error handling
- Retry logic with backoff
- Detailed logging
- JSON output for frontend consumption
- Historic crests and long-range outlook support
