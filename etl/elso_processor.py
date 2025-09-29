"""
ELSO-aligned ETL Pipeline for ECMO Data Processing
Taiwan ECMO CDSS - Extract, Transform, Load module
"""

import pandas as pd
import numpy as np
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ELSODataProcessor:
    """
    ELSO-aligned data processor for ECMO clinical data
    Handles extraction, transformation, and validation of ECMO data
    """
    
    def __init__(self, data_dict_path: str = "../data_dictionary.yaml"):
        """Initialize processor with ELSO data dictionary"""
        self.load_data_dictionary(data_dict_path)
        self.validation_errors = []
    
    def load_data_dictionary(self, path: str):
        """Load ELSO-aligned data dictionary"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.data_dict = yaml.safe_load(f)
            logger.info(f"Loaded data dictionary v{self.data_dict['version']}")
        except FileNotFoundError:
            logger.error(f"Data dictionary not found at {path}")
            self.data_dict = {}
    
    def validate_patient_data(self, patient_data: Dict) -> bool:
        """
        Validate patient data against ELSO standards
        
        Args:
            patient_data: Dictionary containing patient information
            
        Returns:
            bool: True if validation passes
        """
        is_valid = True
        errors = []
        
        # Validate demographics
        if 'demographics' in self.data_dict:
            for field, specs in self.data_dict['demographics'].items():
                if field in patient_data:
                    value = patient_data[field]
                    
                    # Check required fields
                    if specs.get('required', False) and (value is None or value == ''):
                        errors.append(f"Required field {field} is missing")
                        is_valid = False
                    
                    # Check ranges for numeric fields
                    if 'range' in specs and value is not None:
                        min_val, max_val = specs['range']
                        if not (min_val <= value <= max_val):
                            errors.append(f"{field} value {value} outside range [{min_val}, {max_val}]")
                            is_valid = False
                    
                    # Check enum values
                    if specs.get('type') == 'enum' and value not in specs.get('values', []):
                        errors.append(f"{field} value '{value}' not in allowed values: {specs['values']}")
                        is_valid = False
        
        if errors:
            self.validation_errors.extend(errors)
            logger.warning(f"Validation errors for patient {patient_data.get('patient_id', 'unknown')}: {errors}")
        
        return is_valid
    
    def transform_ecmo_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw ECMO data to ELSO standard format
        
        Args:
            raw_data: Raw ECMO data DataFrame
            
        Returns:
            pd.DataFrame: Transformed data aligned with ELSO standards
        """
        logger.info(f"Transforming {len(raw_data)} ECMO records")
        
        transformed_data = raw_data.copy()
        
        # Standardize ECMO types
        ecmo_type_mapping = {
            'venoarterial': 'VA',
            'veno-arterial': 'VA',
            'va': 'VA',
            'venovenous': 'VV',
            'veno-venous': 'VV',
            'vv': 'VV',
            'veno-arterial-venous': 'VAV',
            'vav': 'VAV'
        }
        
        if 'ecmo_type' in transformed_data.columns:
            transformed_data['ecmo_type'] = transformed_data['ecmo_type'].str.lower().map(
                lambda x: ecmo_type_mapping.get(x, x)
            )
        
        # Calculate BMI if height and weight available
        if 'weight_kg' in transformed_data.columns and 'height_cm' in transformed_data.columns:
            transformed_data['bmi'] = transformed_data['weight_kg'] / (
                (transformed_data['height_cm'] / 100) ** 2
            )
        
        # Convert timestamps
        timestamp_cols = ['created_at', 'updated_at', 'ecmo_start_time']
        for col in timestamp_cols:
            if col in transformed_data.columns:
                transformed_data[col] = pd.to_datetime(transformed_data[col])
        
        # Add ELSO compliance flag
        transformed_data['elso_compliant'] = transformed_data.apply(
            lambda row: self.validate_patient_data(row.to_dict()), axis=1
        )
        
        logger.info(f"Transformation complete. {transformed_data['elso_compliant'].sum()} compliant records")
        
        return transformed_data
    
    def calculate_risk_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ECMO risk scores (SAVE-II, RESP, PRESERvE)
        
        Args:
            data: ECMO patient data
            
        Returns:
            pd.DataFrame: Data with calculated risk scores
        """
        logger.info("Calculating ECMO risk scores")
        
        result_data = data.copy()
        
        # SAVE-II Score calculation (simplified version)
        # Note: Full implementation would require all SAVE-II variables
        if all(col in data.columns for col in ['age_years', 'weight_kg', 'cardiac_arrest']):
            save_score = pd.Series(0, index=data.index)
            
            # Age component (simplified)
            save_score += np.where(data['age_years'] > 38, -2, 0)
            save_score += np.where(data['age_years'] > 53, -2, 0)
            
            # Weight component
            save_score += np.where(data['weight_kg'] < 65, -3, 0)
            
            # Cardiac arrest
            save_score += np.where(data['cardiac_arrest'] == True, -2, 0)
            
            result_data['save_ii_score'] = save_score
        
        # RESP Score (simplified - would need full variables)
        if 'age_years' in data.columns and 'ecmo_type' in data.columns:
            resp_score = pd.Series(0, index=data.index)
            
            # Age component
            resp_score += np.where(data['age_years'].between(18, 49), 0, -2)
            resp_score += np.where(data['age_years'] >= 60, -3, 0)
            
            # Only for VV ECMO
            vv_mask = data['ecmo_type'] == 'VV'
            result_data.loc[vv_mask, 'resp_score'] = resp_score[vv_mask]
        
        return result_data
    
    def export_to_elso_format(self, data: pd.DataFrame, output_path: str):
        """
        Export data in ELSO registry format
        
        Args:
            data: Processed ECMO data
            output_path: Output file path
        """
        logger.info(f"Exporting {len(data)} records to ELSO format")
        
        # Select only ELSO-required columns
        elso_columns = []
        for category in self.data_dict.keys():
            if isinstance(self.data_dict[category], dict):
                for field, specs in self.data_dict[category].items():
                    if 'elso_code' in specs:
                        elso_columns.append(field)
        
        # Filter to available columns
        available_columns = [col for col in elso_columns if col in data.columns]
        elso_data = data[available_columns].copy()
        
        # Export to CSV
        elso_data.to_csv(output_path, index=False)
        logger.info(f"ELSO format data exported to {output_path}")


def main():
    """Main ETL processing function"""
    processor = ELSODataProcessor()
    
    # Example usage
    logger.info("ELSO-aligned ETL pipeline initialized")
    logger.info("Ready to process ECMO data with ELSO standards compliance")
    
    return processor


if __name__ == "__main__":
    main()