#!/usr/bin/env python3
"""
Comprehensive detection of temperature data issues including:
1. Failed OCR extractions (NaN values) 
2. Extreme anomalies using sliding window approach
3. Potential Fahrenheit conversion errors
4. Estimation for missing values
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline

def detect_failed_extractions(df):
    """Identify all failed OCR extractions (NaN temperatures)."""
    missing_data = df[df['temperature'].isna()].copy()
    
    failed_extractions = []
    for deployment in missing_data['deployment_id'].unique():
        deployment_data = df[df['deployment_id'] == deployment].sort_values('timestamp').reset_index()
        deployment_missing = missing_data[missing_data['deployment_id'] == deployment]
        
        for _, missing_row in deployment_missing.iterrows():
            # Find surrounding context
            missing_idx = deployment_data[deployment_data['filename'] == missing_row['filename']].index
            
            if len(missing_idx) > 0:
                idx = missing_idx[0]
                
                # Get ±3 surrounding readings for better estimation
                start_idx = max(0, idx - 3)
                end_idx = min(len(deployment_data), idx + 4)
                context = deployment_data.iloc[start_idx:end_idx]
                
                # Calculate estimated temperature from valid surrounding readings
                surrounding_temps = context[context['temperature'].notna()]['temperature'].values
                
                if len(surrounding_temps) > 0:
                    estimated_temp = np.median(surrounding_temps)  # Use median for robustness
                    temp_std = np.std(surrounding_temps) if len(surrounding_temps) > 1 else 0
                else:
                    estimated_temp = np.nan
                    temp_std = np.nan
                
                failed_extractions.append({
                    'filename': missing_row['filename'],
                    'deployment_id': missing_row['deployment_id'], 
                    'timestamp': missing_row['timestamp'],
                    'confidence': missing_row['confidence'],
                    'estimated_temperature': estimated_temp,
                    'context_std': temp_std,
                    'issue_type': 'failed_extraction',
                    'priority': 'high',  # These are missing real data
                    'action': 'manual_review_or_reprocess'
                })
    
    return pd.DataFrame(failed_extractions)

def detect_extreme_anomalies(df_deployment, z_threshold=10.0):
    """Detect extreme anomalies using sliding window regression."""
    data = df_deployment.copy()
    data = data.sort_values('timestamp').reset_index(drop=True)
    
    # Remove missing values for analysis
    valid_data = data.dropna(subset=['temperature']).copy()
    
    if len(valid_data) < 20:
        return []
    
    # Convert timestamp to hours for regression
    valid_data['datetime'] = pd.to_datetime(valid_data['timestamp'].astype(str), format='%Y%m%d%H%M%S')
    valid_data['hours_from_start'] = (valid_data['datetime'] - valid_data['datetime'].iloc[0]).dt.total_seconds() / 3600
    
    # Sliding window parameters
    window_size = min(48, len(valid_data) // 3)
    residuals = np.full(len(valid_data), np.nan)
    
    # Calculate residuals using sliding window
    for i in range(len(valid_data)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(valid_data), i + window_size // 2 + 1)
        
        if end_idx - start_idx < 10:
            continue
            
        window_data = valid_data.iloc[start_idx:end_idx].copy()
        X = window_data['hours_from_start'].values.reshape(-1, 1)
        y = window_data['temperature'].values
        
        # Robust polynomial regression
        poly_reg = Pipeline([
            ('poly', PolynomialFeatures(degree=3)),
            ('regressor', HuberRegressor(epsilon=1.35, max_iter=1000))
        ])
        
        try:
            poly_reg.fit(X, y)
            current_x = valid_data.iloc[i]['hours_from_start']
            prediction = poly_reg.predict([[current_x]])[0]
            residual = valid_data.iloc[i]['temperature'] - prediction
            residuals[i] = residual
        except:
            continue
    
    # Calculate robust z-scores
    valid_residuals = residuals[~np.isnan(residuals)]
    if len(valid_residuals) == 0:
        return []
    
    median_residual = np.median(valid_residuals)
    mad_residual = np.median(np.abs(valid_residuals - median_residual))
    
    extreme_anomalies = []
    for i, residual in enumerate(residuals):
        if not np.isnan(residual):
            z_score = abs(residual - median_residual) / (mad_residual + 1e-8)
            
            if z_score > z_threshold:
                row = valid_data.iloc[i]
                
                # Classify type of anomaly
                if row['temperature'] >= 40:
                    issue_type = 'fahrenheit_conversion'
                    priority = 'high'
                    action = f'convert_to_celsius: {(row["temperature"] - 32) * 5/9:.1f}°C'
                elif row['temperature'] <= 2:
                    issue_type = 'extraction_error_low'
                    priority = 'high' 
                    action = 'manual_review_or_interpolate'
                else:
                    issue_type = 'extreme_outlier'
                    priority = 'medium'
                    action = 'manual_review'
                
                extreme_anomalies.append({
                    'filename': row['filename'],
                    'deployment_id': row['deployment_id'],
                    'timestamp': row['timestamp'],
                    'temperature': row['temperature'],
                    'confidence': row['confidence'],
                    'residual': residual,
                    'z_score': z_score,
                    'issue_type': issue_type,
                    'priority': priority,
                    'action': action
                })
    
    return extreme_anomalies

def comprehensive_data_issue_detection(df):
    """Run comprehensive detection of all temperature data issues."""
    
    print("=== Comprehensive Temperature Data Issues Detection ===")
    
    # 1. Detect failed extractions (NaN values)
    print("\n1. Detecting failed OCR extractions...")
    failed_extractions = detect_failed_extractions(df)
    print(f"   Found {len(failed_extractions)} failed extractions")
    
    # 2. Detect extreme anomalies per deployment
    print("\n2. Detecting extreme anomalies using sliding window regression...")
    all_extreme_anomalies = []
    
    for deployment in df['deployment_id'].unique():
        deployment_data = df[df['deployment_id'] == deployment]
        if len(deployment_data) < 20:
            continue
            
        extreme_anomalies = detect_extreme_anomalies(deployment_data, z_threshold=10.0)
        all_extreme_anomalies.extend(extreme_anomalies)
    
    extreme_anomalies_df = pd.DataFrame(all_extreme_anomalies)
    print(f"   Found {len(extreme_anomalies_df)} extreme anomalies")
    
    # 3. Combine all issues
    print("\n3. Combining and prioritizing all issues...")
    
    # Convert failed extractions to same format
    if len(failed_extractions) > 0:
        failed_extractions['temperature'] = np.nan
        failed_extractions['residual'] = np.nan  
        failed_extractions['z_score'] = np.nan
    
    # Combine dataframes
    if len(extreme_anomalies_df) > 0 and len(failed_extractions) > 0:
        all_issues = pd.concat([failed_extractions, extreme_anomalies_df], ignore_index=True)
    elif len(extreme_anomalies_df) > 0:
        all_issues = extreme_anomalies_df
    elif len(failed_extractions) > 0:
        all_issues = failed_extractions
    else:
        all_issues = pd.DataFrame()
    
    # Sort by priority and z-score
    if len(all_issues) > 0:
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_issues['priority_num'] = all_issues['priority'].map(priority_order)
        all_issues = all_issues.sort_values(['priority_num', 'z_score'], ascending=[True, False])
        all_issues = all_issues.drop('priority_num', axis=1)
    
    return all_issues, failed_extractions, extreme_anomalies_df

def main():
    """Run comprehensive analysis and generate report."""
    
    # Load data
    df = pd.read_csv('temperature_data.csv')
    
    # Run comprehensive detection
    all_issues, failed_extractions, extreme_anomalies = comprehensive_data_issue_detection(df)
    
    # Generate summary report
    print(f"\n=== SUMMARY REPORT ===")
    print(f"Total temperature records: {len(df):,}")
    print(f"Total issues found: {len(all_issues)}")
    print(f"  - Failed extractions (NaN): {len(failed_extractions)}")
    print(f"  - Extreme anomalies: {len(extreme_anomalies)}")
    
    if len(all_issues) > 0:
        print(f"\nIssues by type:")
        print(all_issues['issue_type'].value_counts())
        
        print(f"\nIssues by priority:")
        print(all_issues['priority'].value_counts())
        
        print(f"\nTop 10 most problematic issues:")
        display_cols = ['filename', 'deployment_id', 'temperature', 'z_score', 'issue_type', 'action']
        top_issues = all_issues[display_cols].head(10)
        for _, row in top_issues.iterrows():
            temp_str = f"{row['temperature']:.1f}°C" if pd.notna(row['temperature']) else "NaN"
            z_str = f"(z={row['z_score']:.1f})" if pd.notna(row['z_score']) else ""
            print(f"  {row['filename']}: {temp_str} {z_str} → {row['action']}")
        
        # Save full report
        output_file = 'temperature_data_issues_report.csv'
        all_issues.to_csv(output_file, index=False)
        print(f"\n✅ Full issues report saved to: {output_file}")
        
        # Save failed extractions for potential re-processing
        if len(failed_extractions) > 0:
            failed_file = 'failed_extractions_for_reprocessing.csv'
            failed_extractions.to_csv(failed_file, index=False)
            print(f"✅ Failed extractions saved to: {failed_file}")
    
    return all_issues

if __name__ == "__main__":
    issues = main()