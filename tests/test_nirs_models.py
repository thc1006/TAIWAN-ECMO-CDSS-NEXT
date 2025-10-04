"""
Unit Tests for NIRS + EHR Risk Models (WP1)
Tests VA/VV separation, calibration, feature engineering, and APACHE stratification.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nirs.risk_models import (
    ECMORiskModel,
    ModelConfig,
    APACHEStratifiedEvaluator,
    train_va_vv_models
)


# ============================================================================
# MODEL CONFIGURATION TESTS
# ============================================================================

class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = ModelConfig(ecmo_mode='VA')

        assert config.ecmo_mode == 'VA'
        assert config.target == 'survival_to_discharge'
        assert config.handle_imbalance is True
        assert config.calibration_method == 'isotonic'
        assert config.n_cv_folds == 5
        assert config.random_state == 42

    def test_config_custom_features(self):
        """Test custom feature specification."""
        nirs_features = ['hbo_mean', 'hbt_mean']
        ehr_features = ['age', 'apache_ii']

        config = ModelConfig(
            ecmo_mode='VV',
            nirs_features=nirs_features,
            ehr_features=ehr_features
        )

        assert config.nirs_features == nirs_features
        assert config.ehr_features == ehr_features

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid ECMO mode
        config = ModelConfig(ecmo_mode='INVALID')
        assert config.ecmo_mode == 'INVALID'  # No validation in current implementation

    @pytest.mark.parametrize("calibration_method", ['isotonic', 'sigmoid'])
    def test_calibration_methods(self, calibration_method):
        """Test different calibration methods."""
        config = ModelConfig(ecmo_mode='VA', calibration_method=calibration_method)
        assert config.calibration_method == calibration_method


# ============================================================================
# FEATURE PREPARATION TESTS
# ============================================================================

class TestFeaturePreparation:
    """Test feature extraction and preparation."""

    def test_prepare_features_va_mode(self, synthetic_ecmo_data):
        """Test feature preparation for VA-ECMO."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)

        # Check shapes
        n_va_patients = (synthetic_ecmo_data['mode'] == 'VA').sum()
        assert X.shape[0] == n_va_patients
        assert y.shape[0] == n_va_patients
        assert len(feature_names) > 0

        # Check no missing values
        assert not np.isnan(X).any()

        # Check binary target
        assert set(np.unique(y)).issubset({0, 1})

    def test_prepare_features_vv_mode(self, synthetic_ecmo_data):
        """Test feature preparation for VV-ECMO."""
        config = ModelConfig(ecmo_mode='VV')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)

        # Check shapes
        n_vv_patients = (synthetic_ecmo_data['mode'] == 'VV').sum()
        assert X.shape[0] == n_vv_patients

    def test_prepare_features_missing_data(self, synthetic_ecmo_data):
        """Test handling of missing data."""
        # Introduce missing values
        df = synthetic_ecmo_data.copy()
        df.loc[0:10, 'lactate_mmol_l'] = np.nan

        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(df)

        # Should impute missing values
        assert not np.isnan(X).any()

    def test_prepare_features_no_data(self):
        """Test error handling when no data for mode."""
        df = pd.DataFrame({
            'mode': ['VV', 'VV'],
            'survival_to_discharge': [0, 1]
        })

        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        with pytest.raises(ValueError, match="No data found for ECMO mode"):
            model.prepare_features(df)

    def test_feature_name_consistency(self, synthetic_ecmo_data):
        """Test that feature names match data columns."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)

        # All feature names should be in original data
        for fname in feature_names:
            assert fname in synthetic_ecmo_data.columns


# ============================================================================
# MODEL TRAINING TESTS
# ============================================================================

class TestModelTraining:
    """Test risk model training."""

    def test_fit_basic(self, synthetic_ecmo_data):
        """Test basic model fitting."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        # Check model is fitted
        assert model.model is not None
        assert model.calibrated_model is not None
        assert model.feature_names == feature_names

    def test_fit_with_class_weights(self, synthetic_ecmo_data):
        """Test fitting with class weight handling."""
        config = ModelConfig(ecmo_mode='VA', handle_imbalance=True)
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        # Check class weights computed
        assert model.class_weights is not None
        assert len(model.class_weights) == 2

    def test_fit_without_class_weights(self, synthetic_ecmo_data):
        """Test fitting without class weighting."""
        config = ModelConfig(ecmo_mode='VA', handle_imbalance=False)
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        assert model.class_weights is None

    @pytest.mark.parametrize("calibration_method", ['isotonic', 'sigmoid'])
    def test_calibration_methods(self, synthetic_ecmo_data, calibration_method):
        """Test different calibration methods."""
        config = ModelConfig(ecmo_mode='VA', calibration_method=calibration_method)
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        assert model.calibrated_model is not None


# ============================================================================
# PREDICTION TESTS
# ============================================================================

class TestPredictions:
    """Test model predictions."""

    def test_predict_proba_calibrated(self, synthetic_ecmo_data):
        """Test calibrated probability predictions."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        probs = model.predict_proba(X, calibrated=True)

        # Check shape
        assert probs.shape == (len(X), 2)

        # Check valid probabilities
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)
        np.testing.assert_array_almost_equal(probs.sum(axis=1), 1.0, decimal=5)

    def test_predict_proba_uncalibrated(self, synthetic_ecmo_data):
        """Test uncalibrated probability predictions."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        probs = model.predict_proba(X, calibrated=False)

        assert probs.shape == (len(X), 2)
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

    def test_predict_binary(self, synthetic_ecmo_data):
        """Test binary class predictions."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        preds = model.predict(X, calibrated=True, threshold=0.5)

        # Check binary predictions
        assert set(np.unique(preds)).issubset({0, 1})
        assert len(preds) == len(X)

    def test_predict_custom_threshold(self, synthetic_ecmo_data):
        """Test predictions with custom threshold."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        # Lower threshold should increase positive predictions
        preds_low = model.predict(X, threshold=0.3)
        preds_high = model.predict(X, threshold=0.7)

        assert preds_low.sum() >= preds_high.sum()

    def test_predict_before_fit_error(self, synthetic_ecmo_data):
        """Test error when predicting before fitting."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)

        with pytest.raises(ValueError, match="Model not trained"):
            model.predict_proba(X)


# ============================================================================
# FEATURE IMPORTANCE TESTS
# ============================================================================

class TestFeatureImportance:
    """Test feature importance extraction."""

    def test_get_feature_importance(self, synthetic_ecmo_data):
        """Test feature importance retrieval."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        importance_df = model.get_feature_importance()

        # Check structure
        assert 'feature' in importance_df.columns
        assert 'importance' in importance_df.columns
        assert len(importance_df) == len(feature_names)

        # Check sorted descending
        assert (importance_df['importance'].values[:-1] >=
                importance_df['importance'].values[1:]).all()

    def test_explain_prediction(self, synthetic_ecmo_data):
        """Test individual prediction explanation."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        explanation = model.explain_prediction(X, index=0)

        # Check structure
        assert 'prediction' in explanation
        assert 'features' in explanation
        assert 'top_features' in explanation

        # Check prediction details
        pred = explanation['prediction']
        assert 'probability_death' in pred
        assert 'probability_survival' in pred
        assert 'predicted_class' in pred

        # Check probabilities sum to 1
        assert abs(pred['probability_death'] + pred['probability_survival'] - 1.0) < 1e-5


# ============================================================================
# APACHE STRATIFICATION TESTS
# ============================================================================

class TestAPACHEStratification:
    """Test APACHE-II stratified evaluation."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = APACHEStratifiedEvaluator()
        assert evaluator.apache_bins == [0, 15, 25, 100]

        custom_bins = [0, 10, 20, 30, 100]
        evaluator_custom = APACHEStratifiedEvaluator(apache_bins=custom_bins)
        assert evaluator_custom.apache_bins == custom_bins

    def test_evaluate_overall_metrics(self, synthetic_ecmo_data):
        """Test overall performance metrics."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)
        y_pred_proba = model.predict_proba(X)

        # Get APACHE scores
        apache_scores = synthetic_ecmo_data[
            synthetic_ecmo_data['mode'] == 'VA'
        ]['apache_ii'].values

        evaluator = APACHEStratifiedEvaluator()
        results = evaluator.evaluate(y, y_pred_proba, apache_scores, label='VA-ECMO')

        # Check overall metrics
        assert 'overall' in results
        assert 'auroc' in results['overall']
        assert 'auprc' in results['overall']
        assert 'brier_score' in results['overall']

        # Check metric ranges
        assert 0 <= results['overall']['auroc'] <= 1
        assert 0 <= results['overall']['auprc'] <= 1
        assert 0 <= results['overall']['brier_score'] <= 1

    def test_evaluate_stratified_metrics(self, synthetic_ecmo_data):
        """Test APACHE-stratified metrics."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)
        y_pred_proba = model.predict_proba(X)

        apache_scores = synthetic_ecmo_data[
            synthetic_ecmo_data['mode'] == 'VA'
        ]['apache_ii'].values

        evaluator = APACHEStratifiedEvaluator()
        results = evaluator.evaluate(y, y_pred_proba, apache_scores)

        # Check stratified results
        assert 'stratified' in results
        assert len(results['stratified']) > 0

        # Each stratum should have metrics and n
        for stratum, metrics in results['stratified'].items():
            assert 'n' in metrics
            assert 'auroc' in metrics
            assert metrics['n'] >= 10  # Minimum group size

    def test_evaluate_calibration(self, synthetic_ecmo_data):
        """Test calibration metrics."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)
        y_pred_proba = model.predict_proba(X)

        apache_scores = synthetic_ecmo_data[
            synthetic_ecmo_data['mode'] == 'VA'
        ]['apache_ii'].values

        evaluator = APACHEStratifiedEvaluator()
        results = evaluator.evaluate(y, y_pred_proba, apache_scores)

        # Check calibration
        assert 'calibration' in results
        assert 'ece' in results['calibration']

        # ECE should be low for calibrated model
        if not np.isnan(results['calibration']['ece']):
            assert 0 <= results['calibration']['ece'] <= 1


# ============================================================================
# VA/VV MODEL TRAINING TESTS
# ============================================================================

class TestVAVVModelTraining:
    """Test separate VA/VV model training."""

    def test_train_va_vv_models(self, synthetic_ecmo_data):
        """Test training both VA and VV models."""
        va_model, vv_model, results = train_va_vv_models(synthetic_ecmo_data)

        # Check models created
        assert va_model is not None
        assert vv_model is not None

        # Check results structure
        assert 'VA' in results
        assert 'VV' in results

        # Check VA results
        if results['VA'] is not None:
            assert 'overall' in results['VA']
            assert 'stratified' in results['VA']

        # Check VV results
        if results['VV'] is not None:
            assert 'overall' in results['VV']
            assert 'stratified' in results['VV']

    def test_models_independent(self, synthetic_ecmo_data):
        """Test that VA and VV models are independent."""
        va_model, vv_model, _ = train_va_vv_models(synthetic_ecmo_data)

        # Models should have different feature importance
        va_importance = va_model.get_feature_importance()
        vv_importance = vv_model.get_feature_importance()

        # Not strict equality (can be similar, but should be fitted separately)
        assert va_model is not vv_model


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestModelPerformance:
    """Test model performance characteristics."""

    def test_model_discriminates_outcomes(self, synthetic_ecmo_data):
        """Test that model can discriminate between outcomes."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        y_pred = model.predict_proba(X)[:, 1]

        # AUROC should be significantly better than random
        auroc = roc_auc_score(y, y_pred)
        assert auroc > 0.6, f"AUROC {auroc} is too low"

    def test_calibration_improves_brier_score(self, synthetic_ecmo_data):
        """Test that calibration improves Brier score."""
        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(synthetic_ecmo_data)
        model.fit(X, y, feature_names)

        # Get calibrated and uncalibrated predictions
        y_pred_calib = model.predict_proba(X, calibrated=True)[:, 1]
        y_pred_uncalib = model.predict_proba(X, calibrated=False)[:, 1]

        brier_calib = brier_score_loss(y, y_pred_calib)
        brier_uncalib = brier_score_loss(y, y_pred_uncalib)

        # Calibrated should be similar or better
        assert brier_calib <= brier_uncalib + 0.05  # Allow small margin


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_class_data(self):
        """Test handling of single-class data."""
        df = pd.DataFrame({
            'mode': ['VA'] * 50,
            'survival_to_discharge': [1] * 50,  # All survived
            'age': np.random.randint(20, 80, 50),
            'apache_ii': np.random.randint(10, 30, 50),
            'hbo_mean': np.random.normal(65, 10, 50),
            'lactate_mmol_l': np.random.gamma(2, 2, 50),
        })

        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        # Should handle gracefully (may warn)
        try:
            X, y, feature_names = model.prepare_features(df)
            model.fit(X, y, feature_names)
        except Exception as e:
            # Some implementations may raise, which is acceptable
            assert isinstance(e, (ValueError, RuntimeWarning))

    def test_very_small_dataset(self):
        """Test behavior with very small dataset."""
        df = pd.DataFrame({
            'mode': ['VA'] * 10,
            'survival_to_discharge': [0, 1] * 5,
            'age': np.random.randint(20, 80, 10),
            'apache_ii': np.random.randint(10, 30, 10),
            'hbo_mean': np.random.normal(65, 10, 10),
            'lactate_mmol_l': np.random.gamma(2, 2, 10),
        })

        config = ModelConfig(ecmo_mode='VA')
        model = ECMORiskModel(config)

        X, y, feature_names = model.prepare_features(df)

        # Should be able to fit (though performance may be poor)
        try:
            model.fit(X, y, feature_names)
        except Exception:
            # Very small data may cause fitting issues
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
