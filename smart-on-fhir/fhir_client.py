"""
FHIR Client Utilities for ECMO CDSS
====================================

Utilities for fetching and parsing FHIR resources from EHR systems.
Extracts relevant clinical data for ECMO candidacy assessment.

FHIR R4 Resources:
- Patient: Demographics, age, gender
- Observation: Vitals, labs, NIRS values
- Procedure: ECMO, CRRT, other procedures
- Condition: Diagnoses (cardiac arrest, sepsis, ARDS)
- MedicationRequest: Vasopressors, anticoagulation
- Device: ECMO device parameters
"""

import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientDemographics:
    """Patient demographics from FHIR Patient resource."""
    id: str
    name: str
    birth_date: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    mrn: Optional[str] = None


@dataclass
class ClinicalObservation:
    """Clinical observation from FHIR Observation resource."""
    code: str
    display: str
    value: float
    unit: str
    effective_date: str
    category: str = "vital-signs"


@dataclass
class ECMOClinicalData:
    """Aggregated clinical data for ECMO risk assessment."""
    demographics: PatientDemographics
    vitals: Dict[str, List[ClinicalObservation]] = field(default_factory=dict)
    labs: Dict[str, List[ClinicalObservation]] = field(default_factory=dict)
    nirs_values: Dict[str, List[ClinicalObservation]] = field(default_factory=dict)
    procedures: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    medications: List[Dict[str, Any]] = field(default_factory=list)


class FHIRClient:
    """
    FHIR client for ECMO CDSS data retrieval.

    Handles authentication, pagination, and resource parsing.
    """

    # LOINC codes for key ECMO-related observations
    LOINC_CODES = {
        # NIRS monitoring
        '59452-7': 'Cerebral oxygen saturation (rSO2)',
        '59453-5': 'Somatic oxygen saturation',

        # Arterial Blood Gas
        '2744-1': 'pH of Arterial blood',
        '2703-7': 'Oxygen [Partial pressure] in Arterial blood (PaO2)',
        '2019-8': 'Carbon dioxide [Partial pressure] in Arterial blood (PaCO2)',
        '1925-7': 'Base excess in Arterial blood',
        '2708-6': 'Oxygen saturation in Arterial blood (SaO2)',

        # Lactate
        '2524-7': 'Lactate [Moles/volume] in Serum or Plasma',
        '32693-4': 'Lactate [Mass/volume] in Arterial blood',

        # Vitals
        '8867-4': 'Heart rate',
        '8480-6': 'Systolic blood pressure',
        '8462-4': 'Diastolic blood pressure',
        '85354-9': 'Blood pressure panel with all children optional',
        '2708-6': 'Oxygen saturation in Arterial blood',

        # Labs
        '718-7': 'Hemoglobin [Mass/volume] in Blood',
        '777-3': 'Platelets [#/volume] in Blood',
        '2160-0': 'Creatinine [Mass/volume] in Serum or Plasma',
        '1742-6': 'Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma',
        '1920-8': 'Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma',
        '1975-2': 'Bilirubin.total [Mass/volume] in Serum or Plasma',
    }

    # SNOMED codes for ECMO-related procedures
    SNOMED_PROCEDURES = {
        '233573008': 'Extracorporeal membrane oxygenation',
        '233574002': 'VA ECMO',
        '233575001': 'VV ECMO',
        '233576000': 'Veno-arterial-venous ECMO',
        '265764009': 'Renal dialysis',
        '302497006': 'Hemodialysis',
    }

    # SNOMED codes for relevant conditions
    SNOMED_CONDITIONS = {
        '410429000': 'Cardiac arrest',
        '429007001': 'Cardiogenic shock',
        '67782005': 'Acute respiratory distress syndrome',
        '91302008': 'Sepsis',
        '76571007': 'Septic shock',
        '233604007': 'Pneumonia',
    }

    def __init__(self, base_url: str, access_token: str):
        """
        Initialize FHIR client.

        Args:
            base_url: FHIR server base URL
            access_token: OAuth2 access token
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json',
        }

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make GET request to FHIR server.

        Args:
            endpoint: Resource endpoint (e.g., '/Patient/123')
            params: Query parameters

        Returns:
            JSON response
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"FHIR request failed: {url}, Error: {e}")
            raise

    def _get_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch all pages of a FHIR search result.

        Args:
            endpoint: Resource endpoint
            params: Query parameters

        Returns:
            List of all entries from all pages
        """
        all_entries = []
        next_url = None

        # Initial request
        data = self._get(endpoint, params)

        while True:
            # Extract entries from current page
            if 'entry' in data:
                all_entries.extend(data['entry'])

            # Check for next page
            next_url = None
            if 'link' in data:
                for link in data['link']:
                    if link.get('relation') == 'next':
                        next_url = link.get('url')
                        break

            if not next_url:
                break

            # Fetch next page
            try:
                response = requests.get(next_url, headers=self.headers, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch next page: {e}")
                break

        return all_entries

    def get_patient(self, patient_id: str) -> PatientDemographics:
        """
        Fetch patient demographics.

        Args:
            patient_id: FHIR Patient ID

        Returns:
            PatientDemographics object
        """
        data = self._get(f'/Patient/{patient_id}')

        # Parse patient name
        name = "Unknown"
        if 'name' in data and len(data['name']) > 0:
            name_data = data['name'][0]
            given = ' '.join(name_data.get('given', []))
            family = name_data.get('family', '')
            name = f"{given} {family}".strip()

        # Calculate age from birth date
        age = None
        birth_date = data.get('birthDate')
        if birth_date:
            try:
                birth = datetime.strptime(birth_date, '%Y-%m-%d')
                age = (datetime.now() - birth).days // 365
            except ValueError:
                pass

        # Extract MRN from identifiers
        mrn = None
        if 'identifier' in data:
            for identifier in data['identifier']:
                if identifier.get('type', {}).get('coding', [{}])[0].get('code') == 'MR':
                    mrn = identifier.get('value')
                    break

        return PatientDemographics(
            id=patient_id,
            name=name,
            birth_date=birth_date,
            age=age,
            gender=data.get('gender'),
            mrn=mrn
        )

    def get_observations(
        self,
        patient_id: str,
        category: Optional[str] = None,
        code: Optional[str] = None,
        lookback_days: int = 7
    ) -> List[ClinicalObservation]:
        """
        Fetch observations for a patient.

        Args:
            patient_id: FHIR Patient ID
            category: Observation category (vital-signs, laboratory, etc.)
            code: LOINC code filter
            lookback_days: Number of days to look back

        Returns:
            List of ClinicalObservation objects
        """
        params = {
            'patient': patient_id,
            '_count': 100,
            '_sort': '-date',
        }

        if category:
            params['category'] = category

        if code:
            params['code'] = code

        # Add date filter
        date_from = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        params['date'] = f'ge{date_from}'

        entries = self._get_all_pages('/Observation', params)

        observations = []
        for entry in entries:
            resource = entry.get('resource', {})
            obs = self._parse_observation(resource)
            if obs:
                observations.append(obs)

        return observations

    def _parse_observation(self, resource: Dict) -> Optional[ClinicalObservation]:
        """
        Parse FHIR Observation resource.

        Args:
            resource: FHIR Observation resource

        Returns:
            ClinicalObservation or None if parsing fails
        """
        try:
            # Extract code
            code_data = resource.get('code', {})
            coding = code_data.get('coding', [{}])[0]
            code = coding.get('code', 'unknown')
            display = coding.get('display', code_data.get('text', 'Unknown'))

            # Extract value
            value = None
            unit = ''

            if 'valueQuantity' in resource:
                value = resource['valueQuantity'].get('value')
                unit = resource['valueQuantity'].get('unit', '')
            elif 'valueString' in resource:
                # Try to parse string as number
                try:
                    value = float(resource['valueString'])
                except ValueError:
                    return None

            if value is None:
                return None

            # Extract effective date
            effective_date = resource.get('effectiveDateTime', resource.get('issued', ''))

            # Determine category
            category = 'other'
            if 'category' in resource and len(resource['category']) > 0:
                category_coding = resource['category'][0].get('coding', [{}])[0]
                category = category_coding.get('code', 'other')

            return ClinicalObservation(
                code=code,
                display=display,
                value=float(value),
                unit=unit,
                effective_date=effective_date,
                category=category
            )
        except Exception as e:
            logger.warning(f"Failed to parse observation: {e}")
            return None

    def get_procedures(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetch procedures for a patient.

        Args:
            patient_id: FHIR Patient ID

        Returns:
            List of procedure dictionaries
        """
        params = {
            'patient': patient_id,
            '_count': 50,
            '_sort': '-date',
        }

        entries = self._get_all_pages('/Procedure', params)

        procedures = []
        for entry in entries:
            resource = entry.get('resource', {})

            # Extract procedure code
            code_data = resource.get('code', {})
            coding = code_data.get('coding', [{}])[0]

            procedures.append({
                'code': coding.get('code'),
                'display': coding.get('display', code_data.get('text', 'Unknown procedure')),
                'status': resource.get('status'),
                'performed': resource.get('performedDateTime', resource.get('performedPeriod', {}).get('start')),
            })

        return procedures

    def get_conditions(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetch conditions/diagnoses for a patient.

        Args:
            patient_id: FHIR Patient ID

        Returns:
            List of condition dictionaries
        """
        params = {
            'patient': patient_id,
            '_count': 100,
        }

        entries = self._get_all_pages('/Condition', params)

        conditions = []
        for entry in entries:
            resource = entry.get('resource', {})

            # Extract condition code
            code_data = resource.get('code', {})
            coding = code_data.get('coding', [{}])[0]

            conditions.append({
                'code': coding.get('code'),
                'display': coding.get('display', code_data.get('text', 'Unknown condition')),
                'clinical_status': resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code'),
                'onset': resource.get('onsetDateTime', resource.get('onsetPeriod', {}).get('start')),
            })

        return conditions

    def get_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetch medication requests for a patient.

        Args:
            patient_id: FHIR Patient ID

        Returns:
            List of medication dictionaries
        """
        params = {
            'patient': patient_id,
            '_count': 100,
            'status': 'active',
        }

        entries = self._get_all_pages('/MedicationRequest', params)

        medications = []
        for entry in entries:
            resource = entry.get('resource', {})

            # Extract medication code
            med_data = resource.get('medicationCodeableConcept', {})
            coding = med_data.get('coding', [{}])[0]

            medications.append({
                'code': coding.get('code'),
                'display': coding.get('display', med_data.get('text', 'Unknown medication')),
                'status': resource.get('status'),
                'authored_on': resource.get('authoredOn'),
            })

        return medications

    def get_ecmo_clinical_data(self, patient_id: str) -> ECMOClinicalData:
        """
        Fetch all relevant clinical data for ECMO assessment.

        Args:
            patient_id: FHIR Patient ID

        Returns:
            ECMOClinicalData object with all clinical information
        """
        # Get patient demographics
        demographics = self.get_patient(patient_id)

        # Get all observations
        all_observations = self.get_observations(patient_id, lookback_days=7)

        # Categorize observations
        vitals = {}
        labs = {}
        nirs_values = {}

        for obs in all_observations:
            if obs.code in ['59452-7', '59453-5']:  # NIRS values
                if obs.code not in nirs_values:
                    nirs_values[obs.code] = []
                nirs_values[obs.code].append(obs)
            elif obs.category == 'vital-signs':
                if obs.code not in vitals:
                    vitals[obs.code] = []
                vitals[obs.code].append(obs)
            elif obs.category == 'laboratory':
                if obs.code not in labs:
                    labs[obs.code] = []
                labs[obs.code].append(obs)

        # Get procedures, conditions, medications
        procedures = self.get_procedures(patient_id)
        conditions = self.get_conditions(patient_id)
        medications = self.get_medications(patient_id)

        return ECMOClinicalData(
            demographics=demographics,
            vitals=vitals,
            labs=labs,
            nirs_values=nirs_values,
            procedures=procedures,
            conditions=conditions,
            medications=medications
        )

    def extract_ecmo_features(self, clinical_data: ECMOClinicalData) -> Dict[str, Any]:
        """
        Extract features for ECMO risk model.

        Maps FHIR data to feature format expected by nirs/risk_models.py

        Args:
            clinical_data: ECMOClinicalData object

        Returns:
            Dictionary of features for risk model
        """
        features = {
            'age': clinical_data.demographics.age or 0,
            'gender': clinical_data.demographics.gender,
        }

        # Extract latest values for key parameters

        # NIRS values
        if '59452-7' in clinical_data.nirs_values and clinical_data.nirs_values['59452-7']:
            cerebral_rso2 = [obs.value for obs in clinical_data.nirs_values['59452-7']]
            features['cerebral_rso2_mean'] = sum(cerebral_rso2) / len(cerebral_rso2)
            features['cerebral_rso2_latest'] = cerebral_rso2[0]

        # Lactate
        for code in ['2524-7', '32693-4']:
            if code in clinical_data.labs and clinical_data.labs[code]:
                features['lactate_mmol_l'] = clinical_data.labs[code][0].value
                break

        # ABG values
        if '2744-1' in clinical_data.labs and clinical_data.labs['2744-1']:
            features['abg_ph'] = clinical_data.labs['2744-1'][0].value

        if '2703-7' in clinical_data.labs and clinical_data.labs['2703-7']:
            features['abg_pao2_mmHg'] = clinical_data.labs['2703-7'][0].value

        # Vitals
        if '8867-4' in clinical_data.vitals and clinical_data.vitals['8867-4']:
            features['heart_rate'] = clinical_data.vitals['8867-4'][0].value

        if '8480-6' in clinical_data.vitals and clinical_data.vitals['8480-6']:
            sbp = clinical_data.vitals['8480-6'][0].value
            if '8462-4' in clinical_data.vitals and clinical_data.vitals['8462-4']:
                dbp = clinical_data.vitals['8462-4'][0].value
                features['map_mmHg'] = (sbp + 2 * dbp) / 3

        # Labs
        if '718-7' in clinical_data.labs and clinical_data.labs['718-7']:
            features['hemoglobin_g_dl'] = clinical_data.labs['718-7'][0].value

        if '777-3' in clinical_data.labs and clinical_data.labs['777-3']:
            features['platelets_10e9_l'] = clinical_data.labs['777-3'][0].value

        # Check for cardiac arrest
        features['cardiac_arrest'] = any(
            cond['code'] == '410429000' for cond in clinical_data.conditions
        )

        # Check for ECMO procedures
        features['on_ecmo'] = any(
            proc['code'] in ['233573008', '233574002', '233575001']
            for proc in clinical_data.procedures
        )

        return features
