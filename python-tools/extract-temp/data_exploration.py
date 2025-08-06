#!/usr/bin/env python3
"""
Temperature Data Exploration Script

Loads original temperature data, applies manual corrections, and identifies remaining outliers.
Preserves original data integrity by never modifying source files.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def load_and_merge_data(original_csv, correction_csvs):
    """
    Load original data and merge with correction CSV files.

    Args:
        original_csv: Path to original temperature data
        correction_csvs: List of correction CSV file paths

    Returns:
        pandas.DataFrame: Merged dataset
    """
    print(f"Loading original data from {original_csv}")
    df_original = pd.read_csv(original_csv)
    print(f"Original data: {len(df_original):,} records")

    # Start with copy of original data
    df_merged = df_original.copy()

    # Apply corrections from each CSV file
    for correction_file in correction_csvs:
        if Path(correction_file).exists():
            print(f"Applying corrections from {correction_file}")
            df_corrections = pd.read_csv(correction_file)
            print(f"  - {len(df_corrections)} corrections to apply")

            # Update existing records with corrections
            for _, correction_row in df_corrections.iterrows():
                mask = df_merged['filename'] == correction_row['filename']
                if mask.any():
                    df_merged.loc[mask,
                                  'temperature'] = correction_row['temperature']
                    df_merged.loc[mask,
                                  'confidence'] = correction_row['confidence']
                    df_merged.loc[mask,
                                  'extraction_status'] = correction_row['extraction_status']
                else:
                    print(
                        f"  Warning: {correction_row['filename']} not found in original data")
        else:
            print(f"Correction file not found: {correction_file}")

    return df_merged


def detect_outliers(df, high_threshold=35, low_threshold=2):
    """
    Detect temperature outliers using simple thresholds.

    Args:
        df: DataFrame with temperature data
        high_threshold: Upper threshold for outliers (default: 35°C)
        low_threshold: Lower threshold for outliers (default: 2°C)

    Returns:
        dict: Dictionary with outlier categories
    """
    outliers = {}

    # High temperature outliers (likely Fahrenheit errors)
    outliers['high'] = df[df['temperature'] >= high_threshold].copy()
    outliers['high']['outlier_type'] = 'high_temp'
    outliers['high']['suggested_action'] = outliers['high']['temperature'].apply(
        lambda x: f"Convert F to C: {(x-32)*5/9:.1f}°C" if x >= 40 else "Review manually"
    )

    # Low temperature outliers (likely OCR errors)
    outliers['low'] = df[df['temperature'] <= low_threshold].copy()
    outliers['low']['outlier_type'] = 'low_temp'
    outliers['low']['suggested_action'] = 'Review manually - likely OCR error'

    # Still missing values (NaN)
    outliers['missing'] = df[df['temperature'].isna()].copy()
    outliers['missing']['outlier_type'] = 'missing_value'
    outliers['missing']['suggested_action'] = 'Manual entry required'

    return outliers


def plot_deployment_timeseries(df, outliers_dict, output_dir='plots'):
    """
    Create time series plots for each deployment with outliers highlighted.

    Args:
        df: Main temperature dataset
        outliers_dict: Dictionary of outlier categories
        output_dir: Directory to save plots
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y%m%d%H%M%S')

    # Combine all outliers into single DataFrame for plotting
    all_outliers = pd.concat([
        outliers_dict['high'],
        outliers_dict['low'],
        outliers_dict['missing']
    ], ignore_index=True)

    # Color mapping for outlier types
    outlier_colors = {
        'high_temp': 'red',
        'low_temp': 'purple',
        'missing_value': 'orange'
    }

    # Plot each deployment
    deployments = sorted(df['deployment_id'].unique())

    for deployment in deployments:
        print(f"Creating plot for {deployment}")

        # Filter data for this deployment
        dept_data = df[df['deployment_id'] == deployment].copy()
        dept_data = dept_data.sort_values('datetime')

        dept_outliers = all_outliers[all_outliers['deployment_id'] == deployment]

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

        # Top panel: Full range including outliers
        ax1.plot(dept_data['datetime'], dept_data['temperature'],
                 'b-', alpha=0.6, linewidth=0.8, label='Normal readings')

        # Plot outliers with different colors
        for outlier_type, color in outlier_colors.items():
            type_outliers = dept_outliers[dept_outliers['outlier_type']
                                          == outlier_type]
            if not type_outliers.empty:
                type_outliers['datetime'] = pd.to_datetime(
                    type_outliers['timestamp'], format='%Y%m%d%H%M%S')
                ax1.scatter(type_outliers['datetime'], type_outliers['temperature'],
                            c=color, s=50, alpha=0.8, label=f'{outlier_type} ({len(type_outliers)})',
                            edgecolors='black', linewidth=0.5, zorder=5)

        ax1.set_title(f'{deployment} - Full Temperature Range (All Data)',
                      fontsize=14, fontweight='bold')
        ax1.set_ylabel('Temperature (°C)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Bottom panel: Normal range view (0-35°C)
        normal_data = dept_data[(dept_data['temperature'] >= 0) & (
            dept_data['temperature'] <= 35)]
        ax2.plot(normal_data['datetime'], normal_data['temperature'],
                 'b-', alpha=0.6, linewidth=0.8, label=f'Normal range readings ({len(normal_data)})')

        ax2.set_title(f'{deployment} - Normal Temperature Range (0-35°C)',
                      fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Temperature (°C)', fontsize=12)
        ax2.set_ylim(0, 35)
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Format x-axis
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Save plot
        plot_filename = f"{deployment}_temperature_timeseries.png"
        plt.savefig(output_path / plot_filename, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved: {plot_filename}")


def save_outliers_summary(outliers_dict, output_file='remaining_outliers.csv'):
    """
    Save all detected outliers to a CSV file for future correction rounds.
    Compatible with manual entry script format.

    Args:
        outliers_dict: Dictionary of outlier categories
        output_file: Output CSV filename
    """
    # Combine all outliers
    all_outliers = pd.concat([
        outliers_dict['high'],
        outliers_dict['low'],
        outliers_dict['missing']
    ], ignore_index=True)

    # Create full_path column in same format as missing_temperature_images.csv
    # Construct path from deployment_id and filename
    def create_full_path(row):
        return f"/Volumes/MediaVault/Masters/Camelot_Photos/{row['deployment_id']}/{row['filename']}"

    all_outliers['full_path'] = all_outliers.apply(create_full_path, axis=1)

    # Select relevant columns and sort - include full_path for manual entry script compatibility
    output_columns = [
        'filename', 'full_path', 'deployment_id', 'timestamp', 'temperature',
        'confidence', 'extraction_status', 'outlier_type', 'suggested_action'
    ]

    outliers_export = all_outliers[output_columns].sort_values(
        ['outlier_type', 'deployment_id', 'timestamp'])

    # Save to CSV
    outliers_export.to_csv(output_file, index=False)
    print(f"\nOutliers saved to: {output_file}")
    print(f"Format compatible with manual entry script (includes full_path column)")

    return outliers_export


def print_summary_stats(df, outliers_dict):
    """Print summary statistics about the dataset and outliers."""
    print("\n" + "="*60)
    print("TEMPERATURE DATA SUMMARY")
    print("="*60)

    print(f"Total records: {len(df):,}")
    print(f"Valid temperatures: {df['temperature'].notna().sum():,}")
    print(f"Missing temperatures: {df['temperature'].isna().sum():,}")

    valid_temps = df['temperature'].dropna()
    if len(valid_temps) > 0:
        print(
            f"\nTemperature range: {valid_temps.min():.1f}°C to {valid_temps.max():.1f}°C")
        print(f"Mean temperature: {valid_temps.mean():.1f}°C")
        print(f"Median temperature: {valid_temps.median():.1f}°C")

    print(f"\nDeployments: {len(df['deployment_id'].unique())}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    print("\n" + "="*60)
    print("OUTLIER DETECTION SUMMARY")
    print("="*60)

    total_outliers = sum(len(outliers) for outliers in outliers_dict.values())
    print(f"Total outliers detected: {total_outliers}")

    for outlier_type, outliers in outliers_dict.items():
        print(f"  {outlier_type.title()} outliers: {len(outliers)}")
        if len(outliers) > 0:
            if outlier_type == 'high':
                print(
                    f"    Temperature range: {outliers['temperature'].min():.1f}°C - {outliers['temperature'].max():.1f}°C")
            elif outlier_type == 'low':
                print(
                    f"    Temperature range: {outliers['temperature'].min():.1f}°C - {outliers['temperature'].max():.1f}°C")

    print(f"\nOutlier percentage: {(total_outliers/len(df)*100):.2f}%")


def main():
    """Main execution function."""
    print("Temperature Data Exploration Script")
    print("="*50)

    # File paths
    original_csv = 'temperature_data.csv'
    # Add more files as needed
    correction_csvs = ['missing_temperature_data.csv',
                       'python-tools/extract-temp/manual_extreme_temperature_entries.csv']

    # Load and merge data
    df = load_and_merge_data(original_csv, correction_csvs)

    # Detect outliers using your specified thresholds
    print(f"\nDetecting outliers (≥35°C and ≤2°C)...")
    outliers = detect_outliers(df, high_threshold=35, low_threshold=2)

    # Print summary statistics
    print_summary_stats(df, outliers)

    # Create time series plots
    print(f"\nCreating time series plots...")
    plot_deployment_timeseries(df, outliers)

    # Save outliers to CSV
    outliers_export = save_outliers_summary(outliers, 'remaining_outliers.csv')

    print("\n" + "="*60)
    print("EXPLORATION COMPLETE")
    print("="*60)
    print("Files created:")
    print("  - Individual deployment PNG plots in 'plots/' directory")
    print("  - remaining_outliers.csv - All detected outliers for review")

    if len(outliers_export) > 0:
        print(f"\nNext steps:")
        print(
            f"  1. Review remaining_outliers.csv ({len(outliers_export)} issues)")
        print(f"  2. Create additional correction CSV files as needed")
        print(f"  3. Re-run this script to validate corrections")


if __name__ == "__main__":
    main()
