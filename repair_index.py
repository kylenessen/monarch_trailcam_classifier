#!/usr/bin/env python3
import json
import os
import glob
import argparse
import sys


def repair_index_numbering(directory_path):
    """
    Repair the index numbering in classifications.json to ensure sequential values without gaps.

    Args:
        directory_path: Path to the directory containing images and classifications.json

    Returns:
        A string message indicating success or describing an error
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist"

    # Check if classifications.json exists
    json_path = os.path.join(directory_path, "classifications.json")
    if not os.path.isfile(json_path):
        return "Error: classifications.json not found in the directory"

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return "Error: classifications.json is not a valid JSON file"

    # Get list of image files
    image_files = sorted(glob.glob(os.path.join(directory_path, "*.JPG")))

    # Verify count matches
    if len(image_files) != len(classifications):
        return f"Error: Number of image files ({len(image_files)}) does not match number of JSON entries ({len(classifications)})"

    # Create a mapping of image filenames to their entries in the JSON
    image_entries = {}
    for image_name, data in classifications.items():
        image_entries[image_name] = data

    # Update index numbers
    modified = False
    modified_count = 0
    for i, image_file in enumerate(image_files):
        image_name = os.path.basename(image_file)
        if image_name in image_entries:
            if image_entries[image_name]["index"] != i:
                image_entries[image_name]["index"] = i
                modified_count += 1
                modified = True
        else:
            return f"Error: Image file {image_name} not found in JSON"

    # Save updated JSON if modified
    if modified:
        try:
            with open(json_path, 'w') as f:
                json.dump(classifications, f, indent=2)
            return f"Success: Index numbering has been repaired. Fixed {modified_count} indices."
        except Exception as e:
            return f"Error: Failed to write updated JSON: {str(e)}"
    else:
        return "No changes needed: Index numbering is already correct"


def main():
    parser = argparse.ArgumentParser(
        description='Repair index numbering in classifications.json')
    parser.add_argument(
        'directory', help='Directory containing images and classifications.json')
    args = parser.parse_args()

    result = repair_index_numbering(args.directory)
    print(result)

    # Return appropriate exit code
    if result.startswith("Error:"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
