# CLAUDE.md - Monarch Trailcam Classifier Project Guidelines

## Run Commands
- Run the converter: `python convert_classifications.py`
- Run with custom input: `python convert_classifications.py -i /Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Deployments/SC1/classifications.json`
- Run with output file: `python convert_classifications.py -i /Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Deployments/SC1/classifications.json -o results.json`

## Code Style Guidelines
- **Formatting**: Use 4-space indentation, follow PEP 8 guidelines
- **Imports**: Standard library imports first, then third-party, then local modules
- **Documentation**: Include docstrings for all functions using Google style format
- **Error Handling**: Use try/except blocks for file operations and JSON parsing
- **Naming Conventions**:
  - Variables/functions: snake_case
  - Constants: UPPER_SNAKE_CASE
  - Classes: PascalCase
- **Type Hints**: Consider adding type hints to function signatures for better code clarity
- **Logging**: For serious errors, use print statements with descriptive error messages

## Code Organization
- Keep scripts focused on a single responsibility
- Prefer functions over classes for simple data processing tasks
- Use constants for shared values (e.g., COUNT_MAPPING)
- Separate CLI argument handling from core business logic
- Keep things simple. Don't over-engineer solutions.