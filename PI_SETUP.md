# Storm3 Receiver Pi - Setup Instructions

## Quick Setup (5 Minutes)

Follow these steps on your **Storm3 Receiver Pi** to enable automatic NOAA forecast fetching every 6 hours.

---

## Step 1: Pull Latest Changes

```bash
# Navigate to your repository
cd ~/WabashRiverStage  # Or wherever you cloned the repo

# Pull the latest changes
git pull origin claude/chart-projected-values-011CUq2DURbskKuZE2vCtCzH
```

---

## Step 2: Install Dependencies (if needed)

```bash
# Check if requests library is installed
python3 -c "import requests" 2>/dev/null && echo "✓ requests installed" || pip3 install requests
```

---

## Step 3: Run Setup Script

```bash
# Make sure you're in the repository directory
cd ~/WabashRiverStage

# Run the automated setup script
./setup_noaa_cron.sh
```

**What this does:**
- Creates `logs/` directory
- Adds cron job to run every 6 hours (12 AM, 6 AM, 12 PM, 6 PM)
- Tests the script to make sure it works
- Shows you the installed cron job

---

## Step 4: Verify Installation

```bash
# Check that cron job was added
crontab -l | grep noaa

# Should show:
# 0 */6 * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

---

## That's It! 🎉

The NOAA forecast fetcher will now run automatically every 6 hours.

---

## Monitoring & Maintenance

### View Recent Logs
```bash
cd ~/WabashRiverStage
tail -f logs/noaa_fetch.log
```

### View Latest Forecast Data
```bash
cd ~/WabashRiverStage
cat data/noaa_forecasts.json | python3 -m json.tool | less
```

### Manual Test Run
```bash
cd ~/WabashRiverStage
python3 fetch_noaa_forecasts.py
```

### Check When It Last Ran
```bash
cd ~/WabashRiverStage
ls -lh data/noaa_forecasts.json  # Shows last modified time
```

---

## Schedule Details

**Frequency:** Every 6 hours
**Times:** 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM (local time)
**API Calls:** 8 calls/day (2 gauges × 4 runs)
**Network Usage:** ~10-20 KB per run
**CPU Usage:** ~5-10 seconds per run

**Gauges Monitored:**
- **TERI3** - Wabash River at Terre Haute (upstream)
- **RVTI3** - Wabash River at Riverton (downstream)

---

## Troubleshooting

### Cron job not running?

Check cron service:
```bash
sudo systemctl status cron
```

Check cron logs:
```bash
grep CRON /var/log/syslog | tail -20
```

### Permission errors?

Make script executable:
```bash
chmod +x ~/WabashRiverStage/fetch_noaa_forecasts.py
```

### Python import errors?

Install requests:
```bash
pip3 install requests
```

### Want to change frequency?

Edit crontab:
```bash
crontab -e
```

Change `*/6` to:
- `*/3` for every 3 hours
- `*/12` for every 12 hours
- `*` for every hour

---

## Uninstall

To remove the cron job:
```bash
crontab -e
# Delete the line containing "fetch_noaa_forecasts.py"
```

---

## Files Created

- `logs/noaa_fetch.log` - Execution logs
- `data/noaa_forecasts.json` - Latest forecast data (updated every 6 hours)

---

## Next Steps

After setup is complete and running for a day:

1. **Verify data is updating:**
   ```bash
   watch -n 60 'ls -lh ~/WabashRiverStage/data/noaa_forecasts.json'
   ```

2. **Check for errors:**
   ```bash
   grep -i error ~/WabashRiverStage/logs/noaa_fetch.log
   ```

3. **Ready to integrate into dashboard** - The forecast data is now available at `data/noaa_forecasts.json` and updates automatically!

---

## Support

If you encounter issues:
1. Check `logs/noaa_fetch.log` for error messages
2. Run manually to see detailed output: `python3 fetch_noaa_forecasts.py`
3. Verify NOAA API is accessible: `curl https://api.water.noaa.gov/nwps/v1/gauges/TERI3`

---

**Setup Time:** ~5 minutes
**Maintenance:** Zero (fully automated)
**Resource Impact:** Minimal (~10 seconds every 6 hours)
