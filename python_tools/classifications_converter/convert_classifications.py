#!/usr/bin/env python3
"""
Trail Camera Classification Converter

This script reads a classifications.json file containing trail camera image
classifications, converts categorical count values (like "1-9", "10-99") to 
numerical values, and sums them for each image.

The script performs the following operations:
1. Loads the classifications JSON file
2. Converts categorical count values to numerical equivalents
3. Sums the converted values for each image
4. Outputs a mapping of filenames to their calculated count totals

Count Conversion:
- "1-9" → 1
- "10-99" → 10
- "100-999" → 100
- "1000+" → 1000
- 0 → Ignored in totals

Usage:
    python convert_classifications.py
    python convert_classifications.py -i path/to/classifications.json
    python convert_classifications.py -i input.json -o output.json

Command-line Arguments:
    -i, --input  : Path to input classifications.json file (default: classifications.json)
    -o, --output : Path to output JSON file (optional)
"""

import json

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
    0: 0  # Will be ignored in totals
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

def process_classifications(classifications_data):
    """
    Process the classifications data to calculate numerical totals for each image.
    
    Args:
        classifications_data (dict): The loaded classifications JSON data
        
    Returns:
        dict: Dictionary with image filenames as keys and count totals as values
    """
    results = {}
    
    if not classifications_data:
        print("Error: No valid classification data to process.")
        return results
    
    # Iterate through each image in the JSON
    for filename, image_data in classifications_data.items():
        total_count = 0
        
        # Skip images that aren't confirmed (if confirmation status is available)
        if "confirmed" in image_data and not image_data["confirmed"]:
            continue
        
        # Process each cell in the image
        if "cells" in image_data:
            for cell_id, cell_data in image_data["cells"].items():
                if "count" in cell_data:
                    # Convert categorical count to numerical value
                    count_value = convert_count_value(cell_data["count"])
                    
                    # Only add non-zero counts to the total
                    if count_value > 0:
                        total_count += count_value
        else:
            print(f"Warning: No cells found for image '{filename}'.")
        
        # Store the result for this image
        results[filename] = total_count
    
    return results

def save_results_to_json(results, output_file="count_totals.json"):
    """
    Save the results to a JSON file.
    
    Args:
        results (dict): Dictionary with image filenames as keys and count totals as values
        output_file (str): Path to the output JSON file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
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
        output_file (str, optional): Path to save the results as JSON
    """
    # Load classifications
    classifications_data = load_classifications(file_path)
    
    if not classifications_data:
        return
    
    # Process classifications to get count totals
    results = process_classifications(classifications_data)
    
    # Print results
    if results:
        print("\nCalculated Count Totals:")
        print("------------------------")
        for filename, count in results.items():
            print(f"{filename}: {count}")
        
        # Also print total number of images processed and total monarch count
        print(f"\nTotal images processed: {len(results)}")
        print(f"Total monarch count across all images: {sum(results.values())}")
        
        # Save results to JSON file if specified
        if output_file:
            save_results_to_json(results, output_file)
    else:
        print("No results generated. Check the input file and try again.")

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Convert trail camera classification counts from categorical to numerical values.")
    parser.add_argument("-i", "--input", default="classifications.json", help="Path to input classifications.json file")
    parser.add_argument("-o", "--output", help="Path to output JSON file (optional)")
    
    args = parser.parse_args()
    
    # Run the main function with provided arguments
    main(file_path=args.input, output_file=args.output)