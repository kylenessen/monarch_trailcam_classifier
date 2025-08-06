# Temperature Data Cleaning Methods

## Overview

This document describes the systematic approach used to clean OCR-extracted temperature data from trail camera images. The cleaning process addressed missing values, extreme outliers, and temporal discontinuities through a combination of automated detection and manual validation.

## Data Source

- **Original dataset**: `temperature_data.csv` containing OCR-extracted temperature values from trail camera images
- **Initial records**: ~56,000 temperature readings across multiple deployment sites
- **Primary issues identified**: Missing values (~170 records), extreme outliers (values ≥35°C or ≤2°C), and temporal discontinuities

## Phase 1: Initial Data Exploration and Missing Value Identification

### Tools Used
- `data_exploration.py`: Automated outlier detection and visualization script

### Process
1. **Threshold-based outlier detection**: Applied simple thresholds to identify problematic values:
   - High temperature outliers: ≥35°C (likely Fahrenheit conversion errors)
   - Low temperature outliers: ≤2°C (likely OCR misreads)
   - Missing values: NaN entries where OCR failed completely

2. **Visualization**: Generated time series plots for each deployment to visualize temperature patterns and identify anomalies

3. **Missing value prioritization**: Identified ~170 missing temperature values as the primary data gap requiring immediate attention

## Phase 2: Manual Entry for Missing Values

### Tools Used
- `manual_temperature_entry.py`: Custom GUI application for manual data entry
- Input file: `missing_temperature_images.csv` (list of images with missing temperature data)

### Process
1. **GUI-based manual entry**: Developed a tkinter-based application that:
   - Displayed trail camera images one at a time
   - Provided input field for temperature entry in Celsius
   - Included navigation controls and validation warnings
   - Saved entries with confidence=1.0 and extraction_status="manual_entry"

2. **Output**: `missing_temperature_data.csv` containing manually entered temperature values for previously missing data points

## Phase 3: Manual Entry for Extreme Outliers

### Tools Used
- Same `manual_temperature_entry.py` GUI application
- Input: Extreme outlier list generated from updated analysis

### Process
1. **Re-analysis**: After filling missing values, re-ran outlier detection to identify remaining extreme values

2. **Manual correction of outliers**: Used the same GUI tool to:
   - Review images with temperature readings ≥35°C or ≤2°C
   - Manually re-enter correct temperature values
   - Validate suspected Fahrenheit-to-Celsius conversion errors

3. **Output**: `manual_extreme_temperature_entries.csv` containing corrected extreme temperature values

## Phase 4: Interactive Review for Temporal Discontinuities

### Tools Used
- `manual_review.py`: Interactive Dash web application with Plotly visualization

### Process
1. **Deployment-by-deployment review**: 
   - Loaded combined dataset (original + corrections from previous phases)
   - Generated interactive time series plots for each deployment
   - Enabled point-and-click selection of suspicious values

2. **Discontinuity detection**: Manually identified temperature values that showed significant jumps or drops compared to temporally adjacent readings, indicating potential OCR errors

3. **Iterative marking and correction**:
   - Clicked suspicious points on interactive plots to mark them for follow-up
   - Exported marked points to deployment-specific CSV files (e.g., `SC2_followup.csv`, `SC4_followup.csv`)
   - Used GUI application to manually verify and correct flagged values
   - Re-ran interactive review to catch any remaining issues
   - **Repeated this process multiple times** until no further discontinuities were detected

4. **Validation**: Some initially suspicious values were determined to be correct upon manual verification of source images

## Phase 5: Final Data Integration

### Tools Used
- `clean_temperature_data.py`: Data merging and final output script

### Process
1. **Hierarchical data merging**: Combined original dataset with correction files in order of confidence:
   - Original OCR data (baseline)
   - Missing value corrections
   - Extreme outlier corrections  
   - Temporal discontinuity corrections

2. **Conflict resolution**: Manual entries (confidence=1.0) always overwrote automated OCR values when conflicts existed

3. **Final output**: `cleaned_temperature_data.csv` containing the complete, cleaned temperature dataset

## Key Technical Decisions

### Manual Entry Over Re-OCR
- **Rationale**: Given initial OCR failure, manual entry provided higher reliability than attempting to re-process problematic images
- **Implementation**: Custom GUI tool ensured efficient, systematic data entry with built-in validation

### Iterative Approach
- **Rationale**: Each cleaning phase revealed new data quality issues that required attention
- **Implementation**: Modular scripts allowed repeated analysis and correction cycles

### Data Integrity Preservation
- **Rationale**: Never modified original source data to maintain audit trail
- **Implementation**: Correction files applied as overlays, allowing rollback if needed

### Confidence-Based Merging
- **Rationale**: Manual entries should always override automated extractions
- **Implementation**: Manual entries assigned confidence=1.0; merging logic prioritized higher confidence values

## Quality Assurance

1. **Visual validation**: Time series plots generated at each phase to verify corrections
2. **Iterative review**: Multiple passes through interactive review tool to catch remaining issues
3. **Spot checking**: Manual verification of suspicious values confirmed accuracy of both corrections and originally flagged values determined to be correct

## Final Dataset Quality

- **Total records**: ~56,000 temperature readings
- **Missing values**: Eliminated through systematic manual entry
- **Extreme outliers**: Corrected through manual verification
- **Temporal discontinuities**: Identified and corrected through iterative interactive review
- **Data integrity**: Original values preserved; corrections applied via overlay files