"""
NIRS + EHR Risk Models for ECMO Outcomes
Supports VA/VV separation, class weighting, calibration, and explainability.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    roc_curve, precision_recall_curve
)
from sklearn.utils.class_weight import compute_class_weight
import warnings


@dataclass
class ModelConfig:
    """Configuration for risk model training."""
    ecmo_mode: str  # 'VA' or 'VV'
    target: str = 'survival_to_discharge'
    handle_imbalance: bool = True
    calibration_method: str = 'isotonic'  # 'isotonic' or 'sigmoid' (Platt)
    n_cv_folds: int = 5
    random_state: int = 42

    # NIRS features
    nirs_features: List[str] = None
    # EHR features
    ehr_features: List[str] = None

    def __post_init__(self):
        if self.nirs_features is None:
            self.nirs_features = [
                'hbo_mean', 'hbo_std', 'hbo_slope',
                'hbt_mean', 'hbt_std', 'hbt_slope',
            ]
        if self.ehr_features is None:
            self.ehr_features = [
                'age', 'bmi', 'apache_ii',
                'lactate_mmol_l', 'hemoglobin_g_dl', 'platelets_10e9_l',
                'map_mmHg', 'spo2_pct', 'abg_pao2_mmHg', 'abg_paco2_mmHg',
                'pump_speed_rpm', 'flow_l_min', 'sweep_gas_l_min', 'fio2_ecmo',
            ]


class ECMORiskModel:
    """
    Explainable risk model for ECMO outcomes with VA/VV separation.

    Features:
    - Separate models for VA and VV ECMO modes
    - Class weighting for imbalanced datasets
    - Calibration (isotonic or Platt scaling)
    - APACHE-stratified performance metrics
    - Built-in explainability (feature importance)
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.calibrated_model = None
        self.feature_names = None
        self.class_weights = None
        self.training_metrics = {}

    def _get_base_model(self) -> Any:
        """Get base classifier with class weights if configured."""
        if self.config.handle_imbalance and self.class_weights is not None and len(self.class_weights) == 2:
            # Use computed class weights (only if both classes present)
            class_weight_dict = {
                0: self.class_weights[0],
                1: self.class_weights[1]
            }
        else:
            class_weight_dict = None

        # Default to GradientBoosting for better calibration
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            min_samples_split=20,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=self.config.random_state
        )
        return model

    def _compute_class_weights(self, y: np.ndarray) -> np.ndarray:
        """Compute balanced class weights for imbalanced data."""
        classes = np.unique(y)
        weights = compute_class_weight(
            class_weight='balanced',
            classes=classes,
            y=y
        )
        return weights

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare feature matrix from NIRS + EHR data.

        Args:
            df: DataFrame with NIRS and EHR features

        Returns:
            X: Feature matrix
            y: Target labels
            feature_names: List of feature names
        """
        # Filter by ECMO mode
        df_mode = df[df['mode'] == self.config.ecmo_mode].copy()

        if len(df_mode) == 0:
            raise ValueError(f"No data found for ECMO mode: {self.config.ecmo_mode}")

        # Combine NIRS and EHR features
        all_features = self.config.nirs_features + self.config.ehr_features

        # Select available features
        available_features = [f for f in all_features if f in df_mode.columns]
        if len(available_features) == 0:
            raise ValueError(f"No features found in data. Expected: {all_features}")

        if len(available_features) < len(all_features):
            missing = set(all_features) - set(available_features)
            warnings.warn(f"Missing features: {missing}")

        # Extract features and target
        X = df_mode[available_features].values
        y = df_mode[self.config.target].astype(int).values

        # Handle missing values (simple imputation with median)
        X_df = pd.DataFrame(X, columns=available_features)
        X_df = X_df.fillna(X_df.median())
        X = X_df.values

        return X, y, available_features

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> 'ECMORiskModel':
        """
        Train risk model with calibration.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (n_samples,)
            feature_names: List of feature names

        Returns:
            self
        """
        self.feature_names = feature_names

        # Compute class weights for imbalanced data
        if self.config.handle_imbalance:
            self.class_weights = self._compute_class_weights(y)
            print(f"\n{self.config.ecmo_mode} ECMO - Class distribution:")
            print(f"  Class 0 (died): {np.sum(y == 0)} ({np.mean(y == 0)*100:.1f}%)")
            print(f"  Class 1 (survived): {np.sum(y == 1)} ({np.mean(y == 1)*100:.1f}%)")
            if len(self.class_weights) == 2:
                print(f"  Class weights: 0={self.class_weights[0]:.3f}, 1={self.class_weights[1]:.3f}")
            else:
                print(f"  Warning: Only one class present. Class weights: {self.class_weights}")

        # Train base model
        self.model = self._get_base_model()

        # For gradient boosting, use sample_weight instead of class_weight
        if isinstance(self.model, GradientBoostingClassifier) and self.class_weights is not None and len(self.class_weights) == 2:
            sample_weights = np.ones(len(y))
            sample_weights[y == 0] = self.class_weights[0]
            sample_weights[y == 1] = self.class_weights[1]
            self.model.fit(X, y, sample_weight=sample_weights)
        else:
            self.model.fit(X, y)

        # Apply calibration
        print(f"\nApplying {self.config.calibration_method} calibration...")
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method=self.config.calibration_method,
            cv='prefit'  # Use pre-fitted model
        )

        # For calibration, we need to use a hold-out set or CV
        # Using stratified CV for calibration
        cv = StratifiedKFold(n_splits=min(self.config.n_cv_folds, len(y) // 20))

        # Re-train for proper calibration
        base_model = self._get_base_model()
        if isinstance(base_model, GradientBoostingClassifier) and self.class_weights is not None and len(self.class_weights) == 2:
            base_model.fit(X, y, sample_weight=sample_weights)
        else:
            base_model.fit(X, y)

        self.calibrated_model = CalibratedClassifierCV(
            base_model,
            method=self.config.calibration_method,
            cv=cv
        )
        self.calibrated_model.fit(X, y)

        return self

    def predict_proba(self, X: np.ndarray, calibrated: bool = True) -> np.ndarray:
        """
        Predict probabilities.

        Args:
            X: Feature matrix
            calibrated: Use calibrated model if True

        Returns:
            Probability predictions (n_samples, 2)
        """
        model = self.calibrated_model if calibrated else self.model
        if model is None:
            raise ValueError("Model not trained. Call fit() first.")
        return model.predict_proba(X)

    def predict(self, X: np.ndarray, calibrated: bool = True, threshold: float = 0.5) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Feature matrix
            calibrated: Use calibrated model if True
            threshold: Decision threshold

        Returns:
            Predicted labels (n_samples,)
        """
        proba = self.predict_proba(X, calibrated=calibrated)
        return (proba[:, 1] >= threshold).astype(int)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores.

        Returns:
            DataFrame with features and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        else:
            # For linear models, use coefficient magnitude
            importance = np.abs(self.model.coef_[0])

        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        return df

    def explain_prediction(self, X: np.ndarray, index: int = 0) -> Dict[str, Any]:
        """
        Explain individual prediction.

        Args:
            X: Feature matrix
            index: Sample index to explain

        Returns:
            Dictionary with prediction explanation
        """
        proba = self.predict_proba(X[[index]], calibrated=True)[0]
        features = {
            name: float(X[index, i])
            for i, name in enumerate(self.feature_names)
        }

        importance = self.get_feature_importance()

        return {
            'prediction': {
                'probability_death': float(proba[0]),
                'probability_survival': float(proba[1]),
                'predicted_class': int(proba[1] >= 0.5)
            },
            'features': features,
            'top_features': importance.head(10).to_dict('records')
        }


class APACHEStratifiedEvaluator:
    """
    Evaluate model performance stratified by APACHE-II scores.
    """

    def __init__(self, apache_bins: Optional[List[float]] = None):
        """
        Args:
            apache_bins: Bin edges for APACHE-II stratification
                        Default: [0, 15, 25, 100] for low/medium/high
        """
        if apache_bins is None:
            apache_bins = [0, 15, 25, 100]
        self.apache_bins = apache_bins

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        apache_scores: np.ndarray,
        label: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate model with APACHE-II stratification.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities (n_samples, 2)
            apache_scores: APACHE-II scores
            label: Label for the evaluation (e.g., 'VA-ECMO')

        Returns:
            Dictionary with overall and stratified metrics
        """
        results = {'label': label}

        # Overall metrics
        y_pred = y_pred_proba[:, 1]
        results['overall'] = self._compute_metrics(y_true, y_pred)

        # Stratified metrics
        apache_strata = pd.cut(
            apache_scores,
            bins=self.apache_bins,
            labels=['low', 'medium', 'high'][:len(self.apache_bins)-1],
            include_lowest=True
        )

        results['stratified'] = {}
        for stratum in apache_strata.unique():
            if pd.isna(stratum):
                continue
            mask = (apache_strata == stratum)
            if mask.sum() < 10:  # Skip small groups
                continue

            results['stratified'][str(stratum)] = {
                'n': int(mask.sum()),
                **self._compute_metrics(y_true[mask], y_pred[mask])
            }

        # Calibration metrics
        results['calibration'] = self._compute_calibration(y_true, y_pred)

        return results

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute classification metrics."""
        if len(np.unique(y_true)) < 2:
            return {
                'auroc': np.nan,
                'auprc': np.nan,
                'brier_score': np.nan,
            }

        return {
            'auroc': float(roc_auc_score(y_true, y_pred)),
            'auprc': float(average_precision_score(y_true, y_pred)),
            'brier_score': float(brier_score_loss(y_true, y_pred)),
        }

    def _compute_calibration(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """Compute calibration metrics."""
        try:
            prob_true, prob_pred = calibration_curve(
                y_true, y_pred, n_bins=n_bins, strategy='quantile'
            )

            # Expected Calibration Error (ECE)
            bin_counts = np.histogram(y_pred, bins=n_bins, range=(0, 1))[0]
            bin_weights = bin_counts / len(y_pred)
            ece = np.sum(bin_weights * np.abs(prob_true - prob_pred))

            return {
                'ece': float(ece),
                'prob_true': prob_true.tolist(),
                'prob_pred': prob_pred.tolist(),
            }
        except Exception as e:
            warnings.warn(f"Calibration computation failed: {e}")
            return {'ece': np.nan}

    def print_report(self, results: Dict[str, Any]) -> None:
        """Print formatted evaluation report."""
        print(f"\n{'='*60}")
        print(f"Performance Report: {results['label']}")
        print(f"{'='*60}")

        # Overall metrics
        print("\nOverall Performance:")
        for metric, value in results['overall'].items():
            print(f"  {metric:15s}: {value:.4f}")

        # Calibration
        if 'ece' in results['calibration']:
            print(f"  {'ECE':15s}: {results['calibration']['ece']:.4f}")

        # Stratified metrics
        if results['stratified']:
            print("\nAPACHE-II Stratified Performance:")
            for stratum, metrics in results['stratified'].items():
                print(f"\n  {stratum.upper()} (n={metrics['n']}):")
                for metric, value in metrics.items():
                    if metric != 'n':
                        print(f"    {metric:13s}: {value:.4f}")


def train_va_vv_models(
    df: pd.DataFrame,
    target: str = 'survival_to_discharge',
    apache_col: str = 'apache_ii'
) -> Tuple[ECMORiskModel, ECMORiskModel, Dict[str, Any]]:
    """
    Train separate VA and VV ECMO risk models.

    Args:
        df: DataFrame with ECMO episodes
        target: Target outcome variable
        apache_col: Column name for APACHE-II scores

    Returns:
        va_model: Trained VA-ECMO model
        vv_model: Trained VV-ECMO model
        results: Dictionary with evaluation results
    """
    print("="*60)
    print("Training VA/VV Separated ECMO Risk Models")
    print("="*60)

    results = {}
    models = {}

    for mode in ['VA', 'VV']:
        print(f"\n\n{'*'*60}")
        print(f"Training {mode}-ECMO Model")
        print(f"{'*'*60}")

        # Configure model
        config = ModelConfig(
            ecmo_mode=mode,
            target=target,
            handle_imbalance=True,
            calibration_method='isotonic'
        )

        # Initialize model
        model = ECMORiskModel(config)

        try:
            # Prepare features
            X, y, feature_names = model.prepare_features(df)
            print(f"\nData shape: {X.shape}")
            print(f"Features: {len(feature_names)}")

            # Train model
            model.fit(X, y, feature_names)

            # Evaluate
            y_pred_proba = model.predict_proba(X, calibrated=True)
            apache_scores = df[df['mode'] == mode][apache_col].values

            evaluator = APACHEStratifiedEvaluator()
            eval_results = evaluator.evaluate(
                y, y_pred_proba, apache_scores, label=f'{mode}-ECMO'
            )
            evaluator.print_report(eval_results)

            # Feature importance
            print(f"\n\nTop 10 Most Important Features ({mode}-ECMO):")
            importance_df = model.get_feature_importance()
            print(importance_df.head(10).to_string(index=False))

            models[mode] = model
            results[mode] = eval_results

        except Exception as e:
            print(f"\nError training {mode} model: {e}")
            warnings.warn(f"Failed to train {mode} model: {e}")
            models[mode] = None
            results[mode] = None

    return models.get('VA'), models.get('VV'), results
