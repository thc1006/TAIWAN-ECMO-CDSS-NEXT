"""
NIRS + EHR Risk Models for ECMO Outcomes
Taiwan ECMO CDSS - Near-infrared spectroscopy integrated risk prediction

Separate models for VA-ECMO (cardiac) and VV-ECMO (respiratory) patients
with model calibration and explainable AI features
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import roc_auc_score, brier_score_loss, roc_curve, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import joblib
import logging
from typing import Dict, Tuple, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NIRSECMORiskModel:
    """
    NIRS-enhanced ECMO risk prediction model
    Separate models for VA-ECMO and VV-ECMO with calibration
    """
    
    def __init__(self, ecmo_type: str = 'VA'):
        """
        Initialize risk model
        
        Args:
            ecmo_type: 'VA' for veno-arterial or 'VV' for veno-venous
        """
        self.ecmo_type = ecmo_type
        self.model = None
        self.calibrated_model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.shap_explainer = None
        
        # Risk model features specific to ECMO type
        self.va_features = [
            'age_years', 'weight_kg', 'bmi',
            'pre_ecmo_lactate', 'pre_ecmo_ph', 'pre_ecmo_pco2', 'pre_ecmo_po2',
            'cardiac_arrest', 'cpr_duration_min', 'inotrope_score',
            'cerebral_so2_baseline', 'renal_so2_baseline', 'somatic_so2_baseline',
            'cerebral_so2_min_24h', 'renal_so2_min_24h', 'somatic_so2_min_24h',
            'nirs_trend_cerebral', 'nirs_trend_renal', 'nirs_variability',
            'creatinine_pre', 'bilirubin_pre', 'platelet_count_pre',
            'lvef_pre_ecmo', 'mitral_regurg_severity', 'aortic_regurg_severity'
        ]
        
        self.vv_features = [
            'age_years', 'weight_kg', 'bmi', 
            'pre_ecmo_ph', 'pre_ecmo_pco2', 'pre_ecmo_po2', 'pre_ecmo_fio2',
            'murray_score', 'peep_level', 'plateau_pressure',
            'prone_positioning', 'neuromuscular_blockade',
            'cerebral_so2_baseline', 'renal_so2_baseline', 'somatic_so2_baseline',
            'cerebral_so2_min_24h', 'renal_so2_min_24h', 'somatic_so2_min_24h',
            'nirs_trend_cerebral', 'nirs_trend_renal', 'nirs_variability',
            'immunocompromised', 'chronic_lung_disease', 'pneumonia_type',
            'resp_compliance', 'driving_pressure', 'oxygenation_index'
        ]
        
        self.features = self.va_features if ecmo_type == 'VA' else self.vv_features
        logger.info(f"Initialized {ecmo_type}-ECMO risk model with {len(self.features)} features")
    
    def prepare_nirs_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate NIRS-derived features
        
        Args:
            data: Raw NIRS and clinical data
            
        Returns:
            DataFrame with calculated NIRS features
        """
        logger.info("Calculating NIRS-derived features")
        
        nirs_data = data.copy()
        
        # NIRS trend calculations (slope over first 24 hours)
        for site in ['cerebral', 'renal', 'somatic']:
            col = f'{site}_so2'
            if col in nirs_data.columns:
                # Mock trend calculation - in practice, this would use time series data
                baseline = nirs_data[f'{site}_so2_baseline']
                min_24h = nirs_data[f'{site}_so2_min_24h']
                nirs_data[f'nirs_trend_{site}'] = min_24h - baseline
        
        # NIRS variability (coefficient of variation)
        cerebral_baseline = nirs_data.get('cerebral_so2_baseline', 70)
        cerebral_min = nirs_data.get('cerebral_so2_min_24h', 60)
        nirs_data['nirs_variability'] = np.abs(cerebral_baseline - cerebral_min) / cerebral_baseline
        
        # NIRS adequacy score (composite)
        nirs_data['nirs_adequacy_score'] = (
            (nirs_data.get('cerebral_so2_baseline', 70) * 0.5) +
            (nirs_data.get('renal_so2_baseline', 75) * 0.3) +  
            (nirs_data.get('somatic_so2_baseline', 70) * 0.2)
        ) / 100
        
        return nirs_data
    
    def calculate_risk_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate existing ECMO risk scores for comparison
        
        Args:
            data: Clinical data
            
        Returns:
            DataFrame with risk scores
        """
        result_data = data.copy()
        
        if self.ecmo_type == 'VA':
            # SAVE-II Score (simplified)
            save_score = pd.Series(0, index=data.index)
            
            # Age component
            if 'age_years' in data.columns:
                save_score += np.where(data['age_years'] > 38, -2, 0)
                save_score += np.where(data['age_years'] > 53, -2, 0)
            
            # Weight component  
            if 'weight_kg' in data.columns:
                save_score += np.where(data['weight_kg'] < 65, -3, 0)
            
            # Cardiac arrest
            if 'cardiac_arrest' in data.columns:
                save_score += np.where(data['cardiac_arrest'] == True, -2, 0)
            
            # Pre-ECMO bicarbonate (if available)
            if 'bicarbonate_pre' in data.columns:
                save_score += np.where(data['bicarbonate_pre'] < 15, -3, 0)
            
            result_data['save_ii_score'] = save_score
            
        elif self.ecmo_type == 'VV':
            # RESP Score (simplified)
            resp_score = pd.Series(0, index=data.index)
            
            # Age component
            if 'age_years' in data.columns:
                resp_score += np.where(data['age_years'].between(18, 49), 0, -2)
                resp_score += np.where(data['age_years'] >= 60, -3, 0)
            
            # Immunocompromised status
            if 'immunocompromised' in data.columns:
                resp_score += np.where(data['immunocompromised'] == True, -2, 0)
            
            # Mechanical ventilation duration
            if 'vent_duration_pre_ecmo' in data.columns:
                resp_score += np.where(data['vent_duration_pre_ecmo'] > 7, -1, 0)
            
            result_data['resp_score'] = resp_score
        
        return result_data
    
    def train_model(self, X: pd.DataFrame, y: pd.Series, 
                   validation_split: float = 0.2) -> Dict:
        """
        Train the NIRS-enhanced ECMO risk model
        
        Args:
            X: Feature matrix
            y: Target variable (survival outcome)
            validation_split: Fraction for validation set
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training {self.ecmo_type}-ECMO risk model on {len(X)} patients")
        
        # Prepare NIRS features
        X_enhanced = self.prepare_nirs_features(X)
        X_enhanced = self.calculate_risk_scores(X_enhanced)
        
        # Select features available in the data
        available_features = [f for f in self.features if f in X_enhanced.columns]
        self.feature_names = available_features
        logger.info(f"Using {len(available_features)} available features")
        
        X_model = X_enhanced[available_features]
        
        # Handle missing values
        X_model = X_model.fillna(X_model.median())
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_model, y, test_size=validation_split, 
            random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train ensemble model
        models = {
            'logistic': LogisticRegression(random_state=42, max_iter=1000),
            'rf': RandomForestClassifier(n_estimators=100, random_state=42),
            'gbm': GradientBoostingClassifier(random_state=42)
        }
        
        model_scores = {}
        for name, model in models.items():
            if name == 'logistic':
                model.fit(X_train_scaled, y_train)
                score = roc_auc_score(y_val, model.predict_proba(X_val_scaled)[:, 1])
            else:
                model.fit(X_train, y_train)
                score = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
            
            model_scores[name] = score
            logger.info(f"{name} model AUC: {score:.3f}")
        
        # Select best model
        best_model_name = max(model_scores, key=model_scores.get)
        self.model = models[best_model_name]
        logger.info(f"Selected {best_model_name} as best model (AUC: {model_scores[best_model_name]:.3f})")
        
        # Calibrate the model
        if best_model_name == 'logistic':
            self.calibrated_model = CalibratedClassifierCV(
                self.model, method='isotonic', cv=3
            )
            self.calibrated_model.fit(X_train_scaled, y_train)
            val_probs = self.calibrated_model.predict_proba(X_val_scaled)[:, 1]
        else:
            self.calibrated_model = CalibratedClassifierCV(
                self.model, method='isotonic', cv=3  
            )
            self.calibrated_model.fit(X_train, y_train)
            val_probs = self.calibrated_model.predict_proba(X_val)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_val, val_probs)
        brier_score = brier_score_loss(y_val, val_probs)
        
        # Setup SHAP explainer
        try:
            if best_model_name == 'logistic':
                self.shap_explainer = shap.LinearExplainer(
                    self.calibrated_model.calibrated_classifiers_[0].base_estimator,
                    X_train_scaled
                )
            else:
                # For tree-based models
                self.shap_explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")
        
        metrics = {
            'model_type': best_model_name,
            'auc_score': auc_score,
            'brier_score': brier_score,
            'n_features': len(available_features),
            'n_train': len(X_train),
            'n_val': len(X_val)
        }
        
        logger.info(f"Model training complete. AUC: {auc_score:.3f}, Brier: {brier_score:.3f}")
        
        return metrics
    
    def predict_risk(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict survival risk for new patients
        
        Args:
            X: Feature matrix for new patients
            
        Returns:
            Array of predicted survival probabilities
        """
        if self.calibrated_model is None:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Prepare features
        X_enhanced = self.prepare_nirs_features(X)
        X_enhanced = self.calculate_risk_scores(X_enhanced)
        X_model = X_enhanced[self.feature_names].fillna(X_enhanced.median())
        
        # Scale if using logistic regression
        if hasattr(self.calibrated_model.calibrated_classifiers_[0].base_estimator, 'coef_'):
            X_model = self.scaler.transform(X_model)
        
        return self.calibrated_model.predict_proba(X_model)[:, 1]
    
    def explain_prediction(self, X: pd.DataFrame, patient_idx: int = 0) -> Dict:
        """
        Explain individual patient risk prediction using SHAP
        
        Args:
            X: Feature matrix
            patient_idx: Index of patient to explain
            
        Returns:
            Dictionary with explanation data
        """
        if self.shap_explainer is None:
            logger.warning("SHAP explainer not available")
            return {}
        
        # Prepare features
        X_enhanced = self.prepare_nirs_features(X)
        X_model = X_enhanced[self.feature_names].fillna(X_enhanced.median())
        
        # Scale if needed
        if hasattr(self.calibrated_model.calibrated_classifiers_[0].base_estimator, 'coef_'):
            X_model = self.scaler.transform(X_model)
        
        # Calculate SHAP values
        try:
            shap_values = self.shap_explainer.shap_values(X_model[patient_idx:patient_idx+1])
            
            if isinstance(shap_values, list):  # Binary classification
                shap_values = shap_values[1]
            
            explanation = {
                'shap_values': shap_values[0],
                'feature_names': self.feature_names,
                'feature_values': X_model.iloc[patient_idx].values,
                'base_value': self.shap_explainer.expected_value,
                'predicted_risk': self.predict_risk(X.iloc[patient_idx:patient_idx+1])[0]
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {}
    
    def plot_calibration(self, X_val: pd.DataFrame, y_val: pd.Series):
        """
        Plot model calibration curve
        
        Args:
            X_val: Validation features
            y_val: Validation outcomes
        """
        y_prob = self.predict_risk(X_val)
        
        plt.figure(figsize=(10, 6))
        
        # Calibration plot
        plt.subplot(1, 2, 1)
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_val, y_prob, n_bins=10, normalize=False
        )
        
        plt.plot(mean_predicted_value, fraction_of_positives, "s-", 
                label=f"{self.ecmo_type}-ECMO Model")
        plt.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
        plt.xlabel("Mean Predicted Probability")
        plt.ylabel("Fraction of Positives")
        plt.title(f"{self.ecmo_type}-ECMO Model Calibration")
        plt.legend()
        
        # ROC curve
        plt.subplot(1, 2, 2)
        fpr, tpr, _ = roc_curve(y_val, y_prob)
        auc = roc_auc_score(y_val, y_prob)
        
        plt.plot(fpr, tpr, label=f"ROC curve (AUC = {auc:.3f})")
        plt.plot([0, 1], [0, 1], "k--", label="Random classifier")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"{self.ecmo_type}-ECMO Model ROC")
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f'{self.ecmo_type.lower()}_ecmo_calibration.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_model(self, filepath: str):
        """Save trained model"""
        model_data = {
            'ecmo_type': self.ecmo_type,
            'model': self.calibrated_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'shap_explainer': self.shap_explainer
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        model_data = joblib.load(filepath)
        self.ecmo_type = model_data['ecmo_type']
        self.calibrated_model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.shap_explainer = model_data['shap_explainer']
        logger.info(f"Model loaded from {filepath}")


def generate_demo_data(n_patients: int = 1000, ecmo_type: str = 'VA') -> pd.DataFrame:
    """
    Generate demo ECMO patient data for model development
    
    Args:
        n_patients: Number of patients to generate
        ecmo_type: ECMO type ('VA' or 'VV')
        
    Returns:
        DataFrame with demo patient data
    """
    np.random.seed(42)
    
    data = {
        'patient_id': [f'PT{i:04d}' for i in range(n_patients)],
        'age_years': np.random.normal(55, 15, n_patients).clip(18, 85),
        'weight_kg': np.random.normal(75, 15, n_patients).clip(40, 150),
        'bmi': np.random.normal(25, 5, n_patients).clip(15, 45),
    }
    
    # Add NIRS data
    data.update({
        'cerebral_so2_baseline': np.random.normal(70, 10, n_patients).clip(40, 90),
        'renal_so2_baseline': np.random.normal(75, 8, n_patients).clip(50, 90),
        'somatic_so2_baseline': np.random.normal(70, 8, n_patients).clip(45, 85),
        'cerebral_so2_min_24h': np.random.normal(65, 12, n_patients).clip(30, 85),
        'renal_so2_min_24h': np.random.normal(70, 10, n_patients).clip(40, 85),
        'somatic_so2_min_24h': np.random.normal(65, 10, n_patients).clip(35, 80),
    })
    
    # Add clinical variables based on ECMO type
    if ecmo_type == 'VA':
        data.update({
            'cardiac_arrest': np.random.choice([True, False], n_patients, p=[0.4, 0.6]),
            'cpr_duration_min': np.random.exponential(20, n_patients).clip(0, 120),
            'pre_ecmo_lactate': np.random.exponential(3, n_patients).clip(0.5, 20),
            'lvef_pre_ecmo': np.random.normal(30, 15, n_patients).clip(10, 60),
        })
    else:  # VV
        data.update({
            'murray_score': np.random.normal(3.0, 0.5, n_patients).clip(2.0, 4.0),
            'peep_level': np.random.normal(12, 4, n_patients).clip(5, 25),
            'immunocompromised': np.random.choice([True, False], n_patients, p=[0.3, 0.7]),
            'prone_positioning': np.random.choice([True, False], n_patients, p=[0.6, 0.4]),
        })
    
    # Common variables
    data.update({
        'pre_ecmo_ph': np.random.normal(7.25, 0.15, n_patients).clip(6.8, 7.6),
        'pre_ecmo_pco2': np.random.normal(50, 15, n_patients).clip(20, 100),
        'pre_ecmo_po2': np.random.normal(80, 25, n_patients).clip(30, 150),
        'creatinine_pre': np.random.exponential(1.5, n_patients).clip(0.5, 8),
        'platelet_count_pre': np.random.normal(200, 80, n_patients).clip(20, 500),
    })
    
    df = pd.DataFrame(data)
    
    # Generate survival outcome (simplified risk model)
    risk_factors = (
        (df['age_years'] - 50) * 0.02 +  # Age effect
        (df['cerebral_so2_baseline'] - 70) * -0.03 +  # NIRS effect
        (df['pre_ecmo_lactate'] - 2) * 0.1 +  # Lactate effect
        np.random.normal(0, 0.5, n_patients)  # Random variation
    )
    
    survival_prob = 1 / (1 + np.exp(risk_factors))  # Logistic function
    df['survived_to_discharge'] = np.random.binomial(1, survival_prob, n_patients)
    
    return df


if __name__ == "__main__":
    # Demo usage
    logger.info("NIRS-Enhanced ECMO Risk Models Demo")
    
    # Generate demo data for both VA and VV ECMO
    va_data = generate_demo_data(500, 'VA')
    vv_data = generate_demo_data(500, 'VV')
    
    # Train VA-ECMO model
    va_model = NIRSECMORiskModel('VA')
    X_va = va_data.drop(['patient_id', 'survived_to_discharge'], axis=1)
    y_va = va_data['survived_to_discharge']
    va_metrics = va_model.train_model(X_va, y_va)
    logger.info(f"VA-ECMO model metrics: {va_metrics}")
    
    # Train VV-ECMO model  
    vv_model = NIRSECMORiskModel('VV')
    X_vv = vv_data.drop(['patient_id', 'survived_to_discharge'], axis=1)
    y_vv = vv_data['survived_to_discharge']
    vv_metrics = vv_model.train_model(X_vv, y_vv)
    logger.info(f"VV-ECMO model metrics: {vv_metrics}")
    
    # Save models
    va_model.save_model('va_ecmo_nirs_model.pkl')
    vv_model.save_model('vv_ecmo_nirs_model.pkl')
    
    logger.info("NIRS-Enhanced ECMO Risk Models training complete")