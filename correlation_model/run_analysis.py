#!/usr/bin/env python3
"""
Master Analysis Pipeline
========================
Executes the complete river stage correlation analysis workflow.

Steps:
1. Download historical data from USGS
2. Perform correlation analysis
3. Generate visualizations and reports

Author: Claude Code
Date: 2025-11-05
"""

import subprocess
import sys
import os
from datetime import datetime

SCRIPTS = [
    '01_download_data.py',
    '02_correlation_analysis.py'
]

SCRIPT_DIR = '/home/user/WabashRiverStage/correlation_model'


def run_script(script_path):
    """Run a Python script and capture output."""

    script_name = os.path.basename(script_path)
    print("\n" + "=" * 80)
    print(f"RUNNING: {script_name}")
    print("=" * 80)

    start_time = datetime.now()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=SCRIPT_DIR,
            capture_output=False,
            text=True,
            check=True
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✓ {script_name} completed successfully in {elapsed:.1f} seconds")
        return True

    except subprocess.CalledProcessError as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✗ {script_name} failed after {elapsed:.1f} seconds")
        print(f"Error: {e}")
        return False


def main():
    """Run all analysis scripts in sequence."""

    print("=" * 80)
    print("WABASH RIVER STAGE CORRELATION MODEL")
    print("Complete Analysis Pipeline")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {SCRIPT_DIR}")
    print()

    overall_start = datetime.now()
    success_count = 0
    failed_scripts = []

    for script in SCRIPTS:
        script_path = os.path.join(SCRIPT_DIR, script)

        if not os.path.exists(script_path):
            print(f"\n✗ ERROR: Script not found: {script}")
            failed_scripts.append(script)
            continue

        success = run_script(script_path)

        if success:
            success_count += 1
        else:
            failed_scripts.append(script)
            print(f"\nAborting pipeline due to failure in {script}")
            break

    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Total time: {overall_elapsed:.1f} seconds ({overall_elapsed / 60:.1f} minutes)")
    print(f"Scripts completed: {success_count}/{len(SCRIPTS)}")

    if failed_scripts:
        print(f"\nFailed scripts:")
        for script in failed_scripts:
            print(f"  - {script}")
        print("\n✗ Pipeline completed with errors")
        return 1
    else:
        print("\n✓ Pipeline completed successfully!")
        print(f"\nResults available in:")
        print(f"  {SCRIPT_DIR}/data/ (raw data)")
        print(f"  {SCRIPT_DIR}/results/ (analysis outputs)")
        return 0


if __name__ == '__main__':
    sys.exit(main())
