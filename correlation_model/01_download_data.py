#!/usr/bin/env python3
"""
USGS River Gauge Data Download Script
======================================
Downloads historical daily gage height data from USGS for correlation analysis.

Gauges:
- TERI3 (Terre Haute): 03341500 - Upstream
- Hutsonville: 03341920 - Target location
- RVTI3 (Riverton): 03342000 - Downstream (validation)

Author: Claude Code
Date: 2025-11-05
"""

import requests
import pandas as pd
import json
from datetime import datetime
import os

# Configuration
GAUGES = {
    'TERI3': {
        'site': '03341500',
        'name': 'Wabash River at Terre Haute, IN',
        'upstream': True
    },
    'HUTSONVILLE': {
        'site': '03341910',
        'name': 'Wabash River near Hutsonville, IL',
        'target': True
    },
    'RVTI3': {
        'site': '03342000',
        'name': 'Wabash River at Riverton, IL',
        'downstream': True
    }
}

# Date range for analysis (15 years)
START_DATE = '2010-01-01'
END_DATE = '2025-11-05'

# USGS API endpoint
USGS_API_URL = 'https://waterservices.usgs.gov/nwis/dv/'

# Output directory
OUTPUT_DIR = '/home/user/WabashRiverStage/correlation_model/data'


def fetch_usgs_data(site_number, parameter_code='00060', start_date=START_DATE, end_date=END_DATE):
    """
    Fetch daily values from USGS NWIS.

    Parameters:
    -----------
    site_number : str
        USGS site number
    parameter_code : str
        USGS parameter code (00065 = gage height, 00060 = discharge)
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format

    Returns:
    --------
    pandas.DataFrame
        DataFrame with datetime index and value column
    """

    params = {
        'sites': site_number,
        'parameterCd': parameter_code,
        'startDT': start_date,
        'endDT': end_date,
        'format': 'json'
    }

    param_name = "Discharge (cfs)" if parameter_code == '00060' else "Gage Height (ft)"
    print(f"Fetching data for site {site_number}...")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Parameter: {parameter_code} ({param_name})")

    try:
        response = requests.get(USGS_API_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract time series data
        time_series = data['value']['timeSeries']

        if not time_series:
            print(f"  WARNING: No data returned for site {site_number}")
            return None

        # Get the first time series (should only be one for daily values)
        values = time_series[0]['values'][0]['value']

        # Convert to DataFrame
        df = pd.DataFrame(values)
        df['dateTime'] = pd.to_datetime(df['dateTime'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # Rename based on parameter type
        col_name = 'discharge_cfs' if parameter_code == '00060' else 'stage_ft'
        df = df.rename(columns={'value': col_name})
        df = df.set_index('dateTime')

        # Keep only the data column
        df = df[[col_name]]

        print(f"  Successfully retrieved {len(df)} records")
        print(f"  Date range: {df.index.min()} to {df.index.max()}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Failed to fetch data - {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"  ERROR: Failed to parse data - {e}")
        return None


def calculate_data_quality(df, gauge_name):
    """
    Calculate data quality metrics for a gauge.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with discharge or stage data
    gauge_name : str
        Name of the gauge

    Returns:
    --------
    dict
        Dictionary with quality metrics
    """

    total_days = (df.index.max() - df.index.min()).days + 1
    actual_records = len(df)
    missing_records = total_days - actual_records

    # Get the data column (either discharge or stage)
    data_col = df.columns[0]

    # Count NaN values
    nan_count = df[data_col].isna().sum()
    valid_count = actual_records - nan_count

    # Calculate statistics for valid data
    valid_data = df[data_col].dropna()

    metrics = {
        'gauge': gauge_name,
        'start_date': df.index.min().strftime('%Y-%m-%d'),
        'end_date': df.index.max().strftime('%Y-%m-%d'),
        'total_days': total_days,
        'records_retrieved': actual_records,
        'missing_dates': missing_records,
        'nan_values': nan_count,
        'valid_records': valid_count,
        'completeness_pct': (valid_count / total_days) * 100,
        'min_value': valid_data.min() if len(valid_data) > 0 else None,
        'max_value': valid_data.max() if len(valid_data) > 0 else None,
        'mean_value': valid_data.mean() if len(valid_data) > 0 else None,
        'median_value': valid_data.median() if len(valid_data) > 0 else None,
        'std_value': valid_data.std() if len(valid_data) > 0 else None
    }

    return metrics


def identify_gaps(df, min_gap_days=7):
    """
    Identify gaps in data greater than specified days.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with stage data
    min_gap_days : int
        Minimum gap size to report (days)

    Returns:
    --------
    list
        List of gaps (start_date, end_date, gap_days)
    """

    # Create complete date range
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')

    # Find missing dates
    missing_dates = full_range.difference(df.index)

    if len(missing_dates) == 0:
        return []

    # Group consecutive missing dates
    gaps = []
    gap_start = missing_dates[0]
    prev_date = missing_dates[0]

    for date in missing_dates[1:]:
        if (date - prev_date).days > 1:
            # End of gap
            gap_days = (prev_date - gap_start).days + 1
            if gap_days >= min_gap_days:
                gaps.append((gap_start, prev_date, gap_days))
            gap_start = date
        prev_date = date

    # Check last gap
    gap_days = (prev_date - gap_start).days + 1
    if gap_days >= min_gap_days:
        gaps.append((gap_start, prev_date, gap_days))

    return gaps


def main():
    """Main execution function."""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 80)
    print("USGS River Gauge Data Download")
    print("=" * 80)
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Parameter: 00065 (Gage Height)")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)
    print()

    all_data = {}
    quality_metrics = []

    # Download data for each gauge
    for gauge_id, gauge_info in GAUGES.items():
        print(f"\n{gauge_id} - {gauge_info['name']}")
        print("-" * 80)

        df = fetch_usgs_data(gauge_info['site'])

        if df is not None:
            # Save raw data
            output_file = os.path.join(OUTPUT_DIR, f'{gauge_id.lower()}_daily_discharge.csv')
            df.to_csv(output_file)
            print(f"  Saved to: {output_file}")

            # Calculate quality metrics
            metrics = calculate_data_quality(df, gauge_id)
            quality_metrics.append(metrics)

            # Identify gaps
            gaps = identify_gaps(df, min_gap_days=7)
            if gaps:
                print(f"  Found {len(gaps)} gaps >= 7 days:")
                for gap_start, gap_end, gap_days in gaps[:5]:  # Show first 5
                    print(f"    {gap_start.strftime('%Y-%m-%d')} to {gap_end.strftime('%Y-%m-%d')} ({gap_days} days)")
                if len(gaps) > 5:
                    print(f"    ... and {len(gaps) - 5} more gaps")
            else:
                print(f"  No significant gaps found (>= 7 days)")

            all_data[gauge_id] = df
        else:
            print(f"  FAILED to retrieve data for {gauge_id}")

    # Save quality metrics
    print("\n" + "=" * 80)
    print("DATA QUALITY SUMMARY")
    print("=" * 80)

    if quality_metrics:
        metrics_df = pd.DataFrame(quality_metrics)
        metrics_file = os.path.join(OUTPUT_DIR, 'data_quality_metrics.csv')
        metrics_df.to_csv(metrics_file, index=False)

        # Print summary table
        print("\nCompleteness Summary:")
        print(metrics_df[['gauge', 'valid_records', 'missing_dates', 'completeness_pct']].to_string(index=False))

        print("\nDischarge Statistics (cfs):")
        stats_cols = ['gauge', 'min_value', 'max_value', 'mean_value', 'std_value']
        print(metrics_df[stats_cols].to_string(index=False))

        print(f"\nQuality metrics saved to: {metrics_file}")

    # Create combined dataset for analysis
    if len(all_data) > 0:
        print("\n" + "=" * 80)
        print("Creating Combined Dataset")
        print("=" * 80)

        # Merge all gauges into single DataFrame
        combined = None
        for gauge_id, df in all_data.items():
            # Get the column name (discharge_cfs or stage_ft)
            orig_col = df.columns[0]
            new_col = f'{gauge_id}_{orig_col}'
            df_renamed = df.rename(columns={orig_col: new_col})
            if combined is None:
                combined = df_renamed
            else:
                combined = combined.join(df_renamed, how='outer')

        # Sort by date
        combined = combined.sort_index()

        # Save combined data
        combined_file = os.path.join(OUTPUT_DIR, 'combined_daily_discharge.csv')
        combined.to_csv(combined_file)
        print(f"Combined dataset saved to: {combined_file}")
        print(f"Total records: {len(combined)}")
        print(f"Date range: {combined.index.min()} to {combined.index.max()}")

        # Show preview
        print("\nFirst 5 records:")
        print(combined.head().to_string())

    print("\n" + "=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
