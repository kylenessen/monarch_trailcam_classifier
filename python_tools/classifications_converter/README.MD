# Trail Camera Classification Converter

## Project Overview
A simple Python script to convert categorical count values from trail camera classifications to numerical totals.

## What it does
This script reads a `classifications.json` file containing trail camera image classifications, converts categorical count values (like "1-9", "10-99") to numerical values, and sums them for each image.

## Input
- `classifications.json` file with image classifications

## Output
- Dictionary/JSON with image filenames as keys and calculated count totals as values

## Count Conversion
- "1-9" → 1
- "10-99" → 10
- "100-999" → 100
- "1000+" → 1000
- 0 → Ignored in totals

## Example
For an image with cells containing counts: 0, "1-9", "1-9", "10-99"
The calculated total would be: 0 + 1 + 1 + 10 = 12

## Usage
Just run the script in the same directory as your classifications.json file, or modify the file path in the script.

```
python convert_classifications.py
```

The script will output a simple mapping of filenames to their total counts.


## Example JSON

```json
{
  "SC1_20231117114501.JPG": {
    "confirmed": true,
    "cells": {
      "cell_0_0": {
        "count": 0,
        "directSun": false
      },
      "cell_0_1": {
        "count": "1-9",
        "directSun": false
      },
      "cell_0_2": {
        "count": "10-99",
        "sunlight": false
      },
      "cell_0_3": {
        "count": "10-99",
        "sunlight": false
      },
      "cell_0_4": {
        "count": "1-9",
        "sunlight": false
      },
      "cell_0_5": {
        "count": "1-9",
        "sunlight": false
      },
      "cell_0_6": {
        "count": 0,
        "directSun": false
      }
    },
    "index": 1,
    "user": "SM"
  }
}
```