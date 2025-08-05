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


def extract_timestamp(filename: str) -> str:
    """
    Extract timestamp from filename.
    
    Args:
        filename: Image filename (e.g., 'SC4_20231203223001.JPG')
        
    Returns:
        Timestamp string (e.g., '20231203223001')
    """
    # Remove .JPG extension first
    name_without_ext = filename.rsplit('.', 1)[0]
    # Split on underscores
    parts = name_without_ext.split('_')
    # Find the timestamp part (14 digits)
    for part in parts:
        if len(part) == 14 and part.isdigit():
            return part
    # Fallback: return last part
    return parts[-1]


def extract_deployment_id(filename: str) -> str:
    """
    Extract deployment ID from filename by removing timestamp and extension.
    Handles deployment IDs with underscores (e.g., 'SLC6_1_20240105142001.JPG' -> 'SLC6_1').
    
    Args:
        filename: Image filename (e.g., 'SC4_20231203223001.JPG' or 'SLC6_1_20240105142001.JPG')
        
    Returns:
        Deployment ID (e.g., 'SC4' or 'SLC6_1')
    """
    # Remove .JPG extension first
    name_without_ext = filename.rsplit('.', 1)[0]
    # Split on underscores
    parts = name_without_ext.split('_')
    # Find the timestamp part (14 digits) and take everything before it
    for i, part in enumerate(parts):
        if len(part) == 14 and part.isdigit():
            return '_'.join(parts[:i])
    # Fallback: return everything except last part
    return '_'.join(parts[:-1])


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
    pattern = re.compile(r'^[A-Z0-9_]+_\d{14}\.JPG$', re.IGNORECASE)
    jpg_files = []
    
    for file_path in directory.rglob('*.JPG'):
        if pattern.match(file_path.name):
            jpg_files.append(file_path)
    
    return sorted(jpg_files)


def extract_temperature_with_settings(image_path: str, reader: easyocr.Reader, bounding_box: tuple, preprocessing_params: dict) -> tuple[str, float]:
    """
    Extract temperature with specific settings - helper function for retry logic.
    """
    try:
        # Load image
        img = Image.open(image_path)
        
        # Apply bounding box
        left, top, right, bottom = bounding_box
        cropped = img.crop((left, top, right, bottom))
        
        # Apply preprocessing if specified
        if preprocessing_params.get('enhance', False):
            from PIL import ImageEnhance
            
            # Adjust contrast
            contrast_factor = preprocessing_params.get('contrast', 1.5)
            enhancer = ImageEnhance.Contrast(cropped)
            cropped = enhancer.enhance(contrast_factor)
            
            # Adjust brightness  
            brightness_factor = preprocessing_params.get('brightness', 1.2)
            enhancer = ImageEnhance.Brightness(cropped)
            cropped = enhancer.enhance(brightness_factor)
        
        # Convert PIL image to numpy array for EasyOCR
        import numpy as np
        cropped_array = np.array(cropped)
        
        # Extract text with EasyOCR parameters
        width_ths = preprocessing_params.get('width_ths', 0.7)
        height_ths = preprocessing_params.get('height_ths', 0.7)
        
        results = reader.readtext(
            cropped_array,
            width_ths=width_ths,      # Text box width threshold
            height_ths=height_ths,    # Text box height threshold
            detail=1                  # Return detailed results
        )
        
        return results
        
    except Exception as e:
        return []


def extract_temperature(image_path: str, reader: easyocr.Reader) -> tuple[str, float]:
    """
    Extract temperature from trail camera image with retry logic.
    
    Args:
        image_path: Path to the image file
        reader: Pre-initialized EasyOCR reader
        
    Returns:
        Tuple of (extracted_text, confidence_score)
    """
    try:
        # Load image to get dimensions
        img = Image.open(image_path)
        width, height = img.size
        
        # Define multiple retry strategies
        retry_strategies = [
            # Strategy 1: Original approach
            {
                'bounding_box': (0, int(height * 0.90), int(width * 0.4), height),
                'preprocessing': {'enhance': True, 'contrast': 1.5, 'brightness': 1.2, 'width_ths': 0.7, 'height_ths': 0.7}
            },
            # Strategy 2: Larger bounding box, more aggressive preprocessing
            {
                'bounding_box': (0, int(height * 0.88), int(width * 0.5), height),
                'preprocessing': {'enhance': True, 'contrast': 2.0, 'brightness': 1.4, 'width_ths': 0.5, 'height_ths': 0.5}
            },
            # Strategy 3: Even larger box, different EasyOCR thresholds
            {
                'bounding_box': (0, int(height * 0.85), int(width * 0.6), height),
                'preprocessing': {'enhance': True, 'contrast': 1.8, 'brightness': 1.1, 'width_ths': 0.3, 'height_ths': 0.3}
            },
            # Strategy 4: Full bottom strip, minimal preprocessing
            {
                'bounding_box': (0, int(height * 0.92), width, height),
                'preprocessing': {'enhance': True, 'contrast': 1.2, 'brightness': 1.1, 'width_ths': 0.8, 'height_ths': 0.8}
            }
        ]
        
        # Try each strategy until we find a temperature
        for strategy_idx, strategy in enumerate(retry_strategies):
            results = extract_temperature_with_settings(
                image_path, 
                reader, 
                strategy['bounding_box'], 
                strategy['preprocessing']
            )
            
            if not results:
                continue
            
            # Look for temperature pattern in results - try multiple patterns in order of preference
            temp_result = parse_temperature_from_results(results)
            if temp_result:
                return temp_result
        
        # If all strategies failed, return failure
        return "No temperature found in any retry attempt", 0.0
            
    except Exception as e:
        return f"Error: {str(e)}", 0.0


def parse_temperature_from_results(results) -> tuple[str, float] | None:
    """
    Parse temperature from OCR results using multiple pattern matching strategies.
    
    Args:
        results: EasyOCR results list
        
    Returns:
        Tuple of (temperature_value, confidence) or None if not found
    """
    for (bbox, text, confidence) in results:
        # Pattern 1: Look for Celsius temperature specifically (number before °C)
        # Patterns: "12 °C", "12°C", "12 'C", "12C", "12 ·C"
        celsius_match = re.search(r'(\d+)\s*[°\'·]?\s*C', text, re.IGNORECASE)
        if celsius_match:
            temp_value = celsius_match.group(1)
            return temp_value, confidence
        
        # Pattern 2: Temperature display with T prefix "T 12 °C / 53 °F"
        temp_display_match = re.search(r'T\s+(\d+)\s*[°\'·]?\s*C', text, re.IGNORECASE)
        if temp_display_match:
            temp_value = temp_display_match.group(1)
            return temp_value, confidence
        
        # Pattern 3: Look for "X °C / Y °F" pattern and take the first number (Celsius)
        celsius_fahrenheit_match = re.search(r'(\d+)\s*[°\'·]?\s*C\s*/\s*\d+\s*[°\'·]?\s*F', text, re.IGNORECASE)
        if celsius_fahrenheit_match:
            temp_value = celsius_fahrenheit_match.group(1)
            return temp_value, confidence
            
        # Pattern 4: OCR might misread symbols - look for number before C in temperature context
        # Handle cases where OCR reads symbols as letters/numbers
        temp_context_match = re.search(r'(\d+)\s*[^\w\s]*\s*C(?:\s|/|\s*\d)', text, re.IGNORECASE)
        if temp_context_match:
            temp_value = temp_context_match.group(1)
            return temp_value, confidence
    
    return None




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
        # Extract deployment ID and timestamp from filename
        deployment_id = extract_deployment_id(file_path.name)
        timestamp = extract_timestamp(file_path.name)
        
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
            'timestamp': timestamp,
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
        timestamp = extract_timestamp(input_path.name)
        reader = easyocr.Reader(['en'], gpu=True)
        result, confidence = extract_temperature(str(input_path), reader)
        temp_int, is_valid = validate_temperature(result)
        
        print(f"\nResults:")
        print(f"  Deployment ID: {deployment_id}")
        print(f"  Timestamp: {timestamp}")
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