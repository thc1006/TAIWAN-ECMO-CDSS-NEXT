"""
ECMO Risk Model Demo
Demonstrates full pipeline using synthetic data: data loading → training → validation → prediction
"""

import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from data_loader import MIMICDataLoader, DataConfig
from train_models import ECMOModelTrainer, TrainingConfig
from risk_models import ModelConfig
from model_validation import ModelValidator, ValidationConfig, compare_models
from features import engineer_all_features


def generate_synthetic_ecmo_data(
    n_samples: int = 500,
    mode: str = 'VA',
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic ECMO data for demonstration.

    Args:
        n_samples: Number of samples to generate
        mode: ECMO mode ('VA' or 'VV')
        random_state: Random seed

    Returns:
        DataFrame with synthetic ECMO features
    """
    np.random.seed(random_state)

    print(f"Generating {n_samples} synthetic {mode}-ECMO episodes...")

    # Patient demographics
    age_years = np.random.normal(60, 15, n_samples).clip(18, 90)
    sex = np.random.choice(['M', 'F'], n_samples)
    weight_kg = np.random.normal(75, 15, n_samples).clip(40, 150)
    height_cm = np.random.normal(170, 10, n_samples).clip(150, 200)
    bsa_m2 = np.sqrt(height_cm * weight_kg / 3600)
    bmi = weight_kg / (height_cm / 100) ** 2

    # Pre-ECMO severity
    apache_ii = np.random.poisson(20, n_samples).clip(0, 50)
    sofa_score = np.random.poisson(10, n_samples).clip(0, 24)

    # Pre-ECMO labs
    ph_pre_ecmo = np.random.normal(7.25, 0.15, n_samples).clip(6.8, 7.6)
    pao2_pre_ecmo = np.random.gamma(2, 30, n_samples).clip(30, 150)
    paco2_pre_ecmo = np.random.normal(50, 15, n_samples).clip(20, 100)
    lactate_pre_ecmo = np.random.gamma(2, 2, n_samples).clip(0.5, 20)

    # Pre-ECMO respiratory
    fio2_pre_ecmo = np.random.beta(5, 2, n_samples).clip(0.4, 1.0)
    pf_ratio = pao2_pre_ecmo / fio2_pre_ecmo
    peep_pre_ecmo = np.random.normal(10, 3, n_samples).clip(5, 20)

    # Pre-ECMO chemistry
    sodium_mmol_l = np.random.normal(140, 5, n_samples).clip(120, 160)
    potassium_mmol_l = np.random.normal(4.0, 0.8, n_samples).clip(2.5, 6.5)
    creatinine_mg_dl = np.random.gamma(2, 0.5, n_samples).clip(0.5, 8)
    bun_mg_dl = np.random.gamma(3, 8, n_samples).clip(5, 100)
    bilirubin_mg_dl = np.random.gamma(2, 1, n_samples).clip(0.2, 15)
    glucose_mg_dl = np.random.normal(150, 40, n_samples).clip(60, 400)

    # Pre-ECMO hematology
    hemoglobin_g_dl = np.random.normal(11, 2, n_samples).clip(6, 18)
    hematocrit_pct = hemoglobin_g_dl * 3
    platelets_k_ul = np.random.gamma(5, 40, n_samples).clip(20, 500)
    wbc_k_ul = np.random.gamma(3, 4, n_samples).clip(1, 40)

    # Pre-ECMO coagulation
    pt_sec = np.random.gamma(3, 4, n_samples).clip(10, 40)
    ptt_sec = np.random.gamma(4, 10, n_samples).clip(20, 120)
    inr = np.random.gamma(2, 0.5, n_samples).clip(0.8, 5)
    fibrinogen_mg_dl = np.random.gamma(4, 80, n_samples).clip(100, 600)

    # Pre-ECMO vitals
    hr_pre_ecmo = np.random.normal(100, 20, n_samples).clip(40, 180)
    sbp_pre_ecmo = np.random.normal(100, 25, n_samples).clip(60, 200)
    dbp_pre_ecmo = sbp_pre_ecmo * np.random.uniform(0.5, 0.7, n_samples)
    map_pre_ecmo = (sbp_pre_ecmo + 2 * dbp_pre_ecmo) / 3
    resp_rate_pre_ecmo = np.random.normal(25, 8, n_samples).clip(10, 50)
    spo2_pre_ecmo = np.random.beta(10, 1, n_samples) * 100
    temp_pre_ecmo = np.random.normal(37, 1, n_samples).clip(35, 40)

    # Pre-ECMO mechanical ventilation
    mechanical_vent_hours = np.random.gamma(2, 24, n_samples).clip(0, 240)

    # ECMO episode details
    ecmo_duration_hours = np.random.gamma(3, 48, n_samples).clip(6, 720)
    ecmo_mode = [mode] * n_samples

    # ECMO support parameters
    avg_flow_l_min = np.random.normal(4.5, 1, n_samples).clip(2, 8)
    avg_pump_rpm = avg_flow_l_min * 800 + np.random.normal(0, 200, n_samples)
    avg_sweep_gas_l_min = np.random.normal(5, 1.5, n_samples).clip(1, 10)
    avg_ecmo_fio2 = np.random.beta(8, 2, n_samples).clip(0.5, 1.0)

    # ECMO complications (binary)
    cns_hemorrhage = np.random.binomial(1, 0.05, n_samples)
    pulmonary_hemorrhage = np.random.binomial(1, 0.08, n_samples)
    ischemic_stroke = np.random.binomial(1, 0.06, n_samples)
    myocardial_infarction = np.random.binomial(1, 0.04, n_samples)
    arrhythmia = np.random.binomial(1, 0.15, n_samples)
    limb_ischemia = np.random.binomial(1, 0.1, n_samples) if mode == 'VA' else np.zeros(n_samples)
    acute_kidney_injury = np.random.binomial(1, 0.3, n_samples)
    sepsis = np.random.binomial(1, 0.2, n_samples)
    pneumonia = np.random.binomial(1, 0.15, n_samples)

    # ECMO interventions
    prbc_transfusion = np.random.binomial(1, 0.5, n_samples)
    platelet_transfusion = np.random.binomial(1, 0.3, n_samples)
    renal_replacement_therapy = np.random.binomial(1, 0.25, n_samples)

    # Calculate risk score (for outcome generation)
    risk_score = (
        (apache_ii / 50) * 0.3 +
        (lactate_pre_ecmo / 10) * 0.2 +
        (1 - pf_ratio / 400) * 0.15 +
        (creatinine_mg_dl / 8) * 0.1 +
        (ecmo_duration_hours / 500) * 0.1 +
        (cns_hemorrhage + ischemic_stroke + acute_kidney_injury) * 0.05
    )

    # Generate outcome (survival) based on risk score with some randomness
    survival_prob = 1 / (1 + np.exp(5 * (risk_score - 0.5)))  # Logistic function
    survival_to_discharge = np.random.binomial(1, survival_prob, n_samples)

    # Outcomes
    icu_los_days = ecmo_duration_hours / 24 + np.random.gamma(2, 3, n_samples)
    hosp_los_days = icu_los_days + np.random.gamma(2, 5, n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        # Identifiers
        'subject_id': range(1000, 1000 + n_samples),
        'hadm_id': range(2000, 2000 + n_samples),
        'stay_id': range(3000, 3000 + n_samples),
        'episode_num': 1,

        # ECMO episode
        'ecmo_mode': ecmo_mode,
        'ecmo_duration_hours': ecmo_duration_hours,

        # Demographics
        'age_years': age_years,
        'sex': sex,
        'weight_kg': weight_kg,
        'height_cm': height_cm,
        'bmi': bmi,
        'bsa_m2': bsa_m2,

        # Diagnosis
        'diagnosis_category': np.random.choice(['cardiac', 'respiratory', 'septic_shock'], n_samples),

        # Pre-ECMO severity
        'apache_ii': apache_ii,
        'sofa_score': sofa_score,

        # Pre-ECMO labs
        'ph_pre_ecmo': ph_pre_ecmo,
        'pao2_pre_ecmo': pao2_pre_ecmo,
        'paco2_pre_ecmo': paco2_pre_ecmo,
        'lactate_pre_ecmo': lactate_pre_ecmo,
        'pf_ratio': pf_ratio,
        'fio2_pre_ecmo': fio2_pre_ecmo,
        'peep_pre_ecmo': peep_pre_ecmo,

        # Pre-ECMO chemistry
        'sodium_mmol_l': sodium_mmol_l,
        'potassium_mmol_l': potassium_mmol_l,
        'creatinine_mg_dl': creatinine_mg_dl,
        'bun_mg_dl': bun_mg_dl,
        'bilirubin_mg_dl': bilirubin_mg_dl,
        'glucose_mg_dl': glucose_mg_dl,

        # Pre-ECMO hematology
        'hemoglobin_g_dl': hemoglobin_g_dl,
        'hematocrit_pct': hematocrit_pct,
        'platelets_k_ul': platelets_k_ul,
        'wbc_k_ul': wbc_k_ul,

        # Pre-ECMO coagulation
        'pt_sec': pt_sec,
        'ptt_sec': ptt_sec,
        'inr': inr,
        'fibrinogen_mg_dl': fibrinogen_mg_dl,

        # Pre-ECMO vitals
        'hr_pre_ecmo': hr_pre_ecmo,
        'sbp_pre_ecmo': sbp_pre_ecmo,
        'dbp_pre_ecmo': dbp_pre_ecmo,
        'map_pre_ecmo': map_pre_ecmo,
        'resp_rate_pre_ecmo': resp_rate_pre_ecmo,
        'spo2_pre_ecmo': spo2_pre_ecmo,
        'temp_pre_ecmo': temp_pre_ecmo,

        # Pre-ECMO mechanical ventilation
        'mechanical_vent_hours': mechanical_vent_hours,

        # ECMO support parameters
        'avg_flow_l_min': avg_flow_l_min,
        'avg_pump_rpm': avg_pump_rpm,
        'avg_sweep_gas_l_min': avg_sweep_gas_l_min,
        'avg_ecmo_fio2': avg_ecmo_fio2,

        # Complications
        'cns_hemorrhage': cns_hemorrhage,
        'pulmonary_hemorrhage': pulmonary_hemorrhage,
        'ischemic_stroke': ischemic_stroke,
        'myocardial_infarction': myocardial_infarction,
        'arrhythmia': arrhythmia,
        'limb_ischemia': limb_ischemia,
        'acute_kidney_injury': acute_kidney_injury,
        'sepsis': sepsis,
        'pneumonia': pneumonia,

        # Interventions
        'prbc_transfusion': prbc_transfusion,
        'platelet_transfusion': platelet_transfusion,
        'renal_replacement_therapy': renal_replacement_therapy,

        # Outcomes
        'survival_to_discharge': survival_to_discharge,
        'icu_los_days': icu_los_days,
        'hosp_los_days': hosp_los_days,
    })

    print(f"Generated {len(df)} episodes")
    print(f"Survival rate: {survival_to_discharge.mean()*100:.1f}%")

    return df


def run_demo():
    """
    Run complete demo of ECMO risk modeling pipeline.
    """
    print("="*80)
    print("ECMO RISK MODEL DEMONSTRATION")
    print("="*80)
    print()

    # Step 1: Generate synthetic data
    print("\nStep 1: Generating Synthetic Data")
    print("-" * 80)

    # Generate data for both VA and VV modes
    df_va = generate_synthetic_ecmo_data(n_samples=300, mode='VA', random_state=42)
    df_vv = generate_synthetic_ecmo_data(n_samples=200, mode='VV', random_state=43)
    df = pd.concat([df_va, df_vv], ignore_index=True)

    print(f"\nTotal dataset: {len(df)} episodes")
    print(f"  VA-ECMO: {len(df_va)} episodes")
    print(f"  VV-ECMO: {len(df_vv)} episodes")

    # Step 2: Feature engineering
    print("\n\nStep 2: Feature Engineering")
    print("-" * 80)
    df = engineer_all_features(df, include_interactions=True, include_domain=True)

    # Step 3: Save synthetic data
    output_dir = Path('demo_output')
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / 'synthetic_ecmo_data.csv'
    df.to_csv(csv_path, index=False)
    print(f"\nSaved synthetic data to: {csv_path}")

    # Step 4: Data loading and preprocessing
    print("\n\nStep 3: Data Loading and Preprocessing")
    print("-" * 80)

    data_config = DataConfig(
        data_source='csv',
        features_csv=str(csv_path),
        test_size=0.2,
        val_size=0.2,
        imputation_strategy='median',
        scaling_method='robust',
        handle_outliers=True,
        random_state=42
    )

    loader = MIMICDataLoader(data_config)
    processed_data = loader.load_and_prepare()

    # Step 5: Model training
    print("\n\nStep 4: Model Training")
    print("-" * 80)

    training_config = TrainingConfig(
        model_type='gradient_boosting',
        tune_hyperparameters=False,  # Set to False for demo speed
        use_smote=True,
        use_feature_selection=True,
        feature_selection_method='importance',
        n_features_to_select=30,
        output_dir=str(output_dir / 'models'),
        random_state=42
    )

    models = {}

    for mode in ['VA', 'VV']:
        if mode not in processed_data:
            continue

        print(f"\n\nTraining {mode}-ECMO Model")
        print("=" * 80)

        # Get data
        train_data = processed_data[mode]['train']
        val_data = processed_data[mode]['val']

        # Create model config
        model_config = ModelConfig(
            ecmo_mode=mode,
            target='survival_to_discharge',
            handle_imbalance=True,
            calibration_method='isotonic'
        )

        # Train model
        trainer = ECMOModelTrainer(training_config, model_config)
        model = trainer.train(
            X_train=train_data['X'].values,
            y_train=train_data['y'].values,
            X_val=val_data['X'].values,
            y_val=val_data['y'].values,
            feature_names=loader.get_feature_names()
        )

        # Save model
        trainer.save_model(model, str(output_dir / 'models'))
        models[mode] = (model, trainer)

    # Step 6: Model validation
    print("\n\nStep 5: Model Validation")
    print("-" * 80)

    validation_config = ValidationConfig(
        n_calibration_bins=10,
        n_bootstrap=100,  # Reduced for demo speed
        use_shap=False,  # Disable SHAP for demo speed
        save_plots=True,
        plot_dir=str(output_dir / 'validation')
    )

    validator = ModelValidator(validation_config)

    for mode in ['VA', 'VV']:
        if mode not in processed_data or mode not in models:
            continue

        print(f"\n\nValidating {mode}-ECMO Model")
        print("=" * 80)

        # Get test data
        test_data = processed_data[mode]['test']
        model, trainer = models[mode]

        # Get predictions
        y_test = test_data['y'].values
        X_test = test_data['X'].values

        # Select features if feature selection was used
        if trainer.selected_features:
            feature_idx = [i for i, f in enumerate(loader.get_feature_names())
                          if f in trainer.selected_features]
            X_test = X_test[:, feature_idx]

        y_pred_proba = model.predict_proba(X_test, calibrated=True)[:, 1]

        # Prepare subgroups for analysis
        metadata = test_data['metadata']
        subgroups = {
            'APACHE-II': np.digitize(
                df.loc[metadata.index, 'apache_ii'].values,
                bins=[0, 15, 25, 100]
            )
        }

        # Run validation
        validation_results = validator.validate_model(
            y_true=y_test,
            y_pred_proba=y_pred_proba,
            model_name=f'{mode}-ECMO Risk Model',
            subgroups=subgroups
        )

    # Step 7: Example predictions
    print("\n\nStep 6: Example Predictions")
    print("-" * 80)

    for mode in ['VA', 'VV']:
        if mode not in processed_data or mode not in models:
            continue

        test_data = processed_data[mode]['test']
        model, trainer = models[mode]

        # Get 3 random test examples
        n_examples = min(3, len(test_data['X']))
        example_indices = np.random.choice(len(test_data['X']), n_examples, replace=False)

        print(f"\n{mode}-ECMO Model Predictions (Random Test Examples):")
        print("-" * 80)

        for idx in example_indices:
            X_example = test_data['X'].iloc[idx].values.reshape(1, -1)

            # Select features if needed
            if trainer.selected_features:
                feature_idx = [i for i, f in enumerate(loader.get_feature_names())
                              if f in trainer.selected_features]
                X_example = X_example[:, feature_idx]

            y_true = test_data['y'].iloc[idx]
            y_pred_proba = model.predict_proba(X_example, calibrated=True)[0, 1]

            print(f"\nExample {idx + 1}:")
            print(f"  Predicted survival probability: {y_pred_proba:.3f}")
            print(f"  Actual outcome: {'Survived' if y_true == 1 else 'Died'}")
            print(f"  Risk category: ", end='')
            if y_pred_proba >= 0.7:
                print("Low risk")
            elif y_pred_proba >= 0.4:
                print("Moderate risk")
            else:
                print("High risk")

    # Summary
    print("\n\n" + "="*80)
    print("DEMO COMPLETE!")
    print("="*80)
    print(f"\nAll outputs saved to: {output_dir.absolute()}")
    print("\nGenerated files:")
    print(f"  - Synthetic data: {csv_path}")
    print(f"  - Trained models: {output_dir / 'models'}")
    print(f"  - Validation plots: {output_dir / 'validation'}")
    print("\nKey metrics for VA-ECMO model:")
    if 'VA' in models:
        _, trainer = models['VA']
        if 'val_metrics' in trainer.training_history:
            for metric, value in trainer.training_history['val_metrics'].items():
                print(f"  {metric}: {value:.4f}")

    print("\nNext steps:")
    print("  1. Review validation plots in the output directory")
    print("  2. Examine feature importance in training reports")
    print("  3. Test with real MIMIC-IV data by updating DataConfig")
    print("  4. Tune hyperparameters for better performance")
    print("  5. Deploy models using the saved .pkl files")
    print()


if __name__ == '__main__':
    run_demo()
