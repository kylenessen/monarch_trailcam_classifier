# Trail Camera Classification Converter

## Project Overview
A simple Python script to convert categorical count values from trail camera classifications to numerical totals, and extract deployment ID and timestamp information from filenames.

## What it does
This script reads a `classifications.json` file containing trail camera image classifications, converts categorical count values (like "1-9", "10-99") to numerical values, and sums them for each image. It also extracts the deployment ID and timestamp from the image filenames.

## Input
- `classifications.json` file with image classifications

## Output
- CSV file with columns:
  - `filename`: The image filename
  - `count`: The calculated count total
  - `deployment_id`: The deployment ID extracted from the filename (e.g., "SC1" from "SC1_20231117114501.JPG") 
  - `timestamp`: The timestamp extracted from the filename (e.g., "20231117114501" from "SC1_20231117114501.JPG")

## Count Conversion
- "1-9" → 1
- "10-99" → 10
- "100-999" → 100
- "1000+" → 1000
- 0 → Included in total calculation

## Example
For an image with cells containing counts: 0, "1-9", "1-9", "10-99"
The calculated total would be: 0 + 1 + 1 + 10 = 12

## Usage
Run the script in the same directory as your classifications.json file:

```
python convert_classifications.py
```

Specify a custom input file:

```
python convert_classifications.py -i /path/to/your/classifications.json
```

Specify both input and output files:

```
python convert_classifications.py -i /path/to/your/classifications.json -o results.csv
```

Command-line Arguments:
- `-i, --input`: Path to input classifications.json file (default: classifications.json in current directory)
- `-o, --output`: Path to output CSV file (default: count_totals.csv in current directory)

The script will output a CSV file with filenames, total counts, deployment IDs, and timestamps, and will also print summary statistics to the console.

## Example Output CSV

```
filename,count,deployment_id,timestamp
SC1_20231117114501.JPG,12,SC1,20231117114501
SC1_20231117120030.JPG,5,SC1,20231117120030
```


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