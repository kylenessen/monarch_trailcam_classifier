#!/usr/bin/env python3
"""
Trail Camera Classification Converter

This script reads a classifications.json file containing trail camera image
classifications, converts categorical count values (like "1-9", "10-99") to 
numerical values, and sums them for each image. It also extracts deployment ID
and timestamp information from the image filenames.

The script performs the following operations:
1. Loads the classifications JSON file
2. Converts categorical count values to numerical equivalents
3. Sums the converted values for each image
4. Extracts deployment ID and timestamp from image filenames
5. Outputs a CSV file with columns for filename, total count, deployment ID, and timestamp

Count Conversion:
- "1-9" → 1
- "10-99" → 10
- "100-999" → 100
- "1000+" → 1000
- 0 → Ignored in totals

Filename Parsing:
- Deployment ID: The first part of the filename before the underscore (e.g., "SC1" from "SC1_20231117114501.JPG")
- Timestamp: The part between the underscore and file extension (e.g., "20231117114501" from "SC1_20231117114501.JPG")

Usage:
    python convert_classifications.py
    python convert_classifications.py -i path/to/classifications.json
    python convert_classifications.py -i input.json -o output.csv

Command-line Arguments:
    -i, --input  : Path to input classifications.json file (default: classifications.json)
    -o, --output : Path to output CSV file (optional)
"""

import json
import csv

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

def process_classifications(classifications_data):
    """
    Process the classifications data to calculate numerical totals for each image.
    
    Args:
        classifications_data (dict): The loaded classifications JSON data
        
    Returns:
        dict: Dictionary with image filenames as keys and details including count totals,
              deployment ID, timestamp, and sun cell count as values
    """
    results = {}
    
    if not classifications_data:
        print("Error: No valid classification data to process.")
        return results
    
    # Iterate through each image in the JSON
    for filename, image_data in classifications_data.items():
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
        deployment_id, timestamp = extract_deployment_and_timestamp(filename)
        
        # Store the results for this image
        results[filename] = {
            "count": total_count,
            "deployment_id": deployment_id,
            "timestamp": timestamp,
            "sun_cell_count": sun_cell_count
        }
    
    return results

def save_results_to_csv(results, output_file="count_totals.csv"):
    """
    Save the results to a CSV file.
    
    Args:
        results (dict): Dictionary with image filenames as keys and details
                       including count, deployment_id, timestamp, and sun_cell_count as values
        output_file (str): Path to the output CSV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', newline='') as f:
            fieldnames = ['filename', 'count', 'deployment_id', 'timestamp', 'sun_cell_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for filename, data in results.items():
                writer.writerow({
                    'filename': filename,
                    'count': data['count'],
                    'deployment_id': data['deployment_id'],
                    'timestamp': data['timestamp'],
                    'sun_cell_count': data['sun_cell_count']
                })
                
        print(f"Results saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")
        return False

def main(file_path="classifications.json", output_file=None):
    """
    Main function to run the classification converter.
    
    Args:
        file_path (str): Path to the classifications.json file
        output_file (str, optional): Path to save the results as CSV
    """
    # Load classifications
    classifications_data = load_classifications(file_path)
    
    if not classifications_data:
        return
    
    # Process classifications to get count totals and metadata
    results = process_classifications(classifications_data)
    
    # Print results
    if results:
        print("\nCalculated Results:")
        print("------------------")
        for filename, data in results.items():
            print(f"{filename}: Count={data['count']}, Deployment={data['deployment_id']}, Timestamp={data['timestamp']}, Sun Cells={data['sun_cell_count']}")
        
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
    
    args = parser.parse_args()
    
    # Run the main function with provided arguments
    main(file_path=args.input, output_file=args.output)