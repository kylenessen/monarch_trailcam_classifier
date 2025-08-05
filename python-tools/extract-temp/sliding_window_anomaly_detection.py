#!/usr/bin/env python3
"""
Sliding window regression-based anomaly detection for temperature data.
Implements the approach described: fit local curves to capture daily cycles,
then measure residuals to identify discontinuous readings.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression, HuberRegressor
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def sliding_window_anomaly_detection(df_deployment, window_hours=48, poly_degree=3, 
                                   anomaly_threshold=2.5, use_robust=True):
    """
    Detect anomalies using sliding window regression and residual analysis.
    
    Args:
        df_deployment: DataFrame with temperature data for single deployment
        window_hours: Size of sliding window in hours
        poly_degree: Degree of polynomial for curve fitting
        anomaly_threshold: Number of MAD units for anomaly threshold
        use_robust: Use robust regression (Huber) vs standard regression
        
    Returns:
        DataFrame with anomaly flags and residual scores
    """
    
    # Prepare data
    data = df_deployment.copy()
    data = data.sort_values('timestamp').reset_index(drop=True)
    
    # Convert timestamp to datetime and create hour offset
    data['datetime'] = pd.to_datetime(data['timestamp'].astype(str), format='%Y%m%d%H%M%S')
    data['hours_from_start'] = (data['datetime'] - data['datetime'].iloc[0]).dt.total_seconds() / 3600
    
    # Remove missing values for analysis
    valid_data = data.dropna(subset=['temperature']).copy()
    
    if len(valid_data) < window_hours:
        print(f"Not enough data points ({len(valid_data)}) for window size ({window_hours})")
        return data
    
    # Initialize results
    residuals = np.full(len(valid_data), np.nan)
    predictions = np.full(len(valid_data), np.nan)
    anomaly_flags = np.full(len(valid_data), False)
    
    # Sliding window analysis
    window_size = min(window_hours, len(valid_data) // 3)  # Adaptive window size
    
    for i in range(len(valid_data)):
        # Define window around current point
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(valid_data), i + window_size // 2 + 1)
        
        # Skip if window too small
        if end_idx - start_idx < 10:
            continue
            
        # Extract window data
        window_data = valid_data.iloc[start_idx:end_idx].copy()
        X = window_data['hours_from_start'].values.reshape(-1, 1)
        y = window_data['temperature'].values
        
        # Fit polynomial regression
        if use_robust:
            # Robust regression - less sensitive to outliers
            regressor = HuberRegressor(epsilon=1.35, max_iter=1000)
            poly_reg = Pipeline([
                ('poly', PolynomialFeatures(degree=poly_degree)),
                ('regressor', regressor)
            ])
        else:
            # Standard regression
            poly_reg = Pipeline([
                ('poly', PolynomialFeatures(degree=poly_degree)),
                ('regressor', LinearRegression())
            ])
        
        try:
            # Fit model and predict current point
            poly_reg.fit(X, y)
            current_x = valid_data.iloc[i]['hours_from_start']
            prediction = poly_reg.predict([[current_x]])[0]
            residual = valid_data.iloc[i]['temperature'] - prediction
            
            predictions[i] = prediction
            residuals[i] = residual
            
        except Exception as e:
            continue
    
    # Calculate anomaly threshold using robust statistics
    valid_residuals = residuals[~np.isnan(residuals)]
    if len(valid_residuals) > 0:
        median_residual = np.median(valid_residuals)
        mad_residual = np.median(np.abs(valid_residuals - median_residual))
        
        # Flag anomalies
        for i in range(len(residuals)):
            if not np.isnan(residuals[i]):
                z_score = abs(residuals[i] - median_residual) / (mad_residual + 1e-8)
                anomaly_flags[i] = z_score > anomaly_threshold
    
    # Add results back to valid_data
    valid_data['prediction'] = predictions
    valid_data['residual'] = residuals
    valid_data['anomaly_flag'] = anomaly_flags
    valid_data['residual_zscore'] = np.abs(residuals - np.median(valid_residuals)) / (mad_residual + 1e-8)
    
    # Merge back with original data (including NaN values)
    result = data.merge(valid_data[['datetime', 'prediction', 'residual', 'anomaly_flag', 'residual_zscore']], 
                       on='datetime', how='left')
    
    return result, valid_residuals, mad_residual

def plot_sliding_window_results(result_data, deployment_id, valid_residuals, mad_residual):
    """Plot the results of sliding window anomaly detection."""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # Top plot: Temperature time series with predictions and anomalies
    ax1.scatter(result_data['datetime'], result_data['temperature'], 
               c='steelblue', alpha=0.6, s=8, label='Observed', zorder=1)
    
    # Plot predictions
    pred_data = result_data.dropna(subset=['prediction'])
    ax1.plot(pred_data['datetime'], pred_data['prediction'], 
             color='orange', linewidth=2, label='Local polynomial fit', zorder=2)
    
    # Highlight anomalies
    anomalies = result_data[result_data['anomaly_flag'] == True]
    if len(anomalies) > 0:
        ax1.scatter(anomalies['datetime'], anomalies['temperature'],
                   c='red', s=40, marker='o', edgecolors='darkred', 
                   linewidth=1, label='Anomalies', zorder=3)
        
        # Add text annotations for anomalies
        for _, row in anomalies.iterrows():
            ax1.annotate(f'{row["temperature"]}°C', 
                        (row['datetime'], row['temperature']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9, color='darkred', weight='bold')
    
    ax1.set_title(f'Sliding Window Anomaly Detection - {deployment_id}\n'
                  f'Polynomial degree 3, {len(anomalies)} anomalies detected')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot: Residuals
    residual_data = result_data.dropna(subset=['residual'])
    ax2.scatter(residual_data['datetime'], residual_data['residual'],
               c='steelblue', alpha=0.6, s=8, zorder=1)
    
    # Add threshold lines
    median_residual = np.median(valid_residuals)
    threshold = 2.5 * mad_residual
    ax2.axhline(y=median_residual + threshold, color='red', linestyle='--', 
               alpha=0.7, label=f'Anomaly threshold (±{threshold:.1f}°C)')
    ax2.axhline(y=median_residual - threshold, color='red', linestyle='--', alpha=0.7)
    ax2.axhline(y=median_residual, color='green', linestyle='-', alpha=0.7, label='Median residual')
    
    # Highlight anomaly residuals
    if len(anomalies) > 0:
        anomaly_residuals = anomalies.dropna(subset=['residual'])
        ax2.scatter(anomaly_residuals['datetime'], anomaly_residuals['residual'],
                   c='red', s=40, marker='o', edgecolors='darkred', 
                   linewidth=1, zorder=3)
    
    ax2.set_title('Residuals (Observed - Predicted)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Residual (°C)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def main():
    """Test sliding window approach on UDMH3 deployment."""
    
    # Load data
    df = pd.read_csv('temperature_data.csv')
    
    # Test on UDMH3 (we know it has issues)
    deployment = 'UDMH3'
    deployment_data = df[df['deployment_id'] == deployment]
    
    print(f"Testing sliding window anomaly detection on {deployment}")
    print(f"Data points: {len(deployment_data)}")
    
    # Run sliding window detection
    result, valid_residuals, mad_residual = sliding_window_anomaly_detection(
        deployment_data, 
        window_hours=48,  # 2-day window
        poly_degree=3,    # Cubic polynomial for curves
        anomaly_threshold=2.5,  # Conservative threshold
        use_robust=True   # Robust regression
    )
    
    # Report results
    anomalies = result[result['anomaly_flag'] == True]
    print(f"\nResults:")
    print(f"  Anomalies detected: {len(anomalies)}")
    print(f"  Median residual: {np.median(valid_residuals):.3f}°C")
    print(f"  MAD of residuals: {mad_residual:.3f}°C")
    print(f"  Anomaly threshold: ±{2.5 * mad_residual:.3f}°C from median")
    
    if len(anomalies) > 0:
        print(f"\nDetected anomalies:")
        for _, row in anomalies.iterrows():
            print(f"  {row['filename']}: {row['temperature']}°C "
                  f"(predicted: {row['prediction']:.1f}°C, "
                  f"residual: {row['residual']:+.1f}°C, "
                  f"z-score: {row['residual_zscore']:.1f})")
    
    # Create plot
    fig = plot_sliding_window_results(result, deployment, valid_residuals, mad_residual)
    
    # Save plot
    output_path = f'temperature_plots/{deployment}_sliding_window_detection.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    
    plt.close()
    
    return result, anomalies

if __name__ == "__main__":
    result, anomalies = main()