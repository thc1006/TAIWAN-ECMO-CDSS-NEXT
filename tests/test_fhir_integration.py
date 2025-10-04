"""
Unit Tests for FHIR Integration (WP4)
Tests OAuth2 flow, resource fetching, and feature extraction from FHIR.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'smart-on-fhir'))

from fhir_client import (
    FHIRClient,
    PatientDemographics,
    ClinicalObservation,
    ECMOClinicalData
)


# ============================================================================
# PATIENT RESOURCE TESTS
# ============================================================================

class TestPatientResource:
    """Test patient resource parsing."""

    def test_get_patient_basic(self, mock_fhir_server):
        """Test basic patient retrieval."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.get_patient('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            patient = client.get_patient('test-patient-1')

            assert isinstance(patient, PatientDemographics)
            assert patient.id == 'test-patient-1'
            assert patient.name == 'John Doe'
            assert patient.gender == 'male'

    def test_get_patient_age_calculation(self, mock_fhir_server):
        """Test age calculation from birth date."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            # Patient born in 1970
            patient_data = mock_fhir_server.get_patient('test-patient-1')
            mock_response.json.return_value = patient_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            patient = client.get_patient('test-patient-1')

            # Age should be around 55 (2025 - 1970)
            assert patient.age >= 50
            assert patient.age <= 60

    def test_get_patient_mrn_extraction(self, mock_fhir_server):
        """Test MRN extraction from identifiers."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.get_patient('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            patient = client.get_patient('test-patient-1')

            assert patient.mrn == 'MRN123456'


# ============================================================================
# OBSERVATION RESOURCE TESTS
# ============================================================================

class TestObservationResource:
    """Test observation resource parsing."""

    def test_get_observations_basic(self, mock_fhir_server):
        """Test basic observation retrieval."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_observations('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            observations = client.get_observations('test-patient-1')

            assert isinstance(observations, list)
            assert len(observations) > 0

    def test_parse_observation_nirs(self, mock_fhir_server):
        """Test parsing NIRS observation."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_observations('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            observations = client.get_observations('test-patient-1')

            # Find NIRS observation
            nirs_obs = [obs for obs in observations if obs.code == '59452-7']
            assert len(nirs_obs) > 0

            obs = nirs_obs[0]
            assert obs.value == 68.5
            assert obs.unit == '%'
            assert obs.category == 'vital-signs'

    def test_parse_observation_lactate(self, mock_fhir_server):
        """Test parsing lactate observation."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_observations('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            observations = client.get_observations('test-patient-1')

            # Find lactate observation
            lactate_obs = [obs for obs in observations if obs.code == '2524-7']
            assert len(lactate_obs) > 0

            obs = lactate_obs[0]
            assert obs.value == 3.2
            assert obs.unit == 'mmol/L'

    def test_get_observations_with_filters(self, mock_fhir_server):
        """Test observation retrieval with filters."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_observations('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            # Test category filter
            observations = client.get_observations(
                'test-patient-1',
                category='vital-signs'
            )

            assert isinstance(observations, list)


# ============================================================================
# PROCEDURE RESOURCE TESTS
# ============================================================================

class TestProcedureResource:
    """Test procedure resource parsing."""

    def test_get_procedures_basic(self, mock_fhir_server):
        """Test basic procedure retrieval."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_procedures('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            procedures = client.get_procedures('test-patient-1')

            assert isinstance(procedures, list)
            assert len(procedures) > 0

    def test_parse_ecmo_procedure(self, mock_fhir_server):
        """Test parsing ECMO procedure."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.search_procedures('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            procedures = client.get_procedures('test-patient-1')

            # Find ECMO procedure
            ecmo_procs = [p for p in procedures if p['code'] == '233574002']
            assert len(ecmo_procs) > 0

            proc = ecmo_procs[0]
            assert proc['display'] == 'VA ECMO'
            assert proc['status'] == 'in-progress'


# ============================================================================
# FEATURE EXTRACTION TESTS
# ============================================================================

class TestFeatureExtraction:
    """Test feature extraction from FHIR data."""

    def test_extract_ecmo_features_basic(self, mock_fhir_server):
        """Test basic feature extraction."""
        # Create clinical data
        demographics = PatientDemographics(
            id='test-patient-1',
            name='John Doe',
            age=55,
            gender='male'
        )

        clinical_data = ECMOClinicalData(
            demographics=demographics,
            vitals={},
            labs={},
            nirs_values={},
            procedures=[],
            conditions=[]
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.get_patient('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            features = client.extract_ecmo_features(clinical_data)

            assert 'age' in features
            assert features['age'] == 55
            assert 'gender' in features

    def test_extract_nirs_features(self, mock_fhir_server):
        """Test NIRS feature extraction."""
        demographics = PatientDemographics(
            id='test-patient-1',
            name='John Doe',
            age=55
        )

        nirs_obs = ClinicalObservation(
            code='59452-7',
            display='Cerebral oxygen saturation',
            value=68.5,
            unit='%',
            effective_date='2025-10-05T10:00:00Z',
            category='vital-signs'
        )

        clinical_data = ECMOClinicalData(
            demographics=demographics,
            nirs_values={'59452-7': [nirs_obs]}
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.get_patient('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            features = client.extract_ecmo_features(clinical_data)

            assert 'cerebral_rso2_mean' in features
            assert 'cerebral_rso2_latest' in features
            assert features['cerebral_rso2_latest'] == 68.5

    def test_extract_lab_features(self, mock_fhir_server):
        """Test laboratory feature extraction."""
        demographics = PatientDemographics(
            id='test-patient-1',
            name='John Doe',
            age=55
        )

        lactate_obs = ClinicalObservation(
            code='2524-7',
            display='Lactate',
            value=3.2,
            unit='mmol/L',
            effective_date='2025-10-05T10:00:00Z',
            category='laboratory'
        )

        clinical_data = ECMOClinicalData(
            demographics=demographics,
            labs={'2524-7': [lactate_obs]}
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_fhir_server.get_patient('test-patient-1')
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            features = client.extract_ecmo_features(clinical_data)

            assert 'lactate_mmol_l' in features
            assert features['lactate_mmol_l'] == 3.2


# ============================================================================
# PAGINATION TESTS
# ============================================================================

class TestPagination:
    """Test FHIR bundle pagination."""

    def test_get_all_pages(self, mock_fhir_server):
        """Test fetching all pages of results."""
        # Create multi-page response
        page1 = {
            'resourceType': 'Bundle',
            'entry': [{'resource': {'id': '1'}}],
            'link': [{
                'relation': 'next',
                'url': 'http://localhost:8080/fhir/Observation?page=2'
            }]
        }

        page2 = {
            'resourceType': 'Bundle',
            'entry': [{'resource': {'id': '2'}}],
            'link': []
        }

        with patch('requests.get') as mock_get:
            # First call returns page 1, second call returns page 2
            mock_get.side_effect = [
                Mock(json=lambda: page1, raise_for_status=Mock()),
                Mock(json=lambda: page2, raise_for_status=Mock())
            ]

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            entries = client._get_all_pages('/Observation')

            assert len(entries) == 2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling."""

    def test_network_error(self, mock_fhir_server):
        """Test handling of network errors."""
        import requests

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            with pytest.raises(requests.exceptions.RequestException):
                client.get_patient('test-patient-1')

    def test_http_error(self, mock_fhir_server):
        """Test handling of HTTP errors."""
        import requests

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_get.return_value = mock_response

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            with pytest.raises(requests.exceptions.RequestException):
                client.get_patient('test-patient-1')


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFHIRIntegration:
    """Test full FHIR data retrieval workflow."""

    def test_get_ecmo_clinical_data(self, mock_fhir_server):
        """Test retrieving complete ECMO clinical data."""
        with patch('requests.get') as mock_get:
            # Mock multiple API calls
            def side_effect(*args, **kwargs):
                url = args[0]
                if 'Patient' in url:
                    return Mock(
                        json=lambda: mock_fhir_server.get_patient('test-patient-1'),
                        raise_for_status=Mock()
                    )
                elif 'Observation' in url:
                    return Mock(
                        json=lambda: mock_fhir_server.search_observations('test-patient-1'),
                        raise_for_status=Mock()
                    )
                elif 'Procedure' in url:
                    return Mock(
                        json=lambda: mock_fhir_server.search_procedures('test-patient-1'),
                        raise_for_status=Mock()
                    )
                else:
                    return Mock(
                        json=lambda: {'resourceType': 'Bundle', 'entry': []},
                        raise_for_status=Mock()
                    )

            mock_get.side_effect = side_effect

            client = FHIRClient(
                base_url=mock_fhir_server.base_url,
                access_token=mock_fhir_server.access_token
            )

            clinical_data = client.get_ecmo_clinical_data('test-patient-1')

            # Check structure
            assert isinstance(clinical_data, ECMOClinicalData)
            assert clinical_data.demographics is not None
            assert isinstance(clinical_data.vitals, dict)
            assert isinstance(clinical_data.labs, dict)
            assert isinstance(clinical_data.nirs_values, dict)


# ============================================================================
# LOINC CODE TESTS
# ============================================================================

class TestLOINCCodes:
    """Test LOINC code mappings."""

    def test_loinc_codes_defined(self):
        """Test that LOINC codes are properly defined."""
        assert hasattr(FHIRClient, 'LOINC_CODES')
        assert '59452-7' in FHIRClient.LOINC_CODES  # NIRS
        assert '2524-7' in FHIRClient.LOINC_CODES   # Lactate
        assert '2703-7' in FHIRClient.LOINC_CODES   # PaO2

    def test_snomed_procedures_defined(self):
        """Test that SNOMED procedure codes are defined."""
        assert hasattr(FHIRClient, 'SNOMED_PROCEDURES')
        assert '233573008' in FHIRClient.SNOMED_PROCEDURES  # ECMO
        assert '233574002' in FHIRClient.SNOMED_PROCEDURES  # VA ECMO

    def test_snomed_conditions_defined(self):
        """Test that SNOMED condition codes are defined."""
        assert hasattr(FHIRClient, 'SNOMED_CONDITIONS')
        assert '410429000' in FHIRClient.SNOMED_CONDITIONS  # Cardiac arrest
        assert '67782005' in FHIRClient.SNOMED_CONDITIONS   # ARDS


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
