"""
Data Integration for Cost-Effectiveness Analysis (WP2)

Loads and integrates:
- Patient data from MIMIC-IV or SQL results
- Risk stratification from nirs/risk_models.py
- Cost and outcome metrics
- Risk quintile assignment

Supports both real data and synthetic data for testing.
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import warnings

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ECMODataIntegrator:
    """
    Integrates ECMO patient data with risk predictions and cost metrics.

    Workflow:
    1. Load patient data (from SQL, CSV, or synthetic)
    2. Load risk predictions from NIRS models
    3. Assign risk quintiles
    4. Merge with cost data
    5. Prepare for CEA analysis
    """

    def __init__(self, data_source: str = "synthetic"):
        """
        Initialize data integrator.

        Args:
            data_source: Source of data ('synthetic', 'csv', 'sql', 'mimic')
        """
        self.data_source = data_source
        self.patient_data = None
        self.risk_predictions = None
        self.integrated_data = None

    def load_patient_data(
        self,
        file_path: Optional[str] = None,
        sql_query: Optional[str] = None,
        connection_string: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load patient data from various sources.

        Args:
            file_path: Path to CSV file (if data_source='csv')
            sql_query: SQL query (if data_source='sql')
            connection_string: Database connection (if data_source='sql')

        Returns:
            DataFrame with patient data
        """
        if self.data_source == "synthetic":
            print("Generating synthetic patient data...")
            self.patient_data = self._generate_synthetic_data()

        elif self.data_source == "csv":
            if file_path is None:
                raise ValueError("file_path required for CSV data source")
            print(f"Loading data from CSV: {file_path}")
            self.patient_data = pd.read_csv(file_path)

        elif self.data_source == "sql":
            if sql_query is None or connection_string is None:
                raise ValueError("sql_query and connection_string required for SQL data source")
            print("Loading data from SQL database...")
            try:
                import sqlalchemy
                engine = sqlalchemy.create_engine(connection_string)
                self.patient_data = pd.read_sql(sql_query, engine)
            except ImportError:
                raise ImportError("sqlalchemy required for SQL data source. Install: pip install sqlalchemy")

        elif self.data_source == "mimic":
            if file_path is None:
                # Default MIMIC extraction
                file_path = str(project_root / "sql" / "identify_ecmo.sql")
            print(f"Loading MIMIC-IV data from query: {file_path}")
            # Load SQL query and execute
            # Note: Requires MIMIC-IV database access
            with open(file_path, 'r') as f:
                sql_query = f.read()
            if connection_string is None:
                warnings.warn("No connection string provided. Using synthetic data instead.")
                self.patient_data = self._generate_synthetic_data()
            else:
                import sqlalchemy
                engine = sqlalchemy.create_engine(connection_string)
                self.patient_data = pd.read_sql(sql_query, engine)
        else:
            raise ValueError(f"Unknown data source: {self.data_source}")

        print(f"Loaded {len(self.patient_data)} patient records")
        return self.patient_data

    def _generate_synthetic_data(
        self,
        n_patients: int = 500,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Generate synthetic ECMO patient data with realistic distributions.

        Args:
            n_patients: Number of patients to generate
            seed: Random seed

        Returns:
            DataFrame with synthetic patient data
        """
        np.random.seed(seed)

        data = []
        for i in range(n_patients):
            # Random ECMO mode (60% VA, 40% VV)
            mode = np.random.choice(['VA', 'VV'], p=[0.6, 0.4])

            # Age and comorbidity
            age = np.random.normal(60, 15)
            age = np.clip(age, 18, 90)
            apache_ii = np.random.normal(25, 8)
            apache_ii = np.clip(apache_ii, 5, 50)

            # Base survival rate depends on mode and severity
            if mode == 'VA':
                base_survival = 0.45 - (apache_ii - 25) * 0.01
            else:
                base_survival = 0.55 - (apache_ii - 25) * 0.01
            base_survival = np.clip(base_survival, 0.15, 0.85)

            survival = int(np.random.random() < base_survival)

            # Length of stay (survivors stay longer in ward)
            if mode == 'VA':
                icu_los = np.random.gamma(shape=5, scale=3)  # Mean ~15 days
                ecmo_days = np.random.gamma(shape=3, scale=2)  # Mean ~6 days
            else:
                icu_los = np.random.gamma(shape=4, scale=2.5)  # Mean ~10 days
                ecmo_days = np.random.gamma(shape=2.5, scale=2)  # Mean ~5 days

            # Non-survivors have shorter ICU stay (earlier death)
            if not survival:
                icu_los *= 0.6
                ecmo_days = min(ecmo_days, icu_los)
                ward_los = 0
            else:
                ward_los = np.random.gamma(shape=3, scale=2)  # Mean ~6 days

            # NIRS features (synthetic - realistic ranges)
            hbo_mean = np.random.normal(65, 10)  # Oxygenated hemoglobin (% saturation)
            hbo_std = np.random.normal(8, 2)
            hbo_slope = np.random.normal(-0.5 if survival else -2.0, 1.0)

            hbt_mean = np.random.normal(70, 12)  # Total hemoglobin
            hbt_std = np.random.normal(9, 2)
            hbt_slope = np.random.normal(-0.3 if survival else -1.5, 1.0)

            # EHR features
            bmi = np.random.normal(26, 5)
            lactate = np.random.lognormal(1.0 if survival else 1.8, 0.8)
            hemoglobin = np.random.normal(11, 2)
            platelets = np.random.normal(180 if survival else 120, 50)
            map_mmhg = np.random.normal(70 if survival else 60, 10)
            spo2 = np.random.normal(94 if survival else 88, 5)
            pao2 = np.random.normal(85 if survival else 70, 15)
            paco2 = np.random.normal(42, 8)

            # ECMO settings
            if mode == 'VA':
                pump_speed = np.random.normal(3200, 300)
                flow = np.random.normal(4.5, 0.8)
            else:
                pump_speed = np.random.normal(2800, 250)
                flow = np.random.normal(4.0, 0.6)
            sweep_gas = np.random.normal(6, 1.5)
            fio2_ecmo = np.random.uniform(0.5, 1.0)

            data.append({
                'patient_id': f'P{i+1:04d}',
                'mode': mode,
                'age': age,
                'bmi': bmi,
                'apache_ii': apache_ii,
                'survival_to_discharge': survival,
                'icu_los_days': max(1, icu_los),
                'ward_los_days': max(0, ward_los),
                'ecmo_days': min(ecmo_days, icu_los),
                # NIRS features
                'hbo_mean': hbo_mean,
                'hbo_std': max(0, hbo_std),
                'hbo_slope': hbo_slope,
                'hbt_mean': hbt_mean,
                'hbt_std': max(0, hbt_std),
                'hbt_slope': hbt_slope,
                # EHR features
                'lactate_mmol_l': max(0.5, lactate),
                'hemoglobin_g_dl': max(5, hemoglobin),
                'platelets_10e9_l': max(20, platelets),
                'map_mmHg': max(40, map_mmhg),
                'spo2_pct': np.clip(spo2, 70, 100),
                'abg_pao2_mmHg': max(40, pao2),
                'abg_paco2_mmHg': max(25, paco2),
                # ECMO settings
                'pump_speed_rpm': pump_speed,
                'flow_l_min': max(2, flow),
                'sweep_gas_l_min': max(2, sweep_gas),
                'fio2_ecmo': np.clip(fio2_ecmo, 0.21, 1.0),
            })

        return pd.DataFrame(data)

    def assign_risk_quintiles(
        self,
        risk_scores: Optional[np.ndarray] = None,
        method: str = 'equal_frequency'
    ) -> pd.DataFrame:
        """
        Assign risk quintiles to patients.

        Args:
            risk_scores: Array of risk scores (predicted mortality probability)
                        If None, uses APACHE-II as proxy
            method: Quintile assignment method ('equal_frequency' or 'equal_width')

        Returns:
            DataFrame with risk_quintile column added
        """
        if self.patient_data is None:
            raise ValueError("Patient data not loaded. Call load_patient_data() first.")

        if risk_scores is None:
            print("Using APACHE-II scores as risk proxy (no model predictions provided)")
            risk_scores = self.patient_data['apache_ii'].values

        # Assign quintiles
        if method == 'equal_frequency':
            # Equal number of patients per quintile
            quintiles = pd.qcut(risk_scores, q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        elif method == 'equal_width':
            # Equal risk score ranges
            quintiles = pd.cut(risk_scores, bins=5, labels=[1, 2, 3, 4, 5])
        else:
            raise ValueError(f"Unknown method: {method}")

        self.patient_data['risk_score'] = risk_scores
        self.patient_data['risk_quintile'] = quintiles.astype(int)

        print("\nRisk Quintile Distribution:")
        print(self.patient_data['risk_quintile'].value_counts().sort_index())

        return self.patient_data

    def compute_costs(
        self,
        icu_cost_per_day: float = 30000,
        ward_cost_per_day: float = 8000,
        ecmo_daily_consumable: float = 15000,
        ecmo_setup_cost: float = 100000
    ) -> pd.DataFrame:
        """
        Compute total costs for each patient.

        Args:
            icu_cost_per_day: Daily ICU cost (TWD)
            ward_cost_per_day: Daily ward cost (TWD)
            ecmo_daily_consumable: Daily ECMO consumable cost (TWD)
            ecmo_setup_cost: One-time ECMO setup cost (TWD)

        Returns:
            DataFrame with cost columns added
        """
        if self.patient_data is None:
            raise ValueError("Patient data not loaded. Call load_patient_data() first.")

        # Compute costs
        self.patient_data['icu_cost'] = (
            self.patient_data['icu_los_days'] * icu_cost_per_day
        )
        self.patient_data['ward_cost'] = (
            self.patient_data['ward_los_days'] * ward_cost_per_day
        )
        self.patient_data['ecmo_cost'] = (
            ecmo_setup_cost +
            (self.patient_data['ecmo_days'] * ecmo_daily_consumable)
        )
        self.patient_data['total_cost'] = (
            self.patient_data['icu_cost'] +
            self.patient_data['ward_cost'] +
            self.patient_data['ecmo_cost']
        )

        print(f"\nCost Summary (TWD):")
        print(f"  Mean total cost: {self.patient_data['total_cost'].mean():,.0f}")
        print(f"  Median total cost: {self.patient_data['total_cost'].median():,.0f}")
        print(f"  Min-Max: {self.patient_data['total_cost'].min():,.0f} - {self.patient_data['total_cost'].max():,.0f}")

        return self.patient_data

    def integrate_risk_predictions(
        self,
        va_model=None,
        vv_model=None
    ) -> pd.DataFrame:
        """
        Integrate risk predictions from trained NIRS models.

        Args:
            va_model: Trained VA-ECMO risk model (from nirs/risk_models.py)
            vv_model: Trained VV-ECMO risk model

        Returns:
            DataFrame with risk predictions added
        """
        if self.patient_data is None:
            raise ValueError("Patient data not loaded. Call load_patient_data() first.")

        if va_model is None and vv_model is None:
            print("No models provided. Using APACHE-II as risk proxy.")
            # Normalize APACHE-II to 0-1 range as risk score
            apache_normalized = self.patient_data['apache_ii'] / 50.0
            risk_scores = np.clip(apache_normalized, 0, 1)
        else:
            risk_scores = np.zeros(len(self.patient_data))

            # VA predictions
            if va_model is not None:
                va_mask = self.patient_data['mode'] == 'VA'
                va_data = self.patient_data[va_mask]
                if len(va_data) > 0:
                    try:
                        X_va, _, _ = va_model.prepare_features(va_data)
                        va_probs = va_model.predict_proba(X_va, calibrated=True)
                        risk_scores[va_mask] = va_probs[:, 0]  # Probability of death
                    except Exception as e:
                        warnings.warn(f"VA model prediction failed: {e}")
                        risk_scores[va_mask] = va_data['apache_ii'].values / 50.0

            # VV predictions
            if vv_model is not None:
                vv_mask = self.patient_data['mode'] == 'VV'
                vv_data = self.patient_data[vv_mask]
                if len(vv_data) > 0:
                    try:
                        X_vv, _, _ = vv_model.prepare_features(vv_data)
                        vv_probs = vv_model.predict_proba(X_vv, calibrated=True)
                        risk_scores[vv_mask] = vv_probs[:, 0]  # Probability of death
                    except Exception as e:
                        warnings.warn(f"VV model prediction failed: {e}")
                        risk_scores[vv_mask] = vv_data['apache_ii'].values / 50.0

        # Assign quintiles based on risk scores
        self.assign_risk_quintiles(risk_scores=risk_scores)

        return self.patient_data

    def prepare_for_cea(self) -> pd.DataFrame:
        """
        Prepare final dataset for cost-effectiveness analysis.

        Returns:
            DataFrame ready for ECMOCostEffectivenessAnalysis
        """
        if self.patient_data is None:
            raise ValueError("Patient data not loaded.")

        # Ensure required columns exist
        required_cols = [
            'risk_quintile', 'icu_los_days', 'ward_los_days',
            'ecmo_days', 'survival_to_discharge'
        ]

        missing_cols = [col for col in required_cols if col not in self.patient_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Compute costs if not already done
        if 'total_cost' not in self.patient_data.columns:
            self.compute_costs()

        self.integrated_data = self.patient_data.copy()

        print(f"\nDataset prepared for CEA:")
        print(f"  Total patients: {len(self.integrated_data)}")
        print(f"  VA-ECMO: {(self.integrated_data['mode'] == 'VA').sum()}")
        print(f"  VV-ECMO: {(self.integrated_data['mode'] == 'VV').sum()}")
        print(f"  Overall survival: {self.integrated_data['survival_to_discharge'].mean()*100:.1f}%")

        return self.integrated_data

    def get_quintile_summary(self) -> pd.DataFrame:
        """
        Get summary statistics by risk quintile.

        Returns:
            DataFrame with quintile-level summary
        """
        if self.integrated_data is None:
            self.prepare_for_cea()

        summary = self.integrated_data.groupby('risk_quintile').agg({
            'patient_id': 'count',
            'age': 'mean',
            'apache_ii': 'mean',
            'survival_to_discharge': 'mean',
            'icu_los_days': 'mean',
            'ward_los_days': 'mean',
            'ecmo_days': 'mean',
            'total_cost': 'mean',
        }).round(2)

        summary.columns = [
            'n_patients', 'mean_age', 'mean_apache', 'survival_rate',
            'mean_icu_los', 'mean_ward_los', 'mean_ecmo_days', 'mean_total_cost'
        ]

        return summary


if __name__ == '__main__':
    print("=" * 80)
    print("ECMO Data Integration for Cost-Effectiveness Analysis")
    print("=" * 80)

    # Example 1: Synthetic data
    print("\n\nExample 1: Generate and integrate synthetic data")
    print("-" * 80)

    integrator = ECMODataIntegrator(data_source="synthetic")

    # Load patient data
    data = integrator.load_patient_data()

    # Integrate risk predictions (using APACHE-II as proxy)
    data = integrator.integrate_risk_predictions()

    # Compute costs
    data = integrator.compute_costs()

    # Prepare for CEA
    cea_data = integrator.prepare_for_cea()

    # Get quintile summary
    print("\n\nQuintile Summary:")
    print("-" * 80)
    summary = integrator.get_quintile_summary()
    print(summary.to_string())

    # Example 2: CSV data (if available)
    print("\n\nExample 2: CSV data integration")
    print("-" * 80)
    print("To load from CSV:")
    print("  integrator = ECMODataIntegrator(data_source='csv')")
    print("  data = integrator.load_patient_data(file_path='path/to/ecmo_data.csv')")

    # Example 3: With trained models
    print("\n\nExample 3: Integration with trained risk models")
    print("-" * 80)
    print("To integrate with trained NIRS models:")
    print("  from nirs.risk_models import train_va_vv_models")
    print("  va_model, vv_model, _ = train_va_vv_models(data)")
    print("  integrator.integrate_risk_predictions(va_model=va_model, vv_model=vv_model)")

    print("\n" + "=" * 80)
    print("Data integration complete!")
    print("=" * 80)
