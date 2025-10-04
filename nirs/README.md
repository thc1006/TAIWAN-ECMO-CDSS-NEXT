# NIRS + EHR Risk Models for ECMO Outcomes (WP1)

Comprehensive machine learning pipeline for predicting ECMO outcomes using NIRS (Near-Infrared Spectroscopy) and EHR (Electronic Health Record) data.

## Overview

This module implements a complete end-to-end pipeline for ECMO risk prediction:

1. **Data Loading** - Load MIMIC-IV data from CSV or PostgreSQL
2. **Feature Engineering** - Advanced temporal, interaction, and domain features
3. **Model Training** - Hyperparameter tuning with cross-validation
4. **Model Validation** - Calibration, decision curves, and explainability
5. **Deployment** - Model persistence and prediction interfaces

## Module Structure

```
nirs/
├── data_loader.py          # MIMIC-IV data loading and preprocessing
├── features.py             # Advanced feature engineering
├── risk_models.py          # Core risk model implementation
├── train_models.py         # Training pipeline with hyperparameter tuning
├── model_validation.py     # Validation and explainability tools
├── demo.py                 # End-to-end demonstration with synthetic data
└── README.md              # This file
```

## Key Features

### Data Loading (`data_loader.py`)
- **Multiple data sources**: CSV files (including gzip) and PostgreSQL
- **Stratified splits**: Train/validation/test splits stratified by ECMO mode and outcome
- **Preprocessing pipeline**:
  - Missing value imputation (median, mean, or KNN)
  - Feature scaling (standard or robust)
  - Outlier handling (IQR or z-score)
  - Automatic feature selection
- **MIMIC-IV integration**: Direct support for extract_ecmo_features.sql output

### Feature Engineering (`features.py`)
- **NIRS features**:
  - Temporal statistics (mean, std, range, IQR, CV)
  - Trend analysis (slope, acceleration, direction changes)
  - Variability metrics (entropy, successive differences)
  - Peak/trough detection
- **Interaction features**:
  - NIRS × Hemodynamics (e.g., HbO₂/MAP ratio)
  - Oxygenation indices (P/F ratio, oxygen content)
  - ECMO parameters × BSA (flow index, RPM index)
  - Metabolic indicators (lactate-pH product)
- **Domain knowledge features**:
  - Estimated cardiac output
  - ECMO support adequacy
  - Shock indices (SI, MSI)
  - Differential hypoxia risk (VA-ECMO)
  - Ventilation ratio

### Model Training (`train_models.py`)
- **Multiple algorithms**:
  - Logistic Regression
  - Random Forest
  - Gradient Boosting (default)
  - AdaBoost
- **Hyperparameter tuning**:
  - Grid search or randomized search
  - Cross-validation with stratified folds
  - Multiple scoring metrics (AUROC, AUPRC, Brier)
- **Class imbalance handling**:
  - SMOTE oversampling
  - Class weights
  - Combined SMOTE-Tomek
- **Feature selection**:
  - SelectKBest (mutual information)
  - Recursive feature elimination (RFE)
  - Tree-based importance
- **Model persistence**: Save/load models with all artifacts

### Model Validation (`model_validation.py`)
- **Discrimination metrics**:
  - AUROC with confidence intervals
  - AUPRC (handles class imbalance better)
  - Brier score
- **Calibration**:
  - Calibration plots (reliability diagrams)
  - Expected Calibration Error (ECE)
- **Decision curve analysis**: Net benefit across risk thresholds
- **Bootstrap confidence intervals**: 95% CI for all metrics
- **SHAP explainability**: Feature importance and interaction plots
- **Subgroup analysis**: Performance by age, diagnosis, severity

### Risk Models (`risk_models.py`)
- **VA/VV separation**: Separate models for different ECMO modes
- **Calibration**: Isotonic or Platt scaling
- **APACHE stratification**: Performance metrics by severity
- **Explainability**: Feature importance and prediction explanations

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages:
# - pandas, numpy, scikit-learn, scipy
# - matplotlib, streamlit
# - imbalanced-learn (SMOTE)
# - shap (explainability)
# - psycopg2-binary (PostgreSQL support)
```

### 2. Run Demo

```bash
# Run end-to-end demo with synthetic data
cd nirs
python demo.py
```

This will:
- Generate synthetic ECMO data (VA and VV modes)
- Engineer features
- Train and validate models
- Generate plots and reports
- Save everything to `demo_output/`

### 3. Use with Real Data

```python
from data_loader import MIMICDataLoader, DataConfig
from train_models import train_va_vv_models, TrainingConfig

# Configure data loading
data_config = DataConfig(
    data_source='csv',
    features_csv='path/to/ecmo_features.csv',
    test_size=0.2,
    val_size=0.2,
    imputation_strategy='knn',
    scaling_method='robust'
)

# Configure training
training_config = TrainingConfig(
    model_type='gradient_boosting',
    tune_hyperparameters=True,
    use_smote=True,
    use_feature_selection=True,
    output_dir='models/ecmo_risk'
)

# Load and prepare data
loader = MIMICDataLoader(data_config)
loader.load_and_prepare()

# Train models
models = train_va_vv_models(
    loader,
    training_config,
    output_dir='models/ecmo_risk'
)
```

### 4. Validate Models

```python
from model_validation import ModelValidator, ValidationConfig

# Configure validation
validation_config = ValidationConfig(
    n_calibration_bins=10,
    n_bootstrap=1000,
    use_shap=True,
    save_plots=True,
    plot_dir='validation_plots'
)

# Validate
validator = ModelValidator(validation_config)
results = validator.validate_model(
    y_true=y_test,
    y_pred_proba=y_pred_proba,
    X=X_test,
    model=trained_model,
    feature_names=feature_names,
    model_name='VA-ECMO Risk Model'
)
```

### 5. Make Predictions

```python
from train_models import load_model

# Load trained model
model = load_model('models/ecmo_risk/va_risk_model.pkl')

# Prepare new patient data (same features as training)
X_new = prepare_patient_features(patient_data)

# Get predictions
survival_prob = model.predict_proba(X_new, calibrated=True)[:, 1]

# Interpret
if survival_prob >= 0.7:
    risk_category = "Low risk"
elif survival_prob >= 0.4:
    risk_category = "Moderate risk"
else:
    risk_category = "High risk"
```

## Data Requirements

### Input Data Format

The pipeline expects data matching the output of `sql/extract_ecmo_features.sql`:

**Required columns**:
- `subject_id`, `hadm_id`, `stay_id`, `episode_num` (identifiers)
- `ecmo_mode` ('VA' or 'VV')
- `survival_to_discharge` (target variable, 0/1)

**Feature categories** (80+ features):
- Patient demographics (age, sex, weight, height, BMI, BSA)
- Pre-ECMO severity (APACHE-II, SOFA)
- Pre-ECMO labs (ABG, chemistry, hematology, coagulation)
- Pre-ECMO vitals (HR, BP, SpO₂, temperature)
- Pre-ECMO respiratory (P/F ratio, PEEP, mechanical ventilation)
- ECMO support parameters (flow, pump speed, sweep gas, FiO₂)
- Complications (hemorrhage, stroke, organ dysfunction)
- Interventions (transfusions, CRRT, procedures)
- Outcomes (survival, length of stay)

### Data Sources

1. **MIMIC-IV Database**: Use `sql/extract_ecmo_features.sql` to extract features
2. **Pre-extracted CSV**: Export from database or other EHR system
3. **Synthetic Data**: Use `demo.py` for testing and development

## Model Architecture

### Design Decisions

1. **Separate VA/VV models**: Different physiology requires different models
2. **Gradient Boosting**: Better calibration than Random Forest, interpretable
3. **Isotonic calibration**: More flexible than Platt scaling, better for small datasets
4. **SMOTE**: Handles class imbalance without losing minority class samples
5. **Feature selection**: Reduces overfitting, improves generalization

### Expected Performance

On MIMIC-IV data (typical ranges):

**VA-ECMO**:
- AUROC: 0.75-0.85
- AUPRC: 0.70-0.80
- Brier score: 0.15-0.20
- ECE: <0.05

**VV-ECMO**:
- AUROC: 0.70-0.80
- AUPRC: 0.65-0.75
- Brier score: 0.18-0.23
- ECE: <0.05

Performance varies by:
- Sample size
- Feature completeness
- Outcome prevalence
- Population characteristics

## Output Artifacts

### Training Outputs

For each ECMO mode, saves:
- `{mode}_risk_model.pkl` - Trained model with calibration
- `{mode}_feature_names.json` - List of selected features
- `{mode}_feature_importance.csv` - Feature importance scores
- `{mode}_best_params.json` - Best hyperparameters
- `{mode}_training_history.json` - Training metrics and metadata
- `{mode}_cv_results.csv` - Cross-validation results
- `{mode}_training_report.txt` - Comprehensive training report

### Validation Outputs

For each model, generates:
- `roc_curve.png` - ROC curve with AUROC
- `precision_recall.png` - PR curve with AUPRC
- `calibration.png` - Calibration plot with ECE
- `decision_curve.png` - Decision curve analysis
- `shap/` - SHAP summary and importance plots

## Advanced Usage

### Custom Feature Engineering

```python
from features import engineer_all_features, NIRSFeatureExtractor

# Add custom features before training
df_engineered = engineer_all_features(
    df,
    include_temporal=True,
    include_interactions=True,
    include_domain=True
)

# Extract NIRS features from time series
extractor = NIRSFeatureExtractor(window_hours=6.0)
nirs_features = extractor.extract_all_features(
    df_timeseries,
    value_col='hbo',
    prefix='hbo'
)
```

### Subgroup Analysis

```python
# Analyze performance by subgroups
subgroups = {
    'Age': age_groups,
    'Diagnosis': diagnosis_categories,
    'APACHE-II': apache_strata
}

results = validator.validate_model(
    y_true=y_test,
    y_pred_proba=y_pred,
    subgroups=subgroups,
    model_name='VA-ECMO Model'
)

# Results contain stratified metrics
for subgroup_name, subgroup_results in results['subgroups'].items():
    print(subgroup_results)
```

### Model Comparison

```python
from model_validation import compare_models

# Compare multiple models
models_dict = {
    'Gradient Boosting': (y_true, y_pred_gb),
    'Random Forest': (y_true, y_pred_rf),
    'Logistic Regression': (y_true, y_pred_lr)
}

compare_models(models_dict, save_path='model_comparison.png')
```

## Troubleshooting

### Common Issues

1. **Insufficient data**:
   - Minimum 50 samples per ECMO mode
   - Ideally 200+ for reliable training
   - Use SMOTE if <30% outcome prevalence

2. **Missing features**:
   - Automatic handling via imputation
   - High missingness (>50%) features dropped
   - Configure threshold in DataConfig

3. **Poor calibration**:
   - Try different calibration_method ('sigmoid' vs 'isotonic')
   - Increase validation set size
   - Check for data leakage

4. **Long training time**:
   - Reduce n_iter_random for RandomizedSearchCV
   - Disable hyperparameter tuning for quick tests
   - Use smaller sample_size for SHAP

5. **SHAP errors**:
   - Only works with tree-based models
   - Reduce shap_sample_size if out of memory
   - Set use_shap=False to disable

## References

### Clinical Guidelines
- ELSO Guidelines for Adult Respiratory Failure (2021)
- ELSO Guidelines for Adult Cardiac Failure (2021)

### Machine Learning
- Chen & Guestrin (2016) - XGBoost
- Chawla et al. (2002) - SMOTE
- Lundberg & Lee (2017) - SHAP

### Calibration
- Platt (1999) - Platt scaling
- Zadrozny & Elkan (2002) - Isotonic regression

### MIMIC-IV
- Johnson et al. (2023) - MIMIC-IV v2.2
- Goldberger et al. (2000) - PhysioNet

## Contributing

Enhancements welcome:
1. Additional feature engineering methods
2. New model architectures (neural networks, ensembles)
3. External validation on other datasets
4. Clinical decision support interfaces

## License

See main project LICENSE file.

## Contact

For questions about this module, see main project documentation.
