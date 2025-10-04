"""
ECMO Risk Model Training Pipeline
Supports hyperparameter tuning, cross-validation, feature selection, and model persistence.
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    StratifiedKFold,
    GridSearchCV,
    RandomizedSearchCV
)
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    make_scorer
)
from sklearn.feature_selection import (
    SelectKBest,
    mutual_info_classif,
    RFECV
)
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek

from risk_models import ECMORiskModel, ModelConfig
from data_loader import MIMICDataLoader, DataConfig


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    # Model selection
    model_type: str = 'gradient_boosting'  # 'logistic', 'random_forest', 'gradient_boosting', 'ada_boost'

    # Hyperparameter tuning
    tune_hyperparameters: bool = True
    tuning_method: str = 'grid'  # 'grid' or 'random'
    cv_folds: int = 5
    n_iter_random: int = 50  # For random search

    # Class imbalance handling
    use_smote: bool = True
    smote_strategy: str = 'minority'  # 'minority', 'not majority', or float
    use_class_weights: bool = True

    # Feature selection
    use_feature_selection: bool = True
    feature_selection_method: str = 'rfe'  # 'kbest', 'rfe', 'importance'
    n_features_to_select: Optional[int] = None  # None = auto

    # Training
    random_state: int = 42
    n_jobs: int = -1

    # Output
    output_dir: str = 'models'
    save_intermediate: bool = True


class ECMOModelTrainer:
    """
    Train and optimize ECMO risk prediction models.

    Features:
    - Multiple classifier options
    - Automated hyperparameter tuning
    - Feature selection
    - SMOTE for class imbalance
    - Cross-validation
    - Model persistence
    - Training reports
    """

    def __init__(
        self,
        training_config: TrainingConfig,
        model_config: ModelConfig
    ):
        self.training_config = training_config
        self.model_config = model_config
        self.best_model = None
        self.best_params = None
        self.cv_results = {}
        self.feature_importance = None
        self.selected_features = None
        self.training_history = {}

    def get_param_grid(self, model_type: str) -> Dict[str, List]:
        """
        Get hyperparameter grid for specified model type.

        Args:
            model_type: Type of model

        Returns:
            Parameter grid for tuning
        """
        if model_type == 'logistic':
            return {
                'C': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
                'penalty': ['l1', 'l2', 'elasticnet'],
                'solver': ['saga'],
                'max_iter': [1000],
                'l1_ratio': [0.0, 0.5, 1.0]  # For elasticnet
            }

        elif model_type == 'random_forest':
            return {
                'n_estimators': [50, 100, 200, 300],
                'max_depth': [3, 5, 10, 15, None],
                'min_samples_split': [2, 5, 10, 20],
                'min_samples_leaf': [1, 2, 5, 10],
                'max_features': ['sqrt', 'log2', None],
                'class_weight': ['balanced', 'balanced_subsample']
            }

        elif model_type == 'gradient_boosting':
            return {
                'n_estimators': [50, 100, 150, 200],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'max_depth': [2, 3, 4, 5],
                'min_samples_split': [10, 20, 30],
                'min_samples_leaf': [5, 10, 15],
                'subsample': [0.6, 0.8, 1.0],
                'max_features': ['sqrt', 'log2', None]
            }

        elif model_type == 'ada_boost':
            return {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.5, 1.0],
                'algorithm': ['SAMME', 'SAMME.R']
            }

        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def get_base_estimator(self, model_type: str) -> Any:
        """
        Get base estimator for specified model type.

        Args:
            model_type: Type of model

        Returns:
            Scikit-learn estimator
        """
        rs = self.training_config.random_state

        if model_type == 'logistic':
            return LogisticRegression(
                random_state=rs,
                max_iter=1000,
                solver='saga'
            )

        elif model_type == 'random_forest':
            return RandomForestClassifier(
                random_state=rs,
                n_jobs=self.training_config.n_jobs,
                class_weight='balanced' if self.training_config.use_class_weights else None
            )

        elif model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                random_state=rs
            )

        elif model_type == 'ada_boost':
            return AdaBoostClassifier(random_state=rs)

        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def apply_smote(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply SMOTE to handle class imbalance.

        Args:
            X: Feature matrix
            y: Target labels

        Returns:
            Resampled X and y
        """
        print(f"\nApplying SMOTE...")
        print(f"  Before: {len(y)} samples, {y.sum()} positive ({y.mean()*100:.1f}%)")

        # Use SMOTETomek for combined over/under sampling
        smote = SMOTETomek(
            sampling_strategy=self.training_config.smote_strategy,
            random_state=self.training_config.random_state,
            n_jobs=self.training_config.n_jobs
        )

        X_resampled, y_resampled = smote.fit_resample(X, y)

        print(f"  After:  {len(y_resampled)} samples, {y_resampled.sum()} positive ({y_resampled.mean()*100:.1f}%)")

        return X_resampled, y_resampled

    def select_features(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Perform feature selection.

        Args:
            X: Feature matrix
            y: Target labels
            feature_names: List of feature names

        Returns:
            Selected features and their names
        """
        print(f"\nPerforming feature selection using {self.training_config.feature_selection_method}...")

        if self.training_config.feature_selection_method == 'kbest':
            # Select K best features using mutual information
            k = self.training_config.n_features_to_select or min(50, X.shape[1])
            selector = SelectKBest(mutual_info_classif, k=k)
            X_selected = selector.fit_transform(X, y)
            selected_idx = selector.get_support(indices=True)

        elif self.training_config.feature_selection_method == 'rfe':
            # Recursive feature elimination with cross-validation
            estimator = self.get_base_estimator(self.training_config.model_type)
            selector = RFECV(
                estimator,
                step=1,
                cv=StratifiedKFold(3),
                scoring='roc_auc',
                n_jobs=self.training_config.n_jobs
            )
            X_selected = selector.fit_transform(X, y)
            selected_idx = selector.get_support(indices=True)

        elif self.training_config.feature_selection_method == 'importance':
            # Feature importance from tree-based model
            estimator = RandomForestClassifier(
                n_estimators=100,
                random_state=self.training_config.random_state,
                n_jobs=self.training_config.n_jobs
            )
            estimator.fit(X, y)
            importances = estimator.feature_importances_

            k = self.training_config.n_features_to_select or min(50, X.shape[1])
            selected_idx = np.argsort(importances)[-k:]
            X_selected = X[:, selected_idx]

        else:
            raise ValueError(f"Unknown feature selection method: {self.training_config.feature_selection_method}")

        selected_names = [feature_names[i] for i in selected_idx]

        print(f"  Selected {len(selected_names)} features (from {len(feature_names)})")
        print(f"  Top 10: {selected_names[:10]}")

        self.selected_features = selected_names
        return X_selected, selected_names

    def tune_hyperparameters(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[Any, Dict]:
        """
        Tune hyperparameters using cross-validation.

        Args:
            X: Feature matrix
            y: Target labels

        Returns:
            Best estimator and parameters
        """
        print(f"\nTuning hyperparameters using {self.training_config.tuning_method} search...")

        base_estimator = self.get_base_estimator(self.training_config.model_type)
        param_grid = self.get_param_grid(self.training_config.model_type)

        # Define scoring metrics
        scoring = {
            'roc_auc': 'roc_auc',
            'average_precision': 'average_precision',
            'brier': make_scorer(brier_score_loss, greater_is_better=False, needs_proba=True)
        }

        # Create cross-validation strategy
        cv = StratifiedKFold(
            n_splits=self.training_config.cv_folds,
            shuffle=True,
            random_state=self.training_config.random_state
        )

        # Perform hyperparameter search
        if self.training_config.tuning_method == 'grid':
            search = GridSearchCV(
                base_estimator,
                param_grid,
                scoring=scoring,
                refit='roc_auc',
                cv=cv,
                n_jobs=self.training_config.n_jobs,
                verbose=1,
                return_train_score=True
            )
        else:  # random search
            search = RandomizedSearchCV(
                base_estimator,
                param_grid,
                n_iter=self.training_config.n_iter_random,
                scoring=scoring,
                refit='roc_auc',
                cv=cv,
                n_jobs=self.training_config.n_jobs,
                verbose=1,
                random_state=self.training_config.random_state,
                return_train_score=True
            )

        search.fit(X, y)

        print(f"\nBest parameters:")
        for param, value in search.best_params_.items():
            print(f"  {param}: {value}")

        print(f"\nBest CV scores:")
        for metric in scoring.keys():
            score = search.cv_results_[f'mean_test_{metric}'][search.best_index_]
            std = search.cv_results_[f'std_test_{metric}'][search.best_index_]
            print(f"  {metric}: {score:.4f} (±{std:.4f})")

        # Store CV results
        self.cv_results = {
            'best_params': search.best_params_,
            'best_score': search.best_score_,
            'cv_results': pd.DataFrame(search.cv_results_)
        }

        return search.best_estimator_, search.best_params_

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: List[str]
    ) -> ECMORiskModel:
        """
        Complete training pipeline.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            feature_names: List of feature names

        Returns:
            Trained ECMORiskModel
        """
        print("="*60)
        print(f"Training {self.model_config.ecmo_mode} ECMO Risk Model")
        print("="*60)

        self.training_history['start_time'] = datetime.now().isoformat()

        # Step 1: Apply SMOTE if configured
        if self.training_config.use_smote:
            X_train_resampled, y_train_resampled = self.apply_smote(X_train, y_train)
        else:
            X_train_resampled, y_train_resampled = X_train, y_train

        # Step 2: Feature selection
        if self.training_config.use_feature_selection:
            X_train_selected, selected_features = self.select_features(
                X_train_resampled,
                y_train_resampled,
                feature_names
            )
            # Apply same selection to validation set
            selected_idx = [i for i, name in enumerate(feature_names) if name in selected_features]
            X_val_selected = X_val[:, selected_idx]
        else:
            X_train_selected = X_train_resampled
            X_val_selected = X_val
            selected_features = feature_names

        # Step 3: Hyperparameter tuning
        if self.training_config.tune_hyperparameters:
            best_estimator, best_params = self.tune_hyperparameters(
                X_train_selected,
                y_train_resampled
            )
            self.best_model = best_estimator
            self.best_params = best_params
        else:
            # Train with default parameters
            self.best_model = self.get_base_estimator(self.training_config.model_type)
            self.best_model.fit(X_train_selected, y_train_resampled)
            self.best_params = self.best_model.get_params()

        # Step 4: Evaluate on validation set
        print("\nValidation Set Performance:")
        y_val_pred = self.best_model.predict_proba(X_val_selected)[:, 1]

        val_metrics = {
            'roc_auc': roc_auc_score(y_val, y_val_pred),
            'average_precision': average_precision_score(y_val, y_val_pred),
            'brier_score': brier_score_loss(y_val, y_val_pred)
        }

        for metric, value in val_metrics.items():
            print(f"  {metric}: {value:.4f}")

        self.training_history['val_metrics'] = val_metrics

        # Step 5: Get feature importance
        if hasattr(self.best_model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': selected_features,
                'importance': self.best_model.feature_importances_
            }).sort_values('importance', ascending=False)

            print("\nTop 10 Most Important Features:")
            print(self.feature_importance.head(10).to_string(index=False))

        # Step 6: Create ECMORiskModel wrapper
        model = ECMORiskModel(self.model_config)
        model.model = self.best_model
        model.feature_names = selected_features

        # Apply calibration on validation set
        from sklearn.calibration import CalibratedClassifierCV
        print(f"\nApplying {self.model_config.calibration_method} calibration...")

        calibrated_model = CalibratedClassifierCV(
            self.best_model,
            method=self.model_config.calibration_method,
            cv='prefit'
        )
        calibrated_model.fit(X_val_selected, y_val)
        model.calibrated_model = calibrated_model

        self.training_history['end_time'] = datetime.now().isoformat()

        return model

    def save_model(self, model: ECMORiskModel, output_dir: str):
        """
        Save trained model and artifacts.

        Args:
            model: Trained ECMORiskModel
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        mode = self.model_config.ecmo_mode.lower()

        # Save model
        model_file = output_path / f"{mode}_risk_model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        print(f"\nModel saved to: {model_file}")

        # Save feature names
        feature_file = output_path / f"{mode}_feature_names.json"
        with open(feature_file, 'w') as f:
            json.dump(model.feature_names, f, indent=2)

        # Save feature importance
        if self.feature_importance is not None:
            importance_file = output_path / f"{mode}_feature_importance.csv"
            self.feature_importance.to_csv(importance_file, index=False)

        # Save best parameters
        params_file = output_path / f"{mode}_best_params.json"
        with open(params_file, 'w') as f:
            json.dump(self.best_params, f, indent=2)

        # Save training history
        history_file = output_path / f"{mode}_training_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.training_history, f, indent=2)

        # Save CV results
        if self.cv_results:
            cv_file = output_path / f"{mode}_cv_results.csv"
            self.cv_results['cv_results'].to_csv(cv_file, index=False)

        # Save training report
        self.generate_training_report(output_path / f"{mode}_training_report.txt")

    def generate_training_report(self, output_file: str):
        """
        Generate comprehensive training report.

        Args:
            output_file: Path to output report file
        """
        with open(output_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write(f"ECMO Risk Model Training Report\n")
            f.write(f"Mode: {self.model_config.ecmo_mode}\n")
            f.write("="*60 + "\n\n")

            f.write("Training Configuration:\n")
            f.write("-"*60 + "\n")
            for key, value in asdict(self.training_config).items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")

            f.write("Model Configuration:\n")
            f.write("-"*60 + "\n")
            for key, value in asdict(self.model_config).items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")

            if self.best_params:
                f.write("Best Hyperparameters:\n")
                f.write("-"*60 + "\n")
                for key, value in self.best_params.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

            if 'val_metrics' in self.training_history:
                f.write("Validation Metrics:\n")
                f.write("-"*60 + "\n")
                for key, value in self.training_history['val_metrics'].items():
                    f.write(f"  {key}: {value:.4f}\n")
                f.write("\n")

            if self.feature_importance is not None:
                f.write("Top 20 Most Important Features:\n")
                f.write("-"*60 + "\n")
                f.write(self.feature_importance.head(20).to_string(index=False))
                f.write("\n\n")

            if self.selected_features:
                f.write(f"Total Features Selected: {len(self.selected_features)}\n")
                f.write("-"*60 + "\n")
                for i, feature in enumerate(self.selected_features, 1):
                    f.write(f"  {i}. {feature}\n")

        print(f"Training report saved to: {output_file}")


def load_model(model_path: str) -> ECMORiskModel:
    """
    Load trained model from disk.

    Args:
        model_path: Path to pickled model file

    Returns:
        Loaded ECMORiskModel
    """
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def train_va_vv_models(
    data_loader: MIMICDataLoader,
    training_config: TrainingConfig,
    output_dir: str
) -> Dict[str, ECMORiskModel]:
    """
    Train both VA and VV ECMO risk models.

    Args:
        data_loader: MIMICDataLoader with prepared data
        training_config: Training configuration
        output_dir: Output directory for models

    Returns:
        Dictionary of trained models
    """
    models = {}

    for mode in ['VA', 'VV']:
        if mode not in data_loader.processed_data:
            print(f"\nSkipping {mode} mode - no data available")
            continue

        print(f"\n{'='*60}")
        print(f"Training {mode} ECMO Model")
        print(f"{'='*60}\n")

        # Get data splits
        train_data = data_loader.processed_data[mode]['train']
        val_data = data_loader.processed_data[mode]['val']

        # Create model config
        model_config = ModelConfig(
            ecmo_mode=mode,
            target='survival_to_discharge',
            handle_imbalance=training_config.use_class_weights,
            calibration_method='isotonic'
        )

        # Create trainer
        trainer = ECMOModelTrainer(training_config, model_config)

        # Train model
        model = trainer.train(
            X_train=train_data['X'].values,
            y_train=train_data['y'].values,
            X_val=val_data['X'].values,
            y_val=val_data['y'].values,
            feature_names=data_loader.get_feature_names()
        )

        # Save model
        trainer.save_model(model, output_dir)

        models[mode] = model

    return models


# Example usage
if __name__ == '__main__':
    # Example: Train models from preprocessed data
    from data_loader import MIMICDataLoader, DataConfig

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

    print(f"\n{'='*60}")
    print("Training Complete!")
    print(f"{'='*60}")
    print(f"Models saved to: models/ecmo_risk")
