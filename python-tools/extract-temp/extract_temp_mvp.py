#!/usr/bin/env python3
"""
MVP script to extract temperature from a single trail camera image using OCR.
"""

import argparse
import sys
import warnings
from pathlib import Path
import re
from typing import List, Tuple, Dict, Any

import easyocr
import pandas as pd
from PIL import Image
from tqdm import tqdm

# Suppress the MPS pinned memory warning
warnings.filterwarnings("ignore", message=".*pin_memory.*not supported on MPS.*")


def extract_deployment_id(filename: str) -> str:
    """
    Extract deployment ID from filename (everything before first underscore).
    
    Args:
        filename: Image filename (e.g., 'SC4_20231203223001.JPG')
        
    Returns:
        Deployment ID (e.g., 'SC4')
    """
    return filename.split('_')[0]


def validate_temperature(temp_str: str) -> Tuple[int, bool]:
    """
    Validate extracted temperature value.
    
    Args:
        temp_str: Temperature string to validate
        
    Returns:
        Tuple of (temperature_int, is_valid)
    """
    try:
        temp_int = int(temp_str)
        is_valid = 0 <= temp_int <= 100
        return temp_int, is_valid
    except ValueError:
        return 0, False


def find_jpg_files(directory: Path) -> List[Path]:
    """
    Recursively find all JPG files matching the naming pattern.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of JPG file paths
    """
    pattern = re.compile(r'^[A-Z0-9]+_\d+\.JPG$', re.IGNORECASE)
    jpg_files = []
    
    for file_path in directory.rglob('*.JPG'):
        if pattern.match(file_path.name):
            jpg_files.append(file_path)
    
    return sorted(jpg_files)


def extract_temperature(image_path: str, reader: easyocr.Reader) -> tuple[str, float]:
    """
    Extract temperature from trail camera image.
    
    Args:
        image_path: Path to the image file
        reader: Pre-initialized EasyOCR reader
        
    Returns:
        Tuple of (extracted_text, confidence_score)
    """
    try:
        # Load image
        img = Image.open(image_path)
        
        # Get image dimensions for bounding box calculation
        width, height = img.size
        
        # Define bounding box for temperature display area (bottom overlay)
        # Based on sample images, temperature appears in bottom-left area
        # Rough estimate: left 40% of width, bottom 10% of height
        left = 0
        top = int(height * 0.90)  # Start from 90% down the image
        right = int(width * 0.4)   # First 40% of width
        bottom = height
        
        # Crop to region of interest
        cropped = img.crop((left, top, right, bottom))
        
        # Convert PIL image to numpy array for EasyOCR
        import numpy as np
        cropped_array = np.array(cropped)
        
        # Extract text from cropped region using pre-initialized reader
        results = reader.readtext(cropped_array)
        
        # Look for temperature pattern in results
        for (bbox, text, confidence) in results:
            # Look for text containing temperature patterns (°C, C, €, or just numbers with / pattern)
            if any(char in text for char in ['°C', 'C', '€', '/']):
                # Try to extract number from various temperature patterns
                # Look for patterns like "12°C", "12 C", "12 '€", "12 / 53"
                match = re.search(r'(\d+)', text)
                if match:
                    temp_value = match.group(1)
                    return temp_value, confidence
                else:
                    return text, confidence
        
        # If no temperature found, return all detected text
        if results:
            all_text = ' | '.join([f"{text} (conf: {conf:.2f})" for _, text, conf in results])
            return f"No temperature found. Detected: {all_text}", 0.0
        else:
            return "No text detected", 0.0
            
    except Exception as e:
        return f"Error: {str(e)}", 0.0


def process_directory(directory_path: Path) -> List[Dict[str, Any]]:
    """
    Process all JPG files in directory and extract temperature data.
    
    Args:
        directory_path: Directory containing images
        
    Returns:
        List of dictionaries with extraction results
    """
    # Find all matching JPG files
    jpg_files = find_jpg_files(directory_path)
    
    if not jpg_files:
        print(f"No matching JPG files found in {directory_path}")
        return []
    
    print(f"Found {len(jpg_files)} JPG files to process")
    
    # Initialize EasyOCR reader once (this is the expensive operation)
    print("Initializing EasyOCR reader with GPU acceleration...")
    reader = easyocr.Reader(['en'], gpu=True)
    print("EasyOCR reader initialized")
    
    # Initialize results list
    results = []
    
    # Process each file with progress bar
    for file_path in tqdm(jpg_files, desc="Processing images"):
        # Extract deployment ID from filename
        deployment_id = extract_deployment_id(file_path.name)
        
        # Extract temperature using shared reader
        temp_result, confidence = extract_temperature(str(file_path), reader)
        
        # Validate temperature
        temp_int, is_valid = validate_temperature(temp_result)
        
        # Determine extraction status
        if is_valid:
            status = "success"
            temperature = temp_int
        else:
            status = "failed"
            temperature = None
            if len(results) % 1000 == 0:  # Only print warnings occasionally to avoid spam
                print(f"  Warning: Invalid temperature '{temp_result}' in {file_path.name}")
        
        # Store result
        result = {
            'filename': file_path.name,
            'deployment_id': deployment_id,
            'temperature': temperature,
            'confidence': confidence,
            'extraction_status': status
        }
        results.append(result)
    
    return results


def export_to_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Export results to CSV file.
    
    Args:
        results: List of extraction results
        output_path: Path for output CSV file
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"\nResults exported to: {output_path}")
    
    # Print summary statistics
    total = len(results)
    successful = len(df[df['extraction_status'] == 'success'])
    failed = total - successful
    
    print(f"\nSummary:")
    print(f"  Total images: {total}")
    print(f"  Successful extractions: {successful}")
    print(f"  Failed extractions: {failed}")
    print(f"  Success rate: {successful/total*100:.1f}%")
    
    if successful > 0:
        avg_confidence = df[df['extraction_status'] == 'success']['confidence'].mean()
        print(f"  Average confidence: {avg_confidence:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Extract temperature from trail camera images")
    parser.add_argument(
        "input_path", 
        nargs='?',
        default="sample_images",
        help="Path to directory containing images or single image file (default: sample_images)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CSV filename (default: temperature_data.csv)",
        default="temperature_data.csv"
    )
    
    args = parser.parse_args()
    
    # Check if input path exists
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)
    
    # Handle single file vs directory
    if input_path.is_file():
        # Single image processing (MVP behavior)
        print(f"Processing single image: {input_path}")
        
        deployment_id = extract_deployment_id(input_path.name)
        reader = easyocr.Reader(['en'], gpu=True)
        result, confidence = extract_temperature(str(input_path), reader)
        temp_int, is_valid = validate_temperature(result)
        
        print(f"\nResults:")
        print(f"  Deployment ID: {deployment_id}")
        print(f"  Extracted: {result}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Valid temperature: {is_valid}")
        
    elif input_path.is_dir():
        # Directory processing
        print(f"Processing directory: {input_path}")
        
        # Process all images in directory
        results = process_directory(input_path)
        
        if results:
            # Export to CSV
            output_path = input_path / args.output
            export_to_csv(results, output_path)
        else:
            print("No images were processed")
    
    else:
        print(f"Error: Invalid input path: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()