#!/usr/bin/env python3
"""
Trail Camera Classification Converter

This script reads a classifications.json file containing trail camera image
classifications, converts categorical count values (like "1-9", "10-99") to 
numerical values, and sums them for each image. It also extracts deployment ID
and timestamp information from the image filenames. Optionally, it can incorporate 
wind data from a SQLite database to calculate wind statistics between consecutive images.

The script performs the following operations:
1. Loads the classifications JSON file
2. Optionally loads wind data from a SQLite database
3. Converts categorical count values to numerical equivalents
4. Sums the converted values for each image
5. Extracts deployment ID and timestamp from image filenames
6. If wind data is provided, calculates wind statistics between consecutive images
7. Outputs a CSV file with columns for filename, total count, deployment ID, timestamp, 
   sun cell count, and wind statistics (if available)

Count Conversion:
- "1-9" → 1
- "10-99" → 10
- "100-999" → 100
- "1000+" → 1000
- 0 → Ignored in totals

Filename Parsing:
- Deployment ID: The first part of the filename before the underscore (e.g., "SC1" from "SC1_20231117114501.JPG")
- Timestamp: The part between the underscore and file extension (e.g., "20231117114501" from "SC1_20231117114501.JPG")

Wind Statistics (when wind database is provided):
- Calculated for the period between consecutive images
- Statistics include mean, mode, and variability for wind speed and gust
- Statistics are associated with the later image in each pair

Usage:
    python convert_classifications.py
    python convert_classifications.py -i path/to/classifications.json
    python convert_classifications.py -i input.json -o output.csv
    python convert_classifications.py -i input.json -o output.csv -w wind_data.s3db

Command-line Arguments:
    -i, --input  : Path to input classifications.json file (default: classifications.json)
    -o, --output : Path to output CSV file (optional)
    -w, --wind   : Path to SQLite database containing wind data (optional)
"""

import json
import csv
import os
import glob
import sqlite3
import pandas as pd
from tqdm import tqdm
import numpy as np
from datetime import datetime
from collections import Counter

def load_wind_data(db_path):
    """
    Load wind data from a SQLite database.
    
    Args:
        db_path (str): Path to the SQLite database containing wind data
        
    Returns:
        pd.DataFrame: DataFrame containing wind data with processed columns
    """
    try:
        conn = sqlite3.connect(db_path)
        
        # Read wind data from the database
        df = pd.read_sql_query("SELECT * FROM Wind", conn,
                              dtype={"speed": float, "gust": float, "direction": int, "time": str})
        
        # Convert speed from m/s to mph
        df['speed_mph'] = round(df['speed'] * 2.23694, 1)
        df['gust_mph'] = round(df['gust'] * 2.23694, 1)
        
        # Drop unnecessary columns
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        
        # Convert time to datetime
        df['time'] = pd.to_datetime(df['time'])
        
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading wind data from {db_path}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def load_classifications(file_path="classifications.json"):
    """
    Load the classifications data from a JSON file.
    
    Args:
        file_path (str): Path to the classifications.json file
        
    Returns:
        dict: The loaded JSON data
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: '{file_path}' is not a valid JSON file.")
        return None

# Define count category mapping
COUNT_MAPPING = {
    "1-9": 1,
    "10-99": 10,
    "100-999": 100,
    "1000+": 1000,
    "0": 0,
    0: 0  
}

def convert_count_value(count):
    """
    Convert a categorical count value to a numerical value.
    
    Args:
        count: The categorical count (string or number)
        
    Returns:
        int: The numerical value corresponding to the count category
    """
    # Handle numeric values (0)
    if isinstance(count, (int, float)):
        return COUNT_MAPPING.get(count, 0)
    
    # Handle string values ("1-9", "10-99", etc.)
    if count in COUNT_MAPPING:
        return COUNT_MAPPING[count]
    else:
        # Error handling for unexpected count values
        print(f"Warning: Unexpected count value '{count}'. Using 0 as default.")
        return 0

def extract_deployment_and_timestamp(filename):
    """
    Extract deployment ID and timestamp from the filename.
    
    Args:
        filename (str): The image filename (e.g., SC1_20231117114501.JPG)
        
    Returns:
        tuple: (deployment_id, timestamp) if successful, (None, None) otherwise
    """
    try:
        # Split the filename at underscore
        parts = filename.split('_')
        if len(parts) >= 2:
            deployment_id = parts[0]
            # Get timestamp from the second part (remove file extension)
            timestamp = parts[1].split('.')[0]
            return deployment_id, timestamp
        else:
            print(f"Warning: Couldn't parse deployment ID and timestamp from '{filename}'")
            return None, None
    except Exception as e:
        print(f"Error parsing filename '{filename}': {e}")
        return None, None

def calculate_wind_stats(wind_df, start_time, end_time):
    """
    Calculate wind statistics for observations between two timestamps.
    
    Args:
        wind_df (pd.DataFrame): DataFrame containing wind data
        start_time (datetime): Start time for filtering wind observations
        end_time (datetime): End time for filtering wind observations
        
    Returns:
        dict: Dictionary containing wind statistics (mean, mode, variability for speed and gust)
    """
    # Filter wind data between the two timestamps
    mask = (wind_df['time'] >= start_time) & (wind_df['time'] <= end_time)
    filtered_df = wind_df[mask]
    
    # Initialize results dictionary with default values
    stats = {
        'wind_speed_mean': None,
        'wind_speed_mode': None,
        'wind_speed_var': None,
        'wind_gust_mean': None,
        'wind_gust_mode': None,
        'wind_gust_var': None,
        'wind_observations': 0
    }
    
    # Calculate statistics if we have observations
    if not filtered_df.empty:
        # Count observations
        stats['wind_observations'] = len(filtered_df)
        
        # Wind speed statistics
        stats['wind_speed_mean'] = round(filtered_df['speed_mph'].mean(), 2)
        
        # Calculate mode - handle case where there might be multiple modes
        if not filtered_df['speed_mph'].empty:
            mode_result = Counter(filtered_df['speed_mph']).most_common(1)
            if mode_result:
                stats['wind_speed_mode'] = round(mode_result[0][0], 2)
        
        stats['wind_speed_var'] = round(filtered_df['speed_mph'].var(), 2)
        
        # Wind gust statistics
        stats['wind_gust_mean'] = round(filtered_df['gust_mph'].mean(), 2)
        
        # Calculate mode for gust
        if not filtered_df['gust_mph'].empty:
            mode_result = Counter(filtered_df['gust_mph']).most_common(1)
            if mode_result:
                stats['wind_gust_mode'] = round(mode_result[0][0], 2)
        
        stats['wind_gust_var'] = round(filtered_df['gust_mph'].var(), 2)
    
    return stats

def process_classifications(classifications_data, wind_df=None):
    """
    Process the classifications data to calculate numerical totals for each image.
    
    Args:
        classifications_data (dict): The loaded classifications JSON data
        wind_df (pd.DataFrame, optional): DataFrame containing wind data
        
    Returns:
        dict: Dictionary with image filenames as keys and details including count totals,
              deployment ID, timestamp, wind statistics, and sun cell count as values
    """
    results = {}
    
    if not classifications_data:
        print("Error: No valid classification data to process.")
        return results

    # Get the actual classifications dictionary
    actual_image_classifications = classifications_data.get("classifications")
    if not actual_image_classifications or not isinstance(actual_image_classifications, dict):
        # Attempt to handle old format where the root is the classifications dict
        if isinstance(classifications_data, dict) and all(isinstance(val, dict) for val in classifications_data.values()):
            # Check if top-level keys look like filenames (e.g., contain '_')
            # This is a heuristic and might need refinement
            is_old_format = True
            for key in classifications_data.keys():
                if '_' not in key or not key.upper().endswith(('.JPG', '.JPEG', '.PNG')): # Basic check
                    # If we find keys like "rows", "columns", it's likely the new format with missing "classifications"
                    if key in ["rows", "columns"]:
                         print("Error: 'classifications' key not found in JSON, and other top-level keys like 'rows'/'columns' exist.")
                         return results
                    # If it's just an unexpected key in an otherwise old-format-looking dict, we might allow it
                    # For now, let's be strict if we suspect old format but find non-image keys
            
            # If all checks pass for old format, use classifications_data directly
            # However, the error specifically points to the new structure being used.
            # So, if 'classifications' is missing in the new structure, it's an error.
            print("Error: 'classifications' key not found in JSON or is not a dictionary.")
            return results
        else: # If it's not a dictionary at all or doesn't look like image data
            print("Error: Classification data is not in the expected format (missing 'classifications' dictionary or malformed).")
            return results
            
    # Sort filenames by timestamp to process chronologically
    sorted_filenames = []
    # Iterate over keys of the NESTED dictionary
    for filename in actual_image_classifications.keys():
        deployment_id, timestamp_str = extract_deployment_and_timestamp(filename)
        if timestamp_str:
            try:
                # Create a datetime object for sorting
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                sorted_filenames.append((filename, timestamp))
            except ValueError:
                print(f"Warning: Invalid timestamp format in {filename}")
                sorted_filenames.append((filename, None))
        else:
            sorted_filenames.append((filename, None))
    
    # Sort by timestamp
    sorted_filenames.sort(key=lambda x: x[1] if x[1] is not None else datetime.min)
    
    # Track previous image for wind calculations
    prev_filename = None
    prev_timestamp = None
    
    # Iterate through each image in chronological order
    for filename, current_timestamp in sorted_filenames:
        # Access from the NESTED dictionary
        image_data = actual_image_classifications[filename]
        total_count = 0
        sun_cell_count = 0
        
        # Skip images that aren't confirmed (if confirmation status is available)
        if "confirmed" in image_data and not image_data["confirmed"]:
            continue
        
        # Process each cell in the image
        if "cells" in image_data:
            for cell_id, cell_data in image_data["cells"].items():
                if "count" in cell_data:
                    # Convert categorical count to numerical value
                    count_value = convert_count_value(cell_data["count"])
                    
                    # Add all counts to the total (including zeros)
                    total_count += count_value
                
                # Count cells where sunlight or directSun is true
                if ("sunlight" in cell_data and cell_data["sunlight"]) or \
                   ("directSun" in cell_data and cell_data["directSun"]):
                    sun_cell_count += 1
        else:
            print(f"Warning: No cells found for image '{filename}'.")
        
        # Extract deployment ID and timestamp from filename
        deployment_id, timestamp_str = extract_deployment_and_timestamp(filename)
        
        # Initialize data dictionary for this image
        image_result = {
            "count": total_count,
            "deployment_id": deployment_id,
            "timestamp": timestamp_str,
            "sun_cell_count": sun_cell_count
        }
        
        # Calculate wind statistics if we have wind data and previous timestamp
        if wind_df is not None and not wind_df.empty and prev_timestamp is not None and current_timestamp is not None:
            wind_stats = calculate_wind_stats(wind_df, prev_timestamp, current_timestamp)
            image_result.update(wind_stats)
        
        # Store the results for this image
        results[filename] = image_result
        
        # Update previous timestamp for next iteration
        prev_filename = filename
        prev_timestamp = current_timestamp
    
    return results

def save_results_to_csv(results, output_file="count_totals.csv"):
    """
    Save the results to a CSV file.
    
    Args:
        results (dict): Dictionary with image filenames as keys and details
                       including count, deployment_id, timestamp, sun_cell_count,
                       and wind statistics as values
        output_file (str): Path to the output CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Collect all possible fields from all data entries
        # This ensures we include all possible wind stats fields
        all_fields = set(['filename', 'count', 'deployment_id', 'timestamp', 'sun_cell_count'])
        wind_fields = {
            'wind_observations', 
            'wind_speed_mean', 'wind_speed_mode', 'wind_speed_var',
            'wind_gust_mean', 'wind_gust_mode', 'wind_gust_var'
        }
        
        # Check all entries to find all possible fields
        for data in results.values():
            for field in wind_fields:
                if field in data:
                    all_fields.add(field)
        
        # Convert to list and ensure standard fields come first
        fieldnames = ['filename', 'count', 'deployment_id', 'timestamp', 'sun_cell_count']
        for field in sorted(all_fields - set(fieldnames)):
            fieldnames.append(field)
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            
            writer.writeheader()
            for filename, data in results.items():
                # Start with basic row data
                row_data = {
                    'filename': filename,
                    'count': data['count'],
                    'deployment_id': data['deployment_id'],
                    'timestamp': data['timestamp'],
                    'sun_cell_count': data['sun_cell_count']
                }
                
                # Add all other fields from the data
                for field in data:
                    if field not in row_data:
                        row_data[field] = data[field]
                
                writer.writerow(row_data)
                
        print(f"Results saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")
        return False

def main(file_path="classifications.json", output_file=None, wind_db=None):
    """
    Main function to run the classification converter.
    
    Args:
        file_path (str): Path to the classifications.json file
        output_file (str, optional): Path to save the results as CSV
        wind_db (str, optional): Path to SQLite database containing wind data
    """
    # Load classifications
    classifications_data = load_classifications(file_path)
    
    if not classifications_data:
        return
    
    # Load wind data if a database path was provided
    wind_df = None
    if wind_db:
        print(f"Loading wind data from {wind_db}...")
        wind_df = load_wind_data(wind_db)
        if wind_df.empty:
            print("Warning: Failed to load wind data or no data found.")
        else:
            print(f"Loaded {len(wind_df)} wind observations.")
    
    # Process classifications to get count totals, metadata, and wind statistics
    results = process_classifications(classifications_data, wind_df)
    
    # Print results
    if results:
        print("\nCalculated Results:")
        print("------------------")
        for filename, data in results.items():
            base_info = f"{filename}: Count={data['count']}, Deployment={data['deployment_id']}, Timestamp={data['timestamp']}, Sun Cells={data['sun_cell_count']}"
            
            # Add wind info if available
            if 'wind_speed_mean' in data and data['wind_speed_mean'] is not None:
                wind_info = f", Wind Speed={data['wind_speed_mean']} mph, Wind Gust={data['wind_gust_mean']} mph"
                print(base_info + wind_info)
            else:
                print(base_info)
        
        # Also print total number of images processed and total monarch count
        print(f"\nTotal images processed: {len(results)}")
        total_count = sum(data['count'] for data in results.values())
        print(f"Total monarch count across all images: {total_count}")
        total_sun_cells = sum(data['sun_cell_count'] for data in results.values())
        print(f"Total sun cells across all images: {total_sun_cells}")
        
        # Save results to CSV file if specified
        if output_file:
            save_results_to_csv(results, output_file)
    else:
        print("No results generated. Check the input file and try again.")

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Convert trail camera classification counts from categorical to numerical values.")
    parser.add_argument("-i", "--input", default="classifications.json", help="Path to input classifications.json file")
    parser.add_argument("-o", "--output", help="Path to output CSV file (optional)")
    parser.add_argument("-w", "--wind", help="Path to SQLite database containing wind data (optional)")
    
    args = parser.parse_args()
    
    # Run the main function with provided arguments
    main(file_path=args.input, output_file=args.output, wind_db=args.wind)
