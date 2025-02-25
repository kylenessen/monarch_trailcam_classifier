#!/usr/bin/env python3
import json
import os
import glob
import argparse
import sys


def identify_orphaned_entries(directory_path, verbose=False):
    """
    Identify entries in classifications.json that don't have corresponding image files.

    Args:
        directory_path: Path to the directory containing images and classifications.json
        verbose: Whether to print detailed information about each orphaned entry

    Returns:
        A tuple containing (result_message, orphaned_entries)
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist", None

    # Check if classifications.json exists
    json_path = os.path.join(directory_path, "classifications.json")
    if not os.path.isfile(json_path):
        return "Error: classifications.json not found in the directory", None

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return "Error: classifications.json is not a valid JSON file", None

    # Get list of image files
    image_files = sorted(glob.glob(os.path.join(directory_path, "*.JPG")))
    image_filenames = set(os.path.basename(img) for img in image_files)

    # Find entries in JSON that don't have corresponding image files
    orphaned_entries = {}
    for image_name, data in classifications.items():
        if image_name not in image_filenames:
            orphaned_entries[image_name] = data

    # Prepare result message
    if not orphaned_entries:
        return f"No orphaned entries found. JSON entries: {len(classifications)}, Image files: {len(image_files)}", {}

    result = f"Found {len(orphaned_entries)} orphaned entries in classifications.json.\n"
    result += f"JSON entries: {len(classifications)}, Image files: {len(image_files)}\n"
    result += "Orphaned entries (JSON entries without corresponding image files):"

    # Add detailed information about orphaned entries if verbose
    if verbose:
        for image_name, data in orphaned_entries.items():
            result += f"\n\n{image_name}:"
            result += f"\n  Index: {data.get('index', 'N/A')}"
            result += f"\n  Confirmed: {data.get('confirmed', 'N/A')}"
            result += f"\n  User: {data.get('user', 'N/A')}"
            result += f"\n  Notes: {data.get('notes', 'N/A')}"
            if 'cells' in data and data['cells']:
                result += f"\n  Has classification data: Yes ({len(data['cells'])} cells)"
            else:
                result += f"\n  Has classification data: No"
    else:
        # Just list the filenames if not verbose
        result += "\n" + \
            "\n".join(f"- {name} (index: {data.get('index', 'N/A')})" for name,
                      data in orphaned_entries.items())

    return result, orphaned_entries


def main():
    parser = argparse.ArgumentParser(
        description='Identify orphaned entries in classifications.json (entries without corresponding image files)')
    parser.add_argument(
        'directory', help='Directory containing images and classifications.json')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Print detailed information about orphaned entries')
    args = parser.parse_args()

    result, orphaned_entries = identify_orphaned_entries(
        args.directory, args.verbose)
    print(result)

    # Return appropriate exit code
    if result.startswith("Error:") or orphaned_entries:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
