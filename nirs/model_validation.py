"""
Model Validation and Explainability for ECMO Risk Models
Includes calibration plots, decision curve analysis, SHAP, and subgroup analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    roc_curve, precision_recall_curve, calibration_curve,
    confusion_matrix, classification_report
)
from sklearn.calibration import calibration_curve
import warnings

# Optional SHAP import
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    warnings.warn("SHAP not available. Install with: pip install shap")


@dataclass
class ValidationConfig:
    """Configuration for model validation."""
    # Calibration
    n_calibration_bins: int = 10
    calibration_strategy: str = 'quantile'  # 'uniform' or 'quantile'

    # Decision curve analysis
    threshold_range: Tuple[float, float] = (0.0, 1.0)
    threshold_step: float = 0.01

    # Bootstrap
    n_bootstrap: int = 1000
    bootstrap_ci: float = 0.95

    # SHAP
    use_shap: bool = True
    shap_sample_size: int = 100  # For efficiency

    # Output
    save_plots: bool = True
    plot_dir: str = 'validation_plots'
    dpi: int = 300


class ModelValidator:
    """
    Comprehensive model validation for ECMO risk models.

    Features:
    - Discrimination metrics (AUROC, AUPRC)
    - Calibration plots and metrics
    - Decision curve analysis
    - Bootstrap confidence intervals
    - SHAP-based explainability
    - Subgroup analysis
    """

    def __init__(self, config: ValidationConfig):
        self.config = config
        self.results = {}

    def calculate_discrimination_metrics(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate discrimination metrics.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities

        Returns:
            Dictionary of metrics
        """
        if len(np.unique(y_true)) < 2:
            return {
                'auroc': np.nan,
                'auprc': np.nan,
                'brier_score': np.nan
            }

        metrics = {
            'auroc': roc_auc_score(y_true, y_pred_proba),
            'auprc': average_precision_score(y_true, y_pred_proba),
            'brier_score': brier_score_loss(y_true, y_pred_proba)
        }

        return metrics

    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        title: str = 'ROC Curve',
        save_path: Optional[str] = None
    ):
        """
        Plot ROC curve.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            title: Plot title
            save_path: Path to save plot
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        auroc = roc_auc_score(y_true, y_pred_proba)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f'AUROC = {auroc:.3f}')
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(loc='lower right', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_precision_recall_curve(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        title: str = 'Precision-Recall Curve',
        save_path: Optional[str] = None
    ):
        """
        Plot precision-recall curve.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            title: Plot title
            save_path: Path to save plot
        """
        precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
        auprc = average_precision_score(y_true, y_pred_proba)

        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, linewidth=2, label=f'AUPRC = {auprc:.3f}')
        plt.axhline(y=y_true.mean(), color='k', linestyle='--', linewidth=1,
                   label=f'Baseline = {y_true.mean():.3f}')
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(loc='best', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_calibration_curve(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        title: str = 'Calibration Plot',
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot calibration curve (reliability diagram).

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            title: Plot title
            save_path: Path to save plot

        Returns:
            Dictionary with calibration metrics
        """
        try:
            prob_true, prob_pred = calibration_curve(
                y_true,
                y_pred_proba,
                n_bins=self.config.n_calibration_bins,
                strategy=self.config.calibration_strategy
            )

            # Calculate Expected Calibration Error (ECE)
            bin_edges = np.linspace(0, 1, self.config.n_calibration_bins + 1)
            bin_counts = np.histogram(y_pred_proba, bins=bin_edges)[0]
            bin_weights = bin_counts / len(y_pred_proba)

            # Pad if needed
            if len(prob_true) < len(bin_weights):
                prob_true_padded = np.pad(prob_true, (0, len(bin_weights) - len(prob_true)), constant_values=np.nan)
                prob_pred_padded = np.pad(prob_pred, (0, len(bin_weights) - len(prob_pred)), constant_values=np.nan)
            else:
                prob_true_padded = prob_true[:len(bin_weights)]
                prob_pred_padded = prob_pred[:len(bin_weights)]

            ece = np.nansum(bin_weights * np.abs(prob_true_padded - prob_pred_padded))

            # Plot
            plt.figure(figsize=(8, 8))
            plt.plot(prob_pred, prob_true, 'o-', linewidth=2, markersize=8, label='Model')
            plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect calibration')
            plt.xlabel('Predicted Probability', fontsize=12)
            plt.ylabel('Observed Frequency', fontsize=12)
            plt.title(f'{title}\nECE = {ece:.4f}', fontsize=14, fontweight='bold')
            plt.legend(loc='upper left', fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.xlim([0, 1])
            plt.ylim([0, 1])
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
                plt.close()
            else:
                plt.show()

            return {
                'ece': ece,
                'prob_true': prob_true.tolist(),
                'prob_pred': prob_pred.tolist()
            }

        except Exception as e:
            warnings.warn(f"Calibration plot failed: {e}")
            return {'ece': np.nan}

    def decision_curve_analysis(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        title: str = 'Decision Curve Analysis',
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Perform decision curve analysis.

        Decision curves show net benefit across risk thresholds,
        helping to evaluate clinical utility of the model.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            title: Plot title
            save_path: Path to save plot

        Returns:
            DataFrame with net benefits at each threshold
        """
        thresholds = np.arange(
            self.config.threshold_range[0],
            self.config.threshold_range[1],
            self.config.threshold_step
        )

        net_benefits = []
        prevalence = y_true.mean()

        for threshold in thresholds:
            # Model predictions
            y_pred = (y_pred_proba >= threshold).astype(int)

            # True positives and false positives
            tp = np.sum((y_pred == 1) & (y_true == 1))
            fp = np.sum((y_pred == 1) & (y_true == 0))
            n = len(y_true)

            # Net benefit = (TP - FP * (threshold/(1-threshold))) / N
            if threshold == 1:
                nb = 0
            else:
                nb = (tp - fp * (threshold / (1 - threshold))) / n

            net_benefits.append({
                'threshold': threshold,
                'net_benefit': nb,
                'treat_all': prevalence - (1 - prevalence) * (threshold / (1 - threshold)) if threshold < 1 else 0,
                'treat_none': 0
            })

        df_results = pd.DataFrame(net_benefits)

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(df_results['threshold'], df_results['net_benefit'],
                linewidth=2, label='Model', color='blue')
        plt.plot(df_results['threshold'], df_results['treat_all'],
                linewidth=2, linestyle='--', label='Treat All', color='gray')
        plt.plot(df_results['threshold'], df_results['treat_none'],
                linewidth=1, linestyle=':', label='Treat None', color='black')
        plt.xlabel('Threshold Probability', fontsize=12)
        plt.ylabel('Net Benefit', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(loc='best', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.xlim([0, 1])
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

        return df_results

    def bootstrap_confidence_intervals(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        metrics: List[str] = ['auroc', 'auprc', 'brier_score']
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate bootstrap confidence intervals for metrics.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            metrics: List of metrics to bootstrap

        Returns:
            Dictionary with CI for each metric
        """
        print(f"Computing bootstrap confidence intervals ({self.config.n_bootstrap} iterations)...")

        n_samples = len(y_true)
        bootstrap_scores = {metric: [] for metric in metrics}

        for i in range(self.config.n_bootstrap):
            # Bootstrap sample
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            y_boot = y_true[indices]
            y_pred_boot = y_pred_proba[indices]

            # Calculate metrics
            if len(np.unique(y_boot)) < 2:
                continue

            for metric in metrics:
                if metric == 'auroc':
                    score = roc_auc_score(y_boot, y_pred_boot)
                elif metric == 'auprc':
                    score = average_precision_score(y_boot, y_pred_boot)
                elif metric == 'brier_score':
                    score = brier_score_loss(y_boot, y_pred_boot)
                else:
                    continue

                bootstrap_scores[metric].append(score)

        # Calculate confidence intervals
        alpha = 1 - self.config.bootstrap_ci
        results = {}

        for metric, scores in bootstrap_scores.items():
            if len(scores) == 0:
                continue

            scores = np.array(scores)
            results[metric] = {
                'mean': np.mean(scores),
                'std': np.std(scores),
                'ci_lower': np.percentile(scores, alpha/2 * 100),
                'ci_upper': np.percentile(scores, (1 - alpha/2) * 100)
            }

        return results

    def shap_analysis(
        self,
        model: Any,
        X: pd.DataFrame,
        feature_names: List[str],
        sample_size: Optional[int] = None,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform SHAP analysis for model explainability.

        Args:
            model: Trained model
            X: Feature matrix
            feature_names: List of feature names
            sample_size: Number of samples for SHAP (for efficiency)
            save_path: Directory to save SHAP plots

        Returns:
            Dictionary with SHAP values and importance
        """
        if not SHAP_AVAILABLE:
            warnings.warn("SHAP not available. Skipping SHAP analysis.")
            return {}

        print("Performing SHAP analysis...")

        # Sample data for efficiency
        if sample_size is None:
            sample_size = self.config.shap_sample_size

        if len(X) > sample_size:
            indices = np.random.choice(len(X), size=sample_size, replace=False)
            X_sample = X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]
        else:
            X_sample = X

        try:
            # Create SHAP explainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            # For binary classification, use positive class
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            # Summary plot
            if save_path:
                save_dir = Path(save_path)
                save_dir.mkdir(parents=True, exist_ok=True)

                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, feature_names=feature_names, show=False)
                plt.tight_layout()
                plt.savefig(save_dir / 'shap_summary.png', dpi=self.config.dpi, bbox_inches='tight')
                plt.close()

                # Feature importance plot
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, feature_names=feature_names,
                                plot_type='bar', show=False)
                plt.tight_layout()
                plt.savefig(save_dir / 'shap_importance.png', dpi=self.config.dpi, bbox_inches='tight')
                plt.close()

            # Calculate mean absolute SHAP values
            mean_shap = np.abs(shap_values).mean(axis=0)
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'shap_importance': mean_shap
            }).sort_values('shap_importance', ascending=False)

            return {
                'shap_values': shap_values,
                'importance': importance_df,
                'explainer': explainer
            }

        except Exception as e:
            warnings.warn(f"SHAP analysis failed: {e}")
            return {}

    def subgroup_analysis(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        subgroup_var: np.ndarray,
        subgroup_name: str = 'Subgroup'
    ) -> pd.DataFrame:
        """
        Perform subgroup analysis.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            subgroup_var: Subgroup variable (e.g., age groups, diagnosis)
            subgroup_name: Name of subgroup variable

        Returns:
            DataFrame with performance metrics by subgroup
        """
        print(f"Performing subgroup analysis by {subgroup_name}...")

        results = []

        for subgroup in np.unique(subgroup_var):
            mask = (subgroup_var == subgroup)

            if mask.sum() < 10:  # Skip small groups
                continue

            y_sub = y_true[mask]
            y_pred_sub = y_pred_proba[mask]

            if len(np.unique(y_sub)) < 2:
                continue

            metrics = self.calculate_discrimination_metrics(y_sub, y_pred_sub)
            metrics['subgroup'] = subgroup
            metrics['n'] = mask.sum()
            metrics['prevalence'] = y_sub.mean()

            results.append(metrics)

        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('auroc', ascending=False)

        print(f"\nSubgroup Analysis Results ({subgroup_name}):")
        print(df_results.to_string(index=False))

        return df_results

    def validate_model(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        X: Optional[pd.DataFrame] = None,
        model: Optional[Any] = None,
        feature_names: Optional[List[str]] = None,
        subgroups: Optional[Dict[str, np.ndarray]] = None,
        model_name: str = 'ECMO Risk Model'
    ) -> Dict[str, Any]:
        """
        Complete validation pipeline.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            X: Feature matrix (for SHAP)
            model: Trained model (for SHAP)
            feature_names: List of feature names
            subgroups: Dictionary of subgroup variables
            model_name: Model name for plots

        Returns:
            Dictionary with all validation results
        """
        print("="*60)
        print(f"Model Validation: {model_name}")
        print("="*60)

        results = {'model_name': model_name}

        # Setup output directory
        if self.config.save_plots:
            plot_dir = Path(self.config.plot_dir) / model_name.lower().replace(' ', '_')
            plot_dir.mkdir(parents=True, exist_ok=True)
        else:
            plot_dir = None

        # 1. Discrimination metrics
        print("\n1. Computing discrimination metrics...")
        results['discrimination'] = self.calculate_discrimination_metrics(y_true, y_pred_proba)

        for metric, value in results['discrimination'].items():
            print(f"   {metric}: {value:.4f}")

        # 2. ROC curve
        print("\n2. Generating ROC curve...")
        roc_path = plot_dir / 'roc_curve.png' if plot_dir else None
        self.plot_roc_curve(y_true, y_pred_proba, title=f'{model_name} - ROC Curve', save_path=roc_path)

        # 3. Precision-Recall curve
        print("\n3. Generating Precision-Recall curve...")
        pr_path = plot_dir / 'precision_recall.png' if plot_dir else None
        self.plot_precision_recall_curve(y_true, y_pred_proba, title=f'{model_name} - PR Curve', save_path=pr_path)

        # 4. Calibration
        print("\n4. Assessing calibration...")
        cal_path = plot_dir / 'calibration.png' if plot_dir else None
        results['calibration'] = self.plot_calibration_curve(
            y_true, y_pred_proba, title=f'{model_name} - Calibration', save_path=cal_path
        )
        print(f"   ECE: {results['calibration'].get('ece', np.nan):.4f}")

        # 5. Decision curve analysis
        print("\n5. Performing decision curve analysis...")
        dca_path = plot_dir / 'decision_curve.png' if plot_dir else None
        results['decision_curve'] = self.decision_curve_analysis(
            y_true, y_pred_proba, title=f'{model_name} - DCA', save_path=dca_path
        )

        # 6. Bootstrap confidence intervals
        print("\n6. Computing bootstrap confidence intervals...")
        results['bootstrap_ci'] = self.bootstrap_confidence_intervals(y_true, y_pred_proba)

        for metric, ci_dict in results['bootstrap_ci'].items():
            print(f"   {metric}: {ci_dict['mean']:.4f} ({ci_dict['ci_lower']:.4f}-{ci_dict['ci_upper']:.4f})")

        # 7. SHAP analysis
        if self.config.use_shap and model is not None and X is not None and feature_names is not None:
            print("\n7. Performing SHAP analysis...")
            shap_dir = plot_dir / 'shap' if plot_dir else None
            results['shap'] = self.shap_analysis(model, X, feature_names, save_path=shap_dir)

        # 8. Subgroup analysis
        if subgroups is not None:
            print("\n8. Performing subgroup analyses...")
            results['subgroups'] = {}

            for subgroup_name, subgroup_var in subgroups.items():
                results['subgroups'][subgroup_name] = self.subgroup_analysis(
                    y_true, y_pred_proba, subgroup_var, subgroup_name
                )

        print("\n" + "="*60)
        print("Validation Complete!")
        print("="*60)

        return results


# Utility function
def compare_models(
    models_dict: Dict[str, Tuple[np.ndarray, np.ndarray]],
    save_path: Optional[str] = None
):
    """
    Compare multiple models on the same plot.

    Args:
        models_dict: Dictionary of {model_name: (y_true, y_pred_proba)}
        save_path: Path to save comparison plot
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # ROC curves
    for model_name, (y_true, y_pred) in models_dict.items():
        fpr, tpr, _ = roc_curve(y_true, y_pred)
        auroc = roc_auc_score(y_true, y_pred)
        axes[0].plot(fpr, tpr, linewidth=2, label=f'{model_name} (AUROC={auroc:.3f})')

    axes[0].plot([0, 1], [0, 1], 'k--', linewidth=1)
    axes[0].set_xlabel('False Positive Rate', fontsize=12)
    axes[0].set_ylabel('True Positive Rate', fontsize=12)
    axes[0].set_title('ROC Curves Comparison', fontsize=14, fontweight='bold')
    axes[0].legend(loc='lower right', fontsize=10)
    axes[0].grid(True, alpha=0.3)

    # Precision-Recall curves
    for model_name, (y_true, y_pred) in models_dict.items():
        precision, recall, _ = precision_recall_curve(y_true, y_pred)
        auprc = average_precision_score(y_true, y_pred)
        axes[1].plot(recall, precision, linewidth=2, label=f'{model_name} (AUPRC={auprc:.3f})')

    axes[1].set_xlabel('Recall', fontsize=12)
    axes[1].set_ylabel('Precision', fontsize=12)
    axes[1].set_title('Precision-Recall Curves Comparison', fontsize=14, fontweight='bold')
    axes[1].legend(loc='best', fontsize=10)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


# Example usage
if __name__ == '__main__':
    # Example validation
    config = ValidationConfig(
        n_calibration_bins=10,
        n_bootstrap=1000,
        use_shap=True,
        save_plots=True,
        plot_dir='validation_results'
    )

    validator = ModelValidator(config)

    # Dummy data for demonstration
    np.random.seed(42)
    n_samples = 500
    y_true = np.random.binomial(1, 0.3, n_samples)
    y_pred_proba = np.random.beta(2, 5, n_samples)

    # Run validation
    results = validator.validate_model(
        y_true=y_true,
        y_pred_proba=y_pred_proba,
        model_name='Example ECMO Model'
    )
