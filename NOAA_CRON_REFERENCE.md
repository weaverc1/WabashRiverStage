# NOAA Forecast Cron - Quick Reference

## Current Configuration

**Script:** `fetch_noaa_forecasts.py`
**Schedule:** Every 6 hours
**Times:** 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM (local time)
**Output:** `data/noaa_forecasts.json`
**Logs:** `logs/noaa_fetch.log`

---

## Cron Entry

```bash
0 */6 * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

---

## Why Every 6 Hours?

✅ **Aligned with NOAA updates** - River Forecast Centers update 4x daily (~6-hour intervals)
✅ **Fresh when needed** - Catches all meaningful forecast changes
✅ **Minimal API calls** - Only 8 calls/day (2 gauges × 4 runs)
✅ **No rate limit risk** - Well under any reasonable API threshold
✅ **Low Pi impact** - ~10 seconds every 6 hours

---

## API Usage

| Frequency | Runs/Day | API Calls/Day | Status |
|-----------|----------|---------------|--------|
| **6 hours (recommended)** | 4 | 8 | ✅ Optimal |
| 3 hours | 8 | 16 | ⚠️ More than needed |
| 12 hours | 2 | 4 | ⚠️ Might miss updates |
| 1 hour | 24 | 48 | ❌ Wasteful |

**Current usage:** 8 API calls/day
**NOAA API rate limit:** None documented (public API)
**Safe maximum:** ~1000 calls/day (conservative estimate)

---

## Quick Commands

### Setup (one-time)
```bash
./setup_noaa_cron.sh
```

### View Schedule
```bash
crontab -l | grep noaa
```

### View Logs
```bash
tail -f logs/noaa_fetch.log
```

### Manual Run
```bash
python3 fetch_noaa_forecasts.py
```

### Check Last Update
```bash
ls -lh data/noaa_forecasts.json
cat data/noaa_forecasts.json | grep last_updated
```

---

## Change Frequency

### Edit crontab
```bash
crontab -e
```

### Common Patterns

**Every 3 hours:**
```
0 */3 * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

**Every 12 hours (noon and midnight):**
```
0 0,12 * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

**Every hour (flood monitoring):**
```
0 * * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

**Specific times (e.g., 6 AM and 6 PM only):**
```
0 6,18 * * * cd /path/to/WabashRiverStage && python3 fetch_noaa_forecasts.py >> logs/noaa_fetch.log 2>&1
```

---

## Monitoring

### Success Indicators
✅ `data/noaa_forecasts.json` timestamp updates every 6 hours
✅ File size ~5-10 KB
✅ No errors in `logs/noaa_fetch.log`
✅ JSON contains both TERI3 and RVTI3 data

### Warning Signs
⚠️ File timestamp not updating
⚠️ "error" or "failed" in logs
⚠️ File size 0 bytes or missing
⚠️ API timeout messages

### Check Health
```bash
# One-line health check
[ -f data/noaa_forecasts.json ] && echo "✓ Data file exists" || echo "✗ Missing"
grep -q "TERI3" data/noaa_forecasts.json && echo "✓ Has TERI3 data" || echo "✗ No TERI3"
grep -q "RVTI3" data/noaa_forecasts.json && echo "✓ Has RVTI3 data" || echo "✗ No RVTI3"
```

---

## Troubleshooting

### Cron not running?
```bash
# Check cron service
sudo systemctl status cron

# Check system logs
grep CRON /var/log/syslog | tail -20
```

### Script errors?
```bash
# Run manually to see output
python3 fetch_noaa_forecasts.py

# Check for Python/dependency issues
python3 -c "import requests; print('OK')"
```

### API issues?
```bash
# Test API directly
curl https://api.water.noaa.gov/nwps/v1/gauges/TERI3

# Check network
ping -c 3 api.water.noaa.gov
```

---

## Files

```
WabashRiverStage/
├── fetch_noaa_forecasts.py          # Main script
├── setup_noaa_cron.sh               # Setup automation
├── data/
│   └── noaa_forecasts.json          # Output (updates every 6 hrs)
└── logs/
    └── noaa_fetch.log               # Execution log
```

---

## Uninstall

```bash
# Remove cron job
crontab -e
# (delete the line with fetch_noaa_forecasts.py)

# Or remove all cron jobs for this user (careful!)
crontab -r
```

---

**Last Updated:** 2025-11-05
**Recommendation:** Keep at 6-hour frequency unless specific needs require changes
