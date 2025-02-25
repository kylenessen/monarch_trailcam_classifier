# Index Repair and Diagnostics Tools

This directory contains tools for repairing and diagnosing issues with the `classifications.json` file used in the Monarch Trailcam Classifier project.

## Problem

The `classifications.json` file can sometimes develop issues such as:

1. Gaps in the "index" numbering, causing the program to break
2. Orphaned entries (JSON entries without corresponding image files)
3. Missing entries (image files without corresponding JSON entries)
4. Duplicate indices

These tools help identify and fix these issues.

## Tools

### 1. Index Repair Tool (`index_repair.py`)

This script repairs the index numbering in a `classifications.json` file to ensure sequential values without gaps. It can also identify and handle orphaned entries and missing entries.

#### Usage

```bash
python index_repair.py /path/to/directory [options]
```

#### Options

- `--remove-orphaned`: Remove entries that don't have corresponding image files
- `--no-backup`: Skip creating a backup of the original JSON file
- `--file-extension=EXT`: Extension of image files to look for (default: JPG)
- `--add-missing`: Add entries for image files that don't have corresponding JSON entries
- `--json-filename=FILE`: Name of the JSON file to process (default: classifications.json)
- `--dry-run`: Report what would be done without making changes
- `-v, --verbose`: Increase output verbosity (can be used multiple times)

#### Examples

```bash
# Basic repair of index numbering
python index_repair.py ~/path/to/images/

# Remove orphaned entries and add missing entries
python index_repair.py ~/path/to/images/ --remove-orphaned --add-missing

# Dry run to see what would be changed without making changes
python index_repair.py ~/path/to/images/ --dry-run --verbose

# Use a different file extension and JSON filename
python index_repair.py ~/path/to/images/ --file-extension=jpeg --json-filename=data.json
```

### 2. Index Diagnostics Tool (`index_diagnostics.py`)

This script provides diagnostic functions for analyzing `classifications.json` files and identifying issues such as orphaned entries, missing entries, and duplicate files.

#### Usage

```bash
python index_diagnostics.py <command> /path/to/directory [options]
```

#### Commands

- `orphaned`: Identify orphaned entries (JSON entries without corresponding image files)
- `missing`: Identify missing entries (image files without corresponding JSON entries)
- `originals`: Check for original versions of files with a specific pattern
- `analyze`: Analyze index gaps and inconsistencies

#### Common Options

- `--json-filename=FILE`: Name of the JSON file to process (default: classifications.json)
- `--file-extension=EXT`: Extension of image files to look for (default: JPG)

#### Command-Specific Options

For `orphaned` command:
- `-v, --verbose`: Print detailed information about each orphaned entry

For `originals` command:
- `--pattern=PATTERN`: Pattern to use for identifying potential duplicates (default: " 2.JPG")

#### Examples

```bash
# Identify orphaned entries (JSON entries without corresponding image files)
python index_diagnostics.py orphaned ~/path/to/images/

# Identify missing entries (image files without corresponding JSON entries)
python index_diagnostics.py missing ~/path/to/images/

# Check for original versions of files with a specific pattern
python index_diagnostics.py originals ~/path/to/images/ --pattern=" 2.JPG"

# Analyze index gaps and inconsistencies
python index_diagnostics.py analyze ~/path/to/images/

# Use a different file extension and JSON filename
python index_diagnostics.py orphaned ~/path/to/images/ --file-extension=jpeg --json-filename=data.json
```

## JSON Structure

The scripts expect the `classifications.json` file to have the following structure:

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

## Workflow for Fixing Index Issues

1. **Diagnose the problem**:
   ```bash
   python index_diagnostics.py analyze ~/path/to/images/
   ```

2. **Check for orphaned entries**:
   ```bash
   python index_diagnostics.py orphaned ~/path/to/images/ --verbose
   ```

3. **Check for missing entries**:
   ```bash
   python index_diagnostics.py missing ~/path/to/images/
   ```

4. **If you find duplicate files, check for originals**:
   ```bash
   python index_diagnostics.py originals ~/path/to/images/
   ```

5. **Perform a dry run of the repair**:
   ```bash
   python index_repair.py ~/path/to/images/ --dry-run --verbose
   ```

6. **Repair the index numbering**:
   ```bash
   python index_repair.py ~/path/to/images/
   ```

7. **If needed, remove orphaned entries and add missing entries**:
   ```bash
   python index_repair.py ~/path/to/images/ --remove-orphaned --add-missing
   ```

## Exit Codes

Both scripts return appropriate exit codes:
- 0: Success or no issues found
- 1: Error or issues found

This allows for integration with other scripts or automation tools.