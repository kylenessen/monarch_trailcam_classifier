#!/usr/bin/env python3
"""
MVP script to extract temperature from a single trail camera image using OCR.
"""

import argparse
import sys
from pathlib import Path

import easyocr
from PIL import Image


def extract_temperature(image_path: str) -> tuple[str, float]:
    """
    Extract temperature from trail camera image.
    
    Args:
        image_path: Path to the image file
        
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
        
        # Initialize EasyOCR reader (English only for speed)
        reader = easyocr.Reader(['en'], gpu=False)
        
        # Extract text from cropped region
        results = reader.readtext(cropped_array)
        
        # Look for temperature pattern in results
        import re
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


def main():
    parser = argparse.ArgumentParser(description="Extract temperature from trail camera image")
    parser.add_argument(
        "image_path", 
        nargs='?',
        default="sample_images/SC4_20231203223001.JPG",
        help="Path to image file (default: sample_images/SC4_20231203223001.JPG)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"Processing image: {image_path}")
    print("Extracting temperature...")
    
    # Extract temperature
    result, confidence = extract_temperature(str(image_path))
    
    # Display results
    print(f"\nExtracted: {result}")
    print(f"Confidence: {confidence:.2f}")


if __name__ == "__main__":
    main()