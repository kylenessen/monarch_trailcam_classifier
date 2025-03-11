#!/usr/bin/env python3
"""
Index Repair Tool

This script repairs the index numbering in a classifications.json file to ensure sequential values
without gaps. It can also identify and handle orphaned entries (JSON entries without corresponding
image files) and missing entries (image files without corresponding JSON entries).

Author: Kyle Nessen
"""

import json
import os
import glob
import argparse
import sys
import shutil
from datetime import datetime


def repair_index(directory_path, remove_orphaned=False, backup=True,
                 file_extension="JPG", add_missing=False, json_filename="classifications.json",
                 dry_run=False, verbose=False):
    """
    Repair the index numbering in a classifications JSON file and optionally handle orphaned/missing entries.

    Args:
        directory_path (str): Path to the directory containing images and the classifications JSON file
        remove_orphaned (bool): Whether to remove entries that don't have corresponding image files
        backup (bool): Whether to create a backup of the original JSON file
        file_extension (str): Extension of image files to look for (without the dot)
        add_missing (bool): Whether to add entries for image files that don't have corresponding JSON entries
        json_filename (str): Name of the JSON file to process
        dry_run (bool): If True, report what would be done without making changes
        verbose (bool): Whether to print detailed information during processing

    Returns:
        str: A message indicating success or describing an error
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist"

    # Check if the JSON file exists
    json_path = os.path.join(directory_path, json_filename)
    if not os.path.isfile(json_path):
        return f"Error: {json_filename} not found in the directory"

    # Create backup if requested and not in dry run mode
    backup_path = None
    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{json_path}.{timestamp}.backup"
        try:
            shutil.copy2(json_path, backup_path)
            if verbose:
                print(f"Created backup at {backup_path}")
        except Exception as e:
            return f"Error: Failed to create backup: {str(e)}"

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return f"Error: {json_filename} is not a valid JSON file"
    except Exception as e:
        return f"Error: Failed to read {json_filename}: {str(e)}"

    # Get list of image files with the specified extension
    image_files = sorted(glob.glob(os.path.join(
        directory_path, f"*.{file_extension}")))
    if not image_files:
        return f"Error: No files with extension .{file_extension} found in the directory"

    image_filenames = set(os.path.basename(img) for img in image_files)

    if verbose:
        print(
            f"Found {len(image_files)} image files with extension .{file_extension}")
        print(f"Found {len(classifications)} entries in {json_filename}")

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

    # Process orphaned and missing entries
    changes_made = False

    # Handle orphaned entries
    if orphaned_entries:
        if verbose:
            print(
                f"Found {len(orphaned_entries)} orphaned entries (JSON entries without corresponding image files)")
            if len(orphaned_entries) <= 10 or verbose > 1:
                for entry in orphaned_entries:
                    print(
                        f"  - {entry} (index: {classifications[entry].get('index', 'N/A')})")
            else:
                print(f"  - First 10: {', '.join(orphaned_entries[:10])}...")

        if remove_orphaned and not dry_run:
            for image_name in orphaned_entries:
                del classifications[image_name]
            changes_made = True
            orphaned_message = f"Removed {len(orphaned_entries)} orphaned entries"
        else:
            orphaned_message = f"Found {len(orphaned_entries)} orphaned entries"
            if not dry_run:
                orphaned_message += "\nUse --remove-orphaned flag to remove these entries"
            if not missing_entries and not dry_run:
                return orphaned_message
    else:
        orphaned_message = "No orphaned entries found"

    # Handle missing entries
    if missing_entries:
        if verbose:
            print(
                f"Found {len(missing_entries)} missing entries (image files without JSON entries)")
            if len(missing_entries) <= 10 or verbose > 1:
                for entry in missing_entries:
                    print(f"  - {entry}")
            else:
                print(f"  - First 10: {', '.join(missing_entries[:10])}...")

        if add_missing and not dry_run:
            for image_name in missing_entries:
                # Create a template entry for the missing image
                classifications[image_name] = {
                    "confirmed": False,
                    "cells": {},
                    "index": -1,  # Will be fixed in the index repair step
                    "notes": "",
                    "user": ""
                }
            changes_made = True
            missing_message = f"Added {len(missing_entries)} missing entries"
        else:
            missing_message = f"Found {len(missing_entries)} image files without JSON entries"
            if not dry_run:
                missing_message += "\nUse --add-missing flag to add entries for these files"
            if (not orphaned_entries or not remove_orphaned) and not dry_run:
                return f"{orphaned_message}. {missing_message}"
    else:
        missing_message = "No missing entries found"

    # Verify count matches after potential removal/addition
    if len(image_files) != len(classifications) and not (missing_entries and not add_missing) and not dry_run:
        return f"Error: Number of image files ({len(image_files)}) still does not match number of JSON entries ({len(classifications)})"

    # Create a mapping of image filenames to their entries in the JSON
    image_entries = {}
    for image_name, data in classifications.items():
        image_entries[image_name] = data

    # Update index numbers
    modified = False
    modified_count = 0

    # First, check what indices need to be updated
    indices_to_update = []
    for i, image_file in enumerate(image_files):
        image_name = os.path.basename(image_file)
        if image_name in image_entries:
            # Check if the entry has an "index" field
            if "index" not in image_entries[image_name]:
                indices_to_update.append((image_name, i, "missing"))
            elif image_entries[image_name]["index"] != i:
                indices_to_update.append((image_name, i, "incorrect"))

    if verbose and indices_to_update:
        print(f"Found {len(indices_to_update)} indices that need updating")
        if len(indices_to_update) <= 10 or verbose > 1:
            for name, new_index, reason in indices_to_update:
                current = "N/A" if reason == "missing" else image_entries[name]["index"]
                print(f"  - {name}: {current} -> {new_index} ({reason})")
        else:
            print(f"  - First 10 files with indices to update:")
            for name, new_index, reason in indices_to_update[:10]:
                current = "N/A" if reason == "missing" else image_entries[name]["index"]
                print(f"    {name}: {current} -> {new_index} ({reason})")

    # Now update the indices if not in dry run mode
    if not dry_run:
        for image_name, new_index, _ in indices_to_update:
            image_entries[image_name]["index"] = new_index
            modified_count += 1
            modified = True

    # Save updated JSON if modified and not in dry run mode
    if (modified or (remove_orphaned and orphaned_entries) or (add_missing and missing_entries)) and not dry_run:
        try:
            with open(json_path, 'w') as f:
                json.dump(classifications, f, indent=2)
            changes_made = True

            if modified:
                index_message = f"Fixed {modified_count} indices"
            else:
                index_message = "No index changes needed"

            backup_message = f"Backup created at {backup_path}" if backup else "No backup created"
            return f"Success: {orphaned_message}. {missing_message}. {index_message}. {backup_message}"
        except Exception as e:
            return f"Error: Failed to write updated JSON: {str(e)}"
    else:
        if dry_run:
            index_message = f"Would fix {modified_count} indices" if modified_count > 0 else "No index changes needed"
            orphaned_action = f"Would remove {len(orphaned_entries)} orphaned entries" if remove_orphaned and orphaned_entries else orphaned_message
            missing_action = f"Would add {len(missing_entries)} missing entries" if add_missing and missing_entries else missing_message
            return f"Dry run: {orphaned_action}. {missing_action}. {index_message}."
        else:
            return f"{orphaned_message}. {missing_message}. No index changes needed"


def main():
    parser = argparse.ArgumentParser(
        description='Repair index numbering in a classifications JSON file and handle orphaned/missing entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic repair of index numbering
  python index_repair.py ~/path/to/images/
  
  # Remove orphaned entries and add missing entries
  python index_repair.py ~/path/to/images/ --remove-orphaned --add-missing
  
  # Dry run to see what would be changed without making changes
  python index_repair.py ~/path/to/images/ --dry-run --verbose
  
  # Use a different file extension and JSON filename
  python index_repair.py ~/path/to/images/ --file-extension=jpeg --json-filename=data.json
        """
    )
    parser.add_argument(
        'directory', help='Directory containing images and classifications JSON file')
    parser.add_argument(
        '--remove-orphaned', action='store_true',
        help='Remove entries that don\'t have corresponding image files')
    parser.add_argument(
        '--no-backup', action='store_true',
        help='Skip creating a backup of the original JSON file')
    parser.add_argument(
        '--file-extension', default='JPG',
        help='Extension of image files to look for (default: JPG)')
    parser.add_argument(
        '--add-missing', action='store_true',
        help='Add entries for image files that don\'t have corresponding JSON entries')
    parser.add_argument(
        '--json-filename', default='classifications.json',
        help='Name of the JSON file to process (default: classifications.json)')
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Report what would be done without making changes')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase output verbosity (can be used multiple times)')
    args = parser.parse_args()

    result = repair_index(
        args.directory,
        args.remove_orphaned,
        not args.no_backup,
        args.file_extension,
        args.add_missing,
        args.json_filename,
        args.dry_run,
        args.verbose
    )
    print(result)

    # Return appropriate exit code
    if result.startswith("Error:"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
