#!/bin/bash
#
# Setup Script for NOAA Forecast Fetcher
# This script sets up automated fetching of NOAA river forecasts every 6 hours
#
# Usage: ./setup_noaa_cron.sh
#

set -e  # Exit on error

echo "=========================================="
echo "NOAA Forecast Fetcher - Cron Setup"
echo "=========================================="
echo ""

# Get the absolute path of the repository
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Repository directory: $REPO_DIR"
echo ""

# Create logs directory if it doesn't exist
LOGS_DIR="$REPO_DIR/logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "Creating logs directory: $LOGS_DIR"
    mkdir -p "$LOGS_DIR"
    echo "✓ Logs directory created"
else
    echo "✓ Logs directory already exists"
fi
echo ""

# Create the cron job entry
CRON_JOB="0 */6 * * * cd $REPO_DIR && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "fetch_noaa_forecasts.py"; then
    echo "⚠ Cron job already exists in your crontab"
    echo ""
    echo "Current NOAA forecast cron jobs:"
    crontab -l 2>/dev/null | grep "fetch_noaa_forecasts.py" || true
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entries
        crontab -l 2>/dev/null | grep -v "fetch_noaa_forecasts.py" | crontab -
        echo "✓ Removed old cron job"
    else
        echo "Setup cancelled. Cron job not modified."
        exit 0
    fi
fi

# Add the cron job
(crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
echo "✓ Cron job added successfully"
echo ""

# Display the installed cron job
echo "=========================================="
echo "Installed Cron Job:"
echo "=========================================="
echo "$CRON_JOB"
echo ""
echo "This will run every 6 hours at:"
echo "  - 12:00 AM (midnight)"
echo "  - 6:00 AM"
echo "  - 12:00 PM (noon)"
echo "  - 6:00 PM"
echo ""

# Test the Python script
echo "=========================================="
echo "Testing NOAA Forecast Fetcher..."
echo "=========================================="
if [ -f "$REPO_DIR/fetch_noaa_forecasts.py" ]; then
    cd "$REPO_DIR"
    if python3 fetch_noaa_forecasts.py; then
        echo ""
        echo "✓ Test successful! Forecast data fetched."
        echo ""
        if [ -f "$REPO_DIR/data/noaa_forecasts.json" ]; then
            echo "✓ Output file created: data/noaa_forecasts.json"
            FILE_SIZE=$(du -h "$REPO_DIR/data/noaa_forecasts.json" | cut -f1)
            echo "  File size: $FILE_SIZE"
        fi
    else
        echo ""
        echo "✗ Test failed. Please check the error messages above."
        echo "  You may need to install dependencies:"
        echo "    pip3 install requests"
        exit 1
    fi
else
    echo "✗ Error: fetch_noaa_forecasts.py not found in $REPO_DIR"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "The NOAA forecast fetcher is now scheduled to run every 6 hours."
echo ""
echo "Useful commands:"
echo "  - View cron jobs:  crontab -l"
echo "  - View logs:       tail -f $LOGS_DIR/noaa_fetch.log"
echo "  - Manual run:      cd $REPO_DIR && python3 fetch_noaa_forecasts.py"
echo "  - Remove cron:     crontab -e  (then delete the line)"
echo ""
echo "Log file location: $LOGS_DIR/noaa_fetch.log"
echo "Data file location: $REPO_DIR/data/noaa_forecasts.json"
echo ""
echo "Next scheduled run: Check with 'crontab -l'"
echo ""
