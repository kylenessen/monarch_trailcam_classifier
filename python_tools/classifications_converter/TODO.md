# TODO: Trail Camera Classification Converter (MVP)

## Core Script Development
1. Create a Python script `convert_classifications.py`
2. Import the json library
3. Create a function to load the classifications.json file
4. Define the count category mapping:
   - "1-9" → 1
   - "10-99" → 10
   - "100-999" → 100
   - "1000+" → 1000
   - 0 → Ignore
5. Create a function to convert a single count value using this mapping
6. Implement the main processing loop:
   - Iterate through each image in the JSON
   - For each image, iterate through all cells
   - Convert each count value to a number
   - Sum up the counts for the image
   - Store the result in a dictionary with filename as key
7. Add basic error handling for unexpected count values
8. Print the results to console or write to a simple output file
9. Add some minimal documentation (comments) to explain what the script does

## Testing & Verification
10. Run the script on your classifications.json file
11. Verify a few examples manually to ensure the counts are correct
12. Make any necessary adjustments