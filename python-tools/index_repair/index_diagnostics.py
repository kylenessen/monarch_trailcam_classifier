#!/usr/bin/env python3
"""
Index Diagnostics Tool

This script provides diagnostic functions for analyzing classifications.json files and
identifying issues such as orphaned entries, missing entries, and duplicate files.

Author: Kyle Nessen
"""

import json
import os
import glob
import argparse
import sys
import re
from datetime import datetime


def identify_orphaned_entries(directory_path, json_filename="classifications.json",
                              file_extension="JPG", verbose=False):
    """
    Identify entries in the JSON file that don't have corresponding image files.

    Args:
        directory_path (str): Path to the directory containing images and JSON file
        json_filename (str): Name of the JSON file to process
        file_extension (str): Extension of image files to look for (without the dot)
        verbose (bool): Whether to print detailed information about each orphaned entry

    Returns:
        tuple: (result_message, orphaned_entries_dict)
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist", None

    # Check if JSON file exists
    json_path = os.path.join(directory_path, json_filename)
    if not os.path.isfile(json_path):
        return f"Error: {json_filename} not found in the directory", None

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return f"Error: {json_filename} is not a valid JSON file", None
    except Exception as e:
        return f"Error: Failed to read {json_filename}: {str(e)}", None

    # Get list of image files
    image_files = sorted(glob.glob(os.path.join(
        directory_path, f"*.{file_extension}")))
    image_filenames = set(os.path.basename(img) for img in image_files)

    # Find entries in JSON that don't have corresponding image files
    orphaned_entries = {}
    for image_name, data in classifications.items():
        if image_name not in image_filenames:
            orphaned_entries[image_name] = data

    # Prepare result message
    if not orphaned_entries:
        return f"No orphaned entries found. JSON entries: {len(classifications)}, Image files: {len(image_files)}", {}

    result = f"Found {len(orphaned_entries)} orphaned entries in {json_filename}.\n"
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


def identify_missing_entries(directory_path, json_filename="classifications.json",
                             file_extension="JPG"):
    """
    Identify image files that don't have corresponding entries in the JSON file.

    Args:
        directory_path (str): Path to the directory containing images and JSON file
        json_filename (str): Name of the JSON file to process
        file_extension (str): Extension of image files to look for (without the dot)

    Returns:
        tuple: (result_message, missing_entries_list)
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist", None

    # Check if JSON file exists
    json_path = os.path.join(directory_path, json_filename)
    if not os.path.isfile(json_path):
        return f"Error: {json_filename} not found in the directory", None

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return f"Error: {json_filename} is not a valid JSON file", None
    except Exception as e:
        return f"Error: Failed to read {json_filename}: {str(e)}", None

    # Get list of image files
    image_files = sorted(glob.glob(os.path.join(
        directory_path, f"*.{file_extension}")))
    image_filenames = set(os.path.basename(img) for img in image_files)

    # Find image files that don't have corresponding entries in JSON
    missing_entries = []
    for image_name in image_filenames:
        if image_name not in classifications:
            missing_entries.append(image_name)

    # Prepare result message
    if not missing_entries:
        return f"No missing entries found. JSON entries: {len(classifications)}, Image files: {len(image_files)}", []

    result = f"Found {len(missing_entries)} missing entries in {json_filename}.\n"
    result += f"JSON entries: {len(classifications)}, Image files: {len(image_files)}\n"
    result += "Missing entries (image files without corresponding JSON entries):\n"
    result += "\n".join(f"- {name}" for name in missing_entries)

    return result, missing_entries


def check_original_files(directory_path, orphaned_files=None, pattern=None, file_extension="JPG"):
    """
    Check if original versions of orphaned files exist in the directory.
    This is useful for identifying duplicate files with slight name variations.

    Args:
        directory_path (str): Path to the directory containing images
        orphaned_files (list): List of orphaned filenames to check, or None to use pattern
        pattern (str): Pattern to use for identifying potential duplicates (e.g., " 2.JPG")
        file_extension (str): Extension of image files to look for (without the dot)

    Returns:
        str: A message with the results
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist"

    # Get all image files in the directory
    image_files = glob.glob(os.path.join(
        directory_path, f"*.{file_extension}"))
    image_filenames = set(os.path.basename(img) for img in image_files)

    result = "Checking for original versions of files:\n\n"

    # If no orphaned files provided, use pattern to identify potential duplicates
    if not orphaned_files and pattern:
        orphaned_files = []
        for filename in image_filenames:
            if pattern in filename:
                orphaned_files.append(filename)

    # If still no orphaned files, return early
    if not orphaned_files:
        return "No files to check. Provide either orphaned_files or a pattern."

    # Check each orphaned file
    for orphaned_file in orphaned_files:
        # Generate the potential original filename based on pattern
        if pattern:
            original_filename = orphaned_file.replace(
                pattern, f".{file_extension}")
        else:
            # Try to guess the pattern (common case: " 2.JPG" suffix)
            match = re.search(r'(.+)( \d+)(\..+)$', orphaned_file)
            if match:
                base, number, ext = match.groups()
                original_filename = f"{base}{ext}"
            else:
                result += f"✗ Could not determine original filename for {orphaned_file}\n"
                continue

        # Check if the original file exists
        if original_filename in image_filenames:
            result += f"✓ {original_filename} EXISTS (potential original for {orphaned_file})\n"
        else:
            result += f"✗ {original_filename} DOES NOT EXIST (no original found for {orphaned_file})\n"

    return result


def analyze_index_gaps(directory_path, json_filename="classifications.json"):
    """
    Analyze the index numbering in the JSON file to identify gaps and inconsistencies.

    Args:
        directory_path (str): Path to the directory containing the JSON file
        json_filename (str): Name of the JSON file to process

    Returns:
        str: A message with the analysis results
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        return "Error: Directory does not exist"

    # Check if JSON file exists
    json_path = os.path.join(directory_path, json_filename)
    if not os.path.isfile(json_path):
        return f"Error: {json_filename} not found in the directory"

    # Load JSON file
    try:
        with open(json_path, 'r') as f:
            classifications = json.load(f)
    except json.JSONDecodeError:
        return f"Error: {json_filename} is not a valid JSON file"
    except Exception as e:
        return f"Error: Failed to read {json_filename}: {str(e)}"

    # Extract all indices
    indices = []
    missing_indices = []
    for image_name, data in classifications.items():
        if "index" in data:
            indices.append((image_name, data["index"]))
        else:
            missing_indices.append(image_name)

    # Sort by index
    indices.sort(key=lambda x: x[1])

    # Check for gaps and duplicates
    gaps = []
    duplicates = []
    expected_index = 0

    for i, (image_name, index) in enumerate(indices):
        # Check for duplicates
        if i > 0 and index == indices[i-1][1]:
            duplicates.append((index, image_name, indices[i-1][0]))

        # Check for gaps
        while expected_index < index:
            gaps.append(expected_index)
            expected_index += 1

        expected_index = index + 1

    # Prepare result message
    result = f"Index analysis for {json_filename}:\n"
    result += f"Total entries: {len(classifications)}\n"
    result += f"Entries with index: {len(indices)}\n"

    if missing_indices:
        result += f"Entries missing index field: {len(missing_indices)}\n"
        result += "Files missing index field:\n"
        result += "\n".join(f"- {name}" for name in missing_indices[:10])
        if len(missing_indices) > 10:
            result += f"\n... and {len(missing_indices) - 10} more"
    else:
        result += "All entries have index field\n"

    if gaps:
        result += f"\nFound {len(gaps)} gaps in index numbering:\n"
        if len(gaps) <= 20:
            result += ", ".join(str(gap) for gap in gaps)
        else:
            result += ", ".join(str(gap) for gap in gaps[:10])
            result += f"\n... and {len(gaps) - 10} more"
    else:
        result += "\nNo gaps found in index numbering"

    if duplicates:
        result += f"\n\nFound {len(duplicates)} duplicate indices:\n"
        for index, file1, file2 in duplicates[:10]:
            result += f"- Index {index}: {file1} and {file2}\n"
        if len(duplicates) > 10:
            result += f"... and {len(duplicates) - 10} more"
    else:
        result += "\nNo duplicate indices found"

    # Add range information
    if indices:
        min_index = indices[0][1]
        max_index = indices[-1][1]
        result += f"\n\nIndex range: {min_index} to {max_index}"
        result += f"\nExpected entries for continuous numbering: {max_index - min_index + 1}"
        result += f"\nActual entries: {len(indices)}"
        if max_index - min_index + 1 != len(indices):
            result += f"\nDiscrepancy: {(max_index - min_index + 1) - len(indices)} entries"

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Diagnostic tools for analyzing classifications.json files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Identify orphaned entries (JSON entries without corresponding image files)
  python index_diagnostics.py orphaned ~/path/to/images/
  
  # Identify missing entries (image files without corresponding JSON entries)
  python index_diagnostics.py missing ~/path/to/images/
  
  # Check for original versions of files with a specific pattern
  python index_diagnostics.py originals ~/path/to/images/ --pattern=" 2.JPG"
  
  # Analyze index gaps and inconsistencies
  python index_diagnostics.py analyze ~/path/to/images/
  
  # Use a different file extension and JSON filename
  python index_diagnostics.py orphaned ~/path/to/images/ --file-extension=jpeg --json-filename=data.json
        """
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Diagnostic command to run')

    # Orphaned entries command
    orphaned_parser = subparsers.add_parser(
        'orphaned', help='Identify orphaned entries')
    orphaned_parser.add_argument(
        'directory', help='Directory containing images and JSON file')
    orphaned_parser.add_argument('--json-filename', default='classifications.json',
                                 help='Name of the JSON file to process (default: classifications.json)')
    orphaned_parser.add_argument('--file-extension', default='JPG',
                                 help='Extension of image files to look for (default: JPG)')
    orphaned_parser.add_argument('-v', '--verbose', action='store_true',
                                 help='Print detailed information about each orphaned entry')

    # Missing entries command
    missing_parser = subparsers.add_parser(
        'missing', help='Identify missing entries')
    missing_parser.add_argument(
        'directory', help='Directory containing images and JSON file')
    missing_parser.add_argument('--json-filename', default='classifications.json',
                                help='Name of the JSON file to process (default: classifications.json)')
    missing_parser.add_argument('--file-extension', default='JPG',
                                help='Extension of image files to look for (default: JPG)')

    # Check original files command
    originals_parser = subparsers.add_parser(
        'originals', help='Check for original versions of files')
    originals_parser.add_argument(
        'directory', help='Directory containing images')
    originals_parser.add_argument('--pattern', default=' 2.JPG',
                                  help='Pattern to use for identifying potential duplicates (default: " 2.JPG")')
    originals_parser.add_argument('--file-extension', default='JPG',
                                  help='Extension of image files to look for (default: JPG)')

    # Analyze index gaps command
    analyze_parser = subparsers.add_parser(
        'analyze', help='Analyze index gaps and inconsistencies')
    analyze_parser.add_argument(
        'directory', help='Directory containing JSON file')
    analyze_parser.add_argument('--json-filename', default='classifications.json',
                                help='Name of the JSON file to process (default: classifications.json)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the appropriate command
    if args.command == 'orphaned':
        result, _ = identify_orphaned_entries(
            args.directory, args.json_filename, args.file_extension, args.verbose)
        print(result)
        sys.exit(0 if "No orphaned entries found" in result else 1)

    elif args.command == 'missing':
        result, _ = identify_missing_entries(
            args.directory, args.json_filename, args.file_extension)
        print(result)
        sys.exit(0 if "No missing entries found" in result else 1)

    elif args.command == 'originals':
        result = check_original_files(
            args.directory, None, args.pattern, args.file_extension)
        print(result)
        sys.exit(0)

    elif args.command == 'analyze':
        result = analyze_index_gaps(args.directory, args.json_filename)
        print(result)
        sys.exit(
            0 if "No gaps found" in result and "No duplicate indices found" in result else 1)


if __name__ == "__main__":
    main()
