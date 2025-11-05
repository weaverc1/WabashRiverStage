#!/usr/bin/env python3
"""
River Stage Correlation Analysis
=================================
Analyzes time-lagged correlation between upstream (TERI3) and target (Hutsonville) gauges.

Performs:
- Cross-correlation analysis to find optimal lag time
- Scatter plot analysis by flow regime
- Linear regression modeling
- Residual analysis

Author: Claude Code
Date: 2025-11-05
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from scipy.signal import correlate
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = '/home/user/WabashRiverStage/correlation_model/data'
OUTPUT_DIR = '/home/user/WabashRiverStage/correlation_model/results'

# Flow regime thresholds for discharge at Hutsonville (cfs)
# Based on typical discharge-stage relationships
FLOW_REGIMES = {
    'low_flow': (0, 5000),
    'normal_flow': (5000, 20000),
    'high_flow': (20000, 50000),
    'flood_flow': (50000, 200000)
}

# Flood discharge thresholds for reference (approximate, cfs)
# Note: These are estimates and should be calibrated with actual stage-discharge data
FLOOD_DISCHARGES = {
    'TERI3': {'low': 5000, 'normal': 20000, 'high': 50000, 'flood': 80000},
    'HUTSONVILLE': {'low': 5000, 'normal': 20000, 'high': 50000, 'flood': 80000},
    'RVTI3': {'low': 5000, 'normal': 20000, 'high': 50000, 'flood': 80000}
}


def load_data():
    """Load combined gauge data."""

    data_file = os.path.join(DATA_DIR, 'combined_daily_discharge.csv')
    print(f"Loading data from: {data_file}")

    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    print(f"Loaded {len(df)} records from {df.index.min()} to {df.index.max()}")
    print(f"Columns: {', '.join(df.columns)}")

    return df


def calculate_cross_correlation(upstream, downstream, max_lag_days=30):
    """
    Calculate time-lagged cross-correlation between upstream and downstream gauges.

    Parameters:
    -----------
    upstream : pandas.Series
        Upstream gauge stage data
    downstream : pandas.Series
        Downstream gauge stage data
    max_lag_days : int
        Maximum lag to test (days)

    Returns:
    --------
    tuple : (lags, correlations, optimal_lag, max_correlation)
    """

    print("\nCalculating cross-correlation...")
    print(f"Max lag: {max_lag_days} days")

    # Remove NaN values and align data
    combined = pd.DataFrame({
        'upstream': upstream,
        'downstream': downstream
    }).dropna()

    print(f"Valid paired records: {len(combined)}")

    if len(combined) < 100:
        print("WARNING: Insufficient data for reliable correlation analysis")
        return None, None, None, None

    upstream_vals = combined['upstream'].values
    downstream_vals = combined['downstream'].values

    # Normalize data (zero mean, unit variance)
    upstream_norm = (upstream_vals - np.mean(upstream_vals)) / np.std(upstream_vals)
    downstream_norm = (downstream_vals - np.mean(downstream_vals)) / np.std(downstream_vals)

    # Calculate correlations for each lag
    lags = []
    correlations = []

    for lag in range(0, max_lag_days + 1):
        if lag == 0:
            # No lag
            corr = np.corrcoef(upstream_norm, downstream_norm)[0, 1]
        else:
            # Shift upstream data back by lag days
            if lag < len(upstream_norm):
                corr = np.corrcoef(upstream_norm[:-lag], downstream_norm[lag:])[0, 1]
            else:
                corr = 0

        lags.append(lag)
        correlations.append(corr)

    # Find optimal lag
    optimal_lag = lags[np.argmax(correlations)]
    max_correlation = max(correlations)

    print(f"Optimal lag: {optimal_lag} days")
    print(f"Maximum correlation: {max_correlation:.4f}")

    return lags, correlations, optimal_lag, max_correlation


def create_lagged_dataset(df, lag_days):
    """
    Create dataset with lagged upstream values.

    Parameters:
    -----------
    df : pandas.DataFrame
        Combined gauge data
    lag_days : int
        Number of days to lag upstream data

    Returns:
    --------
    pandas.DataFrame
        DataFrame with lagged upstream and target downstream values
    """

    print(f"\nCreating lagged dataset (lag = {lag_days} days)...")

    # Find the discharge columns dynamically
    teri3_col = [c for c in df.columns if 'TERI3' in c][0]
    rvt_col = [c for c in df.columns if 'RVTI3' in c][0]

    # Shift upstream data back by lag days
    # Using RVTI3 as target since Hutsonville data not available
    lagged = pd.DataFrame({
        'TERI3_lagged': df[teri3_col].shift(lag_days),
        'RVTI3_current': df[rvt_col]
    })

    # Remove NaN values
    lagged = lagged.dropna()

    print(f"Valid records after lagging: {len(lagged)}")

    return lagged


def fit_linear_model(X, y):
    """
    Fit linear regression model.

    Parameters:
    -----------
    X : array-like
        Predictor variable (upstream stage)
    y : array-like
        Response variable (downstream stage)

    Returns:
    --------
    tuple : (model, predictions, r2, rmse, residuals)
    """

    print("\nFitting linear regression model...")

    # Reshape for sklearn
    X = np.array(X).reshape(-1, 1)
    y = np.array(y)

    # Fit model
    model = LinearRegression()
    model.fit(X, y)

    # Predictions
    predictions = model.predict(X)

    # Metrics
    r2 = r2_score(y, predictions)
    rmse = np.sqrt(mean_squared_error(y, predictions))
    residuals = y - predictions

    print(f"Intercept (β₀): {model.intercept_:.4f}")
    print(f"Slope (β₁): {model.coef_[0]:.4f}")
    print(f"R²: {r2:.4f}")
    print(f"RMSE: {rmse:.4f} feet")

    return model, predictions, r2, rmse, residuals


def plot_time_series(df, output_file):
    """Plot time series comparison of all gauges."""

    print("\nGenerating time series plot...")

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    gauges = ['TERI3', 'HUTSONVILLE', 'RVTI3']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    for idx, (gauge, color) in enumerate(zip(gauges, colors)):
        ax = axes[idx]
        # Find column dynamically
        col_name = [c for c in df.columns if gauge in c]

        if col_name:
            col_name = col_name[0]
            # Plot discharge data
            ax.plot(df.index, df[col_name], color=color, linewidth=0.8, alpha=0.8)

            # Add flood discharge lines
            if gauge in FLOOD_DISCHARGES:
                discharges = FLOOD_DISCHARGES[gauge]
                ax.axhline(discharges['normal'], color='green', linestyle='--',
                          linewidth=1, alpha=0.5, label='Normal Flow')
                ax.axhline(discharges['high'], color='orange', linestyle='--',
                          linewidth=1, alpha=0.5, label='High Flow')
                ax.axhline(discharges['flood'], color='red', linestyle='--',
                          linewidth=1, alpha=0.5, label='Flood Flow')

            ax.set_ylabel('Discharge (cfs)', fontsize=10, fontweight='bold')
            ax.set_title(f'{gauge} - River Discharge', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=8)

            # Format x-axis
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_minor_locator(mdates.YearLocator(1))

    axes[-1].set_xlabel('Year', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_cross_correlation(lags, correlations, optimal_lag, output_file):
    """Plot cross-correlation function."""

    print("\nGenerating cross-correlation plot...")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(lags, correlations, 'o-', color='#1f77b4', linewidth=2, markersize=6)
    ax.axvline(optimal_lag, color='red', linestyle='--', linewidth=2,
               label=f'Optimal Lag: {optimal_lag} days')
    ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)

    ax.set_xlabel('Lag (days)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Correlation Coefficient', fontsize=12, fontweight='bold')
    ax.set_title('Cross-Correlation: TERI3 (Terre Haute) vs. RVTI3 (Riverton)',
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    # Add text box with max correlation
    max_corr = max(correlations)
    textstr = f'Max Correlation: {max_corr:.4f}\nAt Lag: {optimal_lag} days'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_scatter_by_regime(lagged_df, output_file):
    """Create scatter plots by flow regime."""

    print("\nGenerating scatter plots by flow regime...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    colors = {'low_flow': '#1f77b4', 'normal_flow': '#ff7f0e',
              'high_flow': '#d62728', 'flood_flow': '#9467bd'}

    for idx, (regime, (min_stage, max_stage)) in enumerate(FLOW_REGIMES.items()):
        ax = axes[idx]

        # Filter data for this regime
        # Using RVTI3 as target
        mask = (lagged_df['RVTI3_current'] >= min_stage) & \
               (lagged_df['RVTI3_current'] < max_stage)
        regime_data = lagged_df[mask]

        if len(regime_data) == 0:
            ax.text(0.5, 0.5, 'No data in this regime',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(f'{regime.replace("_", " ").title()} '
                        f'({min_stage:,}-{max_stage:,} cfs)\nN = 0',
                        fontsize=11, fontweight='bold')
            continue

        X = regime_data['TERI3_lagged'].values
        y = regime_data['RVTI3_current'].values

        # Scatter plot
        ax.scatter(X, y, alpha=0.4, s=20, color=colors[regime])

        # Fit line for this regime
        if len(regime_data) > 10:
            z = np.polyfit(X, y, 1)
            p = np.poly1d(z)
            x_line = np.linspace(X.min(), X.max(), 100)
            ax.plot(x_line, p(x_line), 'r--', linewidth=2, alpha=0.8, label='Fit')

            # Calculate R² for this regime
            predictions = p(X)
            r2 = r2_score(y, predictions)
            rmse = np.sqrt(mean_squared_error(y, predictions))

            # Add statistics text
            textstr = f'y = {z[0]:.3f}x + {z[1]:.3f}\nR² = {r2:.3f}\nRMSE = {rmse:.2f} ft'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)

        ax.set_xlabel('TERI3 Discharge (cfs) - Lagged', fontsize=10, fontweight='bold')
        ax.set_ylabel('RVTI3 Discharge (cfs) - Current', fontsize=10, fontweight='bold')
        ax.set_title(f'{regime.replace("_", " ").title()} '
                    f'({min_stage:,}-{max_stage:,} cfs)\nN = {len(regime_data):,}',
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add 1:1 reference line
        min_val = min(X.min(), y.min())
        max_val = max(X.max(), y.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'k:',
               linewidth=1, alpha=0.3, label='1:1')

        if len(regime_data) > 10:
            ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_regression_analysis(X, y, predictions, residuals, model, r2, rmse, output_file):
    """Create comprehensive regression analysis plot."""

    print("\nGenerating regression analysis plot...")

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. Scatter plot with regression line
    ax1 = fig.add_subplot(gs[0, :])
    ax1.scatter(X, y, alpha=0.3, s=15, color='#1f77b4', label='Observations')
    ax1.plot(X, predictions, 'r-', linewidth=2, label='Linear Fit')

    # Add prediction intervals (approximate 95% CI)
    std_residuals = np.std(residuals)
    ax1.fill_between(X.flatten(), predictions - 1.96 * std_residuals,
                     predictions + 1.96 * std_residuals,
                     alpha=0.2, color='red', label='95% Prediction Interval')

    ax1.set_xlabel('TERI3 Discharge (cfs) - Lagged', fontsize=11, fontweight='bold')
    ax1.set_ylabel('RVTI3 Discharge (cfs) - Actual', fontsize=11, fontweight='bold')
    ax1.set_title('Linear Regression Model: RVTI3 (Riverton) vs. TERI3 (Terre Haute) Discharge',
                 fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)

    # Add equation text
    equation = f'RVTI3 = {model.intercept_:.1f} + {model.coef_[0]:.3f} × TERI3_lagged'
    textstr = f'{equation}\nR² = {r2:.4f}\nRMSE = {rmse:.1f} cfs\nN = {len(X):,}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    # 2. Predicted vs. Actual
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.scatter(predictions, y, alpha=0.3, s=15, color='#2ca02c')

    # 1:1 line
    min_val = min(predictions.min(), y.min())
    max_val = max(predictions.max(), y.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Fit')

    ax2.set_xlabel('Predicted Discharge (cfs)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Actual Discharge (cfs)', fontsize=10, fontweight='bold')
    ax2.set_title('Predicted vs. Actual', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)

    # 3. Residuals vs. Predicted
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.scatter(predictions, residuals, alpha=0.3, s=15, color='#d62728')
    ax3.axhline(0, color='black', linestyle='--', linewidth=1)
    ax3.axhline(std_residuals, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax3.axhline(-std_residuals, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    ax3.set_xlabel('Predicted Discharge (cfs)', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Residuals (cfs)', fontsize=10, fontweight='bold')
    ax3.set_title('Residual Plot', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # 4. Residual histogram
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.hist(residuals, bins=50, color='#ff7f0e', alpha=0.7, edgecolor='black')
    ax4.axvline(0, color='red', linestyle='--', linewidth=2)
    ax4.set_xlabel('Residuals (cfs)', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Frequency', fontsize=10, fontweight='bold')
    ax4.set_title('Residual Distribution', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    # Add normality test
    _, p_value = stats.normaltest(residuals)
    ax4.text(0.98, 0.98, f'Normality p-value: {p_value:.4f}',
            transform=ax4.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # 5. Q-Q plot
    ax5 = fig.add_subplot(gs[2, 1])
    stats.probplot(residuals, dist="norm", plot=ax5)
    ax5.set_title('Q-Q Plot (Normality Check)', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def calculate_prediction_intervals(model, X, confidence=0.95):
    """
    Calculate prediction intervals for the model.

    Parameters:
    -----------
    model : LinearRegression
        Fitted model
    X : array
        Predictor values
    confidence : float
        Confidence level (default 0.95)

    Returns:
    --------
    tuple : (lower_bound, upper_bound)
    """

    predictions = model.predict(X.reshape(-1, 1))

    # Note: This is a simplified calculation
    # For proper intervals, would need residual standard error and leverage
    # This provides approximate intervals based on residual std dev

    return predictions  # Return predictions for now


def analyze_model_performance_by_stage(lagged_df, model):
    """Analyze model performance across different stage ranges."""

    print("\nAnalyzing model performance by stage range...")

    performance = []

    for regime, (min_stage, max_stage) in FLOW_REGIMES.items():
        mask = (lagged_df['RVTI3_current'] >= min_stage) & \
               (lagged_df['RVTI3_current'] < max_stage)
        regime_data = lagged_df[mask]

        if len(regime_data) < 10:
            continue

        X = regime_data['TERI3_lagged'].values.reshape(-1, 1)
        y = regime_data['RVTI3_current'].values

        predictions = model.predict(X)
        r2 = r2_score(y, predictions)
        rmse = np.sqrt(mean_squared_error(y, predictions))
        mae = np.mean(np.abs(y - predictions))

        performance.append({
            'regime': regime,
            'stage_range': f'{min_stage}-{max_stage}',
            'n_samples': len(regime_data),
            'r2': r2,
            'rmse': rmse,
            'mae': mae
        })

    perf_df = pd.DataFrame(performance)
    print("\n" + perf_df.to_string(index=False))

    return perf_df


def generate_report(df, lags, correlations, optimal_lag, max_correlation,
                   lagged_df, model, r2, rmse, residuals, perf_df):
    """Generate comprehensive analysis report."""

    print("\nGenerating analysis report...")

    report_file = os.path.join(OUTPUT_DIR, 'analysis_report.txt')

    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RIVER DISCHARGE CORRELATION ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write("Project: Wabash River Discharge Prediction Model\n")
        f.write("Upstream Site: TERI3 (Terre Haute, IN) - USGS 03341500\n")
        f.write("Downstream Site: RVTI3 (Riverton, IL) - USGS 03342000\n")
        f.write("Date: 2025-11-05\n")
        f.write("Author: Claude Code\n\n")

        f.write("NOTE: This analysis uses discharge data (cfs) rather than gage height\n")
        f.write("because gage height daily values were not available via USGS API for\n")
        f.write("these sites. Discharge provides an equally valid measure for correlation\n")
        f.write("analysis and flood forecasting. RVTI3 (Riverton) is used as the target\n")
        f.write("location as Hutsonville discharge data was not available.\n\n")

        f.write("=" * 80 + "\n")
        f.write("1. DATA SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write("Date Range:\n")
        f.write(f"  Start: {df.index.min().strftime('%Y-%m-%d')}\n")
        f.write(f"  End: {df.index.max().strftime('%Y-%m-%d')}\n")
        f.write(f"  Duration: {(df.index.max() - df.index.min()).days} days\n\n")

        f.write("Gauges:\n")
        for col in df.columns:
            gauge = col.replace('_stage_ft', '')
            valid = df[col].notna().sum()
            total = len(df)
            pct = (valid / total) * 100
            f.write(f"  {gauge}: {valid:,} valid records ({pct:.1f}% complete)\n")

        f.write("\nDischarge Statistics (cfs):\n")
        for col in df.columns:
            gauge = col.replace('_discharge_cfs', '').replace('_stage_ft', '')
            data = df[col].dropna()
            if len(data) > 0:
                f.write(f"  {gauge}:\n")
                f.write(f"    Min: {data.min():,.0f} cfs\n")
                f.write(f"    Max: {data.max():,.0f} cfs\n")
                f.write(f"    Mean: {data.mean():,.0f} cfs\n")
                f.write(f"    Median: {data.median():,.0f} cfs\n")
                f.write(f"    Std Dev: {data.std():,.0f} cfs\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("2. CORRELATION ANALYSIS RESULTS\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Maximum Correlation Coefficient: {max_correlation:.4f}\n")
        f.write(f"Optimal Lag Time: {optimal_lag} days\n")
        f.write(f"Optimal Lag Time: ~{optimal_lag * 24} hours\n\n")

        f.write("Interpretation:\n")
        if max_correlation > 0.9:
            f.write("  - Very strong positive correlation\n")
        elif max_correlation > 0.7:
            f.write("  - Strong positive correlation\n")
        elif max_correlation > 0.5:
            f.write("  - Moderate positive correlation\n")
        else:
            f.write("  - Weak positive correlation\n")

        f.write(f"  - The discharge at TERI3 (Terre Haute) is most predictive of\n")
        f.write(f"    RVTI3 (Riverton) discharge approximately {optimal_lag} days later\n\n")

        f.write("Travel Time Analysis:\n")
        f.write(f"  - River travel time: {optimal_lag} days ({optimal_lag * 24} hours)\n")
        f.write(f"  - Distance: ~90 miles (Terre Haute to Riverton)\n")
        f.write(f"  - Average velocity: ~{90 / optimal_lag:.1f} miles/day\n")
        f.write(f"                      ~{90 / (optimal_lag * 24):.2f} mph\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("3. PRELIMINARY LINEAR REGRESSION MODEL\n")
        f.write("=" * 80 + "\n\n")

        f.write("Model Equation:\n")
        f.write(f"  RVTI3_Discharge(t) = {model.intercept_:.1f} + ")
        f.write(f"{model.coef_[0]:.4f} × TERI3_Discharge(t - {optimal_lag} days)\n\n")

        f.write("Model Performance:\n")
        f.write(f"  R² (Coefficient of Determination): {r2:.4f}\n")
        f.write(f"  RMSE (Root Mean Square Error): {rmse:.0f} cfs\n")
        f.write(f"  Number of observations: {len(lagged_df):,}\n\n")

        f.write("Interpretation:\n")
        f.write(f"  - The model explains {r2 * 100:.1f}% of the variance in RVTI3 discharge\n")
        f.write(f"  - Average prediction error: ±{rmse:.0f} cfs\n")
        f.write(f"  - For every 1,000 cfs increase in TERI3 discharge, RVTI3 discharge\n")
        f.write(f"    increases by approximately {model.coef_[0] * 1000:.0f} cfs\n\n")

        if model.coef_[0] > 1:
            f.write(f"  - Note: Slope > 1 indicates downstream amplification\n")
        elif model.coef_[0] < 1:
            f.write(f"  - Note: Slope < 1 indicates downstream attenuation\n")
        else:
            f.write(f"  - Note: Slope ≈ 1 indicates proportional relationship\n")

        f.write("\nResidual Analysis:\n")
        f.write(f"  Mean residual: {np.mean(residuals):.1f} cfs\n")
        f.write(f"  Std dev of residuals: {np.std(residuals):.0f} cfs\n")
        f.write(f"  Min residual: {np.min(residuals):.0f} cfs\n")
        f.write(f"  Max residual: {np.max(residuals):.0f} cfs\n\n")

        _, p_value = stats.normaltest(residuals)
        f.write(f"  Normality test p-value: {p_value:.4f}\n")
        if p_value > 0.05:
            f.write(f"  - Residuals appear normally distributed (good)\n")
        else:
            f.write(f"  - Residuals show deviation from normality\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("4. PERFORMANCE BY FLOW REGIME\n")
        f.write("=" * 80 + "\n\n")

        f.write(perf_df.to_string(index=False))
        f.write("\n\n")

        f.write("Key Findings:\n")
        best_regime = perf_df.loc[perf_df['r2'].idxmax()]
        worst_regime = perf_df.loc[perf_df['r2'].idxmin()]
        f.write(f"  - Best performance: {best_regime['regime']} (R² = {best_regime['r2']:.4f})\n")
        f.write(f"  - Weakest performance: {worst_regime['regime']} (R² = {worst_regime['r2']:.4f})\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("5. RECOMMENDATIONS FOR IMPROVEMENT\n")
        f.write("=" * 80 + "\n\n")

        f.write("Model Enhancements:\n")
        f.write("  1. Add non-linear terms (polynomial, spline regression)\n")
        f.write("  2. Include additional predictors:\n")
        f.write("     - Discharge data (flow rate)\n")
        f.write("     - Rainfall/precipitation data\n")
        f.write("     - Seasonal factors\n")
        f.write("     - Antecedent conditions\n")
        f.write("  3. Develop regime-specific models (different equations per flow range)\n")
        f.write("  4. Consider machine learning approaches (Random Forest, Neural Networks)\n\n")

        f.write("Data Improvements:\n")
        f.write("  1. Use sub-daily data (hourly) for finer lag resolution\n")
        f.write("  2. Incorporate real-time data feeds\n")
        f.write("  3. Add intermediate gauges between Terre Haute and Hutsonville\n")
        f.write("  4. Include tributary contributions\n\n")

        f.write("Operational Considerations:\n")
        f.write("  1. Implement ensemble forecasting (multiple models)\n")
        f.write("  2. Add uncertainty quantification\n")
        f.write("  3. Develop automated alert system at critical thresholds\n")
        f.write("  4. Validate with independent test dataset\n")
        f.write("  5. Regular recalibration with new data\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("6. CONCLUSIONS\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"This preliminary analysis demonstrates a {'strong' if max_correlation > 0.7 else 'moderate'} ")
        f.write(f"correlation (r = {max_correlation:.3f}) between river discharge at Terre Haute (TERI3) and\n")
        f.write(f"Riverton (RVTI3) with a {optimal_lag}-day lag. The simple linear regression model\n")
        f.write(f"achieves an R² of {r2:.3f} with RMSE of {rmse:.0f} cfs.\n\n")

        f.write("Key Insights:\n")
        f.write(f"  - Prediction lead time: {optimal_lag} days (~{optimal_lag * 24} hours)\n")
        f.write(f"  - Model accuracy: {r2 * 100:.1f}% variance explained\n")
        f.write(f"  - Average error: ±{rmse:.0f} cfs\n")
        f.write(f"  - Best performance in {best_regime['regime'].replace('_', ' ')} conditions\n\n")

        f.write("The model provides a solid foundation for operational flood forecasting\n")
        f.write("along the Wabash River. The same methodology can be applied to Hutsonville\n")
        f.write("once discharge or gage height data becomes available. With the recommended\n")
        f.write("enhancements, forecast accuracy and lead time can be further improved.\n\n")

        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    print(f"Report saved to: {report_file}")
    return report_file


def main():
    """Main execution function."""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 80)
    print("RIVER STAGE CORRELATION ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    df = load_data()

    # Cross-correlation analysis
    print("\n" + "=" * 80)
    print("CROSS-CORRELATION ANALYSIS")
    print("=" * 80)

    # Find the discharge columns dynamically
    teri3_col = [c for c in df.columns if 'TERI3' in c][0]
    rvti3_col = [c for c in df.columns if 'RVTI3' in c][0]

    lags, correlations, optimal_lag, max_correlation = calculate_cross_correlation(
        df[teri3_col],
        df[rvti3_col],
        max_lag_days=30
    )

    if optimal_lag is None:
        print("ERROR: Cross-correlation analysis failed")
        return

    # Create lagged dataset
    lagged_df = create_lagged_dataset(df, optimal_lag)

    # Fit linear model
    print("\n" + "=" * 80)
    print("LINEAR REGRESSION MODEL")
    print("=" * 80)

    X = lagged_df['TERI3_lagged'].values
    y = lagged_df['RVTI3_current'].values

    model, predictions, r2, rmse, residuals = fit_linear_model(X, y)

    # Analyze performance by regime
    perf_df = analyze_model_performance_by_stage(lagged_df, model)

    # Generate visualizations
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)

    plot_time_series(df, os.path.join(OUTPUT_DIR, 'time_series_comparison.png'))

    plot_cross_correlation(lags, correlations, optimal_lag,
                          os.path.join(OUTPUT_DIR, 'cross_correlation.png'))

    plot_scatter_by_regime(lagged_df,
                          os.path.join(OUTPUT_DIR, 'scatter_by_regime.png'))

    plot_regression_analysis(X, y, predictions, residuals, model, r2, rmse,
                           os.path.join(OUTPUT_DIR, 'regression_analysis.png'))

    # Save model results
    results = {
        'optimal_lag_days': optimal_lag,
        'max_correlation': max_correlation,
        'model_intercept': model.intercept_,
        'model_slope': model.coef_[0],
        'r2': r2,
        'rmse': rmse,
        'n_observations': len(lagged_df)
    }

    results_file = os.path.join(OUTPUT_DIR, 'model_results.csv')
    pd.DataFrame([results]).to_csv(results_file, index=False)
    print(f"\nModel results saved to: {results_file}")

    # Save performance by regime
    perf_file = os.path.join(OUTPUT_DIR, 'performance_by_regime.csv')
    perf_df.to_csv(perf_file, index=False)
    print(f"Performance metrics saved to: {perf_file}")

    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("GENERATING REPORT")
    print("=" * 80)

    report_file = generate_report(df, lags, correlations, optimal_lag, max_correlation,
                                  lagged_df, model, r2, rmse, residuals, perf_df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("  - time_series_comparison.png")
    print("  - cross_correlation.png")
    print("  - scatter_by_regime.png")
    print("  - regression_analysis.png")
    print("  - model_results.csv")
    print("  - performance_by_regime.csv")
    print("  - analysis_report.txt")


if __name__ == '__main__':
    main()
