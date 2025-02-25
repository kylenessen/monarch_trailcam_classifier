#!/usr/bin/env python3
import os
import glob
import argparse


def check_original_files(directory_path):
    """
    Check if original versions of the orphaned files exist in the directory.

    Args:
        directory_path: Path to the directory containing images

    Returns:
        A string message with the results
    """
    # List of orphaned files identified earlier
    orphaned_files = [
        "SC2_20231118041501 2.JPG",
        "SC2_20231118103001 2.JPG",
        "SC2_20231118114001 2.JPG",
        "SC2_20231118224001 2.JPG"
    ]

    # Get all image files in the directory
    image_files = glob.glob(os.path.join(directory_path, "*.JPG"))
    image_filenames = set(os.path.basename(img) for img in image_files)

    result = "Checking for original versions of orphaned files:\n\n"

    for orphaned_file in orphaned_files:
        # Generate the potential original filename (without the " 2")
        original_filename = orphaned_file.replace(" 2.JPG", ".JPG")

        # Check if the original file exists
        if original_filename in image_filenames:
            result += f"✓ {original_filename} EXISTS (potential original for {orphaned_file})\n"
        else:
            result += f"✗ {original_filename} DOES NOT EXIST (no original found for {orphaned_file})\n"

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Check if original versions of orphaned files exist')
    parser.add_argument(
        'directory', help='Directory containing images')
    args = parser.parse_args()

    result = check_original_files(args.directory)
    print(result)


if __name__ == "__main__":
    main()
