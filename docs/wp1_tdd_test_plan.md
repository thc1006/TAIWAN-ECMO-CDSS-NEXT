# WP1: NIRS+EHR Risk Models - Comprehensive TDD Test Plan

## Executive Summary

**Project**: Taiwan ECMO CDSS - NIRS-Enhanced Risk Prediction Models
**Target**: AUC ≥0.75, Brier Score <0.15, Test Coverage ≥90%
**Models**: Separate VA-ECMO (24 features) and VV-ECMO (25 features)
**Current Status**: Implementation complete, validation data pending
**Risk**: Class imbalance (mortality 40-60%), missing NIRS data edge cases

---

## 1. Architecture Analysis

### 1.1 Model Pipeline Components

```
Data Input → Feature Engineering → Model Training → Calibration → SHAP Explainability → Prediction
     ↓              ↓                    ↓              ↓                ↓                 ↓
  Raw EHR      NIRS Features      3 Algorithms    Isotonic CV=3    TreeExplainer      Risk Score
  + NIRS       Risk Scores        (LR/RF/GBM)     CalibratedCV     LinearExplainer    + Confidence
```

### 1.2 Feature Engineering Functions

**NIRS-Derived Features** (`prepare_nirs_features`):
- Trend calculations: `nirs_trend_{cerebral,renal,somatic}` (slope over 24h)
- Variability: `nirs_variability` (coefficient of variation)
- Adequacy score: Weighted composite (cerebral 50%, renal 30%, somatic 20%)

**Risk Score Calculations** (`calculate_risk_scores`):
- VA-ECMO: SAVE-II Score (age, weight, cardiac arrest, bicarbonate)
- VV-ECMO: RESP Score (age, immunocompromised, ventilation duration)

### 1.3 Model Training Workflow

1. Feature preparation (NIRS + risk scores)
2. Missing value imputation (median)
3. Train/validation split (80/20, stratified)
4. Feature scaling (StandardScaler for LogisticRegression)
5. Ensemble training (LR, RF, GBM)
6. Best model selection (highest validation AUC)
7. Isotonic calibration (CV=3)
8. SHAP explainer initialization

### 1.4 Critical Issues Identified

- **Class Imbalance**: No SMOTE or class weighting implemented
- **Missing Data**: Only median imputation, no handling for completely missing NIRS
- **Validation**: No stratification by APACHE severity
- **Edge Cases**: No tests for all-zero features or outliers
- **Performance**: No regression testing for model updates

---

## 2. TDD Test Strategy

### 2.1 Test Pyramid

```
                    /\
                   /  \
                  / E2E\        Integration (10%)
                 /------\
                /        \
               / Integra \     Component (20%)
              /------------\
             /              \
            /   Unit Tests   \  Unit (70%)
           /------------------\
```

### 2.2 Test Categories

| Category | Purpose | Coverage Target | Automation |
|----------|---------|----------------|------------|
| Unit Tests | Individual functions | 90% | pytest |
| Component Tests | Model pipelines | 85% | pytest + fixtures |
| Integration Tests | End-to-end workflows | 75% | pytest + mock data |
| Performance Tests | Benchmarking | N/A | pytest-benchmark |
| Edge Case Tests | Robustness | 100% scenarios | pytest + hypothesis |

---

## 3. Unit Test Specifications

### 3.1 Feature Engineering Tests

**File**: `tests/unit/test_feature_engineering.py`

#### Test: `test_prepare_nirs_features_basic`
```python
def test_prepare_nirs_features_basic():
    """Test NIRS feature calculation with valid data"""
    # Arrange
    model = NIRSECMORiskModel('VA')
    data = pd.DataFrame({
        'cerebral_so2_baseline': [70.0, 65.0, 75.0],
        'cerebral_so2_min_24h': [60.0, 55.0, 70.0],
        'renal_so2_baseline': [75.0, 70.0, 80.0],
        'renal_so2_min_24h': [70.0, 65.0, 75.0],
        'somatic_so2_baseline': [70.0, 68.0, 72.0],
        'somatic_so2_min_24h': [65.0, 60.0, 68.0]
    })

    # Act
    result = model.prepare_nirs_features(data)

    # Assert
    assert 'nirs_trend_cerebral' in result.columns
    assert 'nirs_trend_renal' in result.columns
    assert 'nirs_variability' in result.columns
    assert 'nirs_adequacy_score' in result.columns

    # Trend should be negative (min < baseline)
    assert (result['nirs_trend_cerebral'] < 0).all()

    # Variability should be 0-1 range
    assert (result['nirs_variability'] >= 0).all()
    assert (result['nirs_variability'] <= 1).all()

    # Adequacy score should be 0-1 range
    assert (result['nirs_adequacy_score'] >= 0).all()
    assert (result['nirs_adequacy_score'] <= 1).all()
```

**Acceptance Criteria**:
- ✓ Trends calculated correctly (baseline - min_24h)
- ✓ Variability in valid range [0, 1]
- ✓ Adequacy score weighted correctly (0.5/0.3/0.2)

#### Test: `test_prepare_nirs_features_missing_data`
```python
def test_prepare_nirs_features_missing_data():
    """Test NIRS features with missing values"""
    model = NIRSECMORiskModel('VA')
    data = pd.DataFrame({
        'cerebral_so2_baseline': [70.0, np.nan, 75.0],
        'cerebral_so2_min_24h': [60.0, 55.0, np.nan],
        'renal_so2_baseline': [np.nan, 70.0, 80.0]
    })

    result = model.prepare_nirs_features(data)

    # Should use default values (70, 75, 70)
    assert not result['nirs_adequacy_score'].isna().any()
    assert (result['nirs_adequacy_score'] > 0).all()
```

**Acceptance Criteria**:
- ✓ Missing values filled with clinical defaults
- ✓ No NaN in derived features
- ✓ Default values: cerebral=70, renal=75, somatic=70

#### Test: `test_prepare_nirs_features_edge_cases`
```python
@pytest.mark.parametrize("edge_case,expected", [
    ("all_zero", 0.0),
    ("all_max", 0.9),
    ("extreme_variability", 1.0),
    ("negative_values", ValueError)
])
def test_prepare_nirs_features_edge_cases(edge_case, expected):
    """Test edge cases for NIRS features"""
    # Test all-zero, max values, extreme variability, negatives
    pass
```

---

### 3.2 Risk Score Tests

**File**: `tests/unit/test_risk_scores.py`

#### Test: `test_save_ii_score_calculation_va`
```python
def test_save_ii_score_calculation_va():
    """Test SAVE-II score for VA-ECMO"""
    model = NIRSECMORiskModel('VA')
    data = pd.DataFrame({
        'age_years': [40, 55, 70],  # 0, -2, -4 points
        'weight_kg': [60, 75, 80],  # -3, 0, 0 points
        'cardiac_arrest': [True, False, True],  # -2, 0, -2 points
        'bicarbonate_pre': [12, 18, 20]  # -3, 0, 0 points
    })

    result = model.calculate_risk_scores(data)

    assert 'save_ii_score' in result.columns
    assert result['save_ii_score'].iloc[0] == -8  # Age 40, weight<65, CA, HCO3<15
    assert result['save_ii_score'].iloc[1] == -2  # Age 55 only
    assert result['save_ii_score'].iloc[2] == -6  # Age 70, CA
```

**Acceptance Criteria**:
- ✓ Age thresholds correct (38, 53)
- ✓ Weight threshold <65kg
- ✓ Cardiac arrest penalty -2
- ✓ Bicarbonate <15 penalty -3

#### Test: `test_resp_score_calculation_vv`
```python
def test_resp_score_calculation_vv():
    """Test RESP score for VV-ECMO"""
    model = NIRSECMORiskModel('VV')
    data = pd.DataFrame({
        'age_years': [25, 50, 65],  # 0, -2, -5 points
        'immunocompromised': [False, True, False],  # 0, -2, 0 points
        'vent_duration_pre_ecmo': [3, 8, 10]  # 0, -1, -1 points
    })

    result = model.calculate_risk_scores(data)

    assert 'resp_score' in result.columns
    assert result['resp_score'].iloc[0] == 0  # Age 18-49, not IC, vent<7d
    assert result['resp_score'].iloc[1] == -5  # Age 50-59, IC, vent>7d
    assert result['resp_score'].iloc[2] == -6  # Age 60+, vent>7d
```

---

### 3.3 Model Training Tests

**File**: `tests/unit/test_model_training.py`

#### Test: `test_train_model_basic_va`
```python
def test_train_model_basic_va():
    """Test VA-ECMO model training with synthetic data"""
    # Arrange
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=200, mortality_rate=0.5)

    # Act
    metrics = model.train_model(X, y, validation_split=0.2)

    # Assert
    assert metrics['auc_score'] >= 0.70  # Minimum threshold
    assert metrics['brier_score'] <= 0.20  # Maximum threshold
    assert metrics['n_train'] == 160
    assert metrics['n_val'] == 40
    assert model.calibrated_model is not None
    assert model.feature_names is not None
    assert len(model.feature_names) > 0
```

**Acceptance Criteria**:
- ✓ AUC ≥0.70 (relaxed for synthetic data)
- ✓ Brier ≤0.20 (relaxed for synthetic data)
- ✓ Train/val split correct (80/20)
- ✓ Model and features stored

#### Test: `test_train_model_class_imbalance`
```python
@pytest.mark.parametrize("mortality_rate", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_train_model_class_imbalance(mortality_rate):
    """Test model performance across class imbalance scenarios"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=300, mortality_rate=mortality_rate)

    metrics = model.train_model(X, y)

    # Model should handle imbalance gracefully
    assert metrics['auc_score'] >= 0.65  # Lower bound for extreme imbalance

    # Check prediction distribution
    preds = model.predict_risk(X)
    assert preds.min() >= 0.0
    assert preds.max() <= 1.0
    assert 0.1 < preds.mean() < 0.9  # Not stuck at extremes
```

**Acceptance Criteria**:
- ✓ Handles 10-90% mortality rates
- ✓ AUC ≥0.65 for extreme imbalance
- ✓ Predictions not collapsed to 0 or 1

---

### 3.4 Calibration Tests

**File**: `tests/unit/test_calibration.py`

#### Test: `test_calibration_brier_score`
```python
def test_calibration_brier_score():
    """Test model calibration quality with Brier score"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=500, mortality_rate=0.5)

    model.train_model(X, y, validation_split=0.2)

    # Get validation data
    _, X_val, _, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # Calculate Brier score
    y_prob = model.predict_risk(X_val)
    brier = brier_score_loss(y_val, y_prob)

    # Target: Brier <0.15
    assert brier < 0.15, f"Brier score {brier:.3f} exceeds threshold 0.15"
```

**Acceptance Criteria**:
- ✓ Brier score <0.15 (calibration target)
- ✓ Calibration improves uncalibrated baseline by ≥10%

#### Test: `test_calibration_curve_reliability`
```python
def test_calibration_curve_reliability():
    """Test calibration curve stays close to diagonal"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=1000)
    model.train_model(X, y)

    X_test, y_test = generate_synthetic_va_data(n=200)
    y_prob = model.predict_risk(X_test)

    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_test, y_prob, n_bins=10, normalize=False
    )

    # Calculate Expected Calibration Error (ECE)
    ece = np.mean(np.abs(fraction_of_positives - mean_predicted_value))

    assert ece < 0.10, f"ECE {ece:.3f} exceeds 0.10 threshold"
```

**Acceptance Criteria**:
- ✓ Expected Calibration Error (ECE) <0.10
- ✓ All bins within ±15% of perfect calibration

---

### 3.5 SHAP Explainability Tests

**File**: `tests/unit/test_shap_explainability.py`

#### Test: `test_shap_values_consistency`
```python
def test_shap_values_consistency():
    """Test SHAP values sum to prediction difference"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=200)
    model.train_model(X, y)

    X_test = X.sample(10, random_state=42)

    for idx in range(len(X_test)):
        explanation = model.explain_prediction(X_test, patient_idx=idx)

        if explanation:  # SHAP available
            shap_sum = explanation['shap_values'].sum() + explanation['base_value']
            predicted = explanation['predicted_risk']

            # SHAP values should approximately sum to prediction
            # Allow small numerical differences
            assert np.isclose(shap_sum, predicted, atol=0.05), \
                f"SHAP sum {shap_sum:.3f} != prediction {predicted:.3f}"
```

**Acceptance Criteria**:
- ✓ SHAP values sum to (prediction - base_value) within 5%
- ✓ All feature attributions present
- ✓ No NaN or infinite values

#### Test: `test_shap_feature_importance_ranking`
```python
def test_shap_feature_importance_ranking():
    """Test SHAP feature importance is clinically sensible"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=500, mortality_rate=0.5)
    model.train_model(X, y)

    X_test = X.sample(50)

    # Collect SHAP values
    all_shap_values = []
    for idx in range(len(X_test)):
        exp = model.explain_prediction(X_test, patient_idx=idx)
        if exp:
            all_shap_values.append(np.abs(exp['shap_values']))

    if len(all_shap_values) > 0:
        # Average absolute SHAP values
        mean_shap = np.mean(all_shap_values, axis=0)
        feature_importance = dict(zip(model.feature_names, mean_shap))

        # Clinical expectation: age, lactate, NIRS should be top features
        top_5 = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        top_features = [f[0] for f in top_5]

        clinical_features = ['age_years', 'pre_ecmo_lactate', 'cerebral_so2_baseline']
        overlap = len(set(top_features) & set(clinical_features))

        # At least 2 of 3 clinical features in top 5
        assert overlap >= 2, f"Top features {top_features} missing clinical features"
```

**Acceptance Criteria**:
- ✓ Age, lactate, cerebral NIRS in top 5 features
- ✓ SHAP values stable across bootstrap samples
- ✓ Positive/negative attribution direction clinically correct

---

## 4. Component Test Specifications

### 4.1 VA vs VV Separation Tests

**File**: `tests/integration/test_va_vv_separation.py`

#### Test: `test_va_vv_different_features`
```python
def test_va_vv_different_features():
    """Test VA and VV models use appropriate features"""
    va_model = NIRSECMORiskModel('VA')
    vv_model = NIRSECMORiskModel('VV')

    # VA-specific features
    assert 'cardiac_arrest' in va_model.features
    assert 'lvef_pre_ecmo' in va_model.features
    assert 'save_ii_score' in va_model.calculate_risk_scores(pd.DataFrame()).columns

    # VV-specific features
    assert 'murray_score' in vv_model.features
    assert 'prone_positioning' in vv_model.features
    assert 'resp_score' in vv_model.calculate_risk_scores(pd.DataFrame()).columns

    # Features should not overlap inappropriately
    assert 'murray_score' not in va_model.features
    assert 'cardiac_arrest' not in vv_model.features
```

#### Test: `test_va_vv_performance_parity`
```python
def test_va_vv_performance_parity():
    """Test both models achieve similar performance on their domains"""
    # Train VA model
    va_model = NIRSECMORiskModel('VA')
    X_va, y_va = generate_synthetic_va_data(n=500)
    va_metrics = va_model.train_model(X_va, y_va)

    # Train VV model
    vv_model = NIRSECMORiskModel('VV')
    X_vv, y_vv = generate_synthetic_vv_data(n=500)
    vv_metrics = vv_model.train_model(X_vv, y_vv)

    # Both should exceed performance thresholds
    assert va_metrics['auc_score'] >= 0.75
    assert vv_metrics['auc_score'] >= 0.75

    # Performance should be within 10% of each other
    auc_diff = abs(va_metrics['auc_score'] - vv_metrics['auc_score'])
    assert auc_diff < 0.10, f"AUC difference {auc_diff:.3f} too large"
```

**Acceptance Criteria**:
- ✓ Both models achieve AUC ≥0.75
- ✓ VA includes cardiac-specific features
- ✓ VV includes respiratory-specific features
- ✓ Performance difference <10%

---

### 4.2 End-to-End Pipeline Tests

**File**: `tests/integration/test_e2e_pipeline.py`

#### Test: `test_full_pipeline_va`
```python
def test_full_pipeline_va():
    """Test complete VA-ECMO prediction pipeline"""
    # Generate training data
    train_data = generate_demo_data(n_patients=400, ecmo_type='VA')
    X_train = train_data.drop(['patient_id', 'survived_to_discharge'], axis=1)
    y_train = train_data['survived_to_discharge']

    # Initialize and train model
    model = NIRSECMORiskModel('VA')
    metrics = model.train_model(X_train, y_train)

    # Generate new patient
    new_patient = generate_demo_data(n_patients=1, ecmo_type='VA')
    X_new = new_patient.drop(['patient_id', 'survived_to_discharge'], axis=1)

    # Predict risk
    risk_score = model.predict_risk(X_new)

    # Explain prediction
    explanation = model.explain_prediction(X_new, patient_idx=0)

    # Save and load model
    model.save_model('tests/fixtures/test_va_model.pkl')
    loaded_model = NIRSECMORiskModel('VA')
    loaded_model.load_model('tests/fixtures/test_va_model.pkl')
    loaded_risk = loaded_model.predict_risk(X_new)

    # Assertions
    assert 0.0 <= risk_score[0] <= 1.0
    assert len(explanation) > 0
    assert np.isclose(risk_score[0], loaded_risk[0], atol=1e-6)
```

**Acceptance Criteria**:
- ✓ Complete workflow executes without errors
- ✓ Risk score in [0, 1] range
- ✓ SHAP explanation generated
- ✓ Model save/load preserves predictions

---

## 5. Edge Case & Robustness Tests

### 5.1 Missing Data Scenarios

**File**: `tests/edge_cases/test_missing_data.py`

#### Test: `test_all_nirs_missing`
```python
def test_all_nirs_missing():
    """Test model with completely missing NIRS data"""
    model = NIRSECMORiskModel('VA')

    # Create data with only non-NIRS features
    data = pd.DataFrame({
        'age_years': [55, 60, 45],
        'weight_kg': [75, 80, 70],
        'bmi': [25, 28, 24],
        'pre_ecmo_lactate': [3.0, 5.0, 2.0],
        'cardiac_arrest': [True, False, True]
    })

    # Should use default NIRS values
    result = model.prepare_nirs_features(data)

    assert 'nirs_adequacy_score' in result.columns
    assert not result['nirs_adequacy_score'].isna().any()

    # Train with missing NIRS
    X, y = generate_synthetic_va_data(n=200)
    X_no_nirs = X.drop([c for c in X.columns if 'so2' in c or 'nirs' in c], axis=1)

    metrics = model.train_model(X_no_nirs, y)

    # Should still train but with warning
    assert metrics['auc_score'] >= 0.60  # Lower threshold without NIRS
```

**Acceptance Criteria**:
- ✓ Model trains with zero NIRS features
- ✓ Uses clinical defaults for missing NIRS
- ✓ AUC ≥0.60 without NIRS data
- ✓ Logs warning about missing critical features

---

### 5.2 Outlier Handling

**File**: `tests/edge_cases/test_outliers.py`

#### Test: `test_extreme_values`
```python
@pytest.mark.parametrize("outlier_type", [
    "extreme_age",
    "extreme_lactate",
    "zero_nirs",
    "negative_values"
])
def test_extreme_values(outlier_type):
    """Test model robustness to outliers"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=200)
    model.train_model(X, y)

    # Create outlier data
    X_outlier = X.sample(1).copy()

    if outlier_type == "extreme_age":
        X_outlier['age_years'] = 120  # Unrealistic age
    elif outlier_type == "extreme_lactate":
        X_outlier['pre_ecmo_lactate'] = 50  # Extreme lactate
    elif outlier_type == "zero_nirs":
        X_outlier['cerebral_so2_baseline'] = 0  # Zero NIRS
    elif outlier_type == "negative_values":
        X_outlier['weight_kg'] = -5  # Invalid negative

    # Should handle gracefully
    try:
        risk = model.predict_risk(X_outlier)
        assert 0.0 <= risk[0] <= 1.0
    except Exception as e:
        pytest.fail(f"Model failed on {outlier_type}: {e}")
```

**Acceptance Criteria**:
- ✓ No crashes on extreme values
- ✓ Predictions remain in [0, 1]
- ✓ Logs warnings for suspicious values

---

## 6. Performance Regression Tests

### 6.1 Model Performance Benchmarks

**File**: `tests/benchmarks/test_performance_regression.py`

#### Test: `test_auc_regression`
```python
def test_auc_regression():
    """Test model AUC doesn't regress on reference dataset"""
    # Load reference dataset and model
    reference_auc = load_reference_benchmark('va_ecmo_auc')

    # Train current model
    model = NIRSECMORiskModel('VA')
    X, y = load_reference_data('va_ecmo')
    metrics = model.train_model(X, y)

    # AUC should not decrease by >5%
    auc_change = metrics['auc_score'] - reference_auc
    assert auc_change >= -0.05, \
        f"AUC regressed from {reference_auc:.3f} to {metrics['auc_score']:.3f}"
```

#### Test: `test_inference_speed`
```python
def test_inference_speed(benchmark):
    """Test prediction speed meets requirements"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=200)
    model.train_model(X, y)

    X_test = X.sample(100)

    # Benchmark prediction time
    result = benchmark(model.predict_risk, X_test)

    # Should predict 100 patients in <1 second
    assert benchmark.stats['mean'] < 0.01  # 10ms per patient
```

**Acceptance Criteria**:
- ✓ AUC regression <5% from baseline
- ✓ Inference <10ms per patient
- ✓ SHAP explanation <100ms per patient

---

## 7. Class Imbalance Handling Tests

### 7.1 SMOTE Implementation Tests

**File**: `tests/integration/test_class_imbalance.py`

#### Test: `test_smote_integration`
```python
def test_smote_integration():
    """Test SMOTE for minority class oversampling"""
    from imblearn.over_sampling import SMOTE

    model = NIRSECMORiskModel('VA')

    # Create imbalanced data (20% mortality)
    X, y = generate_synthetic_va_data(n=500, mortality_rate=0.2)

    # Apply SMOTE before training
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_enhanced = model.prepare_nirs_features(X)
    X_model = X_enhanced[model.features].fillna(X_enhanced.median())

    X_resampled, y_resampled = smote.fit_resample(X_model, y)

    # Check balance improved
    assert 0.4 <= y_resampled.mean() <= 0.6

    # Train with resampled data
    # Note: This requires modifying train_model() to accept pre-resampled data
    # For now, test SMOTE pipeline separately
```

#### Test: `test_class_weight_balancing`
```python
def test_class_weight_balancing():
    """Test class_weight parameter for imbalanced data"""
    model = NIRSECMORiskModel('VA')
    X, y = generate_synthetic_va_data(n=500, mortality_rate=0.2)

    # Train with class weights
    # Note: Requires modification to train_model() to support class_weight
    # This test documents the requirement

    # Expected: class_weight='balanced' for LogisticRegression
    # class_weight param for RandomForest
    pass
```

**Acceptance Criteria**:
- ✓ SMOTE increases minority class to 40-60% balance
- ✓ Class weights implemented for all model types
- ✓ Performance on minority class improves ≥10%

---

## 8. APACHE-Stratified Performance Tests

### 8.1 Severity Stratification

**File**: `tests/integration/test_apache_stratification.py`

#### Test: `test_performance_by_apache_severity`
```python
@pytest.mark.parametrize("apache_range", [
    ("low", 0, 15),
    ("medium", 15, 25),
    ("high", 25, 50)
])
def test_performance_by_apache_severity(apache_range):
    """Test model performance across APACHE severity strata"""
    severity_name, apache_min, apache_max = apache_range

    model = NIRSECMORiskModel('VA')

    # Generate data with APACHE scores
    X, y = generate_synthetic_va_data_with_apache(n=300)

    # Stratify by APACHE
    mask = (X['apache_ii_score'] >= apache_min) & (X['apache_ii_score'] < apache_max)
    X_strata = X[mask]
    y_strata = y[mask]

    if len(X_strata) > 50:  # Minimum sample size
        model.train_model(X_strata, y_strata)

        # Test on same stratum
        X_test, y_test = generate_synthetic_va_data_with_apache(n=100)
        X_test_strata = X_test[
            (X_test['apache_ii_score'] >= apache_min) &
            (X_test['apache_ii_score'] < apache_max)
        ]
        y_test_strata = y_test.loc[X_test_strata.index]

        y_prob = model.predict_risk(X_test_strata)
        auc = roc_auc_score(y_test_strata, y_prob)

        # Target: AUC ≥0.70 for each severity stratum
        assert auc >= 0.70, f"AUC {auc:.3f} below threshold for {severity_name} severity"
```

**Acceptance Criteria**:
- ✓ AUC ≥0.70 for low severity (APACHE 0-15)
- ✓ AUC ≥0.70 for medium severity (APACHE 15-25)
- ✓ AUC ≥0.70 for high severity (APACHE 25-50)
- ✓ Calibration maintained across strata

---

## 9. Test Fixtures and Mock Data

### 9.1 Synthetic Data Generators

**File**: `tests/fixtures/data_generators.py`

```python
def generate_synthetic_va_data(
    n: int = 200,
    mortality_rate: float = 0.5,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate synthetic VA-ECMO data with realistic distributions

    Args:
        n: Number of patients
        mortality_rate: Target mortality rate (0.0-1.0)
        seed: Random seed for reproducibility

    Returns:
        (X, y): Feature DataFrame and outcome Series
    """
    np.random.seed(seed)

    # Demographics
    age = np.random.gamma(shape=5, scale=10, size=n) + 30
    age = np.clip(age, 18, 90)

    weight = np.random.normal(75, 15, n)
    weight = np.clip(weight, 40, 150)

    bmi = weight / ((170 + np.random.normal(0, 10, n))/100)**2
    bmi = np.clip(bmi, 15, 45)

    # Cardiac features
    cardiac_arrest = np.random.binomial(1, 0.4, n)
    cpr_duration = np.where(
        cardiac_arrest,
        np.random.exponential(25, n),
        0
    )
    cpr_duration = np.clip(cpr_duration, 0, 120)

    # NIRS features (correlated with outcome)
    cerebral_baseline = np.random.normal(70, 10, n)
    cerebral_baseline = np.clip(cerebral_baseline, 40, 90)

    # Lower NIRS for sicker patients
    cerebral_min = cerebral_baseline - np.random.exponential(8, n)
    cerebral_min = np.clip(cerebral_min, 30, 85)

    # Generate outcome based on risk factors
    logit = (
        -2.0 +  # Baseline
        0.03 * (age - 55) +  # Age effect
        0.02 * (bmi - 25) +  # BMI effect
        0.8 * cardiac_arrest +  # Cardiac arrest
        0.02 * cpr_duration +  # CPR duration
        -0.05 * cerebral_baseline +  # NIRS effect
        np.random.normal(0, 0.5, n)  # Random noise
    )

    # Adjust for target mortality rate
    prob = 1 / (1 + np.exp(-logit))
    prob = prob * (mortality_rate / prob.mean())  # Scale to target
    prob = np.clip(prob, 0.01, 0.99)

    outcome = np.random.binomial(1, 1 - prob, n)  # Survival (1) vs death (0)

    # Assemble DataFrame
    X = pd.DataFrame({
        'age_years': age,
        'weight_kg': weight,
        'bmi': bmi,
        'cardiac_arrest': cardiac_arrest.astype(bool),
        'cpr_duration_min': cpr_duration,
        'cerebral_so2_baseline': cerebral_baseline,
        'cerebral_so2_min_24h': cerebral_min,
        'renal_so2_baseline': np.random.normal(75, 8, n).clip(50, 90),
        'renal_so2_min_24h': np.random.normal(70, 10, n).clip(40, 85),
        'somatic_so2_baseline': np.random.normal(70, 8, n).clip(45, 85),
        'somatic_so2_min_24h': np.random.normal(65, 10, n).clip(35, 80),
        'pre_ecmo_lactate': np.random.exponential(3, n).clip(0.5, 20),
        'pre_ecmo_ph': np.random.normal(7.25, 0.15, n).clip(6.8, 7.6),
        'pre_ecmo_pco2': np.random.normal(50, 15, n).clip(20, 100),
        'pre_ecmo_po2': np.random.normal(80, 25, n).clip(30, 150),
        'creatinine_pre': np.random.exponential(1.5, n).clip(0.5, 8),
        'platelet_count_pre': np.random.normal(200, 80, n).clip(20, 500),
        'lvef_pre_ecmo': np.random.normal(30, 15, n).clip(10, 60),
        'inotrope_score': np.random.poisson(15, n).clip(0, 100),
        'mitral_regurg_severity': np.random.choice([0, 1, 2, 3, 4], n, p=[0.4, 0.3, 0.2, 0.08, 0.02]),
        'aortic_regurg_severity': np.random.choice([0, 1, 2, 3, 4], n, p=[0.5, 0.3, 0.15, 0.04, 0.01]),
        'bilirubin_pre': np.random.exponential(1.0, n).clip(0.2, 15)
    })

    y = pd.Series(outcome, name='survived_to_discharge')

    return X, y


def generate_synthetic_vv_data(
    n: int = 200,
    mortality_rate: float = 0.5,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic VV-ECMO data with realistic distributions"""
    np.random.seed(seed)

    # Similar structure for VV-specific features
    # Murray score, PEEP, prone positioning, etc.
    pass  # Implementation similar to VA
```

### 9.2 Reference Benchmark Data

**File**: `tests/fixtures/benchmarks.yaml`

```yaml
va_ecmo_auc: 0.78
vv_ecmo_auc: 0.76
va_ecmo_brier: 0.14
vv_ecmo_brier: 0.15
inference_time_ms: 8.5
shap_time_ms: 85.0
```

---

## 10. Test Execution Plan

### 10.1 Test Commands

```bash
# Run all tests
pytest tests/ -v --cov=nirs --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/edge_cases/ -v
pytest tests/benchmarks/ -v --benchmark-only

# Run with coverage threshold
pytest tests/ --cov=nirs --cov-fail-under=90

# Run parallel (for speed)
pytest tests/ -n auto

# Run with markers
pytest tests/ -m "not slow"
```

### 10.2 CI/CD Integration

```yaml
# .github/workflows/test_wp1.yml
name: WP1 NIRS Model Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-benchmark

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=nirs

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Check coverage
        run: pytest tests/ --cov=nirs --cov-fail-under=90

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 11. Acceptance Criteria Summary

### 11.1 Performance Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| **AUC-ROC** | ≥0.75 | Clinical utility threshold |
| **Brier Score** | <0.15 | Calibration quality |
| **Sensitivity** | ≥0.80 | Detect high-risk patients |
| **Specificity** | ≥0.70 | Avoid unnecessary alarms |
| **Test Coverage** | ≥90% | Code quality assurance |
| **Inference Time** | <10ms | Real-time bedside use |

### 11.2 Robustness Requirements

- ✓ Handles 10-90% class imbalance (SMOTE/class_weight)
- ✓ Functions with zero NIRS features (≥0.60 AUC)
- ✓ Stable across APACHE severity strata
- ✓ No crashes on extreme values
- ✓ Predictions consistent after save/load
- ✓ SHAP values mathematically correct

### 11.3 Validation Requirements

- ✓ Separate VA and VV model validation
- ✓ Cross-validation (5-fold minimum)
- ✓ External validation on Taiwan ECMO registry data
- ✓ Temporal validation (train on 2020-2022, test on 2023+)
- ✓ Calibration plot + ECE for each model

---

## 12. Implementation Priority

### Phase 1: Foundation (Week 1)
1. Set up test infrastructure (`pytest`, fixtures)
2. Implement synthetic data generators
3. Create unit tests for feature engineering
4. Create unit tests for risk scores

### Phase 2: Core Testing (Week 2)
5. Model training tests (basic + class imbalance)
6. Calibration tests (Brier + ECE)
7. SHAP explainability tests
8. VA vs VV separation tests

### Phase 3: Robustness (Week 3)
9. Edge case tests (missing data, outliers)
10. APACHE-stratified performance tests
11. Performance regression tests
12. Integration tests (end-to-end pipeline)

### Phase 4: Validation (Week 4)
13. Real-world data validation
14. Clinical expert review
15. Documentation and reporting
16. CI/CD integration

---

## 13. Open Issues and Recommendations

### 13.1 Implementation Gaps

1. **Class Imbalance**: No SMOTE or class_weight in current implementation
   - **Recommendation**: Add `imbalanced-learn` dependency, integrate SMOTE in `train_model()`
   - **Priority**: HIGH

2. **APACHE Stratification**: No severity score in features
   - **Recommendation**: Add `apache_ii_score` calculation or require as input
   - **Priority**: MEDIUM

3. **Missing NIRS Handling**: Only uses default values
   - **Recommendation**: Implement multiple imputation or flagging mechanism
   - **Priority**: MEDIUM

4. **Model Selection**: Always picks single "best" model
   - **Recommendation**: Consider ensemble voting or stacking
   - **Priority**: LOW

### 13.2 Testing Infrastructure Needed

- [ ] `pytest` configuration file (`pytest.ini`)
- [ ] Test fixtures directory with sample data
- [ ] Mock MIMIC-IV ECMO data generator
- [ ] Benchmark reference data storage
- [ ] CI/CD workflow files
- [ ] Coverage reporting setup

### 13.3 Documentation Needs

- [ ] API documentation for model classes
- [ ] Clinical interpretation guide for SHAP values
- [ ] User guide for model deployment
- [ ] Validation report template
- [ ] Model card (Model Cards for Model Reporting)

---

## 14. Success Criteria

**WP1 considered COMPLETE when:**

1. ✅ All unit tests passing (≥90% coverage)
2. ✅ All integration tests passing
3. ✅ VA model achieves AUC ≥0.75, Brier <0.15 on validation data
4. ✅ VV model achieves AUC ≥0.75, Brier <0.15 on validation data
5. ✅ Both models stable across APACHE severity strata
6. ✅ SHAP explanations validated by clinical experts
7. ✅ Edge cases handled gracefully (no crashes)
8. ✅ CI/CD pipeline running on every commit
9. ✅ Documentation complete and approved
10. ✅ External validation on Taiwan ECMO registry data complete

---

## Appendix A: Test File Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── data_generators.py         # Synthetic data generation
│   ├── benchmarks.yaml            # Reference performance metrics
│   └── sample_data/               # Small real-world samples
├── unit/
│   ├── test_feature_engineering.py
│   ├── test_risk_scores.py
│   ├── test_model_training.py
│   ├── test_calibration.py
│   └── test_shap_explainability.py
├── integration/
│   ├── test_va_vv_separation.py
│   ├── test_e2e_pipeline.py
│   ├── test_class_imbalance.py
│   └── test_apache_stratification.py
├── edge_cases/
│   ├── test_missing_data.py
│   └── test_outliers.py
└── benchmarks/
    └── test_performance_regression.py
```

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Author**: Claude Code Agent (ML Model Developer)
**Status**: DRAFT - Awaiting Review