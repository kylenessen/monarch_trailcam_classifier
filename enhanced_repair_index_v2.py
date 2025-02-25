#!/usr/bin/env python3
import json
import os
import glob
import argparse
import sys
import shutil
from datetime import datetime


def repair_index(directory_path, remove_orphaned=False, backup=True,
                 file_extension="JPG", add_missing=False, json_filename="classifications.json"):
    """
    Repair the index numbering in classifications.json and optionally remove orphaned entries.

    Args:
        directory_path: Path to the directory containing images and classifications.json
        remove_orphaned: Whether to remove entries that don't have corresponding image files
        backup: Whether to create a backup of the original classifications.json file
        file_extension: Extension of image files to look for (without the dot)
        add_missing: Whether to add entries for image files that don't have corresponding JSON entries
        json_filename: Name of the JSON file to process

    Returns:
        A string message indicating success or describing an error
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist"

    # Check if the JSON file exists
    json_path = os.path.join(directory_path, json_filename)
    if not os.path.isfile(json_path):
        return f"Error: {json_filename} not found in the directory"

    # Create backup if requested
    backup_path = None
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
        return f"Error: {json_filename} is not a valid JSON file"

    # Get list of image files with the specified extension
    image_files = sorted(glob.glob(os.path.join(
        directory_path, f"*.{file_extension}")))
    if not image_files:
        return f"Error: No files with extension .{file_extension} found in the directory"

    image_filenames = set(os.path.basename(img) for img in image_files)

    # Identify orphaned entries (entries without corresponding image files)
    orphaned_entries = []
    for image_name in list(classifications.keys()):
        if image_name not in image_filenames:
            orphaned_entries.append(image_name)

    # Identify missing entries (image files without corresponding JSON entries)
    missing_entries = []
    for image_name in image_filenames:
        if image_name not in classifications:
            missing_entries.append(image_name)

    # Add missing entries if requested
    if missing_entries and add_missing:
        for image_name in missing_entries:
            # Create a template entry for the missing image
            classifications[image_name] = {
                "confirmed": False,
                "cells": {},
                "index": -1,  # Will be fixed in the index repair step
                "notes": "",
                "user": ""
            }

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
            if not missing_entries:
                return orphaned_message
    else:
        orphaned_message = "No orphaned entries found"

    # Report on missing entries
    if missing_entries:
        if add_missing:
            missing_message = f"Added {len(missing_entries)} missing entries"
        else:
            missing_message = f"Found {len(missing_entries)} image files without JSON entries: {', '.join(missing_entries)}"
            missing_message += "\nUse --add-missing flag to add entries for these files"
            if not orphaned_entries or not remove_orphaned:
                return f"{orphaned_message}. {missing_message}"
    else:
        missing_message = "No missing entries found"

    # Verify count matches after potential removal/addition
    if len(image_files) != len(classifications) and not (missing_entries and not add_missing):
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
            # Check if the entry has an "index" field
            if "index" not in image_entries[image_name]:
                image_entries[image_name]["index"] = i
                modified_count += 1
                modified = True
            elif image_entries[image_name]["index"] != i:
                image_entries[image_name]["index"] = i
                modified_count += 1
                modified = True
        else:
            # This should not happen if we've handled missing entries correctly
            if not add_missing and image_name in missing_entries:
                continue  # Skip this file if we're not adding missing entries
            return f"Error: Image file {image_name} not found in JSON (this is a bug)"

    # Save updated JSON if modified
    if modified or (remove_orphaned and orphaned_entries) or (add_missing and missing_entries):
        try:
            with open(json_path, 'w') as f:
                json.dump(classifications, f, indent=2)

            if modified:
                index_message = f"Fixed {modified_count} indices"
            else:
                index_message = "No index changes needed"

            backup_message = f"Backup created at {backup_path}" if backup else "No backup created"
            return f"Success: {orphaned_message}. {missing_message}. {index_message}. {backup_message}"
        except Exception as e:
            return f"Error: Failed to write updated JSON: {str(e)}"
    else:
        return f"{orphaned_message}. {missing_message}. No index changes needed"


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
    parser.add_argument(
        '--file-extension', default='JPG',
        help='Extension of image files to look for (default: JPG)')
    parser.add_argument(
        '--add-missing', action='store_true',
        help='Add entries for image files that don\'t have corresponding JSON entries')
    parser.add_argument(
        '--json-filename', default='classifications.json',
        help='Name of the JSON file to process (default: classifications.json)')
    args = parser.parse_args()

    result = repair_index(
        args.directory,
        args.remove_orphaned,
        not args.no_backup,
        args.file_extension,
        args.add_missing,
        args.json_filename
    )
    print(result)

    # Return appropriate exit code
    if result.startswith("Error:"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
