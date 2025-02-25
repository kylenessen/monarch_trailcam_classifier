#!/usr/bin/env python3
import json
import os
import glob
import argparse
import sys
import shutil
from datetime import datetime


def repair_index(directory_path, remove_orphaned=False, backup=True):
    """
    Repair the index numbering in classifications.json and optionally remove orphaned entries.

    Args:
        directory_path: Path to the directory containing images and classifications.json
        remove_orphaned: Whether to remove entries that don't have corresponding image files
        backup: Whether to create a backup of the original classifications.json file

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

    # Create backup if requested
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{json_path}.{timestamp}.backup"
        try:
            shutil.copy2(json_path, backup_path)
        except Exception as e:
            return f"Error: Failed to create backup: {str(e)}"

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return "Error: classifications.json is not a valid JSON file"

    # Get list of image files
    image_files = sorted(glob.glob(os.path.join(directory_path, "*.JPG")))
    image_filenames = set(os.path.basename(img) for img in image_files)

    # Identify orphaned entries (entries without corresponding image files)
    orphaned_entries = []
    for image_name in list(classifications.keys()):
        if image_name not in image_filenames:
            orphaned_entries.append(image_name)

    # Report on orphaned entries
    if orphaned_entries:
        if remove_orphaned:
            # Remove orphaned entries if requested
            for image_name in orphaned_entries:
                del classifications[image_name]
            orphaned_message = f"Removed {len(orphaned_entries)} orphaned entries: {', '.join(orphaned_entries)}"
        else:
            # Just report orphaned entries without removing them
            orphaned_message = f"Found {len(orphaned_entries)} orphaned entries: {', '.join(orphaned_entries)}"
            orphaned_message += "\nUse --remove-orphaned flag to remove these entries"
            return orphaned_message
    else:
        orphaned_message = "No orphaned entries found"

    # Verify count matches after potential removal
    if len(image_files) != len(classifications):
        return f"Error: Number of image files ({len(image_files)}) still does not match number of JSON entries ({len(classifications)})"

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
    if modified or remove_orphaned:
        try:
            with open(json_path, 'w') as f:
                json.dump(classifications, f, indent=2)

            if modified:
                index_message = f"Fixed {modified_count} indices"
            else:
                index_message = "No index changes needed"

            return f"Success: {orphaned_message}. {index_message}. Backup created at {backup_path if backup else 'No backup created'}"
        except Exception as e:
            return f"Error: Failed to write updated JSON: {str(e)}"
    else:
        return f"{orphaned_message}. No index changes needed"


def main():
    parser = argparse.ArgumentParser(
        description='Repair index numbering in classifications.json and optionally remove orphaned entries')
    parser.add_argument(
        'directory', help='Directory containing images and classifications.json')
    parser.add_argument(
        '--remove-orphaned', action='store_true',
        help='Remove entries that don\'t have corresponding image files')
    parser.add_argument(
        '--no-backup', action='store_true',
        help='Skip creating a backup of the original classifications.json file')
    args = parser.parse_args()

    result = repair_index(
        args.directory, args.remove_orphaned, not args.no_backup)
    print(result)

    # Return appropriate exit code
    if result.startswith("Error:"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
