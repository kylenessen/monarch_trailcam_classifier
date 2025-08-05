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

### Error Handling
- Log failed extractions to console
- Continue processing on individual failures
- Include extraction status in output CSV

### Dependencies
- `easyocr`: OCR processing
- `pandas`: Data handling and CSV export
- `PIL/Pillow`: Image manipulation
- `tqdm`: Progress bar display

## Sample Data
Located in `sample_images/`:
- `SC11_20240106033501.JPG`
- `SC4_20231203223001.JPG` 
- `UDMH2_20240105142001.JPG`

## Implementation Notes
- Keep simple - this is a one-off project
- Hard-code bounding box coordinates initially
- No edge case handling needed for this iteration
- Focus on extracting temperature digits cleanly