# Temperature Anomaly Detection Exploration: Journey and Lessons Learned

## Overview

This document captures the exploration journey for detecting and correcting temperature anomalies in trail camera OCR-extracted data. The goal was to identify discontinuous temperature readings caused by OCR errors, particularly Fahrenheit vs Celsius confusion.

**Key Challenge**: Trail cameras display temperatures in both units (e.g., "12°C / 53°F"), and OCR occasionally reads the Fahrenheit value instead of the intended Celsius value.

## The Dataset

- **56,066 temperature records** from 18 trail camera deployments
- **99.7% success rate** from initial OCR extraction
- **170 failed extractions** (NaN values) representing real data that OCR couldn't read
- Temperature range: 0-72°C (including obvious errors)

### Sample Data Structure
```csv
filename,deployment_id,timestamp,temperature,confidence,extraction_status
SC1_20231117114001.JPG,SC1,20231117114001,22.0,0.7918646618999018,success
SC3_20231124082001.JPG,SC3,20231124082001,71.0,0.497045,success  # <-- Fahrenheit error
SC5_20240120095001.JPG,SC5,20240120095001,0.0,0.483301,success   # <-- Extraction error
```

## Journey of Exploration

### Phase 1: Simple Threshold Detection
**Initial Approach**: Flag temperatures ≥40°C as Fahrenheit conversion errors.

**Results**: Found 14 clear outliers (40-72°C) that converted to reasonable Celsius values.

```python
# Simple threshold approach
fahrenheit_errors = df[df['temperature'] >= 40]
for _, row in fahrenheit_errors.iterrows():
    celsius = (row['temperature'] - 32) * 5/9
    print(f"{row['temperature']}°F → {celsius:.1f}°C")
```

**Learning**: This caught obvious cases but missed subtler anomalies and didn't address missing data.

### Phase 2: Temperature Jump Detection
**Approach**: Detect discontinuous spikes using 3-point patterns (normal → spike → normal).

```python
def detect_temperature_spikes(df_deployment, spike_threshold=8):
    data = df_deployment.sort_values('timestamp').reset_index(drop=True)
    data['temp_diff'] = data['temperature'].diff()
    data['next_diff'] = data['temp_diff'].shift(-1)
    
    spike_indices = []
    for i in range(1, len(data)-1):
        curr_jump = data.iloc[i]['temp_diff']
        next_jump = data.iloc[i]['next_diff']
        
        # Check for spike pattern: large jump in, large jump out (opposite direction)
        if (abs(curr_jump) > spike_threshold and 
            abs(next_jump) > spike_threshold and
            curr_jump * next_jump < 0):  # Opposite signs
            spike_indices.append(i)
    
    return spike_indices
```

**Results**: Found 73 discontinuous spikes across all deployments.

**Issues Discovered**:
1. **Missing values (NaN) broke detection** - algorithm couldn't handle edges
2. **Consecutive anomalies missed** - only caught single-point spikes  
3. **False positives** from adjacent anomalies disrupting patterns

**Key Insight**: The user correctly identified that NaN values represent **real temperature readings that failed OCR**, not missing data points.

### Phase 3: Sliding Window Regression Approach
**User's Sophisticated Idea**: Fit local polynomial curves to capture daily temperature cycles, then detect outliers using residuals.

**Implementation**:
```python
def sliding_window_anomaly_detection(df_deployment, window_hours=48, poly_degree=3):
    # Convert timestamp to datetime and create hour offset
    data['hours_from_start'] = (data['datetime'] - data['datetime'].iloc[0]).dt.total_seconds() / 3600
    
    # Sliding window analysis
    for i in range(len(valid_data)):
        # Define window around current point
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(valid_data), i + window_size // 2 + 1)
        
        # Fit robust polynomial regression
        poly_reg = Pipeline([
            ('poly', PolynomialFeatures(degree=poly_degree)),
            ('regressor', HuberRegressor(epsilon=1.35, max_iter=1000))
        ])
        
        poly_reg.fit(X, y)
        prediction = poly_reg.predict([[current_x]])[0]
        residual = actual_temperature - prediction
        
        # Calculate robust z-score using Median Absolute Deviation (MAD)
        z_score = abs(residual - median_residual) / (mad_residual + 1e-8)
```

**Results**: Found 395 anomalies with high sensitivity to natural temperature variations.

**User's Insight**: This approach is theoretically superior because it:
- Handles daily temperature cycles naturally
- Uses robust statistical methods (MAD instead of standard deviation)
- Builds confidence intervals from historical patterns
- Can detect both dramatic spikes AND gradual deviations

**Problem**: Too sensitive - flagged normal temperature variations as anomalies.

### Phase 4: The Missing Data Revelation
**Critical User Observation**: "The NaN values ARE an issue I need to correct. Those values actually do exist."

This was a breakthrough moment. The 170 NaN values weren't missing data points - they were **failed OCR extractions of real temperature displays**.

**Analysis of Failed Extractions**:
```python
# Context analysis around failed extractions
for _, missing_row in missing_data.iterrows():
    # Find surrounding temperatures
    surrounding_temps = get_context_temperatures(missing_row, window=6)
    estimated_temp = np.median(surrounding_temps)
    print(f"Failed: {missing_row['filename']} → Estimated: {estimated_temp:.1f}°C")
```

**Example**:
```
Failed extraction: SC10_20240128084001.JPG
Context: 15°C → 16°C → ??? → 18°C → 18°C
Estimated: ~16.8°C
```

### Phase 5: Focus on Extremes (Final Approach)
**Strategy**: Instead of complex statistical methods, focus on obviously problematic values.

**Three-Tier Classification**:
```python
# 1. Failed OCR extractions (NaN values) - HIGHEST PRIORITY
failed_extractions = df[df['temperature'].isna()]  # 170 cases

# 2. Extreme highs (Fahrenheit conversion errors)  
fahrenheit_errors = df[df['temperature'] >= 40]   # 14 cases

# 3. Extreme lows (extraction errors)
extraction_errors = df[df['temperature'] <= 2]    # 104 cases
```

**Results**: **288 total extreme issues** (0.5% of data)
- **170 failed extractions**: Real data that needs recovery
- **14 Fahrenheit conversions**: Clear mathematical fixes
- **104 low-value errors**: Likely OCR misreads (0-2°C)

## Visualization and Validation

Created comprehensive plots showing temporal patterns with anomalies highlighted:

```python
# Plot with different markers for each issue type
issue_colors = {
    'failed_extraction': 'red',      # Red X's
    'fahrenheit_conversion': 'orange', # Orange circles  
    'extraction_error_low': 'purple'   # Purple squares
}

# Two-panel approach:
# Top: Full time series with all issues
# Bottom: Normal range view (excluding extreme Fahrenheit errors)
```

**Visual Validation**: Plots confirmed that flagged readings were indeed discontinuous and broke natural temperature patterns.

## Algorithms That Match the Sliding Window Approach

The user's intuition about fitting curves and measuring residuals aligns with established methods:

1. **LOESS/LOWESS** - Locally weighted scatterplot smoothing
2. **STL Decomposition** - Seasonal and Trend decomposition using Loess
3. **Seasonal Hybrid ESD** - Twitter's anomaly detection algorithm  
4. **Facebook Prophet** - Anomaly detection with seasonality
5. **Robust Regression + Residual Analysis** - Exactly what we implemented

## Key Lessons Learned

### What Worked Well
1. **Simple thresholds (≥40°C, ≤2°C)** effectively caught obvious errors
2. **Visual validation** through time series plots was crucial
3. **Focusing on extremes** avoided statistical over-sensitivity
4. **Three-tier classification** provided actionable categories

### What Didn't Work
1. **Complex statistical methods were too sensitive** for this dataset
2. **Missing proper handling of NaN values** initially derailed detection
3. **Single-point spike detection** missed edge cases and consecutive errors

### Critical Insights
1. **NaN values represent lost real data**, not missing measurements
2. **Temperature data has strong temporal continuity** - dramatic jumps are almost always errors
3. **Visual inspection is essential** for validating statistical approaches
4. **Simple is often better** than sophisticated for noisy real-world data

### The "Discontinuous" Concept
**User's Key Insight**: Look for single observations that are "WAY out of line from the previous and following observation."

This concept of discontinuity was more effective than:
- Standard statistical outlier detection
- Global z-score thresholds  
- Complex regression residuals

## Remaining Questions and Future Approaches

### Unresolved Issues
1. **Are there subtle Fahrenheit errors below 40°C?** (e.g., 32°F = 0°C confusion)
2. **How to optimally estimate the 170 failed extractions?**
3. **Are there systematic patterns** in OCR failures by deployment, time, or conditions?

### Potential Next Steps
1. **Reprocess failed extraction images** with different OCR settings
2. **Implement hybrid approach**: Simple thresholds + contextual validation
3. **Temporal interpolation** for failed extractions using surrounding readings
4. **Manual validation** of borderline cases

### Alternative Approaches to Try
1. **Change Point Detection** algorithms (PELT, CUSUM)
2. **Isolation Forest** for multivariate anomaly detection
3. **Time series forecasting** with prediction intervals
4. **Domain-specific rules** based on biological temperature constraints

## Code Artifacts Generated

### Scripts Created
1. `extract_temp.py` - Original OCR extraction script
2. `plot_temperature_anomalies.py` - Basic time series visualization  
3. `sliding_window_anomaly_detection.py` - Sophisticated regression approach
4. `comprehensive_data_issues_detector.py` - Multi-method detection (incomplete)
5. `plot_deployment_with_issues.py` - Visualization with issue highlighting

### Data Files Created
1. `temperature_data.csv` - Main dataset (56K records)
2. `extreme_temperature_issues.csv` - Final issue classification (288 records)
3. `anomaly_summary.csv` - Per-deployment statistics
4. Multiple PNG plots for visual validation

### Key Code Patterns
```python
# Robust statistical measures
median_residual = np.median(residuals)
mad_residual = np.median(np.abs(residuals - median_residual))
z_score = abs(residual - median_residual) / (mad_residual + 1e-8)

# Temporal context analysis
def get_surrounding_context(data, index, window=3):
    start = max(0, index - window)
    end = min(len(data), index + window + 1)
    return data.iloc[start:end]

# Issue classification pattern
if temperature >= 40:
    issue_type = 'fahrenheit_conversion'
    action = f'convert: {(temp-32)*5/9:.1f}°C'
elif pd.isna(temperature):
    issue_type = 'failed_extraction' 
    action = 'manual_review_or_reprocess'
elif temperature <= 2:
    issue_type = 'extraction_error_low'
    action = 'interpolate_or_review'
```

## Final Thoughts for Future Explorers

The journey revealed that **data quality issues in OCR-extracted scientific data require domain-specific approaches**. While sophisticated statistical methods have their place, understanding the underlying data generation process (OCR reading temperature displays) was more valuable than advanced algorithms.

The most successful approach combined:
- Simple, interpretable thresholds
- Visual validation
- Domain knowledge about temperature measurement  
- Recognition that "missing" data often represents failed extraction of real measurements

**The user's intuition about "discontinuous" observations was spot-on** - it led to the most actionable results with minimal false positives.

Future work should focus on:
1. Recovering the 170 failed extractions (highest value)
2. Systematic correction of the 14 clear Fahrenheit errors  
3. Validation of the 104 low-value errors through temporal interpolation

The exploration demonstrates that **effective anomaly detection requires iteration between statistical methods, domain expertise, and visual validation**.