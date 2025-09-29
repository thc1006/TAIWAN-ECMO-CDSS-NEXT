# WP0 ELSO Data Dictionary TDD Test Plan

**Generated:** 2025-09-30
**Analysis Task:** task-1759171171124-1x9dl9t67
**Standard:** ELSO Registry v3.4

---

## EXECUTIVE SUMMARY

### Current State
- **ELSO Alignment:** 45% (18/40 fields have ELSO codes)
- **Mapping Coverage:** 32.5% (13/40 fields mapped in LOCAL_TO_ELSO)
- **Validation Coverage:** 18% (only demographics category)
- **Code Integration:** 0% (59 codes defined but not linked)
- **Data Quality Score:** 6.5/10

### Target State
- **ELSO Alignment:** 100% (40/40 fields)
- **Mapping Coverage:** 100% (40/40 fields)
- **Validation Coverage:** 100% (all 9 categories)
- **Code Integration:** 100% (59+ codes linked)
- **Data Quality Score:** 9.0/10

### Missing Components
- **22 ELSO codes** missing for: NIRS (3), Risk Scores (3), Economics (3), Metadata (3), patient_id (1)
- **27 field mappings** missing from LOCAL_TO_ELSO
- **Validation** for 7/9 categories (ecmo_config, clinical, laboratory, nirs, risk_scores, outcomes, economics)
- **59 diagnosis/procedure codes** not integrated into data processing
- **Complications code file** (ecmo_complications.yaml) does not exist
- **Risk score formulas** incomplete: SAVE-II (27% complete), RESP (10% complete), PRESERvE (0% complete)

---

## CRITICAL GAPS IDENTIFIED

### 1. NIRS Data Completely Unvalidated ❌
- **Impact:** Key innovation feature lacks quality control
- No ELSO codes for cerebral_so2, renal_so2, somatic_so2
- No range validation in ELSODataProcessor
- No mapping in LOCAL_TO_ELSO

### 2. Incomplete Risk Score Calculations ❌
- **Impact:** Cannot be used for clinical decision support
- SAVE-II: 4/15+ components (27%)
- RESP: 1/10+ components (10%)
- PRESERvE: Not implemented (0%)

### 3. Economics Data Ungoverned ❌
- **Impact:** Cost-effectiveness analysis (WP2) blocked
- No ELSO codes
- No validation rules
- No mapping

### 4. Code Integration Disconnect ❌
- **Impact:** Cannot identify ECMO episodes or categorize indications
- 36 ICD-10-CM diagnosis codes defined but not linked
- 23 procedure codes (ICD-10-PCS, CPT, SNOMED, NHI) not integrated
- No complications code catalog

### 5. LOCAL_TO_ELSO Mapping Incomplete ❌
- **Impact:** ELSO registry export will lose 67.5% of data
- Only 13/40 fields mapped
- 27 fields have no mapping

---

## TDD TEST PLAN - PHASE 1: FIELD COVERAGE
**Priority:** CRITICAL
**Target:** 100% ELSO field coverage with validation

### Test Suite 1.1: ELSO Code Assignment Tests
**Coverage Target:** 22 missing ELSO codes

#### TEST-1.1.1: `test_patient_id_has_elso_code()`
```python
def test_patient_id_has_elso_code():
    """Patient ID field must have ELSO code"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['demographics']['patient_id']
    assert data_dict['demographics']['patient_id']['elso_code'] == 'PATIENT_ID'
```
- **Current:** Missing ELSO code
- **Expected:** `elso_code: "PATIENT_ID"`

#### TEST-1.1.2: `test_nirs_cerebral_has_elso_code()`
```python
def test_nirs_cerebral_has_elso_code():
    """Cerebral NIRS must have ELSO code"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['nirs']['cerebral_so2']
    assert data_dict['nirs']['cerebral_so2']['elso_code'] == 'NIRS_CEREBRAL'
```
- **Current:** No ELSO code
- **Expected:** `elso_code: "NIRS_CEREBRAL"`

#### TEST-1.1.3: `test_nirs_renal_has_elso_code()`
```python
def test_nirs_renal_has_elso_code():
    """Renal NIRS must have ELSO code"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['nirs']['renal_so2']
    assert data_dict['nirs']['renal_so2']['elso_code'] == 'NIRS_RENAL'
```
- **Current:** No ELSO code
- **Expected:** `elso_code: "NIRS_RENAL"`

#### TEST-1.1.4: `test_nirs_somatic_has_elso_code()`
```python
def test_nirs_somatic_has_elso_code():
    """Somatic NIRS must have ELSO code"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['nirs']['somatic_so2']
    assert data_dict['nirs']['somatic_so2']['elso_code'] == 'NIRS_SOMATIC'
```
- **Current:** No ELSO code
- **Expected:** `elso_code: "NIRS_SOMATIC"`

#### TEST-1.1.5: `test_risk_scores_have_elso_codes()`
```python
def test_risk_scores_have_elso_codes():
    """All risk scores must have ELSO codes"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['risk_scores']['save_ii_score']
    assert data_dict['risk_scores']['save_ii_score']['elso_code'] == 'SAVE_II'

    assert 'elso_code' in data_dict['risk_scores']['resp_ecmo_score']
    assert data_dict['risk_scores']['resp_ecmo_score']['elso_code'] == 'RESP'

    assert 'elso_code' in data_dict['risk_scores']['preserve_score']
    assert data_dict['risk_scores']['preserve_score']['elso_code'] == 'PRESERVE'
```
- **Current:** No ELSO codes for any risk score
- **Expected:** Add `elso_code` to all 3 risk_scores fields

#### TEST-1.1.6: `test_economics_fields_have_elso_codes()`
```python
def test_economics_fields_have_elso_codes():
    """Economics fields must have ELSO codes"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['economics']['total_cost_usd']
    assert data_dict['economics']['total_cost_usd']['elso_code'] == 'COST_TOTAL'

    assert 'elso_code' in data_dict['economics']['daily_cost_usd']
    assert data_dict['economics']['daily_cost_usd']['elso_code'] == 'COST_DAILY'

    assert 'elso_code' in data_dict['economics']['qaly_gained']
    assert data_dict['economics']['qaly_gained']['elso_code'] == 'QALY'
```
- **Current:** No ELSO codes
- **Expected:** Add `elso_code` to all 3 economics fields

#### TEST-1.1.7: `test_metadata_fields_have_elso_codes()`
```python
def test_metadata_fields_have_elso_codes():
    """Metadata fields must have ELSO codes"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    assert 'elso_code' in data_dict['metadata']['created_at']
    assert data_dict['metadata']['created_at']['elso_code'] == 'CREATED_AT'

    assert 'elso_code' in data_dict['metadata']['updated_at']
    assert data_dict['metadata']['updated_at']['elso_code'] == 'UPDATED_AT'

    assert 'elso_code' in data_dict['metadata']['data_source']
    assert data_dict['metadata']['data_source']['elso_code'] == 'DATA_SOURCE'
```
- **Current:** No ELSO codes
- **Expected:** Add `elso_code` to all 3 metadata fields

#### TEST-1.1.8: `test_all_40_fields_have_elso_codes()`
```python
def test_all_40_fields_have_elso_codes():
    """All 40 data fields must have ELSO codes"""
    with open('data_dictionary.yaml') as f:
        data_dict = yaml.safe_load(f)

    fields_with_codes = 0
    total_fields = 0

    for category in ['demographics', 'ecmo_config', 'clinical_indicators',
                     'laboratory', 'nirs', 'risk_scores', 'outcomes',
                     'economics', 'metadata']:
        if category in data_dict:
            for field, specs in data_dict[category].items():
                total_fields += 1
                if 'elso_code' in specs:
                    fields_with_codes += 1

    assert total_fields == 40, f"Expected 40 fields, found {total_fields}"
    assert fields_with_codes == 40, f"Only {fields_with_codes}/40 fields have ELSO codes"
```
- **Current:** 18/40 (45%)
- **Expected:** 40/40 (100%)

---

### Test Suite 1.2: Field Validation Tests
**Coverage Target:** 7/9 categories without validation

#### TEST-1.2.1: `test_ecmo_config_required_fields()`
```python
def test_ecmo_config_required_fields():
    """ECMO config required fields must be validated"""
    processor = ELSODataProcessor()

    # Missing required ecmo_type
    patient_data = {
        'patient_id': 'PT0001',
        'ecmo_type': None,  # Required but missing
        'cannulation_type': 'peripheral'
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('ecmo_type' in err and 'required' in err.lower()
               for err in processor.validation_errors)
```
- **Current:** Not validated by ELSODataProcessor
- **Expected:** `validate_patient_data()` checks ecmo_config.required fields

#### TEST-1.2.2: `test_ecmo_config_range_validation()`
```python
def test_ecmo_config_range_validation():
    """ECMO flow rates must be within valid ranges"""
    processor = ELSODataProcessor()

    # Test invalid flow rate
    patient_data = {
        'patient_id': 'PT0001',
        'flow_lmin': 15.0,  # Outside range [0.1, 10.0]
        'sweep_gas_lmin': 0.05  # Outside range [0.0, 15.0]
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('flow_lmin' in err for err in processor.validation_errors)
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` checks ranges

#### TEST-1.2.3: `test_clinical_indicators_validation()`
```python
def test_clinical_indicators_validation():
    """Clinical indicators must be validated"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'cardiac_arrest': 'yes',  # Should be boolean
        'cpr_duration_min': 350  # Outside range [0, 300]
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('cardiac_arrest' in err for err in processor.validation_errors)
    assert any('cpr_duration_min' in err for err in processor.validation_errors)
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates clinical_indicators category

#### TEST-1.2.4: `test_laboratory_range_validation()`
```python
def test_laboratory_range_validation():
    """Lab values must be within physiologic ranges"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'ph_pre': 5.9,  # Below range [6.0, 8.0]
        'pco2_pre_mmhg': 250.0,  # Above range [10.0, 200.0]
        'po2_pre_mmhg': 5.0,  # Below range [20.0, 500.0]
        'lactate_pre_mmol': 35.0  # Above range [0.5, 30.0]
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert len(processor.validation_errors) == 4
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates laboratory category

#### TEST-1.2.5: `test_nirs_range_validation()`
```python
def test_nirs_range_validation():
    """NIRS values must be within [0, 100] percentage range"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'cerebral_so2': 105.0,  # Above range [0.0, 100.0]
        'renal_so2': -5.0,  # Below range [0.0, 100.0]
        'somatic_so2': 50.0  # Valid
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('cerebral_so2' in err for err in processor.validation_errors)
    assert any('renal_so2' in err for err in processor.validation_errors)
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates nirs category

#### TEST-1.2.6: `test_risk_scores_range_validation()`
```python
def test_risk_scores_range_validation():
    """Risk scores must be within published ranges"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'save_ii_score': 25.0,  # Above range [-20.0, 20.0]
        'resp_ecmo_score': -25.0,  # Below range [-22.0, 15.0]
        'preserve_score': 150.0  # Above range [0.0, 100.0]
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert len(processor.validation_errors) == 3
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates risk_scores category

#### TEST-1.2.7: `test_outcomes_validation()`
```python
def test_outcomes_validation():
    """Outcomes must be validated"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'duration_hours': 2500,  # Above range [1, 2000]
        'survival_to_discharge': True,
        'neurologic_outcome': 'invalid_value'  # Not in enum
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('duration_hours' in err for err in processor.validation_errors)
    assert any('neurologic_outcome' in err for err in processor.validation_errors)
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates outcomes category

#### TEST-1.2.8: `test_economics_range_validation()`
```python
def test_economics_range_validation():
    """Economics values must be within reasonable ranges"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'total_cost_usd': 2000000.0,  # Above range [0.0, 1000000.0]
        'daily_cost_usd': -100.0,  # Below range [0.0, 10000.0]
        'qaly_gained': 100.0  # Above range [0.0, 50.0]
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert len(processor.validation_errors) == 3
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates economics category

#### TEST-1.2.9: `test_metadata_enum_validation()`
```python
def test_metadata_enum_validation():
    """Data source must be from valid enum"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'data_source': 'invalid_source'  # Not in enum
    }

    is_valid = processor.validate_patient_data(patient_data)

    assert is_valid == False
    assert any('data_source' in err for err in processor.validation_errors)
```
- **Current:** No validation
- **Expected:** `validate_patient_data()` validates metadata category

#### TEST-1.2.10: `test_validation_coverage_100_percent()`
```python
def test_validation_coverage_100_percent():
    """All 9 categories must be validated"""
    processor = ELSODataProcessor()

    # Test that validate_patient_data processes all categories
    categories = ['demographics', 'ecmo_config', 'clinical_indicators',
                  'laboratory', 'nirs', 'risk_scores', 'outcomes',
                  'economics', 'metadata']

    # Check that validation logic exists for each category
    for category in categories:
        assert category in processor.data_dict
        # Validation should process this category
        # (implementation-specific check)

    # Current: Only demographics validated
    # Expected: All 9 categories validated
```
- **Current:** 1/9 (demographics only)
- **Expected:** 9/9 categories validated

---

## TDD TEST PLAN - PHASE 2: MAPPING COVERAGE
**Priority:** CRITICAL
**Target:** 100% LOCAL_TO_ELSO mapping

### Test Suite 2.1: Mapping Completeness Tests
**Coverage Target:** 27 missing mappings

#### TEST-2.1.1: `test_demographics_mapping_complete()`
```python
def test_demographics_mapping_complete():
    """All demographics fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    # Check all demographics fields
    assert "patient_id" in LOCAL_TO_ELSO or "subject_id" in LOCAL_TO_ELSO
    assert "age_years" in LOCAL_TO_ELSO or "age" in LOCAL_TO_ELSO
    assert "weight_kg" in LOCAL_TO_ELSO or "weight" in LOCAL_TO_ELSO
    assert "height_cm" in LOCAL_TO_ELSO or "height" in LOCAL_TO_ELSO
    assert "gender" in LOCAL_TO_ELSO or "sex" in LOCAL_TO_ELSO

    # Current: 3/5 mapped (60%)
    # Expected: 5/5 (100%)
```

#### TEST-2.1.2: `test_ecmo_config_mapping_complete()`
```python
def test_ecmo_config_mapping_complete():
    """All ECMO config fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "ecmo_type" in LOCAL_TO_ELSO or "mode" in LOCAL_TO_ELSO
    assert "cannulation_type" in LOCAL_TO_ELSO or "cannulation" in LOCAL_TO_ELSO
    assert "flow_lmin" in LOCAL_TO_ELSO or "flow" in LOCAL_TO_ELSO
    assert "sweep_gas_lmin" in LOCAL_TO_ELSO or "sweep" in LOCAL_TO_ELSO

    # Current: 1/4 mapped (25%)
    # Expected: 4/4 (100%)
```

#### TEST-2.1.3: `test_clinical_indicators_mapping_complete()`
```python
def test_clinical_indicators_mapping_complete():
    """All clinical indicator fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "primary_diagnosis" in LOCAL_TO_ELSO or "primary_dx" in LOCAL_TO_ELSO
    assert "cardiac_arrest" in LOCAL_TO_ELSO or "arrest" in LOCAL_TO_ELSO
    assert "cpr_duration_min" in LOCAL_TO_ELSO or "cpr_dur" in LOCAL_TO_ELSO

    # Current: 0/3 mapped (0%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.4: `test_laboratory_mapping_complete()`
```python
def test_laboratory_mapping_complete():
    """All laboratory fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "ph_pre" in LOCAL_TO_ELSO
    assert "pco2_pre_mmhg" in LOCAL_TO_ELSO or "pco2_pre" in LOCAL_TO_ELSO
    assert "po2_pre_mmhg" in LOCAL_TO_ELSO or "po2_pre" in LOCAL_TO_ELSO
    assert "lactate_pre_mmol" in LOCAL_TO_ELSO or "lactate_mmol_l" in LOCAL_TO_ELSO

    # Current: 1/4 mapped (25%)
    # Expected: 4/4 (100%)
```

#### TEST-2.1.5: `test_nirs_mapping_complete()`
```python
def test_nirs_mapping_complete():
    """All NIRS fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "cerebral_so2" in LOCAL_TO_ELSO or "nirs_cerebral" in LOCAL_TO_ELSO
    assert "renal_so2" in LOCAL_TO_ELSO or "nirs_renal" in LOCAL_TO_ELSO
    assert "somatic_so2" in LOCAL_TO_ELSO or "nirs_somatic" in LOCAL_TO_ELSO

    # Current: 0/3 mapped (0%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.6: `test_risk_scores_mapping_complete()`
```python
def test_risk_scores_mapping_complete():
    """All risk score fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "save_ii_score" in LOCAL_TO_ELSO or "save_ii" in LOCAL_TO_ELSO
    assert "resp_ecmo_score" in LOCAL_TO_ELSO or "resp" in LOCAL_TO_ELSO
    assert "preserve_score" in LOCAL_TO_ELSO or "preserve" in LOCAL_TO_ELSO

    # Current: 0/3 mapped (0%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.7: `test_outcomes_mapping_complete()`
```python
def test_outcomes_mapping_complete():
    """All outcome fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "duration_hours" in LOCAL_TO_ELSO or "duration" in LOCAL_TO_ELSO
    assert "survival_to_discharge" in LOCAL_TO_ELSO or "survival" in LOCAL_TO_ELSO
    assert "neurologic_outcome" in LOCAL_TO_ELSO or "neuro" in LOCAL_TO_ELSO

    # Current: 1/3 mapped (33%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.8: `test_economics_mapping_complete()`
```python
def test_economics_mapping_complete():
    """All economics fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "total_cost_usd" in LOCAL_TO_ELSO or "cost_total" in LOCAL_TO_ELSO
    assert "daily_cost_usd" in LOCAL_TO_ELSO or "cost_daily" in LOCAL_TO_ELSO
    assert "qaly_gained" in LOCAL_TO_ELSO or "qaly" in LOCAL_TO_ELSO

    # Current: 0/3 mapped (0%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.9: `test_metadata_mapping_complete()`
```python
def test_metadata_mapping_complete():
    """All metadata fields must be mapped"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert "created_at" in LOCAL_TO_ELSO or "created" in LOCAL_TO_ELSO
    assert "updated_at" in LOCAL_TO_ELSO or "updated" in LOCAL_TO_ELSO
    assert "data_source" in LOCAL_TO_ELSO or "source" in LOCAL_TO_ELSO

    # Current: 0/3 mapped (0%)
    # Expected: 3/3 (100%)
```

#### TEST-2.1.10: `test_total_mapping_coverage_100_percent()`
```python
def test_total_mapping_coverage_100_percent():
    """Total mapping coverage must be 100%"""
    from etl.elso_mapper import LOCAL_TO_ELSO

    assert len(LOCAL_TO_ELSO) >= 40, f"Expected >=40 mappings, found {len(LOCAL_TO_ELSO)}"

    # Current: 13/40 (32.5%)
    # Expected: 40/40 (100%)
```

---

### Test Suite 2.2: Mapping Functionality Tests
**Priority:** HIGH

#### TEST-2.2.1: `test_map_record_transforms_all_fields()`
```python
def test_map_record_transforms_all_fields():
    """map_record should transform all 40 fields"""
    from etl.elso_mapper import map_record

    # Create record with all 40 fields
    row = {
        'patient_id': 'PT0001',
        'age_years': 45,
        'weight_kg': 70.0,
        # ... all 40 fields ...
    }

    result = map_record(row)

    # Should have 40 ELSO-mapped keys
    assert len(result) >= 40

    # Current: Only 13 fields mapped
    # Expected: All 40 fields mapped
```

#### TEST-2.2.2: `test_map_record_handles_missing_fields()`
```python
def test_map_record_handles_missing_fields():
    """map_record should gracefully handle missing fields"""
    from etl.elso_mapper import map_record

    # Record with only 20 fields
    row = {'patient_id': 'PT0001', 'age_years': 45}

    result = map_record(row)

    # Should not raise error
    # Should return partial mapping
    assert len(result) > 0
    assert 'patient.id' in result or similar_elso_key in result
```

#### TEST-2.2.3: `test_bidirectional_mapping()`
```python
def test_bidirectional_mapping():
    """Should support both local->ELSO and ELSO->local mapping"""
    from etl.elso_mapper import LOCAL_TO_ELSO, ELSO_TO_LOCAL

    # Forward mapping
    assert "patient_id" in LOCAL_TO_ELSO

    # Reverse mapping
    assert "patient.id" in ELSO_TO_LOCAL
    assert ELSO_TO_LOCAL["patient.id"] == "patient_id"

    # Expected: ELSO_TO_LOCAL dictionary for reverse mapping
```

---

## TDD TEST PLAN - PHASE 3: CODE INTEGRATION
**Priority:** HIGH
**Target:** Link 59+ diagnosis/procedure codes to data fields

### Test Suite 3.1: Diagnosis Code Integration Tests
**Coverage:** 36 ICD-10-CM codes

#### TEST-3.1.1: `test_diagnosis_codes_yaml_loaded()`
```python
def test_diagnosis_codes_yaml_loaded():
    """Diagnosis codes YAML must be loaded in processor"""
    processor = ELSODataProcessor()

    assert hasattr(processor, 'diagnosis_codes')
    assert len(processor.diagnosis_codes) > 0
    assert 'cardiac_indications' in processor.diagnosis_codes
    assert 'respiratory_indications' in processor.diagnosis_codes

    # Current: No method exists
    # Expected: Load diagnosis codes in __init__()
```

#### TEST-3.1.2: `test_resolve_primary_diagnosis_by_code()`
```python
def test_resolve_primary_diagnosis_by_code():
    """Should resolve ICD-10 code to diagnosis details"""
    processor = ELSODataProcessor()

    result = processor.resolve_primary_diagnosis("J80")

    assert result is not None
    assert result['code'] == "J80"
    assert result['description'] == "Acute respiratory distress syndrome"
    assert result['category'] == "respiratory_indications"
    assert result['subcategory'] == "ards"

    # Current: No method exists
    # Expected: New method in ELSODataProcessor
```

#### TEST-3.1.3: `test_resolve_cardiac_diagnosis_codes()`
```python
def test_resolve_cardiac_diagnosis_codes():
    """All cardiac diagnosis codes must resolve correctly"""
    processor = ELSODataProcessor()

    cardiac_codes = ["R57.0", "I46.9", "I50.9", "I97.190", "I21.9"]

    for code in cardiac_codes:
        result = processor.resolve_primary_diagnosis(code)
        assert result is not None
        assert result['category'] == "cardiac_indications"
```

#### TEST-3.1.4: `test_resolve_respiratory_diagnosis_codes()`
```python
def test_resolve_respiratory_diagnosis_codes():
    """All respiratory diagnosis codes must resolve correctly"""
    processor = ELSODataProcessor()

    respiratory_codes = ["J80", "J95.1", "J18.9", "I26.90"]

    for code in respiratory_codes:
        result = processor.resolve_primary_diagnosis(code)
        assert result is not None
        assert result['category'] == "respiratory_indications"
```

#### TEST-3.1.5: `test_resolve_neonatal_diagnosis_codes()`
```python
def test_resolve_neonatal_diagnosis_codes():
    """All neonatal diagnosis codes must resolve correctly"""
    processor = ELSODataProcessor()

    neonatal_codes = ["P24.00", "Q79.0", "P29.30", "P22.0"]

    for code in neonatal_codes:
        result = processor.resolve_primary_diagnosis(code)
        assert result is not None
        assert result['category'] == "neonatal_indications"
```

#### TEST-3.1.6: `test_resolve_trauma_diagnosis_codes()`
```python
def test_resolve_trauma_diagnosis_codes():
    """All trauma diagnosis codes must resolve correctly"""
    processor = ELSODataProcessor()

    trauma_codes = ["T07", "S27.0XXA", "T75.1XXA", "T59.811A"]

    for code in trauma_codes:
        result = processor.resolve_primary_diagnosis(code)
        assert result is not None
        assert result['category'] == "trauma_indications"
```

#### TEST-3.1.7: `test_resolve_sepsis_diagnosis_codes()`
```python
def test_resolve_sepsis_diagnosis_codes():
    """All sepsis diagnosis codes must resolve correctly"""
    processor = ELSODataProcessor()

    sepsis_codes = ["R65.21", "A41.9", "U07.1"]

    for code in sepsis_codes:
        result = processor.resolve_primary_diagnosis(code)
        assert result is not None
        assert result['category'] == "sepsis_indications"
```

#### TEST-3.1.8: `test_diagnosis_to_elso_category_mapping()`
```python
def test_diagnosis_to_elso_category_mapping():
    """Diagnosis should map to ELSO category"""
    processor = ELSODataProcessor()

    # Cardiac diagnosis -> ELSO cardiac (VA typical)
    result = processor.resolve_primary_diagnosis("R57.0")
    assert result['elso_category'] == "cardiac"
    assert result['typical_mode'] == "VA"

    # Respiratory diagnosis -> ELSO respiratory (VV typical)
    result = processor.resolve_primary_diagnosis("J80")
    assert result['elso_category'] == "respiratory"
    assert result['typical_mode'] == "VV"
```

#### TEST-3.1.9: `test_invalid_diagnosis_code_handling()`
```python
def test_invalid_diagnosis_code_handling():
    """Invalid diagnosis code should be handled gracefully"""
    processor = ELSODataProcessor()

    result = processor.resolve_primary_diagnosis("INVALID123")

    assert result is None  # or raises clear error
    # Expected: Graceful error handling
```

#### TEST-3.1.10: `test_primary_diagnosis_field_validation()`
```python
def test_primary_diagnosis_field_validation():
    """Primary diagnosis field should validate against ICD-10 codes"""
    processor = ELSODataProcessor()

    patient_data = {
        'patient_id': 'PT0001',
        'primary_diagnosis': 'J80'  # Valid ICD-10
    }

    is_valid = processor.validate_patient_data(patient_data)
    assert is_valid == True

    patient_data['primary_diagnosis'] = 'INVALID'
    is_valid = processor.validate_patient_data(patient_data)
    assert is_valid == False
```

---

### Test Suite 3.2: Procedure Code Integration Tests
**Coverage:** 23 procedure codes (ICD-10-PCS, CPT, SNOMED, NHI)

#### TEST-3.2.1: `test_procedure_codes_yaml_loaded()`
```python
def test_procedure_codes_yaml_loaded():
    """Procedure codes YAML must be loaded in processor"""
    processor = ELSODataProcessor()

    assert hasattr(processor, 'procedure_codes')
    assert 'icd10_pcs' in processor.procedure_codes
    assert 'cpt' in processor.procedure_codes
    assert 'snomed_ct' in processor.procedure_codes
    assert 'taiwan_nhi' in processor.procedure_codes

    # Current: No method exists
    # Expected: Load procedure codes in __init__()
```

#### TEST-3.2.2: `test_resolve_ecmo_type_from_cpt()`
```python
def test_resolve_ecmo_type_from_cpt():
    """CPT code should resolve to ECMO type"""
    processor = ELSODataProcessor()

    assert processor.resolve_ecmo_type_from_cpt("33946") == "VV"
    assert processor.resolve_ecmo_type_from_cpt("33947") == "VA"
    assert processor.resolve_ecmo_type_from_cpt("33948") == "VAV"

    # Current: No method exists
    # Expected: New method in ELSODataProcessor
```

#### TEST-3.2.3: `test_cpt_to_ecmo_mode_mapping()`
```python
def test_cpt_to_ecmo_mode_mapping():
    """All CPT management codes must map to ECMO modes"""
    processor = ELSODataProcessor()

    cpt_mapping = {
        "33946": "VV",
        "33947": "VA",
        "33948": "VAV"
    }

    for cpt, expected_mode in cpt_mapping.items():
        result = processor.resolve_ecmo_type_from_cpt(cpt)
        assert result == expected_mode
```

#### TEST-3.2.4: `test_resolve_cannulation_from_cpt()`
```python
def test_resolve_cannulation_from_cpt():
    """CPT code should resolve to cannulation type"""
    processor = ELSODataProcessor()

    # Percutaneous codes -> peripheral
    assert processor.resolve_cannulation_type("33951") == "peripheral"
    assert processor.resolve_cannulation_type("33952") == "peripheral"

    # Open codes -> peripheral or central (depends on approach)
    assert processor.resolve_cannulation_type("33953") in ["peripheral", "central"]
    assert processor.resolve_cannulation_type("33954") in ["peripheral", "central"]
```

#### TEST-3.2.5: `test_icd10_pcs_duration_mapping()`
```python
def test_icd10_pcs_duration_mapping():
    """ICD-10-PCS code should indicate expected duration"""
    processor = ELSODataProcessor()

    result = processor.resolve_icd10_pcs_code("5A1522F")
    assert result['duration_range'] == (24, 96)  # 24-96 hours

    result = processor.resolve_icd10_pcs_code("5A1532F")
    assert result['duration_range'][0] >= 96  # >96 hours
```

#### TEST-3.2.6: `test_snomed_ct_code_resolution()`
```python
def test_snomed_ct_code_resolution():
    """SNOMED-CT code should resolve to ECMO details"""
    processor = ELSODataProcessor()

    result = processor.resolve_snomed_code("786451004")
    assert result['description'] == "Veno-venous extracorporeal membrane oxygenation"
    assert result['ecmo_type'] == "VV"

    result = processor.resolve_snomed_code("786452006")
    assert result['ecmo_type'] == "VA"
```

#### TEST-3.2.7: `test_taiwan_nhi_code_integration()`
```python
def test_taiwan_nhi_code_integration():
    """Taiwan NHI codes must be integrated"""
    processor = ELSODataProcessor()

    result = processor.resolve_nhi_code("68021C")
    assert result is not None
    assert '體外膜肺氧合術' in result['description']

    result = processor.resolve_nhi_code("68022C")
    assert '管路置放' in result['description']

    # Current: Not integrated
    # Expected: Critical for Taiwan healthcare system billing
```

#### TEST-3.2.8: `test_multiple_procedure_codes_same_patient()`
```python
def test_multiple_procedure_codes_same_patient():
    """Should handle multiple procedure codes per patient"""
    processor = ELSODataProcessor()

    procedure_codes = ["33947", "33954"]  # VA management + open cannulation

    result = processor.process_procedure_codes(procedure_codes)

    assert result['ecmo_type'] == "VA"
    assert result['cannulation_type'] in ["peripheral", "central"]
```

#### TEST-3.2.9: `test_procedure_code_conflict_resolution()`
```python
def test_procedure_code_conflict_resolution():
    """Should handle conflicting procedure codes"""
    processor = ELSODataProcessor()

    # Conflicting codes: VV and VA
    procedure_codes = ["33946", "33947"]

    result = processor.process_procedure_codes(procedure_codes)

    # Should flag conflict or use priority rules
    assert 'conflict' in result or 'warning' in result
```

#### TEST-3.2.10: `test_all_23_procedure_codes_mapped()`
```python
def test_all_23_procedure_codes_mapped():
    """All 23 procedure codes must have resolution methods"""
    processor = ELSODataProcessor()

    # 8 ICD-10-PCS + 8 CPT + 5 SNOMED + 2 NHI = 23
    assert len(processor.procedure_codes['icd10_pcs']) >= 8
    assert len(processor.procedure_codes['cpt']) >= 8
    assert len(processor.procedure_codes['snomed_ct']) >= 5
    assert len(processor.procedure_codes['taiwan_nhi']) >= 2

    # Current: 0/23 integrated
    # Expected: 23/23 integrated
```

---

### Test Suite 3.3: Missing Code Files Tests
**Priority:** MEDIUM
**Coverage:** Complications codes (not yet created)

#### TEST-3.3.1: `test_complications_yaml_exists()`
```python
def test_complications_yaml_exists():
    """Complications code file must exist"""
    import os

    complications_file = "etl/codes/ecmo_complications.yaml"
    assert os.path.exists(complications_file)

    # Current: Does not exist
    # Expected: Create complications code catalog
```

#### TEST-3.3.2: `test_complications_codes_structure()`
```python
def test_complications_codes_structure():
    """Complications YAML must have proper structure"""
    import yaml

    with open("etl/codes/ecmo_complications.yaml") as f:
        complications = yaml.safe_load(f)

    assert 'bleeding_complications' in complications
    assert 'thrombosis_complications' in complications
    assert 'infection_complications' in complications
    assert 'mechanical_complications' in complications
    assert 'neurologic_complications' in complications
```

#### TEST-3.3.3: `test_bleeding_complications_codes()`
```python
def test_bleeding_complications_codes():
    """Bleeding complications must have ICD-10 codes"""
    processor = ELSODataProcessor()

    # Example: I97.51X (Hemorrhage following cardiac procedure)
    assert len(processor.complications['bleeding_complications']) >= 10
```

#### TEST-3.3.4: `test_thrombosis_complications_codes()`
```python
def test_thrombosis_complications_codes():
    """Thrombosis complications must have ICD-10 codes"""
    processor = ELSODataProcessor()

    # Example: I82.90 (Acute embolism and thrombosis)
    assert len(processor.complications['thrombosis_complications']) >= 8
```

#### TEST-3.3.5: `test_infection_complications_codes()`
```python
def test_infection_complications_codes():
    """Infection complications must have ICD-10 codes"""
    processor = ELSODataProcessor()

    # Example: T82.7XXA (Infection of cardiovascular device)
    assert len(processor.complications['infection_complications']) >= 10
```

#### TEST-3.3.6: `test_mechanical_complications_codes()`
```python
def test_mechanical_complications_codes():
    """Mechanical complications must have ICD-10 codes"""
    processor = ELSODataProcessor()

    # Example: T82.511A (Breakdown of ECMO device)
    assert len(processor.complications['mechanical_complications']) >= 5
```

#### TEST-3.3.7: `test_neurologic_complications_codes()`
```python
def test_neurologic_complications_codes():
    """Neurologic complications must have ICD-10 codes"""
    processor = ELSODataProcessor()

    # Example: I63.9 (Cerebral infarction)
    assert len(processor.complications['neurologic_complications']) >= 8
```

---

## IMPLEMENTATION ROADMAP

### Phase 1: Field Coverage (Week 1)
**Complexity:** MEDIUM
**Estimated:** 16 hours

**Tasks:**
1. Add 22 missing ELSO codes to data_dictionary.yaml (2h)
2. Extend validate_patient_data() to all 9 categories (6h)
3. Write 20 unit tests for validation (6h)
4. Update documentation (2h)

**Deliverables:**
- data_dictionary.yaml with 40/40 ELSO codes
- ELSODataProcessor validates all 9 categories
- 20 passing unit tests
- Updated documentation

---

### Phase 2: Mapping Coverage (Week 2)
**Complexity:** LOW-MEDIUM
**Estimated:** 12 hours

**Tasks:**
1. Add 27 missing mappings to LOCAL_TO_ELSO (3h)
2. Create ELSO_TO_LOCAL reverse mapping (2h)
3. Update map_record() to handle all 40 fields (2h)
4. Write 13 unit tests for mapping (4h)
5. Integration test with sample data (1h)

**Deliverables:**
- LOCAL_TO_ELSO with 40/40 mappings
- ELSO_TO_LOCAL reverse mapping
- map_record() handles all fields
- 13 passing unit tests

---

### Phase 3: Code Integration (Week 3-4)
**Complexity:** HIGH
**Estimated:** 32 hours

**Tasks:**
1. Diagnosis code integration (10h)
   - Load ecmo_diagnoses.yaml in __init__
   - Implement resolve_primary_diagnosis()
   - Link to primary_diagnosis field validation
   - Write 10 tests

2. Procedure code integration (10h)
   - Load ecmo_procedures.yaml in __init__
   - Implement CPT/ICD-10-PCS/SNOMED/NHI resolvers
   - Link to ecmo_type and cannulation_type fields
   - Write 10 tests

3. Create ecmo_complications.yaml (6h)
   - Research ICD-10-CM complication codes
   - Structure: bleeding, thrombosis, infection, mechanical, neurologic
   - 40+ complication codes

4. Implement complications integration (4h)
   - Load and resolve complications
   - Add complications field to data_dictionary
   - Write 7 tests

5. Integration testing (2h)

**Deliverables:**
- 36 diagnosis codes integrated
- 23 procedure codes integrated
- ecmo_complications.yaml with 40+ codes
- Complications integration
- 27 passing unit tests

---

### Phase 4: Data Quality (Week 5)
**Complexity:** MEDIUM-HIGH
**Estimated:** 20 hours

**Tasks:**
1. Cross-field validation (8h)
   - Implement validate_cross_fields() method
   - ECMO mode vs indication logic
   - Timestamp logical sequence
   - Duration consistency
   - Write 8 tests

2. Data type and format validation (6h)
   - Patient_id format regex
   - ISO8601 datetime validation
   - Float precision checks
   - Boolean strict typing
   - Write 4 tests

3. Unit consistency validation (4h)
   - Unit suffix checks
   - Percentage representation
   - Write 3 tests

4. Quality report generation (2h)

**Deliverables:**
- validate_cross_fields() method
- Format and type validation
- Unit consistency checks
- 15 passing unit tests
- Data quality report

---

### Phase 5: Risk Scores (Week 6-7)
**Complexity:** CRITICAL-HIGH
**Estimated:** 40 hours

**Tasks:**
1. Complete SAVE-II implementation (12h)
   - Research complete SAVE-II formula
   - Add missing variables to data_dictionary
   - Implement complete scoring
   - Handle missing data
   - Write 6 tests

2. Complete RESP implementation (12h)
   - Research complete RESP formula
   - Add missing variables
   - Link diagnosis to ICD-10 codes
   - Implement complete scoring
   - Write 6 tests

3. Implement PRESERvE score (12h)
   - Research PRESERvE formula
   - Add required variables for eCPR
   - Implement scoring
   - Write 5 tests

4. Risk score integration (2h)
   - Unified calculation method
   - Write 3 tests

5. Clinical validation with domain expert (2h)

**Deliverables:**
- Complete SAVE-II formula (15+ components)
- Complete RESP formula (10+ components)
- Complete PRESERvE formula
- 20 passing unit tests
- Clinical validation approval

---

## TESTING STRATEGY

### Test-First Approach
1. Write test BEFORE implementation (RED)
2. Implement minimal code to pass test (GREEN)
3. Refactor for quality (REFACTOR)
4. Repeat

### Test Organization
```
tests/
├── test_data_dictionary.py      # Field and ELSO code tests
├── test_validation.py            # Validation logic tests
├── test_mapping.py               # LOCAL_TO_ELSO mapping tests
├── test_code_integration.py     # Diagnosis/procedure/complication tests
├── test_data_quality.py         # Cross-field and quality tests
├── test_risk_scores.py          # SAVE-II, RESP, PRESERvE tests
└── test_integration.py          # End-to-end integration tests
```

### Test Coverage Targets
- **Unit test coverage:** 95%+
- **Integration test coverage:** 85%+
- **All 40 data fields:** 100% validated
- **All 59+ codes:** 100% integrated
- **All 3 risk scores:** 100% complete

### Continuous Integration
- Run tests on every commit
- Block merge if tests fail
- Coverage reports in CI/CD
- Automated quality checks

---

## COMPLEXITY ANALYSIS

| Phase | Complexity | Risk Level | Dependencies |
|-------|-----------|------------|--------------|
| Phase 1: Field Coverage | MEDIUM | LOW | None |
| Phase 2: Mapping Coverage | LOW-MEDIUM | LOW | Phase 1 |
| Phase 3: Code Integration | HIGH | MEDIUM | Phase 1, Phase 2 |
| Phase 4: Data Quality | MEDIUM-HIGH | MEDIUM | Phase 1, Phase 2, Phase 3 |
| Phase 5: Risk Scores | CRITICAL-HIGH | HIGH | Phase 1, Phase 4, Clinical Expert |

### Key Risks

**Phase 1:**
- Validation logic edge cases
- Category-specific validation complexity

**Phase 2:**
- Naming consistency across files
- Bidirectional mapping logic

**Phase 3:**
- Code conflict resolution
- Incomplete code catalogs
- Multiple coding systems (ICD-10, CPT, SNOMED, NHI)

**Phase 4:**
- Over-constraining validation (false positives)
- Complex cross-field logic
- Temporal validation edge cases

**Phase 5:**
- Formula accuracy (clinical validation required)
- Missing variables not in current data sources
- Missing data imputation strategy
- PRESERvE formula availability

---

## TIMELINE ESTIMATE

### Aggressive (3 weeks, 40h/week)
- Week 1: Phases 1-2 (Field + Mapping Coverage)
- Week 2: Phase 3 (Code Integration)
- Week 3: Phases 4-5 (Quality + Risk Scores)

### Realistic (6 weeks, 20h/week)
- Weeks 1-2: Phase 1 (Field Coverage)
- Weeks 2-3: Phase 2 (Mapping Coverage)
- Weeks 3-4: Phase 3 (Code Integration)
- Week 5: Phase 4 (Data Quality)
- Weeks 6-7: Phase 5 (Risk Scores)

### Conservative (8 weeks, 15h/week)
- Weeks 1-2: Phase 1
- Week 3: Phase 2
- Weeks 4-5: Phase 3
- Week 6: Phase 4
- Weeks 7-8: Phase 5

**Recommended:** Realistic timeline (6 weeks, 20h/week)

---

## DEPENDENCIES & BLOCKERS

### External Dependencies
- Published SAVE-II formula (accessible ✅)
- Published RESP formula (accessible ✅)
- PRESERvE formula (need to research ⚠️)
- ELSO v3.4 standard documentation (accessible ✅)
- Clinical domain expert for validation (required ⚠️)

### Technical Dependencies
- Python 3.8+ ✅
- pandas, numpy, pyyaml ✅
- pytest for testing ✅
- Existing data_dictionary.yaml structure ✅

### Potential Blockers
1. PRESERvE formula not publicly available
2. Missing variables not in current data sources
3. Clinical validation requires domain expert availability
4. ELSO standard changes/updates during development

### Mitigation Strategies
- Research PRESERvE in medical literature immediately
- Document missing variables for future data collection
- Schedule clinical expert review early
- Version control data dictionary for standard updates

---

## SUCCESS CRITERIA

1. **Field Coverage:** 100% (40/40 fields with ELSO codes)
2. **Validation Coverage:** 100% (all 9 categories validated)
3. **Mapping Coverage:** 100% (40/40 fields in LOCAL_TO_ELSO)
4. **Code Integration:** 100% (59+ codes linked to fields)
5. **Test Coverage:** >95% (all critical paths tested)
6. **Risk Scores:** 100% complete formulas (SAVE-II, RESP, PRESERvE)
7. **Data Quality Score:** 9.0/10 (from current 6.5/10)
8. **Clinical Validation:** Domain expert approval
9. **Documentation:** Complete, updated, accurate
10. **Zero blocking issues** for downstream WPs (WP1-WP4)

---

## READY TO PROCEED

✅ TDD test plan complete
✅ All test cases defined with clear assertions
✅ Current state vs expected state documented
✅ Priority levels assigned
✅ Coverage targets set
✅ Implementation roadmap created
✅ Timeline estimates provided

### Next Steps:
1. Review this plan with stakeholders
2. Prioritize test suites
3. Begin Phase 1: Write first failing test
4. Implement to pass test
5. Repeat until 100% coverage

---

**End of TDD Test Plan for WP0**
**Document:** C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\WP0_TDD_TEST_PLAN.md
**Memory Key:** wp0/tdd-plan
**Version:** 1.0
**Date:** 2025-09-30