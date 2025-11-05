#!/bin/bash
# Setup script for Hutsonville Forecast Integration
# Run this after pulling the latest changes

set -e  # Exit on any error

echo "============================================================"
echo "Hutsonville Forecast Setup Script"
echo "============================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Step 1: Check Python3 is available
echo "Step 1: Checking Python3..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Step 2: Check required Python packages
echo "Step 2: Checking Python dependencies..."
MISSING_PACKAGES=""

for package in requests; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES="$MISSING_PACKAGES $package"
    fi
done

if [ -n "$MISSING_PACKAGES" ]; then
    echo "Installing missing packages:$MISSING_PACKAGES"
    pip3 install $MISSING_PACKAGES
    echo "✓ Packages installed"
else
    echo "✓ All required packages present (requests)"
fi
echo ""

# Step 3: Make scripts executable
echo "Step 3: Making scripts executable..."
chmod +x generate_hutsonville_forecast.py
chmod +x fetch_noaa_forecasts.py
echo "✓ Scripts are executable"
echo ""

# Step 4: Test NOAA forecast fetch
echo "Step 4: Fetching NOAA forecast data..."
python3 fetch_noaa_forecasts.py
if [ $? -eq 0 ]; then
    echo "✓ NOAA forecast fetch successful"
else
    echo "ERROR: Failed to fetch NOAA forecasts"
    exit 1
fi
echo ""

# Step 5: Generate Hutsonville forecast
echo "Step 5: Generating Hutsonville forecast..."
python3 generate_hutsonville_forecast.py
if [ $? -eq 0 ]; then
    echo "✓ Hutsonville forecast generated successfully"
else
    echo "ERROR: Failed to generate Hutsonville forecast"
    exit 1
fi
echo ""

# Step 6: Check if data files exist
echo "Step 6: Verifying data files..."
if [ -f "data/noaa_forecasts.json" ]; then
    echo "✓ data/noaa_forecasts.json exists"
else
    echo "ERROR: data/noaa_forecasts.json not found"
    exit 1
fi

if [ -f "data/river_data.json" ]; then
    echo "✓ data/river_data.json exists"
else
    echo "ERROR: data/river_data.json not found"
    exit 1
fi
echo ""

# Step 7: Setup/Update cron jobs
echo "Step 7: Setting up cron jobs..."
echo ""
echo "Current crontab entries:"
crontab -l 2>/dev/null | grep -E "(fetch_noaa|generate_hutsonville|update_river)" || echo "(none found)"
echo ""

# Create a new cron entry
CRON_TEMP=$(mktemp)
crontab -l 2>/dev/null > "$CRON_TEMP" || true

# Remove old forecast-related entries if they exist
sed -i '/fetch_noaa_forecasts.py/d' "$CRON_TEMP"
sed -i '/generate_hutsonville_forecast.py/d' "$CRON_TEMP"

# Add new entries (every 30 minutes, staggered)
echo "" >> "$CRON_TEMP"
echo "# Fetch NOAA forecasts every 30 minutes at :05 and :35" >> "$CRON_TEMP"
echo "5,35 * * * * cd $SCRIPT_DIR && /usr/bin/python3 fetch_noaa_forecasts.py >> /tmp/noaa_fetch.log 2>&1" >> "$CRON_TEMP"
echo "" >> "$CRON_TEMP"
echo "# Generate Hutsonville forecast every 30 minutes at :10 and :40 (after NOAA fetch)" >> "$CRON_TEMP"
echo "10,40 * * * * cd $SCRIPT_DIR && /usr/bin/python3 generate_hutsonville_forecast.py >> /tmp/forecast_gen.log 2>&1" >> "$CRON_TEMP"

# Install the new crontab
crontab "$CRON_TEMP"
rm "$CRON_TEMP"

echo "✓ Cron jobs configured:"
echo "  - NOAA forecast fetch: Every 30 minutes (:05, :35)"
echo "  - Hutsonville forecast: Every 30 minutes (:10, :40)"
echo ""

# Step 8: Show the new crontab
echo "Step 8: Verifying crontab..."
echo ""
crontab -l | grep -E "(fetch_noaa|generate_hutsonville)" || echo "ERROR: Cron entries not found"
echo ""

# Step 9: Check forecast in river_data.json
echo "Step 9: Checking forecast data in river_data.json..."
if python3 -c "import json; data=json.load(open('data/river_data.json')); print(f\"✓ Forecast points: {len(data.get('forecast', []))}\")" 2>/dev/null; then
    python3 -c "import json; data=json.load(open('data/river_data.json')); forecast=data.get('forecast', []); print(f\"✓ Forecast method: {data.get('forecast_method', 'N/A')}\") if forecast else None"
else
    echo "⚠ Could not verify forecast data"
fi
echo ""

# Step 10: Summary
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "✓ NOAA forecasts will update every 30 minutes"
echo "✓ Hutsonville forecasts will generate every 30 minutes"
echo "✓ Charts will show forecast line automatically"
echo ""
echo "Logs:"
echo "  NOAA fetch: /tmp/noaa_fetch.log"
echo "  Forecast generation: /tmp/forecast_gen.log"
echo ""
echo "Manual commands:"
echo "  Fetch NOAA data:    python3 fetch_noaa_forecasts.py"
echo "  Generate forecast:  python3 generate_hutsonville_forecast.py"
echo "  View forecast logs: tail -f /tmp/forecast_gen.log"
echo ""
echo "Next steps:"
echo "  1. Wait a few minutes for the next cron run"
echo "  2. Check the website - you should see an orange dashed forecast line"
echo "  3. Monitor logs if needed: tail -f /tmp/forecast_gen.log"
echo ""
echo "============================================================"
