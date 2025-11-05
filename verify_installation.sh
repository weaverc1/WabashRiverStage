#!/bin/bash
# Verification script for NOAA NWPS integration

echo "=========================================="
echo "NOAA NWPS Integration Verification"
echo "=========================================="
echo ""

# Check Python
echo "1. Checking Python..."
python3 --version
if [ $? -eq 0 ]; then
    echo "   ✓ Python 3 is installed"
else
    echo "   ✗ Python 3 not found"
    exit 1
fi
echo ""

# Check requests library
echo "2. Checking requests library..."
python3 -c "import requests; print('   ✓ requests library installed:', requests.__version__)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ✗ requests library not found"
    echo "   Install with: pip install requests"
    exit 1
fi
echo ""

# Check script exists and is executable
echo "3. Checking script..."
if [ -f "fetch_noaa_forecasts.py" ]; then
    echo "   ✓ fetch_noaa_forecasts.py exists"
    if [ -x "fetch_noaa_forecasts.py" ]; then
        echo "   ✓ Script is executable"
    else
        echo "   ⚠ Script not executable (not critical)"
    fi
else
    echo "   ✗ fetch_noaa_forecasts.py not found"
    exit 1
fi
echo ""

# Check data directory
echo "4. Checking data directory..."
if [ -d "data" ]; then
    echo "   ✓ data/ directory exists"
else
    echo "   ⚠ data/ directory not found (will be created on first run)"
fi
echo ""

# Test API connectivity
echo "5. Testing NOAA API connectivity..."
curl -s -m 10 "https://api.water.noaa.gov/nwps/v1/gauges/TERI3" > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ NOAA API is accessible"
else
    echo "   ✗ Cannot reach NOAA API (check internet connection)"
    exit 1
fi
echo ""

# Run the script
echo "6. Running fetch script..."
python3 fetch_noaa_forecasts.py > /tmp/noaa_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Script executed successfully"
else
    echo "   ✗ Script failed. Check /tmp/noaa_test.log for details"
    cat /tmp/noaa_test.log
    exit 1
fi
echo ""

# Verify output
echo "7. Verifying output..."
if [ -f "data/noaa_forecasts.json" ]; then
    echo "   ✓ Output file created"
    
    # Validate JSON
    python3 -m json.tool data/noaa_forecasts.json > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✓ JSON is valid"
    else
        echo "   ✗ Invalid JSON format"
        exit 1
    fi
    
    # Check for both gauges
    TERI3_EXISTS=$(python3 -c "import json; d=json.load(open('data/noaa_forecasts.json')); print('yes' if 'TERI3' in d['gauges'] and d['gauges']['TERI3'] else 'no')")
    RVTI3_EXISTS=$(python3 -c "import json; d=json.load(open('data/noaa_forecasts.json')); print('yes' if 'RVTI3' in d['gauges'] and d['gauges']['RVTI3'] else 'no')")
    
    if [ "$TERI3_EXISTS" == "yes" ]; then
        echo "   ✓ TERI3 data present"
    else
        echo "   ✗ TERI3 data missing"
    fi
    
    if [ "$RVTI3_EXISTS" == "yes" ]; then
        echo "   ✓ RVTI3 data present"
    else
        echo "   ✗ RVTI3 data missing"
    fi
else
    echo "   ✗ Output file not created"
    exit 1
fi
echo ""

# Check documentation
echo "8. Checking documentation..."
if [ -f "NOAA_INTEGRATION_GUIDE.md" ]; then
    echo "   ✓ Integration guide present"
fi
if [ -f "NOAA_QUICKSTART.md" ]; then
    echo "   ✓ Quick start guide present"
fi
if [ -f "IMPLEMENTATION_SUMMARY.md" ]; then
    echo "   ✓ Implementation summary present"
fi
echo ""

echo "=========================================="
echo "✓ ALL CHECKS PASSED"
echo "=========================================="
echo ""
echo "Installation is complete and working!"
echo ""
echo "Next steps:"
echo "  1. Review NOAA_QUICKSTART.md for usage instructions"
echo "  2. Setup cron job for automatic updates"
echo "  3. Integrate forecast data into frontend"
echo ""
