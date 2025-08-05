---
date: '2025-08-04T22:21:28+00:00'
duration_seconds: 3.6
keywords:
- python
- data extraction
- ocr
- image processing
- data architecture
- sqlite
- csv
llm_service: openrouter
original_filename: 250804_1521.mp3
processed_date: '2025-08-04T23:26:55.503985'
word_count: 536
---
# Project Data Plan: Extraction and Architecture

I'm at the point where I can start doing some analysis, but first, I need to process and structure the data. The first task is extracting temperature values from the images.

## Python Script: Temperature Extraction

The goal is to create a Python script that extracts temperature values from a directory of images.

### Script Logic
1.  **Input**: The user will pass a path to the main deployments directory.
2.  **File Discovery**: The script will recursively search the entire directory for images that match a specific file name pattern. This provides a validation step to ensure only the correct photos are processed.
3.  **Processing Loop**: The script can be slow, so a simple loop through each found file is acceptable. For each image:
    *   **Crop Image**: Crop the image to a specific bounding box that contains only the temperature number. This can be loaded into memory without saving a temporary file.
        *   *Consideration*: The bounding box coordinates could be hard-coded since the files are identical. However, it might be better to use a relative measure in case file sizes or resolutions change in the future.
    *   **OCR**: Use an OCR library to extract the number from the cropped image.
    *   **Data Validation**: The extracted value should be validated as an integer, likely between 0 and 100.
4.  **Data Extraction**: For each image, the script should capture:
    *   The full file path and name (to use as a key for joining with other data).
    *   The extracted temperature value.
    *   The OCR confidence score, if available.
    *   The deployment ID, which can be extracted from the filename or the top-level folder name.

### Output
*   All extracted data should be collected into a single data frame in memory.
*   Finally, export the data frame to a single CSV file saved in the same directory.

## Overall Data Architecture

I need to consolidate all the disparate project information into one place. I'm considering either a series of linked CSV files or creating a single SQLite database for all the data.

### Data Sources to Consolidate

1.  **Temperature Data**: This will come from the new Python script described above.

2.  **Wind Data**: The wind data currently exists in separate SQL databases for each sensor. The goal is to combine these into a single table with a `sensor_name` column to differentiate them. This will create a single location for all wind metric logic.

3.  **Deployment Metadata**: I need a table for deployment metadata, containing:
    *   Deployment ID
    *   Latitude & Longitude
    *   Height above ground
    *   View angle
    *   Who labeled it
    *   View ID
    *   Associated wind meter
    *   Dates of deployment

4.  **Abundance Indexes (Butterfly Counts)**: This is the most complex part to structure. Some ideas include:
    *   **Simple Count**: A table with the total number of butterflies and the total number of butterflies in direct sun for each photo.
    *   **Percentage**: A metric like "percentage of monarchs in the sun."
    *   **Cell-Level Tracking**: Tracking sun exposure for each butterfly at a cell level. This seems messy and might not be necessary for the analysis.

*Note: The long, irrelevant conversation with a neighbor has been excluded from this summary as requested.*