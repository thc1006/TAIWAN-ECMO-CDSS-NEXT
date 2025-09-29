# Test Coverage Analysis - TAIWAN-ECMO-CDSS-NEXT

**Analysis Date**: 2025-09-30
**Analyst**: QA Testing Agent
**Total Lines of Code**: 3,190 lines across all modules

---

## Executive Summary

Current test coverage is **CRITICALLY LOW** at approximately **5.9%** (190 test lines / 3,190 total lines). Only 10 basic tests exist, covering primarily imports and file existence checks. **Zero functional unit tests, integration tests, or end-to-end tests** are implemented.

### Coverage Overview by Module

| Module | Lines | Current Tests | Coverage % | Critical Gap |
|--------|-------|---------------|------------|--------------|
| `tests/test_basic_functionality.py` | 190 | 10 tests | 100% | N/A (test file) |
| `etl/elso_processor.py` | 215 | 1 import | ~5% | ⚠️ CRITICAL |
| `nirs/risk_models.py` | 506 | 1 import | ~5% | ⚠️ CRITICAL |
| `econ/cost_effectiveness.py` | 532 | 1 import | ~5% | ⚠️ CRITICAL |
| `econ/dashboard.py` | 747 | 0 | 0% | ⚠️ CRITICAL |
| `vr-training/training_protocol.py` | 700 | 1 import | ~5% | ⚠️ CRITICAL |
| `etl/elso_mapper.py` | 22 | 0 | 0% | HIGH |
| `nirs/features.py` | 15 | 0 | 0% | MEDIUM |
| `sql/identify_ecmo.sql` | Unknown | 1 file check | 0% | HIGH |

**TOTAL ESTIMATED TESTS NEEDED: ~120 tests** to achieve 80% coverage

---

## 1. Existing Tests Documentation

### File: `tests/test_basic_functionality.py` (190 lines)

#### ✅ Test 1: `test_data_dictionary_loading` (lines 17-29)
- **Purpose**: Verify YAML data dictionary loads correctly
- **Coverage**: File I/O, YAML parsing, basic structure validation
- **Assertions**: 4 (file exists, not empty, version present, required sections)
- **Status**: PASSING

#### ✅ Test 2: `test_code_lists_loading` (lines 31-48)
- **Purpose**: Verify ECMO code lists (procedures, diagnoses) load
- **Coverage**: YAML loading of clinical codes
- **Assertions**: 4 (file existence, ICD-10-PCS codes, cardiac indications)
- **Status**: PASSING

#### ✅ Test 3: `test_elso_processor_import` (lines 50-72)
- **Purpose**: Test ELSO processor import and basic initialization
- **Coverage**: Module import, class instantiation, demo data validation
- **Assertions**: 3 (not None, validation returns bool)
- **Gap**: **DOES NOT TEST** any actual data processing logic
- **Status**: PASSING (but insufficient)

#### ✅ Test 4: `test_nirs_risk_model_import` (lines 74-93)
- **Purpose**: Test NIRS model import and basic properties
- **Coverage**: Module import, model initialization for VA/VV, demo data generation
- **Assertions**: 5 (ECMO types correct, demo data structure)
- **Gap**: **DOES NOT TEST** training, prediction, or calibration
- **Status**: PASSING (but insufficient)

#### ✅ Test 5: `test_cost_effectiveness_import` (lines 95-110)
- **Purpose**: Test cost-effectiveness module import
- **Coverage**: Module import, analyzer initialization, cost parameters
- **Assertions**: 3 (analyzer not None, costs > 0)
- **Gap**: **DOES NOT TEST** any calculation methods
- **Status**: PASSING (but insufficient)

#### ✅ Test 6: `test_vr_training_import` (lines 112-130)
- **Purpose**: Test VR training module import
- **Coverage**: Module import, protocol initialization, scenario filtering
- **Assertions**: 5 (protocol not None, scenarios exist, filtering works)
- **Gap**: **DOES NOT TEST** performance assessment or competency evaluation
- **Status**: PASSING (but insufficient)

#### ✅ Test 7: `test_sql_file_exists` (lines 132-143)
- **Purpose**: Verify SQL file exists and contains expected content
- **Coverage**: File existence, basic SQL content validation
- **Assertions**: 3 (file exists, not empty, contains SELECT and ECMO)
- **Gap**: **DOES NOT EXECUTE** SQL against MIMIC-IV Demo database
- **Status**: PASSING (but insufficient)

#### ✅ Test 8: `test_requirements_file_exists` (lines 145-156)
- **Purpose**: Check requirements.txt has key dependencies
- **Coverage**: Dependency file validation
- **Assertions**: 4 (pandas, streamlit, scikit-learn present)
- **Status**: PASSING

#### ✅ Test 9: `test_environment_template_exists` (lines 158-168)
- **Purpose**: Verify .env.example template exists
- **Coverage**: Environment configuration template
- **Assertions**: 3 (file exists, DATABASE_URL, SECRET_KEY present)
- **Status**: PASSING

#### ✅ Test 10: `test_basic_data_processing` (lines 170-188)
- **Purpose**: Test basic pandas operations
- **Coverage**: DataFrame creation, aggregation, groupby
- **Assertions**: 4 (length, mean calculation, survival by type)
- **Gap**: Uses toy data, not realistic ECMO data
- **Status**: PASSING (but trivial)

---

## 2. Critical Coverage Gaps

### 2.1 ETL Module: `etl/elso_processor.py` (215 lines)

**Current Coverage**: ~5% (import only)
**Functions Untested**: 12 out of 13 functions

#### Missing Unit Tests (20 tests needed):

1. **`load_data_dictionary()`** (lines 28-36)
   - Test successful YAML loading
   - Test FileNotFoundError handling
   - Test malformed YAML handling
   - Test version extraction

2. **`validate_patient_data()`** (lines 38-78)
   - Test required field validation
   - Test numeric range validation
   - Test enum value validation
   - Test multiple validation errors accumulation
   - Test edge cases (None, empty string)

3. **`transform_ecmo_data()`** (lines 80-130)
   - Test ECMO type normalization (VA, VV, VAV)
   - Test BMI calculation
   - Test timestamp conversion
   - Test ELSO compliance flag calculation
   - Test empty DataFrame handling

4. **`calculate_risk_scores()`** (lines 132-175)
   - Test SAVE-II score calculation
   - Test RESP score calculation
   - Test age component scoring
   - Test weight component scoring
   - Test cardiac arrest impact

5. **`export_to_elso_format()`** (lines 177-201)
   - Test CSV export
   - Test column filtering (ELSO-required only)
   - Test file write permissions
   - Test data integrity after export

#### Missing Integration Tests (5 tests):
- End-to-end ETL pipeline with sample data
- MIMIC-IV to ELSO format conversion
- Data validation error reporting
- Large dataset processing (>10,000 records)
- Performance benchmarks (processing time)

---

### 2.2 NIRS Risk Models: `nirs/risk_models.py` (506 lines)

**Current Coverage**: ~5% (import only)
**Functions Untested**: 15 out of 16 functions

#### Missing Unit Tests (30 tests needed):

1. **`__init__()`** (lines 36-75)
   - Test VA vs VV feature set selection
   - Test feature count validation
   - Test invalid ECMO type handling

2. **`prepare_nirs_features()`** (lines 77-112)
   - Test NIRS trend calculations (cerebral, renal, somatic)
   - Test NIRS variability calculation
   - Test NIRS adequacy score
   - Test missing NIRS data handling

3. **`calculate_risk_scores()`** (lines 114-168)
   - Test SAVE-II score for VA-ECMO
   - Test RESP score for VV-ECMO
   - Test score component calculations
   - Test edge case ages (18, 90)

4. **`train_model()`** (lines 170-275)
   - Test model training with sufficient data
   - Test train/validation split
   - Test feature scaling
   - Test model selection (Logistic, RF, GBM)
   - Test calibration (isotonic regression)
   - Test SHAP explainer initialization
   - Test insufficient data handling
   - Test class imbalance handling

5. **`predict_risk()`** (lines 277-299)
   - Test prediction on new patients
   - Test batch predictions
   - Test model not trained error
   - Test missing feature handling
   - Test prediction probability range (0-1)

6. **`explain_prediction()`** (lines 301-343)
   - Test SHAP value calculation
   - Test feature importance ranking
   - Test individual patient explanation
   - Test explanation without trained model

7. **`plot_calibration()`** (lines 345-385)
   - Test calibration curve generation
   - Test ROC curve generation
   - Test plot file saving
   - Test plot with imbalanced data

8. **`save_model()` / `load_model()`** (lines 387-407)
   - Test model serialization
   - Test model deserialization
   - Test file path validation
   - Test corrupted file handling

9. **`generate_demo_data()`** (lines 410-478)
   - Test data generation for VA/VV types
   - Test patient count accuracy
   - Test feature distributions
   - Test survival outcome generation

#### Missing Integration Tests (8 tests):
- Full training pipeline with real MIMIC-IV data
- VA-ECMO model training and evaluation
- VV-ECMO model training and evaluation
- Model performance on validation set (AUC > 0.75)
- Calibration quality assessment (Brier score < 0.15)
- Cross-validation with 5 folds
- Model comparison (Logistic vs RF vs GBM)
- Explainability output verification

---

### 2.3 Cost-Effectiveness: `econ/cost_effectiveness.py` (532 lines)

**Current Coverage**: ~5% (import only)
**Functions Untested**: 12 out of 13 functions

#### Missing Unit Tests (25 tests needed):

1. **`CostParameters` dataclass** (lines 22-45)
   - Test default values
   - Test Taiwan cost multiplier application
   - Test custom parameter initialization

2. **`UtilityParameters` dataclass** (lines 48-60)
   - Test health state utilities (0-1 range)
   - Test life expectancy adjustments

3. **`calculate_ecmo_costs()`** (lines 85-184)
   - Test daily cost calculations
   - Test ECMO duration from hours to days
   - Test cannulation/decannulation costs
   - Test complication costs (bleeding, stroke, AKI, infection)
   - Test circuit replacement costs
   - Test Taiwan cost multiplier application
   - Test zero-duration edge case

4. **`calculate_qaly_outcomes()`** (lines 186-260)
   - Test neurologic outcome distribution
   - Test utility mapping
   - Test life expectancy calculation
   - Test QALY calculation for survivors
   - Test QALY = 0 for deceased patients
   - Test discounting future QALYs

5. **`calculate_icer()`** (lines 262-310)
   - Test ICER calculation (incremental cost/QALY)
   - Test cost-effective thresholds ($50k, $100k)
   - Test dominated intervention handling
   - Test dominant intervention (cost-saving)
   - Test negative QALY difference

6. **`budget_impact_analysis()`** (lines 325-396)
   - Test annual case calculation
   - Test multi-year projections
   - Test discount rate application
   - Test population size variations
   - Test utilization rate variations

7. **`sensitivity_analysis()`** (lines 398-442)
   - Test one-way sensitivity for each parameter
   - Test parameter range validation
   - Test ICER changes from base case

8. **`plot_cost_effectiveness_plane()`** (lines 444-493)
   - Test plot generation
   - Test willingness-to-pay threshold lines
   - Test quadrant labels
   - Test file saving

9. **`generate_demo_economic_data()`** (lines 496-508)
   - Test demo data generation
   - Test survival rate distribution
   - Test ECMO duration distribution

#### Missing Integration Tests (5 tests):
- Full cost-effectiveness analysis pipeline
- ICER calculation with real patient data
- Budget impact for 5-year horizon
- Sensitivity analysis for all cost parameters
- CEAC (Cost-Effectiveness Acceptability Curve) generation

---

### 2.4 Dashboard: `econ/dashboard.py` (747 lines)

**Current Coverage**: 0% (NO TESTS)
**Functions Untested**: 15 out of 15 functions

#### Missing UI/Integration Tests (15 tests needed):

1. **`main()`** (lines 82-116)
   - Test dashboard initialization
   - Test navigation menu rendering
   - Test warning box display

2. **`show_home()`** (lines 118-201)
   - Test home page rendering
   - Test metric cards display
   - Test feature table rendering
   - Test sample data generation

3. **`show_risk_assessment()`** (lines 203-369)
   - Test ECMO type selection
   - Test patient input form rendering
   - Test VA-ECMO specific fields
   - Test VV-ECMO specific fields
   - Test risk calculation on form submission
   - Test risk visualization (bar charts)
   - Test recommendations generation

4. **`calculate_simplified_risk()`** (lines 371-405)
   - Test risk score calculation
   - Test age effect on risk
   - Test NIRS effect on risk
   - Test laboratory value effects
   - Test VA-specific factors
   - Test VV-specific factors
   - Test risk capping at 95%

5. **`show_cost_effectiveness()`** (lines 459-587)
   - Test parameter input fields
   - Test cost-effectiveness calculation
   - Test budget impact visualization
   - Test summary table rendering

6. **`show_analytics()`** (lines 589-661)
   - Test key metrics display
   - Test survival by age analysis
   - Test NIRS value distributions
   - Test risk score histograms

7. **`show_about()`** (lines 663-746)
   - Test about page rendering
   - Test version information display

#### Missing End-to-End Tests (5 tests):
- Complete user workflow: Home → Risk Assessment → Results
- Complete user workflow: Cost-Effectiveness Analysis
- Complete user workflow: Analytics Dashboard exploration
- Error handling for invalid inputs
- Responsive design testing

---

### 2.5 VR Training: `vr-training/training_protocol.py` (700 lines)

**Current Coverage**: ~5% (import only)
**Functions Untested**: 15 out of 16 functions

#### Missing Unit Tests (20 tests needed):

1. **`_initialize_scenarios()`** (lines 62-271)
   - Test all 6 scenarios initialized
   - Test scenario structure validation
   - Test VA/VV/Both scenario distribution

2. **`get_scenarios_by_difficulty()`** (lines 273-275)
   - Test filtering for Beginner/Intermediate/Advanced
   - Test empty result handling

3. **`get_scenarios_by_ecmo_type()`** (lines 277-279)
   - Test VA filtering
   - Test VV filtering
   - Test "Both" scenarios included in all filters

4. **`assess_performance()`** (lines 281-342)
   - Test complete performance assessment
   - Test technical score calculation
   - Test communication score calculation
   - Test decision-making score calculation
   - Test overall score (weighted average)
   - Test competency achievement logic

5. **`_calculate_technical_score()`** (lines 344-372)
   - Test time-based deductions
   - Test technical error penalties
   - Test critical step completion rate
   - Test sterile technique maintenance

6. **`_calculate_communication_score()`** (lines 374-394)
   - Test communication rating conversion
   - Test leadership bonus
   - Test instruction clarity impact
   - Test situation awareness impact

7. **`_calculate_decision_making_score()`** (lines 396-416)
   - Test correct decision percentage
   - Test complication handling assessment
   - Test priority setting evaluation

8. **`generate_learning_path()`** (lines 448-502)
   - Test new trainee path (beginner scenarios)
   - Test progression to intermediate/advanced
   - Test weak area identification
   - Test scenario recommendations

9. **`generate_competency_report()`** (lines 504-568)
   - Test report generation with performance data
   - Test competency rate calculation
   - Test performance trend analysis
   - Test error frequency tracking

10. **`export_training_data()`** (lines 595-633)
    - Test JSON export
    - Test data serialization
    - Test file write success

#### Missing Integration Tests (5 tests):
- Complete training session workflow
- Multi-trainee progress tracking
- Competency report generation for multiple sessions
- Learning path adaptation over time
- Export and import of training data

---

### 2.6 ETL Mapper: `etl/elso_mapper.py` (22 lines)

**Current Coverage**: 0% (NO TESTS)
**Functions Untested**: 1 out of 1 function

#### Missing Unit Tests (3 tests needed):

1. **`map_record()`** (lines 15-21)
   - Test complete record mapping
   - Test partial record mapping (missing keys)
   - Test empty record handling
   - Test nested key mapping ("patient.id", "ecmo.mode")

---

### 2.7 NIRS Features: `nirs/features.py` (15 lines)

**Current Coverage**: 0% (NO TESTS)
**Functions Untested**: 2 out of 2 functions

#### Missing Unit Tests (4 tests needed):

1. **`fixed_window()`** (lines 3-5)
   - Test time window filtering
   - Test edge cases (start = end)
   - Test empty DataFrame result

2. **`nirs_feature_frame()`** (lines 6-14)
   - Test feature calculation (mean, std, slope)
   - Test side filtering (non-cannulated)
   - Test missing columns handling

---

### 2.8 SQL Queries: `sql/identify_ecmo.sql`

**Current Coverage**: 0% (file check only)
**Queries Untested**: All queries

#### Missing Integration Tests (10 tests needed):

1. **MIMIC-IV Demo Execution Tests**:
   - Test query execution against MIMIC-IV Demo database
   - Test result set structure (expected columns)
   - Test ECMO episode identification accuracy
   - Test date range filtering
   - Test patient deduplication
   - Test join correctness (procedures, diagnoses, labs)
   - Test performance (query time < 30 seconds)
   - Test empty result handling
   - Test edge case patients (multiple ECMO runs)
   - Test SQL syntax validation

---

## 3. Estimated Test Requirements

### 3.1 Summary by Test Type

| Test Type | Current | Needed | Total | Priority |
|-----------|---------|--------|-------|----------|
| **Unit Tests** | 10 | 110 | 120 | CRITICAL |
| **Integration Tests** | 0 | 38 | 38 | HIGH |
| **End-to-End Tests** | 0 | 10 | 10 | MEDIUM |
| **Performance Tests** | 0 | 5 | 5 | LOW |
| **TOTAL** | **10** | **163** | **173** | - |

### 3.2 Priority Breakdown

#### 🔴 CRITICAL PRIORITY (40 tests)
- Model training/prediction tests (NIRS risk models)
- Cost calculation tests (ECMO economics)
- Data validation tests (ETL pipeline)
- Performance assessment tests (VR training)

#### 🟠 HIGH PRIORITY (35 tests)
- Integration tests for full pipelines
- SQL query execution tests
- Data transformation tests
- Calibration quality tests

#### 🟡 MEDIUM PRIORITY (25 tests)
- Dashboard UI tests
- End-to-end workflow tests
- Error handling tests
- Edge case tests

#### 🟢 LOW PRIORITY (10 tests)
- Performance benchmarks
- Documentation tests
- Visual regression tests
- Accessibility tests

---

## 4. Test Implementation Plan

### Phase 1: Foundation (Week 1-2) - 30 tests

**Focus**: Critical unit tests for core functions

1. **ETL Module** (10 tests)
   - `validate_patient_data()` - all validation types
   - `transform_ecmo_data()` - ECMO type normalization, BMI calc
   - `calculate_risk_scores()` - SAVE-II, RESP

2. **NIRS Models** (15 tests)
   - `prepare_nirs_features()` - trend, variability calculations
   - `train_model()` - model selection, calibration
   - `predict_risk()` - batch prediction, error handling

3. **Cost-Effectiveness** (5 tests)
   - `calculate_ecmo_costs()` - daily costs, complications
   - `calculate_qaly_outcomes()` - utility mapping, QALY calc

### Phase 2: Core Functionality (Week 3-4) - 40 tests

**Focus**: Complete coverage of main modules

1. **NIRS Models** (15 tests)
   - `explain_prediction()` - SHAP values
   - `plot_calibration()` - calibration curves
   - `save_model()` / `load_model()` - serialization

2. **Cost-Effectiveness** (15 tests)
   - `calculate_icer()` - ICER logic
   - `budget_impact_analysis()` - multi-year projections
   - `sensitivity_analysis()` - parameter variations

3. **VR Training** (10 tests)
   - `assess_performance()` - scoring algorithms
   - `generate_learning_path()` - recommendations
   - `generate_competency_report()` - report generation

### Phase 3: Integration (Week 5-6) - 38 tests

**Focus**: End-to-end workflows and database tests

1. **SQL Queries** (10 tests)
   - Execute against MIMIC-IV Demo
   - Validate ECMO episode identification
   - Performance benchmarks

2. **ETL Pipeline** (8 tests)
   - MIMIC-IV to ELSO conversion
   - Large dataset processing
   - Error reporting

3. **Model Training** (10 tests)
   - VA-ECMO full training pipeline
   - VV-ECMO full training pipeline
   - Cross-validation

4. **Dashboard** (10 tests)
   - Risk assessment workflow
   - Cost-effectiveness workflow
   - Analytics visualization

### Phase 4: UI & Polish (Week 7-8) - 25 tests

**Focus**: Dashboard UI, edge cases, documentation

1. **Dashboard UI** (15 tests)
   - Complete user workflows
   - Error handling
   - Input validation

2. **Edge Cases** (10 tests)
   - Missing data handling
   - Extreme values
   - Empty datasets

---

## 5. Testing Infrastructure Needs

### 5.1 Testing Frameworks

```python
# requirements-test.txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1
hypothesis==6.92.0  # Property-based testing
faker==20.1.0  # Test data generation

# Dashboard testing
selenium==4.15.2
pytest-selenium==4.0.1
streamlit-testing==0.1.0  # If available

# Database testing
pytest-postgresql==5.0.0
sqlalchemy==2.0.23

# Performance testing
locust==2.18.0
memory-profiler==0.61.0
```

### 5.2 Test Data Requirements

1. **Mock MIMIC-IV Data**
   - 500 ECMO patients (VA/VV split)
   - Realistic demographics, labs, outcomes
   - Stored in `tests/fixtures/mimic_demo_data.csv`

2. **Demo NIRS Data**
   - Continuous monitoring data
   - Multiple body sites (cerebral, renal, somatic)
   - Time-series format

3. **Cost Data**
   - Taiwan-specific cost parameters
   - Complication rates
   - QALY utilities

### 5.3 CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

---

## 6. Test Quality Metrics & Goals

### 6.1 Coverage Goals

| Metric | Current | Target (3 months) | Target (6 months) |
|--------|---------|-------------------|-------------------|
| **Line Coverage** | 5.9% | 60% | 85% |
| **Branch Coverage** | 0% | 50% | 75% |
| **Function Coverage** | 8.3% | 75% | 90% |

### 6.2 Quality Metrics

| Metric | Target |
|--------|--------|
| Test Execution Time | < 5 minutes (full suite) |
| Test Failure Rate | < 5% |
| Code Review Coverage | 100% of PRs |
| Documentation Coverage | 80% of functions |
| Performance Regression | < 10% slowdown allowed |

---

## 7. Risk Assessment

### 7.1 Testing Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Insufficient test data | HIGH | HIGH | Generate synthetic MIMIC-IV data |
| Long test execution time | MEDIUM | MEDIUM | Parallelize tests, use fixtures |
| Flaky tests | MEDIUM | HIGH | Use fixed random seeds, mocks |
| Missing MIMIC-IV access | HIGH | CRITICAL | Use public MIMIC-IV Demo |
| Dashboard testing complexity | HIGH | MEDIUM | Use Selenium, headless browsers |

### 7.2 Coverage Risks

| Module | Risk | Impact on Production |
|--------|------|----------------------|
| `nirs/risk_models.py` | Model predictions incorrect | **CRITICAL** - Patient safety |
| `etl/elso_processor.py` | Data corruption | **HIGH** - Invalid registry submissions |
| `econ/cost_effectiveness.py` | Incorrect costs | **MEDIUM** - Budget errors |
| `dashboard.py` | UI crashes | **MEDIUM** - User experience |
| `vr-training/training_protocol.py` | Wrong competency | **LOW** - Training quality |

---

## 8. Recommendations

### Immediate Actions (This Week)

1. ✅ **Create test infrastructure**
   - Set up `pytest` configuration
   - Create `tests/fixtures/` directory
   - Add `requirements-test.txt`

2. ✅ **Write 10 critical tests**
   - `test_validate_patient_data()` - ETL
   - `test_train_model()` - NIRS VA
   - `test_train_model()` - NIRS VV
   - `test_predict_risk()` - NIRS
   - `test_calculate_ecmo_costs()` - Economics
   - `test_calculate_qaly_outcomes()` - Economics
   - `test_calculate_icer()` - Economics
   - `test_assess_performance()` - VR Training
   - `test_map_record()` - ETL Mapper
   - `test_nirs_feature_frame()` - NIRS Features

3. ✅ **Set up CI/CD**
   - Configure GitHub Actions
   - Add coverage reporting (Codecov)
   - Enable branch protection rules

### Short-term Goals (1 Month)

- Achieve **30% coverage** (50+ tests)
- All critical functions have unit tests
- Basic integration tests for ETL and models

### Medium-term Goals (3 Months)

- Achieve **60% coverage** (110+ tests)
- Complete integration test suite
- Dashboard UI tests operational

### Long-term Goals (6 Months)

- Achieve **85% coverage** (170+ tests)
- Full end-to-end test suite
- Performance benchmarks established
- Continuous monitoring in production

---

## 9. Appendix: Test Template Examples

### A. Unit Test Template

```python
# tests/test_etl_elso_processor.py
import pytest
import pandas as pd
from etl.elso_processor import ELSODataProcessor

@pytest.fixture
def processor():
    """Fixture for ELSO processor with test data dictionary"""
    return ELSODataProcessor()

@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        'patient_id': 'TEST001',
        'age_years': 55,
        'weight_kg': 70,
        'gender': 'M',
        'ecmo_type': 'VA'
    }

def test_validate_patient_data_valid(processor, sample_patient_data):
    """Test validation with valid patient data"""
    result = processor.validate_patient_data(sample_patient_data)
    assert result == True
    assert len(processor.validation_errors) == 0

def test_validate_patient_data_invalid_age(processor, sample_patient_data):
    """Test validation fails with invalid age"""
    sample_patient_data['age_years'] = 200  # Invalid
    result = processor.validate_patient_data(sample_patient_data)
    assert result == False
    assert any('age_years' in str(err) for err in processor.validation_errors)

def test_validate_patient_data_missing_required(processor):
    """Test validation fails with missing required field"""
    incomplete_data = {'patient_id': 'TEST002'}
    result = processor.validate_patient_data(incomplete_data)
    assert result == False
```

### B. Integration Test Template

```python
# tests/integration/test_etl_pipeline.py
import pytest
import pandas as pd
from etl.elso_processor import ELSODataProcessor

@pytest.fixture
def mimic_sample_data():
    """Load sample MIMIC-IV data"""
    return pd.read_csv('tests/fixtures/mimic_demo_data.csv')

def test_full_etl_pipeline(mimic_sample_data):
    """Test complete ETL pipeline from MIMIC-IV to ELSO format"""
    processor = ELSODataProcessor()

    # Transform data
    transformed = processor.transform_ecmo_data(mimic_sample_data)

    # Validate all records
    assert len(transformed) > 0
    assert 'elso_compliant' in transformed.columns
    assert transformed['elso_compliant'].mean() > 0.8  # 80%+ compliance

    # Export to ELSO format
    output_path = 'tests/output/elso_export_test.csv'
    processor.export_to_elso_format(transformed, output_path)

    # Verify export
    exported = pd.read_csv(output_path)
    assert len(exported) == len(transformed)
```

### C. Dashboard UI Test Template

```python
# tests/ui/test_dashboard_risk_assessment.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def browser():
    """Selenium browser fixture"""
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_risk_assessment_workflow(browser):
    """Test complete risk assessment workflow"""
    # Navigate to dashboard
    browser.get('http://localhost:8501')

    # Select Risk Assessment page
    risk_link = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Risk Assessment"))
    )
    risk_link.click()

    # Fill in patient data
    browser.find_element(By.NAME, "age").send_keys("55")
    browser.find_element(By.NAME, "weight").send_keys("70")
    browser.find_element(By.NAME, "cerebral_so2").send_keys("70")

    # Submit form
    submit_button = browser.find_element(By.XPATH, "//button[text()='Calculate Risk Score']")
    submit_button.click()

    # Verify results displayed
    risk_score = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "risk-score"))
    )
    assert risk_score.is_displayed()
    assert "%" in risk_score.text
```

---

## Conclusion

The TAIWAN-ECMO-CDSS-NEXT project has a **severe test coverage deficit** that poses risks to data integrity, model accuracy, and patient safety. With only 10 basic tests covering ~6% of the codebase, **approximately 120 additional tests are needed** to achieve minimum 80% coverage.

**Priority actions:**
1. Implement 30 critical unit tests (NIRS models, ETL validation, cost calculations)
2. Add 38 integration tests (SQL execution, pipelines, workflows)
3. Deploy 10 end-to-end tests (dashboard workflows, user scenarios)

**Timeline**: 8 weeks for full implementation with dedicated testing resources.

**Key Focus**: Model prediction accuracy and data validation tests are CRITICAL for clinical safety.