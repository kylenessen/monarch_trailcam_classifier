# Index Repair Script

This script repairs the index numbering in a `classifications.json` file to ensure sequential values without gaps.

## Problem

The `classifications.json` file has a gap in the "index" numbering around 170, causing the program to break. This script repairs the index numbering to ensure sequential values without gaps.

## Usage

```bash
python repair_index.py /path/to/directory
```

Where `/path/to/directory` is the path to the directory containing the image files (JPG) and the `classifications.json` file.

For example, to repair the classifications.json file in the SC2 deployment:

```bash
python repair_index.py ~/Library/CloudStorage/OneDrive-CalPoly/Deployments/SC2/
```

## How It Works

1. The script loads the `classifications.json` file from the specified directory
2. It gets a list of all JPG image files in the directory
3. It verifies that the number of entries in the JSON matches the number of image files
4. It sorts the image files alphabetically (which should correspond to chronological order)
5. It updates the "index" field in each JSON entry to match the sorted order
6. It saves the updated JSON file if any changes were made

## JSON Structure

The script expects the `classifications.json` file to have the following structure:

```json
{
  "IMAGE_FILENAME.JPG": {
    "confirmed": true,
    "cells": {},
    "index": 0,
    "notes": "",
    "user": "VVR"
  },
  "ANOTHER_IMAGE.JPG": {
    "confirmed": true,
    "cells": {},
    "index": 1,
    "notes": "",
    "user": "VVR"
  },
  ...
}
```

## Error Handling

The script checks for various error conditions:
- If the directory exists
- If `classifications.json` exists in the directory
- If the file count matches JSON entry count
- If the JSON structure is valid

## Exit Codes

- 0: Success
- 1: Error