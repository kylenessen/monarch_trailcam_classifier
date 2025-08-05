import os
import sys
import shutil
import argparse
from pathlib import Path

def process_images(folder_path):
    """
    Processes images in a folder: keeps the 1st of every 6, moves the other 5.

    Args:
        folder_path (str): The path to the folder containing images.
    """
    input_path = Path(folder_path)
    if not input_path.is_dir():
        print(f"Error: Folder not found at '{folder_path}'")
        sys.exit(1)

    skipped_dir_name = "skipped_images"
    skipped_path = input_path / skipped_dir_name
    skipped_path.mkdir(exist_ok=True) # Create the directory if it doesn't exist

    image_extensions = {".jpg", ".jpeg"}
    image_files = sorted([
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ])

    if not image_files:
        print(f"No JPG/JPEG images found in '{folder_path}'.")
        return

    moved_count = 0
    kept_count = 0
    total_count = len(image_files)

    print(f"Processing {total_count} images in '{folder_path}'...")

    for i, img_file in enumerate(image_files):
        # Keep the 1st image (index 0), move 2nd-6th (index 1-5)
        # Keep the 7th image (index 6), move 8th-12th (index 7-11)
        # etc.
        # The pattern is: keep if index % 6 == 0, move otherwise
        if i % 6 == 0:
            kept_count += 1
            # print(f"Keeping: {img_file.name}") # Optional: uncomment for verbose output
        else:
            try:
                destination = skipped_path / img_file.name
                shutil.move(str(img_file), str(destination))
                moved_count += 1
                # print(f"Moving:  {img_file.name} to {skipped_dir_name}/") # Optional: uncomment for verbose output
            except Exception as e:
                print(f"Error moving {img_file.name}: {e}")

    print("\nProcessing complete.")
    print(f"Total images processed: {total_count}")
    print(f"Images kept: {kept_count}")
    print(f"Images moved to '{skipped_dir_name}': {moved_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Keep the first image, move the next five, and repeat for all JPG/JPEG images in a folder."
    )
    parser.add_argument(
        "folder_path",
        help="Path to the folder containing the timelapse images."
    )
    args = parser.parse_args()

    process_images(args.folder_path)
