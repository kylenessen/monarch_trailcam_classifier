import os
import shutil
import random
import uuid
import tkinter as tk
from tkinter import filedialog


def select_directory(title="Select Directory"):
    """Open a file dialog to select a directory."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(title=title)
    return clean_path(directory) if directory else None


def get_photos_by_folder(source_dir):
    """Get photos organized by subfolder."""
    photos_by_folder = {}
    # Common image file extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}

    # Get immediate subfolders
    subfolders = [f.path for f in os.scandir(source_dir) if f.is_dir()]

    # Process each subfolder
    for folder in subfolders:
        folder_photos = []
        # Walk through the current subfolder
        for root, _, files in os.walk(folder):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    folder_photos.append(os.path.join(root, file))

        if folder_photos:  # Only add folders that contain photos
            photos_by_folder[folder] = folder_photos

    return photos_by_folder


def generate_random_filename(original_filename):
    """Generate a random filename while preserving the extension."""
    _, ext = os.path.splitext(original_filename)
    random_name = str(uuid.uuid4())
    return f"{random_name}{ext}"


def copy_random_photos(source_dir, dest_dir, photos_per_folder=10):
    """Copy random photos from each subfolder with randomized names."""
    # Get photos organized by subfolder
    photos_by_folder = get_photos_by_folder(source_dir)

    if not photos_by_folder:
        print(f"No photos found in {source_dir}")
        return

    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    total_copied = 0
    for folder, photos in photos_by_folder.items():
        folder_name = os.path.basename(folder)
        num_to_copy = min(len(photos), photos_per_folder)

        # Randomly select photos from this folder
        selected_photos = random.sample(photos, num_to_copy)

        print(f"\nProcessing folder: {folder_name}")

        # Copy selected photos with random names
        for i, photo_path in enumerate(selected_photos, 1):
            # Generate a random filename
            new_filename = generate_random_filename(photo_path)
            dest_path = os.path.join(dest_dir, new_filename)

            # Copy the file
            shutil.copy2(photo_path, dest_path)
            print(f"Copied {i}/{num_to_copy} from {folder_name}")
            total_copied += 1

    return total_copied


def clean_path(path):
    """Remove quotes and extra whitespace from path."""
    return path.strip().strip("'").strip('"') if path else None


def main():
    # Get directory paths using file dialogs
    print("Please select the source directory...")
    source_dir = select_directory("Select Source Directory")
    if not source_dir:
        print("No source directory selected. Exiting...")
        return

    print("Please select the destination directory...")
    dest_dir = select_directory("Select Destination Directory")
    if not dest_dir:
        print("No destination directory selected. Exiting...")
        return

    # Validate source directory exists
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    try:
        total_copied = copy_random_photos(source_dir, dest_dir)
        print(f"\nPhoto copying completed successfully!")
        print(f"Total photos copied: {total_copied}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
