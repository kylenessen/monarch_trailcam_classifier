#!/usr/bin/env python3
"""
Plot temperature time series for a deployment highlighting all identified extreme issues.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

def plot_deployment_with_issues(deployment_id, df, issues_df, output_dir='temperature_plots'):
    """
    Create temperature time series plot with all extreme issues highlighted.
    """
    # Filter data for this deployment
    deployment_data = df[df['deployment_id'] == deployment_id].copy()
    deployment_data = deployment_data.sort_values('timestamp').reset_index()
    
    # Filter issues for this deployment
    deployment_issues = issues_df[issues_df['deployment_id'] == deployment_id].copy()
    
    # Convert timestamp to datetime
    deployment_data['datetime'] = pd.to_datetime(
        deployment_data['timestamp'].astype(str), 
        format='%Y%m%d%H%M%S'
    )
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # === TOP PLOT: Full time series with issues ===
    
    # Plot all normal points (valid temperatures)
    normal_data = deployment_data[deployment_data['temperature'].notna()]
    ax1.scatter(normal_data['datetime'], normal_data['temperature'], 
               c='steelblue', alpha=0.7, s=8, label='Valid readings', zorder=1)
    
    # Highlight different types of issues
    issue_colors = {
        'failed_extraction': 'red',
        'fahrenheit_conversion': 'orange', 
        'extraction_error_low': 'purple'
    }
    
    issue_markers = {
        'failed_extraction': 'x',
        'fahrenheit_conversion': 'o',
        'extraction_error_low': 's'
    }
    
    issue_sizes = {
        'failed_extraction': 80,
        'fahrenheit_conversion': 60,
        'extraction_error_low': 40
    }
    
    for issue_type in deployment_issues['issue_type'].unique():
        issue_subset = deployment_issues[deployment_issues['issue_type'] == issue_type]
        
        # For failed extractions, we need to plot them at estimated positions
        if issue_type == 'failed_extraction':
            # Plot failed extractions as red X's at timeline position, height=0
            failed_datetimes = []
            for _, issue_row in issue_subset.iterrows():
                # Find matching row in deployment data
                matching_row = deployment_data[deployment_data['filename'] == issue_row['filename']]
                if len(matching_row) > 0:
                    failed_datetimes.append(matching_row.iloc[0]['datetime'])
            
            if failed_datetimes:
                # Plot at bottom of temperature range
                min_temp = normal_data['temperature'].min() if len(normal_data) > 0 else 0
                ax1.scatter(failed_datetimes, [min_temp - 2] * len(failed_datetimes),
                           c=issue_colors[issue_type], marker=issue_markers[issue_type], 
                           s=issue_sizes[issue_type], alpha=0.9, 
                           label=f'Failed extractions ({len(issue_subset)})', zorder=3)
        else:
            # For other issues, plot at their actual temperature values
            issue_datetimes = []
            issue_temps = []
            
            for _, issue_row in issue_subset.iterrows():
                matching_row = deployment_data[deployment_data['filename'] == issue_row['filename']]
                if len(matching_row) > 0:
                    issue_datetimes.append(matching_row.iloc[0]['datetime'])
                    issue_temps.append(issue_row['temperature'])
            
            if issue_datetimes:
                label_map = {
                    'fahrenheit_conversion': f'Fahrenheit errors ({len(issue_subset)})',
                    'extraction_error_low': f'Low value errors ({len(issue_subset)})'
                }
                
                ax1.scatter(issue_datetimes, issue_temps,
                           c=issue_colors[issue_type], marker=issue_markers[issue_type],
                           s=issue_sizes[issue_type], alpha=0.9, edgecolors='darkred',
                           linewidth=1, label=label_map.get(issue_type, issue_type), zorder=3)
    
    # Add annotations for extreme values
    for issue_type in ['fahrenheit_conversion', 'extraction_error_low']:
        issue_subset = deployment_issues[deployment_issues['issue_type'] == issue_type]
        for _, issue_row in issue_subset.iterrows():
            matching_row = deployment_data[deployment_data['filename'] == issue_row['filename']]
            if len(matching_row) > 0:
                datetime_val = matching_row.iloc[0]['datetime']
                temp_val = issue_row['temperature']
                
                if issue_type == 'fahrenheit_conversion':
                    celsius_val = (temp_val - 32) * 5/9
                    ax1.annotate(f'{temp_val}°C\\n→{celsius_val:.1f}°C', 
                                (datetime_val, temp_val),
                                xytext=(5, 10), textcoords='offset points',
                                fontsize=8, color='darkorange', weight='bold')
                else:
                    ax1.annotate(f'{temp_val}°C', 
                                (datetime_val, temp_val),
                                xytext=(5, 5), textcoords='offset points',
                                fontsize=8, color='purple', weight='bold')
    
    # Formatting top plot
    ax1.set_title(f'Temperature Time Series with Extreme Issues - {deployment_id}\\n'
                  f'{len(deployment_data)} total readings, {len(deployment_issues)} extreme issues detected',
                  fontsize=14, weight='bold')
    ax1.set_ylabel('Temperature (°C)', fontsize=12)
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # === BOTTOM PLOT: Zoomed view on normal range ===
    
    # Plot normal temperature range (exclude extreme highs)
    normal_range_data = normal_data[normal_data['temperature'] <= 35]
    if len(normal_range_data) > 0:
        ax2.scatter(normal_range_data['datetime'], normal_range_data['temperature'],
                   c='steelblue', alpha=0.7, s=8, label='Valid readings', zorder=1)
        
        # Show low value errors and failed extractions in normal range
        for issue_type in ['extraction_error_low', 'failed_extraction']:
            issue_subset = deployment_issues[deployment_issues['issue_type'] == issue_type]
            
            if issue_type == 'failed_extraction':
                # Estimate positions for failed extractions
                failed_datetimes = []
                estimated_temps = []
                
                for _, issue_row in issue_subset.iterrows():
                    matching_row = deployment_data[deployment_data['filename'] == issue_row['filename']]
                    if len(matching_row) > 0:
                        failed_datetimes.append(matching_row.iloc[0]['datetime'])
                        
                        # Estimate temperature from surrounding context
                        idx = matching_row.index[0]
                        start_idx = max(0, idx - 3)
                        end_idx = min(len(deployment_data), idx + 4)
                        context = deployment_data.iloc[start_idx:end_idx]
                        surrounding = context[context['temperature'].notna()]['temperature']
                        est_temp = surrounding.median() if len(surrounding) > 0 else 10
                        estimated_temps.append(est_temp)
                
                if failed_datetimes:
                    ax2.scatter(failed_datetimes, estimated_temps,
                               c='red', marker='x', s=80, alpha=0.9,
                               label=f'Failed extractions (est.)', zorder=3)
                    
                    # Add estimated value annotations
                    for dt, temp in zip(failed_datetimes, estimated_temps):
                        ax2.annotate(f'~{temp:.0f}°C', (dt, temp),
                                    xytext=(5, 5), textcoords='offset points',
                                    fontsize=8, color='red', weight='bold')
            
            elif issue_type == 'extraction_error_low':
                issue_datetimes = []
                issue_temps = []
                
                for _, issue_row in issue_subset.iterrows():
                    matching_row = deployment_data[deployment_data['filename'] == issue_row['filename']]
                    if len(matching_row) > 0 and issue_row['temperature'] <= 35:
                        issue_datetimes.append(matching_row.iloc[0]['datetime'])
                        issue_temps.append(issue_row['temperature'])
                
                if issue_datetimes:
                    ax2.scatter(issue_datetimes, issue_temps,
                               c='purple', marker='s', s=40, alpha=0.9, edgecolors='darkred',
                               label=f'Low value errors', zorder=3)
    
    # Formatting bottom plot
    ax2.set_title('Normal Temperature Range View (excluding Fahrenheit errors)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Temperature (°C)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis dates for both plots
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(deployment_data)//15)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add statistics text box
    stats_text = f'Issues Summary:\\n'
    for issue_type in deployment_issues['issue_type'].value_counts().index:
        count = len(deployment_issues[deployment_issues['issue_type'] == issue_type])
        stats_text += f'• {issue_type}: {count}\\n'
    
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save plot
    filename = f'{deployment_id}_extreme_issues_plot.png'
    filepath = f'{output_dir}/{filename}'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filepath

def main():
    # Load data
    df = pd.read_csv('temperature_data.csv')
    issues_df = pd.read_csv('extreme_temperature_issues.csv')
    
    # Find deployment with most diverse issues
    issues_by_deployment = issues_df['deployment_id'].value_counts()
    target_deployment = issues_by_deployment.index[0]  # UDMH1 has most issues
    
    print(f'Creating plot for {target_deployment} with {issues_by_deployment[target_deployment]} extreme issues...')
    
    # Create plot
    filepath = plot_deployment_with_issues(target_deployment, df, issues_df)
    print(f'Plot saved to: {filepath}')
    
    # Show breakdown of issues for this deployment
    deployment_issues = issues_df[issues_df['deployment_id'] == target_deployment]
    print(f'\\nIssue breakdown for {target_deployment}:')
    print(deployment_issues['issue_type'].value_counts())
    
    return filepath

if __name__ == "__main__":
    main()