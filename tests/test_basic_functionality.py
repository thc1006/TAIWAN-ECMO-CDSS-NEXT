"""
Basic functionality tests for Taiwan ECMO CDSS
Tests core components without requiring external dependencies
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
import yaml
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_data_dictionary_loading():
    """Test that data dictionary can be loaded"""
    data_dict_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_dictionary.yaml')
    
    assert os.path.exists(data_dict_path), "Data dictionary file not found"
    
    with open(data_dict_path, 'r') as f:
        data_dict = yaml.safe_load(f)
    
    assert data_dict is not None, "Data dictionary is empty"
    assert 'version' in data_dict, "Version not specified in data dictionary"
    assert 'demographics' in data_dict, "Demographics section missing"
    assert 'ecmo_config' in data_dict, "ECMO config section missing"

def test_code_lists_loading():
    """Test that code lists can be loaded"""
    codes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'etl', 'codes')
    
    procedures_path = os.path.join(codes_dir, 'ecmo_procedures.yaml')
    diagnoses_path = os.path.join(codes_dir, 'ecmo_diagnoses.yaml')
    
    assert os.path.exists(procedures_path), "ECMO procedures codes file not found"
    assert os.path.exists(diagnoses_path), "ECMO diagnoses codes file not found"
    
    with open(procedures_path, 'r') as f:
        procedures = yaml.safe_load(f)
    
    with open(diagnoses_path, 'r') as f:
        diagnoses = yaml.safe_load(f)
    
    assert 'icd10_pcs' in procedures, "ICD-10-PCS codes missing"
    assert 'cardiac_indications' in diagnoses, "Cardiac indications missing"

def test_elso_processor_import():
    """Test that ELSO processor can be imported"""
    try:
        from etl.elso_processor import ELSODataProcessor
        
        # Test initialization
        processor = ELSODataProcessor()
        assert processor is not None
        
        # Test demo data validation
        demo_data = {
            'patient_id': 'TEST001',
            'age_years': 55,
            'weight_kg': 70,
            'gender': 'M'
        }
        
        # This should not raise an exception
        is_valid = processor.validate_patient_data(demo_data)
        assert isinstance(is_valid, bool)
        
    except ImportError as e:
        pytest.skip(f"Could not import ELSO processor: {e}")

def test_nirs_risk_model_import():
    """Test that NIRS risk models can be imported"""
    try:
        from nirs.risk_models import NIRSECMORiskModel, generate_demo_data
        
        # Test model initialization
        va_model = NIRSECMORiskModel('VA')
        vv_model = NIRSECMORiskModel('VV')
        
        assert va_model.ecmo_type == 'VA'
        assert vv_model.ecmo_type == 'VV'
        
        # Test demo data generation
        demo_data = generate_demo_data(10, 'VA')
        assert len(demo_data) == 10
        assert 'patient_id' in demo_data.columns
        assert 'survived_to_discharge' in demo_data.columns
        
    except ImportError as e:
        pytest.skip(f"Could not import NIRS risk models: {e}")

def test_cost_effectiveness_import():
    """Test that cost-effectiveness module can be imported"""
    try:
        from econ.cost_effectiveness import ECMOCostEffectivenessAnalyzer, CostParameters
        
        # Test analyzer initialization
        analyzer = ECMOCostEffectivenessAnalyzer()
        assert analyzer is not None
        
        # Test cost parameters
        cost_params = CostParameters()
        assert cost_params.ecmo_daily_cost > 0
        assert cost_params.taiwan_cost_multiplier > 0
        
    except ImportError as e:
        pytest.skip(f"Could not import cost-effectiveness module: {e}")

def test_vr_training_import():
    """Test that VR training module can be imported"""
    try:
        from vr_training.training_protocol import ECMOVRTrainingProtocol, TrainingScenario
        
        # Test protocol initialization
        protocol = ECMOVRTrainingProtocol()
        assert protocol is not None
        assert len(protocol.scenarios) > 0
        
        # Test scenario filtering
        va_scenarios = protocol.get_scenarios_by_ecmo_type('VA')
        vv_scenarios = protocol.get_scenarios_by_ecmo_type('VV')
        
        assert len(va_scenarios) > 0
        assert len(vv_scenarios) > 0
        
    except ImportError as e:
        pytest.skip(f"Could not import VR training module: {e}")

def test_sql_file_exists():
    """Test that SQL file exists and is readable"""
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'identify_ecmo.sql')
    
    assert os.path.exists(sql_path), "ECMO identification SQL file not found"
    
    with open(sql_path, 'r') as f:
        sql_content = f.read()
    
    assert len(sql_content) > 0, "SQL file is empty"
    assert 'SELECT' in sql_content.upper(), "SQL file does not contain SELECT statements"
    assert 'ECMO' in sql_content.upper(), "SQL file does not reference ECMO"

def test_requirements_file_exists():
    """Test that requirements.txt exists"""
    req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
    
    assert os.path.exists(req_path), "requirements.txt file not found"
    
    with open(req_path, 'r') as f:
        requirements = f.read()
    
    assert 'pandas' in requirements, "pandas not in requirements"
    assert 'streamlit' in requirements, "streamlit not in requirements"
    assert 'scikit-learn' in requirements, "scikit-learn not in requirements"

def test_environment_template_exists():
    """Test that environment template exists"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.example')
    
    assert os.path.exists(env_path), ".env.example file not found"
    
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    assert 'DATABASE_URL' in env_content, "DATABASE_URL not in environment template"
    assert 'SECRET_KEY' in env_content, "SECRET_KEY not in environment template"

def test_basic_data_processing():
    """Test basic data processing functionality"""
    # Create sample ECMO data
    sample_data = pd.DataFrame({
        'patient_id': ['PT001', 'PT002', 'PT003'],
        'age_years': [45, 62, 38],
        'weight_kg': [70, 85, 65],
        'ecmo_type': ['VA', 'VV', 'VA'],
        'survived_to_discharge': [True, False, True]
    })
    
    # Test basic operations
    assert len(sample_data) == 3
    assert sample_data['age_years'].mean() == 48.33333333333333
    
    # Test groupby operations
    survival_by_type = sample_data.groupby('ecmo_type')['survived_to_discharge'].mean()
    assert 'VA' in survival_by_type.index
    assert 'VV' in survival_by_type.index

if __name__ == "__main__":
    pytest.main([__file__])