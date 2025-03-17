#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the converter script with any provided arguments
python convert_classifications.py -i /Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Deployments/SC4/classifications.json -o results.csv -w /Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Deployments/SC4/StarDust.s3db

# Deactivate the virtual environment
deactivate


# Run this script with the following command:
# bash run_converter.sh