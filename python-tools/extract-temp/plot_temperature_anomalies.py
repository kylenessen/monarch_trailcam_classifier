#!/usr/bin/env python3
"""
Plot temperature time series for each deployment with anomaly detection.
Saves individual PNG files for visual inspection of temperature patterns and discontinuities.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
import numpy as np

def detect_temperature_spikes(df_deployment, spike_threshold=8):
    """
    Detect discontinuous temperature spikes in deployment data.
    
    Args:
        df_deployment: DataFrame with temperature data for single deployment
        spike_threshold: Minimum temperature change (°C) to consider a spike
        
    Returns:
        List of indices where spikes occur
    """
    data = df_deployment.copy()
    data = data.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate temperature differences
    data['temp_diff'] = data['temperature'].diff()
    data['next_diff'] = data['temp_diff'].shift(-1)
    
    spike_indices = []
    
    for i in range(1, len(data)-1):
        curr_jump = data.iloc[i]['temp_diff']
        next_jump = data.iloc[i]['next_diff']
        
        # Check for spike pattern: large jump in, large jump out (opposite direction)
        if (abs(curr_jump) > spike_threshold and 
            abs(next_jump) > spike_threshold and
            curr_jump * next_jump < 0):  # Opposite signs
            
            # Store original index from the full dataset
            original_idx = data.iloc[i].name
            spike_indices.append(original_idx)
    
    return spike_indices

def plot_deployment_temperatures(df, deployment_id, spike_indices, output_dir):
    """
    Create temperature time series plot for a single deployment.
    
    Args:
        df: Full temperature DataFrame
        deployment_id: Deployment to plot
        spike_indices: List of indices flagged as anomalies
        output_dir: Directory to save plot
    """
    # Filter data for this deployment
    deployment_data = df[df['deployment_id'] == deployment_id].copy()
    deployment_data = deployment_data.sort_values('timestamp').reset_index()
    
    # Convert timestamp to datetime
    deployment_data['datetime'] = pd.to_datetime(
        deployment_data['timestamp'].astype(str), 
        format='%Y%m%d%H%M%S'
    )
    
    # Identify which points are anomalies
    deployment_data['is_anomaly'] = deployment_data.index.isin(spike_indices)
    
    # Create the plot
    plt.figure(figsize=(16, 8))
    
    # Plot normal points
    normal_data = deployment_data[~deployment_data['is_anomaly']]
    plt.scatter(normal_data['datetime'], normal_data['temperature'], 
               c='steelblue', alpha=0.7, s=8, label='Normal readings', zorder=1)
    
    # Plot anomalies
    anomaly_data = deployment_data[deployment_data['is_anomaly']]
    if len(anomaly_data) > 0:
        plt.scatter(anomaly_data['datetime'], anomaly_data['temperature'], 
                   c='red', alpha=0.9, s=40, label='Temperature spikes', 
                   marker='o', edgecolors='darkred', linewidth=1, zorder=2)
        
        # Add text annotations for anomalies
        for _, row in anomaly_data.iterrows():
            plt.annotate(f'{row["temperature"]}°C', 
                        (row['datetime'], row['temperature']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9, color='darkred', weight='bold')
    
    # Formatting
    plt.title(f'Temperature Time Series - {deployment_id}\n'
              f'{len(deployment_data)} readings, {len(anomaly_data)} anomalies detected',
              fontsize=14, weight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Temperature (°C)', fontsize=12)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(deployment_data)//20)))
    plt.xticks(rotation=45)
    
    # Add grid and legend
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    
    # Add statistics text box
    stats_text = f'Min: {deployment_data["temperature"].min():.1f}°C\n'
    stats_text += f'Max: {deployment_data["temperature"].max():.1f}°C\n'
    stats_text += f'Mean: {deployment_data["temperature"].mean():.1f}°C\n'
    stats_text += f'Std: {deployment_data["temperature"].std():.1f}°C'
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Save plot
    plt.tight_layout()
    filename = f'{deployment_id}_temperature_timeseries.png'
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return len(anomaly_data)

def main():
    # Load temperature data
    print("Loading temperature data...")
    df = pd.read_csv('temperature_data.csv')
    
    # Create output directory
    output_dir = Path('temperature_plots')
    output_dir.mkdir(exist_ok=True)
    print(f"Plots will be saved to: {output_dir.absolute()}")
    
    # Get all deployments
    deployments = sorted(df['deployment_id'].unique())
    print(f"Found {len(deployments)} deployments to plot")
    
    total_anomalies = 0
    deployment_stats = []
    
    # Process each deployment
    for i, deployment in enumerate(deployments, 1):
        print(f"Processing {deployment} ({i}/{len(deployments)})...")
        
        # Get deployment data
        deployment_data = df[df['deployment_id'] == deployment]
        
        # Skip if too few data points
        if len(deployment_data) < 10:
            print(f"  Skipping {deployment} - only {len(deployment_data)} readings")
            continue
        
        # Detect anomalies for this deployment
        spike_indices = detect_temperature_spikes(deployment_data)
        
        # Create plot
        num_anomalies = plot_deployment_temperatures(df, deployment, spike_indices, output_dir)
        total_anomalies += num_anomalies
        
        # Store stats
        deployment_stats.append({
            'deployment': deployment,
            'total_readings': len(deployment_data),
            'anomalies': num_anomalies,
            'min_temp': deployment_data['temperature'].min(),
            'max_temp': deployment_data['temperature'].max(),
            'mean_temp': deployment_data['temperature'].mean()
        })
        
        print(f"  Created plot with {num_anomalies} anomalies detected")
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total plots created: {len([s for s in deployment_stats if s['total_readings'] >= 10])}")
    print(f"Total anomalies detected: {total_anomalies}")
    print(f"Plots saved in: {output_dir.absolute()}")
    
    # Create summary statistics
    stats_df = pd.DataFrame(deployment_stats)
    if len(stats_df) > 0:
        print(f"\nDeployments with most anomalies:")
        top_anomalies = stats_df.nlargest(5, 'anomalies')
        for _, row in top_anomalies.iterrows():
            print(f"  {row['deployment']}: {row['anomalies']} anomalies ({row['total_readings']} readings)")
        
        # Save summary to CSV
        summary_file = output_dir / 'anomaly_summary.csv'
        stats_df.to_csv(summary_file, index=False)
        print(f"\nSummary statistics saved to: {summary_file}")

if __name__ == "__main__":
    main()