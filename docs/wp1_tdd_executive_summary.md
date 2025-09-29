# WP1 NIRS+EHR Risk Models - TDD Analysis Executive Summary

## Overview

Comprehensive Test-Driven Development analysis of Taiwan ECMO CDSS NIRS-enhanced risk prediction models completed. Full detailed plan available in `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\wp1_tdd_test_plan.md`.

---

## Current Implementation Status

### Architecture Analysis

**Model Pipeline**:
```
Raw Data → NIRS Features → Risk Scores → Training → Calibration → SHAP → Prediction
```

**Models Implemented**:
- LogisticRegression (with StandardScaler)
- RandomForestClassifier (100 trees)
- GradientBoostingClassifier
- Isotonic calibration (CV=3)
- SHAP explainability (Linear + Tree)

**Features**:
- VA-ECMO: 24 features (cardiac-focused)
- VV-ECMO: 25 features (respiratory-focused)

**NIRS Features**:
- Trend calculations (24h slope): cerebral, renal, somatic
- Variability (coefficient of variation)
- Adequacy score (weighted composite: 50% cerebral, 30% renal, 20% somatic)

**Risk Scores**:
- VA: SAVE-II Score (age, weight, cardiac arrest, bicarbonate)
- VV: RESP Score (age, immunocompromised, ventilation duration)

---

## Critical Gaps Identified

### 1. Class Imbalance Handling ⚠️ HIGH PRIORITY

**Issue**: No SMOTE or class_weight implementation despite 40-60% mortality rates

**Impact**: Model may underperform on minority class (survivors or non-survivors depending on dataset)

**Recommendation**:
```python
# Add to train_model():
from imblearn.over_sampling import SMOTE

if handle_imbalance:
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train, y_train = smote.fit_resample(X_train, y_train)

# For LogisticRegression:
LogisticRegression(class_weight='balanced')

# For RandomForest:
RandomForestClassifier(class_weight='balanced')
```

### 2. APACHE Stratification ⚠️ MEDIUM PRIORITY

**Issue**: No severity-based performance validation

**Impact**: Model performance unknown across different patient severity strata

**Recommendation**: Add APACHE-II score calculation and stratified testing (low: 0-15, medium: 15-25, high: 25-50)

### 3. Missing NIRS Edge Cases ⚠️ MEDIUM PRIORITY

**Issue**: Only median imputation for missing values; no handling for completely absent NIRS data

**Impact**: May fail or produce poor predictions when NIRS monitoring unavailable

**Recommendation**: Implement multiple imputation or flag-based approach for missing NIRS sensors

### 4. Performance Regression Testing ⚠️ MEDIUM PRIORITY

**Issue**: No benchmark tests for model updates

**Impact**: Risk of performance degradation with code changes

**Recommendation**: Establish baseline benchmarks and regression tests (AUC ±5% tolerance)

---

## Comprehensive Test Plan

### Test Structure (90+ tests planned)

**Unit Tests (70%)**: 63 tests
- Feature engineering: 12 tests
- Risk score calculations: 8 tests
- Model training: 15 tests
- Calibration: 10 tests
- SHAP explainability: 10 tests
- Edge cases: 8 tests

**Integration Tests (20%)**: 18 tests
- VA vs VV separation: 6 tests
- End-to-end pipeline: 6 tests
- Class imbalance handling: 6 tests

**Performance Tests (10%)**: 9 tests
- APACHE stratification: 3 tests
- Benchmark regression: 3 tests
- Speed benchmarks: 3 tests

### Test Coverage Targets

| Component | Coverage | Tests |
|-----------|----------|-------|
| Feature Engineering | 95% | 12 |
| Risk Scores | 100% | 8 |
| Model Training | 90% | 15 |
| Calibration | 90% | 10 |
| SHAP | 85% | 10 |
| Edge Cases | 100% | 8 |
| **Overall** | **≥90%** | **90+** |

---

## Acceptance Criteria

### Performance Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **AUC-ROC** | ≥0.75 | Unknown (no validation data) | ❓ Pending |
| **Brier Score** | <0.15 | Unknown | ❓ Pending |
| **Sensitivity** | ≥0.80 | Unknown | ❓ Pending |
| **Specificity** | ≥0.70 | Unknown | ❓ Pending |
| **Test Coverage** | ≥90% | 0% (no tests) | ❌ Missing |
| **Inference Time** | <10ms | ~8.5ms (estimated) | ✅ Likely OK |

### Robustness Requirements

- ✅ Separate VA and VV models implemented
- ❌ Class imbalance handling (SMOTE/class_weight)
- ❌ APACHE stratification validation
- ⚠️ Missing NIRS handling (partial - uses defaults)
- ❌ Outlier robustness tests
- ❌ Save/load consistency tests
- ✅ SHAP explainability implemented
- ❌ SHAP mathematical correctness validation

---

## Key Test Specifications

### 1. Feature Engineering Tests

**File**: `tests/unit/test_feature_engineering.py`

```python
def test_prepare_nirs_features_basic():
    """Test NIRS trend, variability, adequacy calculations"""
    # Validate: trends negative (min < baseline)
    # Validate: variability in [0,1]
    # Validate: adequacy weighted 0.5/0.3/0.2

def test_prepare_nirs_features_missing_data():
    """Test defaults: cerebral=70, renal=75, somatic=70"""
    # Validate: no NaN in output
    # Validate: defaults applied correctly

def test_prepare_nirs_features_edge_cases():
    """Test all-zero, all-max, negative values"""
    # Validate: graceful handling or errors
```

### 2. Model Training Tests

**File**: `tests/unit/test_model_training.py`

```python
def test_train_model_basic_va():
    """Test VA-ECMO with synthetic data (n=200)"""
    # Target: AUC ≥0.70, Brier ≤0.20 (relaxed for synthetic)
    # Validate: train/val split 80/20
    # Validate: calibrated_model created

@pytest.mark.parametrize("mortality_rate", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_train_model_class_imbalance(mortality_rate):
    """Test across 10-90% mortality"""
    # Target: AUC ≥0.65 for extreme imbalance
    # Validate: predictions not collapsed to 0 or 1
```

### 3. Calibration Tests

**File**: `tests/unit/test_calibration.py`

```python
def test_calibration_brier_score():
    """Target: Brier <0.15"""
    # Validate: calibration improves baseline by ≥10%

def test_calibration_curve_reliability():
    """Target: ECE <0.10"""
    # Validate: all bins within ±15% of perfect calibration
```

### 4. SHAP Tests

**File**: `tests/unit/test_shap_explainability.py`

```python
def test_shap_values_consistency():
    """Validate: shap_sum ≈ prediction (within 5%)"""

def test_shap_feature_importance_ranking():
    """Clinical expectation: age, lactate, NIRS in top 5"""
    # Validate: ≥2 of 3 clinical features in top 5
```

### 5. APACHE Stratification Tests

**File**: `tests/integration/test_apache_stratification.py`

```python
@pytest.mark.parametrize("apache_range", [
    ("low", 0, 15),
    ("medium", 15, 25),
    ("high", 25, 50)
])
def test_performance_by_apache_severity(apache_range):
    """Target: AUC ≥0.70 for each stratum"""
    # Validate: calibration maintained across strata
```

---

## Synthetic Data Generators

### VA-ECMO Generator

```python
def generate_synthetic_va_data(
    n: int = 200,
    mortality_rate: float = 0.5,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Realistic distributions:
    - Age: Gamma(5, 10) + 30, clipped [18, 90]
    - Cardiac arrest: 40% prevalence
    - NIRS baseline: Normal(70, 10), clipped [40, 90]
    - Outcome model: Logistic with age, BMI, CA, CPR, NIRS effects
    """
```

**Features**:
- Demographics (age, weight, BMI)
- Cardiac (arrest, CPR duration, inotrope score, LVEF)
- NIRS (cerebral, renal, somatic baseline + min_24h)
- Labs (lactate, creatinine, platelets)
- Echo (mitral/aortic regurgitation)

### VV-ECMO Generator

```python
def generate_synthetic_vv_data(
    n: int = 200,
    mortality_rate: float = 0.5,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    VV-specific features:
    - Murray score, PEEP, plateau pressure
    - Prone positioning (60% prevalence)
    - Immunocompromised (30% prevalence)
    - Respiratory mechanics (compliance, driving pressure)
    """
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1) ⏱️ 5 days

**Tasks**:
1. Set up `pytest` infrastructure (`pytest.ini`, `conftest.py`)
2. Create test directory structure (`tests/{unit,integration,edge_cases,benchmarks}`)
3. Implement synthetic data generators (`generate_synthetic_va_data`, `generate_synthetic_vv_data`)
4. Create fixtures (`tests/fixtures/data_generators.py`, `benchmarks.yaml`)

**Deliverables**:
- Test infrastructure ready
- Data generators validated
- Fixtures available

### Phase 2: Core Testing (Week 2) ⏱️ 7 days

**Tasks**:
5. Unit tests for feature engineering (12 tests)
6. Unit tests for risk scores (8 tests)
7. Model training tests (15 tests, including class imbalance)
8. Calibration tests (10 tests: Brier, ECE, curve)
9. SHAP explainability tests (10 tests)

**Deliverables**:
- 55 unit tests passing
- Coverage ≥85% on core functions

### Phase 3: Robustness (Week 3) ⏱️ 7 days

**Tasks**:
10. VA vs VV separation tests (6 tests)
11. End-to-end pipeline tests (6 tests)
12. Class imbalance handling tests (6 tests) - **requires SMOTE implementation**
13. Edge case tests (8 tests: missing data, outliers)
14. APACHE stratification tests (3 tests) - **requires APACHE score**

**Deliverables**:
- 29 integration/edge case tests passing
- Robustness validated
- Implementation gaps addressed

### Phase 4: Validation & Deployment (Week 4) ⏱️ 7 days

**Tasks**:
15. Performance regression tests (3 tests)
16. Speed benchmarks (3 tests: inference, SHAP, batch)
17. Real-world validation data preparation
18. External validation on Taiwan ECMO registry
19. CI/CD integration (GitHub Actions workflow)
20. Documentation and reporting

**Deliverables**:
- 90+ tests passing
- Coverage ≥90%
- CI/CD pipeline operational
- Validation report complete

---

## Critical Dependencies

### Python Packages Required

```bash
pip install pytest>=7.0.0
pip install pytest-cov>=4.0.0
pip install pytest-benchmark>=4.0.0
pip install pytest-xdist>=3.0.0  # Parallel testing
pip install hypothesis>=6.0.0     # Property-based testing
pip install imbalanced-learn>=0.10.0  # SMOTE
```

### Test Data Requirements

1. **Synthetic Data**: Generated programmatically (no external dependency)
2. **Reference Benchmarks**: Establish baselines in first run, store in `tests/fixtures/benchmarks.yaml`
3. **Real-world Validation**: Taiwan ECMO registry data (PHI protected, not in repo)
4. **MIMIC-IV ECMO**: Public dataset for external validation

---

## Risk Mitigation

### High-Risk Areas

1. **Class Imbalance**
   - **Risk**: Model biased toward majority class
   - **Mitigation**: SMOTE + class_weight + stratified sampling
   - **Testing**: Parametrized tests across 10-90% mortality

2. **Missing NIRS Data**
   - **Risk**: Predictions fail or degrade without NIRS
   - **Mitigation**: Multiple imputation + default values + flag features
   - **Testing**: Edge case tests with zero NIRS features

3. **APACHE Stratification**
   - **Risk**: Model underperforms on sickest patients
   - **Mitigation**: Stratified validation + severity-specific thresholds
   - **Testing**: APACHE-stratified performance tests

4. **Calibration Quality**
   - **Risk**: Probabilities not well-calibrated (overconfident)
   - **Mitigation**: Isotonic calibration + Brier score monitoring
   - **Testing**: Calibration curve tests + ECE <0.10 threshold

---

## Success Metrics Dashboard

### Model Performance

| Model | AUC Target | Brier Target | Status |
|-------|------------|--------------|--------|
| VA-ECMO | ≥0.75 | <0.15 | ❓ Pending Validation |
| VV-ECMO | ≥0.75 | <0.15 | ❓ Pending Validation |

### Test Coverage

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| Overall | ≥90% | 0% | ❌ Not Started |
| Feature Eng | ≥95% | 0% | ❌ Not Started |
| Model Training | ≥90% | 0% | ❌ Not Started |
| Calibration | ≥90% | 0% | ❌ Not Started |

### Implementation Status

| Task | Priority | Status | ETA |
|------|----------|--------|-----|
| Test Infrastructure | HIGH | ❌ Not Started | Week 1 |
| Unit Tests | HIGH | ❌ Not Started | Week 2 |
| SMOTE Integration | HIGH | ❌ Not Implemented | Week 3 |
| APACHE Stratification | MEDIUM | ❌ Not Implemented | Week 3 |
| CI/CD Pipeline | MEDIUM | ❌ Not Started | Week 4 |
| Real-world Validation | HIGH | ❌ Not Started | Week 4 |

---

## Recommendations

### Immediate Actions (Week 1)

1. **Install Testing Dependencies**
   ```bash
   pip install pytest pytest-cov pytest-benchmark imbalanced-learn hypothesis
   ```

2. **Create Test Directory Structure**
   ```bash
   mkdir -p tests/{unit,integration,edge_cases,benchmarks,fixtures}
   ```

3. **Implement Data Generators**
   - Priority: `generate_synthetic_va_data()` and `generate_synthetic_vv_data()`
   - Validate against real data distributions

4. **Set Up CI/CD**
   - Create `.github/workflows/test_wp1.yml`
   - Configure coverage reporting (Codecov or similar)

### Short-term (Weeks 2-3)

5. **Address Class Imbalance**
   - Integrate SMOTE in `train_model()`
   - Add `class_weight` parameter support
   - Test across 10-90% mortality ranges

6. **Add APACHE Stratification**
   - Implement APACHE-II score calculation
   - Create stratified test datasets
   - Validate performance per stratum

7. **Improve Missing Data Handling**
   - Implement multiple imputation option
   - Add flags for missing NIRS sensors
   - Test with zero NIRS features

### Long-term (Week 4+)

8. **External Validation**
   - Taiwan ECMO registry validation
   - MIMIC-IV ECMO cohort validation
   - Temporal validation (train 2020-2022, test 2023+)

9. **Clinical Integration**
   - SHAP value clinical review by ECMO experts
   - Threshold optimization for clinical workflows
   - User acceptance testing

10. **Documentation**
    - API documentation (Sphinx)
    - Clinical interpretation guide
    - Deployment manual

---

## Contact & Resources

**Full Test Plan**: `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\docs\wp1_tdd_test_plan.md` (14,000+ words, 90+ test specifications)

**Memory Keys**:
- `wp1/tdd-plan`: Full test plan stored in swarm memory
- `wp1/analysis/architecture`: Architecture analysis
- `wp1/tdd-plan/metrics`: Test thresholds and targets

**Related Files**:
- Implementation: `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\nirs\risk_models.py`
- Features: `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\nirs\features.py`
- Prompt: `C:\Users\thc1006\Desktop\dev\TAIWAN-ECMO-CDSS-NEXT\prompts\WP1_nirs_model.md`

**Next Steps**: Proceed to Phase 1 implementation or request specific test file generation.

---

**Status**: Analysis Complete ✅
**Date**: 2025-09-30
**Analyzed By**: Claude Code Agent (ML Model Developer)