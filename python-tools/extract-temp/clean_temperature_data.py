#!/usr/bin/env python3
"""
Temperature Data Cleaning Script

Loads original temperature data, applies all correction CSV files, and outputs
a single cleaned dataset. Based on data_exploration.py but focused solely on
producing clean output data.
"""

import pandas as pd
from pathlib import Path


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
                    df_merged.loc[mask, 'temperature'] = correction_row['temperature']
                    df_merged.loc[mask, 'confidence'] = correction_row['confidence']
                    df_merged.loc[mask, 'extraction_status'] = correction_row['extraction_status']
                else:
                    print(f"  Warning: {correction_row['filename']} not found in original data")
        else:
            print(f"Correction file not found: {correction_file}")
    
    return df_merged


def main():
    """Main execution function."""
    print("Temperature Data Cleaning Script")
    print("=" * 40)
    
    # File paths - same as data_exploration.py
    original_csv = 'temperature_data.csv'
    correction_csvs = [
        'missing_temperature_data.csv',
        'manual_extreme_temperature_entries.csv', 
        'manual_temperature_entries_data.csv',
        'manual_temperature_SC2_data.csv'
    ]
    
    # Load and merge data
    df_cleaned = load_and_merge_data(original_csv, correction_csvs)
    
    # Output cleaned data
    output_file = 'cleaned_temperature_data.csv'
    df_cleaned.to_csv(output_file, index=False)
    
    print(f"\nCleaned data saved to: {output_file}")
    print(f"Total records: {len(df_cleaned):,}")
    print(f"Records with temperature data: {df_cleaned['temperature'].notna().sum():,}")
    print(f"Records still missing temperature: {df_cleaned['temperature'].isna().sum():,}")


if __name__ == "__main__":
    main()