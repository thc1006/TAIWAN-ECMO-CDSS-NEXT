"""
Pytest Fixtures and Test Utilities for Taiwan ECMO CDSS
Provides synthetic data, mock servers, and shared test utilities.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import tempfile
import os
from pathlib import Path
import yaml
import json


# ============================================================================
# SYNTHETIC DATA FIXTURES
# ============================================================================

@pytest.fixture
def synthetic_ecmo_data() -> pd.DataFrame:
    """
    Generate synthetic ECMO patient data for testing.

    Returns:
        DataFrame with realistic ECMO patient data including:
        - Demographics
        - Clinical features (NIRS, vitals, labs)
        - ECMO parameters
        - Outcomes
    """
    np.random.seed(42)
    n_patients = 200

    data = []
    for i in range(n_patients):
        # Demographics
        age = np.random.randint(18, 85)
        bmi = np.random.normal(25, 5)

        # ECMO mode (60% VA, 40% VV)
        mode = np.random.choice(['VA', 'VV'], p=[0.6, 0.4])

        # APACHE-II score (correlates with mortality)
        apache_ii = np.random.randint(10, 40)

        # NIRS features
        # Higher APACHE → lower rSO2, higher variability
        hbo_mean = max(40, np.random.normal(65 - apache_ii*0.5, 10))
        hbo_std = np.random.gamma(2, 3)
        hbo_slope = np.random.normal(-0.1, 0.5)
        hbt_mean = max(30, np.random.normal(60 - apache_ii*0.4, 10))
        hbt_std = np.random.gamma(2, 3)
        hbt_slope = np.random.normal(-0.1, 0.5)

        # Labs and vitals
        lactate_mmol_l = max(0.5, np.random.gamma(2, 2))
        hemoglobin_g_dl = np.random.normal(11, 2)
        platelets_10e9_l = max(20, np.random.normal(150, 60))
        map_mmHg = max(40, np.random.normal(70, 15))
        spo2_pct = min(100, max(70, np.random.normal(92, 8)))
        abg_pao2_mmHg = max(40, np.random.normal(80, 20))
        abg_paco2_mmHg = max(20, np.random.normal(40, 10))

        # ECMO parameters
        pump_speed_rpm = np.random.randint(2000, 4000)
        flow_l_min = np.random.uniform(3.0, 6.0)
        sweep_gas_l_min = np.random.uniform(2.0, 8.0)
        fio2_ecmo = np.random.uniform(0.4, 1.0)

        # Outcome (survival correlates with APACHE, lactate, NIRS)
        # Lower APACHE, lower lactate, higher rSO2 → better survival
        survival_prob = 1 / (1 + np.exp(
            0.1 * apache_ii +
            0.3 * lactate_mmol_l -
            0.05 * hbo_mean -
            2
        ))
        survival_to_discharge = int(np.random.random() < survival_prob)

        # Length of stay
        icu_los_days = max(1, np.random.gamma(8, 2) if survival_to_discharge else np.random.gamma(5, 1.5))
        ward_los_days = max(0, np.random.gamma(6, 1.5) if survival_to_discharge else 0)
        ecmo_days = max(1, np.random.gamma(4, 1.5))

        data.append({
            'patient_id': f'P{i+1:04d}',
            'mode': mode,
            'age': age,
            'bmi': bmi,
            'apache_ii': apache_ii,
            'hbo_mean': hbo_mean,
            'hbo_std': hbo_std,
            'hbo_slope': hbo_slope,
            'hbt_mean': hbt_mean,
            'hbt_std': hbt_std,
            'hbt_slope': hbt_slope,
            'lactate_mmol_l': lactate_mmol_l,
            'hemoglobin_g_dl': hemoglobin_g_dl,
            'platelets_10e9_l': platelets_10e9_l,
            'map_mmHg': map_mmHg,
            'spo2_pct': spo2_pct,
            'abg_pao2_mmHg': abg_pao2_mmHg,
            'abg_paco2_mmHg': abg_paco2_mmHg,
            'pump_speed_rpm': pump_speed_rpm,
            'flow_l_min': flow_l_min,
            'sweep_gas_l_min': sweep_gas_l_min,
            'fio2_ecmo': fio2_ecmo,
            'survival_to_discharge': survival_to_discharge,
            'icu_los_days': icu_los_days,
            'ward_los_days': ward_los_days,
            'ecmo_days': ecmo_days,
        })

    return pd.DataFrame(data)


@pytest.fixture
def synthetic_cea_data() -> pd.DataFrame:
    """
    Generate synthetic cost-effectiveness analysis data.

    Returns:
        DataFrame with quintile-stratified patient data
    """
    np.random.seed(42)
    data = []

    for quintile in range(1, 6):
        # Risk-stratified outcomes
        base_survival = 0.65 - (quintile - 1) * 0.10
        base_icu_los = 10 + (quintile - 1) * 5
        base_ward_los = 5 + (quintile - 1) * 3
        base_ecmo_days = 5 + (quintile - 1) * 2

        for _ in range(40):
            survival = int(np.random.random() < base_survival)

            icu_los = max(1, np.random.normal(
                base_icu_los * (0.8 if survival else 1.2),
                base_icu_los * 0.3
            ))
            ward_los = max(0, np.random.normal(
                base_ward_los * survival,
                base_ward_los * 0.4
            ))
            ecmo_days = max(1, np.random.normal(base_ecmo_days, base_ecmo_days * 0.25))

            data.append({
                'risk_quintile': quintile,
                'survival_to_discharge': survival,
                'icu_los_days': icu_los,
                'ward_los_days': ward_los,
                'ecmo_days': ecmo_days,
            })

    return pd.DataFrame(data)


@pytest.fixture
def synthetic_vr_scenarios() -> Dict:
    """
    Generate synthetic VR training scenario definitions.

    Returns:
        Dictionary with scenario data
    """
    return {
        'scenarios': [
            {
                'id': 'SCN-001',
                'title': 'VA ECMO Cannulation - Femoral Approach',
                'difficulty': 'beginner',
                'ecmo_mode': 'VA',
                'duration_min': 30,
                'decision_points': [
                    {
                        'id': 'DP-001-01',
                        'question': 'Select cannulation approach',
                        'options': [
                            {'value': 'femoral_percutaneous', 'correct': True},
                            {'value': 'femoral_surgical', 'correct': True},
                            {'value': 'subclavian', 'correct': False},
                        ],
                        'scoring_weight': 20,
                        'critical': True,
                    },
                    {
                        'id': 'DP-001-02',
                        'question': 'Distal perfusion cannula needed?',
                        'options': [
                            {'value': 'yes_routinely', 'correct': True},
                            {'value': 'no', 'correct': False},
                        ],
                        'scoring_weight': 15,
                        'critical': True,
                    }
                ],
                'assessment_rubric': {
                    'technical_skill': 30,
                    'clinical_decision_making': 30,
                    'nirs_interpretation': 15,
                    'complication_management': 15,
                    'communication': 10,
                }
            }
        ]
    }


@pytest.fixture
def synthetic_vr_log_data() -> Dict:
    """
    Generate synthetic VR session log data.

    Returns:
        Dictionary with VR session data
    """
    return {
        'session_id': 'VR-2025-001',
        'participant_id': 'P001',
        'scenario_id': 'SCN-001',
        'scenario_title': 'VA ECMO Cannulation - Femoral Approach',
        'difficulty': 'beginner',
        'ecmo_mode': 'VA',
        'start_time': '2025-10-05T09:00:00',
        'end_time': '2025-10-05T09:38:00',
        'total_duration_min': 38.0,
        'first_attempt_success': True,
        'scenario_completed': True,
        'complications_encountered': ['limb_ischemia'],
        'interventions_performed': ['distal_perfusion_cannula'],
        'decision_points': [
            {
                'id': 'DP-001-01',
                'timestamp_min': 2.0,
                'selected_option': 'femoral_percutaneous',
                'time_to_decision_sec': 45.2
            },
            {
                'id': 'DP-001-02',
                'timestamp_min': 18.0,
                'selected_option': 'yes_routinely',
                'time_to_decision_sec': 32.1
            }
        ]
    }


# ============================================================================
# MOCK FHIR SERVER FIXTURE
# ============================================================================

class MockFHIRServer:
    """Mock FHIR server for testing."""

    def __init__(self):
        self.base_url = "http://localhost:8080/fhir"
        self.access_token = "mock_token_12345"
        self.patients = {}
        self.observations = {}
        self.procedures = {}
        self.conditions = {}
        self.medications = {}

        # Populate with test data
        self._populate_test_data()

    def _populate_test_data(self):
        """Create synthetic FHIR resources."""
        # Patient
        self.patients['test-patient-1'] = {
            'resourceType': 'Patient',
            'id': 'test-patient-1',
            'name': [{
                'given': ['John'],
                'family': 'Doe'
            }],
            'birthDate': '1970-05-15',
            'gender': 'male',
            'identifier': [{
                'type': {
                    'coding': [{
                        'code': 'MR'
                    }]
                },
                'value': 'MRN123456'
            }]
        }

        # Observations - NIRS
        self.observations['nirs-1'] = {
            'resourceType': 'Observation',
            'id': 'nirs-1',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '59452-7',
                    'display': 'Cerebral oxygen saturation'
                }]
            },
            'valueQuantity': {
                'value': 68.5,
                'unit': '%'
            },
            'effectiveDateTime': '2025-10-05T10:00:00Z',
            'category': [{
                'coding': [{
                    'code': 'vital-signs'
                }]
            }]
        }

        # Observations - Lactate
        self.observations['lactate-1'] = {
            'resourceType': 'Observation',
            'id': 'lactate-1',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '2524-7',
                    'display': 'Lactate'
                }]
            },
            'valueQuantity': {
                'value': 3.2,
                'unit': 'mmol/L'
            },
            'effectiveDateTime': '2025-10-05T10:00:00Z',
            'category': [{
                'coding': [{
                    'code': 'laboratory'
                }]
            }]
        }

        # Procedure - ECMO
        self.procedures['ecmo-1'] = {
            'resourceType': 'Procedure',
            'id': 'ecmo-1',
            'code': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '233574002',
                    'display': 'VA ECMO'
                }]
            },
            'status': 'in-progress',
            'performedDateTime': '2025-10-04T08:00:00Z'
        }

        # Condition - Cardiac arrest
        self.conditions['cardiac-arrest-1'] = {
            'resourceType': 'Condition',
            'id': 'cardiac-arrest-1',
            'code': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '410429000',
                    'display': 'Cardiac arrest'
                }]
            },
            'clinicalStatus': {
                'coding': [{
                    'code': 'active'
                }]
            },
            'onsetDateTime': '2025-10-04T07:30:00Z'
        }

    def get_patient(self, patient_id: str) -> Dict:
        """Get patient resource."""
        return self.patients.get(patient_id)

    def search_observations(self, patient_id: str, **params) -> Dict:
        """Search observations."""
        return {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'entry': [
                {'resource': obs} for obs in self.observations.values()
            ]
        }

    def search_procedures(self, patient_id: str) -> Dict:
        """Search procedures."""
        return {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'entry': [
                {'resource': proc} for proc in self.procedures.values()
            ]
        }


@pytest.fixture
def mock_fhir_server():
    """Provide mock FHIR server instance."""
    return MockFHIRServer()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_sqlite_db():
    """
    Create temporary SQLite database for SQL testing.

    Yields:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


# ============================================================================
# FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_yaml_file():
    """
    Create temporary YAML file for scenario testing.

    Yields:
        Path to temporary YAML file
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_path = f.name

    yield yaml_path

    # Cleanup
    if os.path.exists(yaml_path):
        os.remove(yaml_path)


@pytest.fixture
def temp_output_dir():
    """
    Create temporary directory for test outputs.

    Yields:
        Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def assert_dataframe_schema(df: pd.DataFrame, required_columns: List[str]):
    """Assert that DataFrame has required columns."""
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"Missing columns: {missing}"


def assert_metric_in_range(value: float, min_val: float, max_val: float, name: str = "metric"):
    """Assert that metric is within expected range."""
    assert min_val <= value <= max_val, \
        f"{name} = {value} is outside valid range [{min_val}, {max_val}]"


def assert_probabilities_valid(probs: np.ndarray):
    """Assert that probabilities are valid (0-1, sum to 1)."""
    assert np.all(probs >= 0), "Probabilities must be >= 0"
    assert np.all(probs <= 1), "Probabilities must be <= 1"
    if probs.ndim == 2:
        row_sums = probs.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, 1.0, decimal=5,
                                              err_msg="Probabilities must sum to 1")


# ============================================================================
# PARAMETRIZE HELPERS
# ============================================================================

# Common test parameters
ECMO_MODES = ['VA', 'VV']
DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']
AGE_GROUPS = ['neonate', 'pediatric', 'adult']


# Export all fixtures
__all__ = [
    'synthetic_ecmo_data',
    'synthetic_cea_data',
    'synthetic_vr_scenarios',
    'synthetic_vr_log_data',
    'mock_fhir_server',
    'temp_sqlite_db',
    'temp_yaml_file',
    'temp_output_dir',
    'assert_dataframe_schema',
    'assert_metric_in_range',
    'assert_probabilities_valid',
    'ECMO_MODES',
    'DIFFICULTY_LEVELS',
    'AGE_GROUPS',
]
