# Temperature Extraction Script Specification

## Overview
Extract temperature values from trail camera images using OCR to support sunlight-temperature hypothesis analysis.

## Requirements

### Input
- Directory path containing deployment photos
- Images follow naming pattern: `{DEPLOYMENT_ID}_{TIMESTAMP}.JPG`
  - Examples: `SC4_20231203223001.JPG`, `SC11_20240106033501.JPG`, `UDMH2_20240105142001.JPG`
- Deployment ID extraction: everything before the first underscore

### Processing
- **OCR Library**: EasyOCR (robust for digit extraction, built-in confidence scoring)
- **Image Handling**: Process images as-is, no preprocessing required
- **Bounding Box**: Hard-coded coordinates (consistent camera models assumed)
- **Validation**: Simple integer validation between 0-100
- **Progress**: Display progress bar during processing

### Output
CSV file with columns:
- `filename`: Full filename
- `deployment_id`: Extracted from filename (text before first underscore)
- `temperature`: Extracted temperature value (integer)
- `confidence`: OCR confidence score
- `extraction_status`: "success" or "failed"

### Assumptions
- All images are same size/format (consistent camera models)
- No error displays in temperature readings (no "ERR", "---", etc.)
- No image preprocessing needed
- Performance not critical (simple sequential processing acceptable)

## Current Implementation Status

### ✅ MVP Script Complete (`extract_temp_mvp.py`)
**Functionality:**
- Single image temperature extraction
- EasyOCR integration with CPU processing
- Hard-coded bounding box: bottom 10% of image, left 40% of width
- Robust pattern matching for temperature text (handles OCR misreads like '€ vs °C)
- Command-line interface with default sample image

**Testing Results:**
- `SC4_20231203223001.JPG`: Successfully extracted "12" from "12°C / 53°F"
- `SC11_20240106033501.JPG`: Successfully extracted "7" from "7°C / 44°F"  
- `UDMH2_20240105142001.JPG`: Successfully extracted "19" from "19°C / 66°F"

**Dependencies (via UV):**
- `easyocr==1.7.2`: OCR processing
- `pillow==11.3.0`: Image manipulation
- `numpy`: Array conversion for EasyOCR

### 🚧 Still Needed
1. **Directory Processing**: Extend to process entire directories recursively
2. **CSV Export**: Add pandas dependency and export functionality
3. **Progress Bar**: Add tqdm for batch processing feedback
4. **Deployment ID Extraction**: Parse filename for deployment ID
5. **Validation**: Ensure extracted values are reasonable (0-100)

## Technical Approach

### Script Logic
1. **File Discovery**: Recursively find all `.JPG` files matching the naming pattern
2. **Processing Loop**: For each image:
   - Extract deployment ID from filename
   - Crop to hard-coded bounding box containing temperature display
   - Use EasyOCR to extract number
   - Validate as integer 0-100
   - Record result with confidence score
3. **Output**: Export all results to CSV in same directory

### Proven Bounding Box Coordinates
```python
# Works for all tested camera models
left = 0
top = int(height * 0.90)  # Bottom 10% of image
right = int(width * 0.4)   # Left 40% of width  
bottom = height
```

### Error Handling
- Log failed extractions to console
- Continue processing on individual failures
- Include extraction status in output CSV

## Sample Data
Located in `sample_images/`:
- `SC11_20240106033501.JPG` - 7°C
- `SC4_20231203223001.JPG` - 12°C
- `UDMH2_20240105142001.JPG` - 19°C

## Implementation Notes
- Keep simple - this is a one-off project
- Hard-coded bounding box works across all camera models tested
- EasyOCR handles temperature display variations well
- No edge case handling needed for this iteration
- Focus on extracting temperature digits cleanly