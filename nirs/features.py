"""
Advanced NIRS + EHR Feature Engineering for ECMO Outcomes
Includes temporal features, interaction features, and domain knowledge features.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
from scipy import stats
from scipy.signal import find_peaks
import warnings


def fixed_window(df, start='10:00', end='11:00', time_col='timestamp'):
    """Extract data within a fixed time window."""
    mask = (df[time_col].dt.strftime('%H:%M') >= start) & (df[time_col].dt.strftime('%H:%M') <= end)
    return df.loc[mask].copy()


def nirs_feature_frame(df, side_col='side', value_cols=('hbo','hbt','pump_rpm','flow_l_min')):
    """Basic NIRS feature extraction (legacy function)."""
    non_cann = df.loc[df[side_col]=='non_cannulated'].copy() if side_col in df else df.copy()
    out = {}
    for c in value_cols:
        if c in non_cann:
            s = non_cann[c].astype(float)
            out[f'{c}_mean'] = s.mean()
            out[f'{c}_std'] = s.std()
            out[f'{c}_slope'] = (s.iloc[-1]-s.iloc[0]) / max(len(s)-1,1)
    return pd.DataFrame([out])


# ============================================================================
# Advanced NIRS Feature Engineering
# ============================================================================

class NIRSFeatureExtractor:
    """
    Advanced NIRS feature extraction for ECMO outcomes.

    Features:
    - Temporal statistics (mean, std, min, max, trend)
    - Variability metrics (coefficient of variation, entropy)
    - Trend analysis (slope, acceleration, direction changes)
    - Peak/trough detection
    - Time-domain features (autocorrelation, stationarity)
    - Differential hypoxia index for VA-ECMO
    """

    def __init__(self, window_hours: float = 6.0):
        """
        Args:
            window_hours: Time window for feature extraction
        """
        self.window_hours = window_hours

    def extract_temporal_statistics(self, series: pd.Series) -> Dict[str, float]:
        """
        Extract temporal statistics from time series.

        Args:
            series: Time series data

        Returns:
            Dictionary of temporal features
        """
        if len(series) == 0 or series.isna().all():
            return {
                'mean': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'median': np.nan,
                'q25': np.nan,
                'q75': np.nan,
                'range': np.nan,
                'iqr': np.nan,
                'cv': np.nan  # Coefficient of variation
            }

        values = series.dropna()

        return {
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'median': values.median(),
            'q25': values.quantile(0.25),
            'q75': values.quantile(0.75),
            'range': values.max() - values.min(),
            'iqr': values.quantile(0.75) - values.quantile(0.25),
            'cv': values.std() / values.mean() if values.mean() != 0 else np.nan
        }

    def extract_trend_features(self, series: pd.Series) -> Dict[str, float]:
        """
        Extract trend and change features.

        Args:
            series: Time series data

        Returns:
            Dictionary of trend features
        """
        if len(series) < 2 or series.isna().all():
            return {
                'slope': np.nan,
                'slope_pct': np.nan,
                'acceleration': np.nan,
                'n_direction_changes': np.nan,
                'trend_strength': np.nan
            }

        values = series.dropna().values
        n = len(values)

        # Linear trend (slope)
        x = np.arange(n)
        slope, intercept = np.polyfit(x, values, 1)

        # Slope as percentage of mean
        mean_val = values.mean()
        slope_pct = (slope / mean_val * 100) if mean_val != 0 else 0

        # Acceleration (second derivative)
        if n >= 3:
            acceleration = np.polyfit(x, values, 2)[0]
        else:
            acceleration = 0

        # Count direction changes
        diffs = np.diff(values)
        sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)

        # Trend strength (R² of linear fit)
        residuals = values - (slope * x + intercept)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((values - values.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return {
            'slope': slope,
            'slope_pct': slope_pct,
            'acceleration': acceleration,
            'n_direction_changes': sign_changes,
            'trend_strength': r_squared
        }

    def extract_variability_features(self, series: pd.Series) -> Dict[str, float]:
        """
        Extract variability and entropy features.

        Args:
            series: Time series data

        Returns:
            Dictionary of variability features
        """
        if len(series) < 2 or series.isna().all():
            return {
                'successive_diff_mean': np.nan,
                'successive_diff_std': np.nan,
                'entropy': np.nan
            }

        values = series.dropna().values

        # Successive differences
        diffs = np.diff(values)
        successive_diff_mean = np.mean(np.abs(diffs))
        successive_diff_std = np.std(diffs)

        # Approximate entropy
        try:
            # Bin values into 10 bins for entropy calculation
            hist, _ = np.histogram(values, bins=10, density=True)
            hist = hist[hist > 0]  # Remove zero bins
            entropy = -np.sum(hist * np.log2(hist))
        except:
            entropy = np.nan

        return {
            'successive_diff_mean': successive_diff_mean,
            'successive_diff_std': successive_diff_std,
            'entropy': entropy
        }

    def extract_peak_features(self, series: pd.Series) -> Dict[str, float]:
        """
        Extract peak/trough detection features.

        Args:
            series: Time series data

        Returns:
            Dictionary of peak features
        """
        if len(series) < 5 or series.isna().all():
            return {
                'n_peaks': np.nan,
                'n_troughs': np.nan,
                'peak_prominence_mean': np.nan
            }

        values = series.dropna().values

        # Find peaks
        peaks, properties = find_peaks(values, prominence=0.1)
        troughs, _ = find_peaks(-values, prominence=0.1)

        # Peak prominence
        if len(peaks) > 0 and 'prominences' in properties:
            peak_prominence_mean = np.mean(properties['prominences'])
        else:
            peak_prominence_mean = 0

        return {
            'n_peaks': len(peaks),
            'n_troughs': len(troughs),
            'peak_prominence_mean': peak_prominence_mean
        }

    def extract_all_features(
        self,
        df: pd.DataFrame,
        value_col: str,
        prefix: str = ''
    ) -> Dict[str, float]:
        """
        Extract all NIRS features for a single parameter.

        Args:
            df: DataFrame with time series data
            value_col: Column name for values
            prefix: Prefix for feature names

        Returns:
            Dictionary of all features
        """
        if value_col not in df.columns:
            return {}

        series = df[value_col]

        # Combine all feature types
        features = {}
        features.update({f'{prefix}_temp_{k}': v for k, v in self.extract_temporal_statistics(series).items()})
        features.update({f'{prefix}_trend_{k}': v for k, v in self.extract_trend_features(series).items()})
        features.update({f'{prefix}_var_{k}': v for k, v in self.extract_variability_features(series).items()})
        features.update({f'{prefix}_peak_{k}': v for k, v in self.extract_peak_features(series).items()})

        return features


# ============================================================================
# Interaction Features
# ============================================================================

def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction features between NIRS and EHR parameters.

    Args:
        df: DataFrame with NIRS and EHR features

    Returns:
        DataFrame with added interaction features
    """
    df = df.copy()

    # NIRS × Hemodynamics
    if 'hbo_mean' in df.columns and 'map_mmhg' in df.columns:
        df['hbo_map_ratio'] = df['hbo_mean'] / df['map_mmhg']

    if 'hbt_mean' in df.columns and 'hr_bpm' in df.columns:
        df['hbt_hr_product'] = df['hbt_mean'] * df['hr_bpm']

    # Oxygenation indices
    if 'pao2_pre_ecmo' in df.columns and 'fio2_pre_ecmo' in df.columns:
        df['pf_ratio'] = df['pao2_pre_ecmo'] / df['fio2_pre_ecmo']

    if 'spo2_pct' in df.columns and 'hemoglobin_g_dl' in df.columns:
        df['oxygen_content_est'] = df['spo2_pct'] * df['hemoglobin_g_dl'] / 100

    # ECMO parameters × BSA
    if 'avg_flow_l_min' in df.columns and 'bsa_m2' in df.columns:
        df['flow_index'] = df['avg_flow_l_min'] / df['bsa_m2']

    if 'avg_pump_rpm' in df.columns and 'bsa_m2' in df.columns:
        df['rpm_index'] = df['avg_pump_rpm'] / df['bsa_m2']

    # Metabolic indicators
    if 'lactate_pre_ecmo' in df.columns and 'ph_pre_ecmo' in df.columns:
        df['lactate_ph_product'] = df['lactate_pre_ecmo'] * (8 - df['ph_pre_ecmo'])  # Higher = worse

    if 'glucose_mg_dl' in df.columns and 'lactate_pre_ecmo' in df.columns:
        df['glucose_lactate_ratio'] = df['glucose_mg_dl'] / df['lactate_pre_ecmo']

    # Organ dysfunction scores
    if 'creatinine_mg_dl' in df.columns and 'bun_mg_dl' in df.columns:
        df['bun_cr_ratio'] = df['bun_mg_dl'] / df['creatinine_mg_dl']

    if 'bilirubin_mg_dl' in df.columns and 'platelets_k_ul' in df.columns:
        df['bili_platelet_product'] = df['bilirubin_mg_dl'] * (400 - df['platelets_k_ul'])

    return df


# ============================================================================
# Domain Knowledge Features
# ============================================================================

def calculate_differential_hypoxia_index(
    spo2_right_arm: float,
    spo2_lower_limb: float,
    ecmo_mode: str
) -> float:
    """
    Calculate differential hypoxia index for VA-ECMO.

    Differential hypoxia occurs in VA-ECMO when native cardiac output competes
    with ECMO blood flow, leading to different oxygenation in upper vs lower body.

    Args:
        spo2_right_arm: SpO2 in right arm (pre-ductal)
        spo2_lower_limb: SpO2 in lower limb (post-ductal)
        ecmo_mode: ECMO mode ('VA' or 'VV')

    Returns:
        Differential hypoxia index (0-100)
    """
    if ecmo_mode != 'VA':
        return 0.0

    if pd.isna(spo2_right_arm) or pd.isna(spo2_lower_limb):
        return np.nan

    # Positive difference indicates differential hypoxia
    diff = spo2_right_arm - spo2_lower_limb

    # Clinically significant if >10%
    return max(0, diff)


def calculate_ecmo_support_adequacy(
    flow_l_min: float,
    cardiac_output_est: float,
    ecmo_mode: str
) -> float:
    """
    Calculate ECMO support adequacy as percentage of cardiac output.

    Args:
        flow_l_min: ECMO flow in L/min
        cardiac_output_est: Estimated cardiac output in L/min
        ecmo_mode: ECMO mode

    Returns:
        Support adequacy percentage (0-100+)
    """
    if pd.isna(flow_l_min) or pd.isna(cardiac_output_est) or cardiac_output_est == 0:
        return np.nan

    adequacy = (flow_l_min / cardiac_output_est) * 100

    return adequacy


def estimate_cardiac_output(
    hr_bpm: float,
    map_mmhg: float,
    bsa_m2: float,
    age_years: float
) -> float:
    """
    Estimate cardiac output using simplified formula.

    CO (L/min) ≈ Cardiac Index × BSA
    Cardiac Index ≈ (MAP × HR) / 5000  (simplified)

    Args:
        hr_bpm: Heart rate
        map_mmhg: Mean arterial pressure
        bsa_m2: Body surface area
        age_years: Age

    Returns:
        Estimated cardiac output in L/min
    """
    if any(pd.isna([hr_bpm, map_mmhg, bsa_m2])):
        return np.nan

    # Rough estimate: CI = 2.5-4.0 L/min/m² for adults
    # Adjust for age
    if age_years < 18:
        base_ci = 4.0
    elif age_years < 65:
        base_ci = 3.0
    else:
        base_ci = 2.5

    # Adjust for hemodynamics (simplified)
    ci_adjustment = (hr_bpm / 70) * (map_mmhg / 80)
    ci = base_ci * min(ci_adjustment, 2.0)  # Cap at 2x baseline

    co = ci * bsa_m2

    return co


def calculate_ecmo_efficiency_score(
    pao2_pre_ecmo: float,
    pao2_on_ecmo: float,
    flow_l_min: float,
    sweep_gas_l_min: float
) -> float:
    """
    Calculate ECMO oxygenation efficiency score.

    Args:
        pao2_pre_ecmo: PaO2 before ECMO
        pao2_on_ecmo: PaO2 on ECMO
        flow_l_min: ECMO blood flow
        sweep_gas_l_min: Sweep gas flow

    Returns:
        Efficiency score (higher = better oxygenation per unit flow)
    """
    if any(pd.isna([pao2_pre_ecmo, pao2_on_ecmo, flow_l_min, sweep_gas_l_min])):
        return np.nan

    # Oxygenation improvement
    pao2_delta = pao2_on_ecmo - pao2_pre_ecmo

    # Efficiency = improvement per unit of support
    total_flow = flow_l_min + sweep_gas_l_min
    if total_flow == 0:
        return np.nan

    efficiency = pao2_delta / total_flow

    return efficiency


def create_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create domain knowledge-based features.

    Args:
        df: DataFrame with ECMO data

    Returns:
        DataFrame with added domain features
    """
    df = df.copy()

    # Estimate cardiac output
    if all(col in df.columns for col in ['hr_pre_ecmo', 'map_pre_ecmo', 'bsa_m2', 'age_years']):
        df['estimated_cardiac_output'] = df.apply(
            lambda row: estimate_cardiac_output(
                row['hr_pre_ecmo'],
                row['map_pre_ecmo'],
                row['bsa_m2'],
                row['age_years']
            ),
            axis=1
        )

        # ECMO support adequacy
        if 'avg_flow_l_min' in df.columns:
            df['ecmo_support_adequacy'] = df.apply(
                lambda row: calculate_ecmo_support_adequacy(
                    row['avg_flow_l_min'],
                    row.get('estimated_cardiac_output', np.nan),
                    row['ecmo_mode']
                ),
                axis=1
            )

    # Differential hypoxia index (for VA-ECMO)
    # Note: Requires pre-ductal and post-ductal SpO2 measurements
    # Placeholder - would need actual measurement locations
    if 'spo2_pre_ecmo' in df.columns and 'ecmo_mode' in df.columns:
        df['differential_hypoxia_risk'] = df.apply(
            lambda row: 1 if row['ecmo_mode'] == 'VA' and row.get('spo2_pre_ecmo', 100) < 90 else 0,
            axis=1
        )

    # Shock index (HR/SBP)
    if 'hr_pre_ecmo' in df.columns and 'sbp_pre_ecmo' in df.columns:
        df['shock_index'] = df['hr_pre_ecmo'] / df['sbp_pre_ecmo']
        df['shock_index_elevated'] = (df['shock_index'] > 0.9).astype(int)

    # Modified shock index (HR/MAP)
    if 'hr_pre_ecmo' in df.columns and 'map_pre_ecmo' in df.columns:
        df['modified_shock_index'] = df['hr_pre_ecmo'] / df['map_pre_ecmo']

    # Ventilation ratio
    if all(col in df.columns for col in ['resp_rate_pre_ecmo', 'paco2_pre_ecmo']):
        # VR = (minute ventilation × PaCO2) / (predicted minute vent × predicted PaCO2)
        # Simplified: RR × PaCO2 / (normal RR × normal PaCO2)
        df['ventilation_ratio'] = (df['resp_rate_pre_ecmo'] * df['paco2_pre_ecmo']) / (12 * 40)

    return df


# ============================================================================
# Complete Feature Engineering Pipeline
# ============================================================================

def engineer_all_features(
    df: pd.DataFrame,
    include_temporal: bool = True,
    include_interactions: bool = True,
    include_domain: bool = True
) -> pd.DataFrame:
    """
    Complete feature engineering pipeline.

    Args:
        df: Input DataFrame with raw ECMO data
        include_temporal: Include temporal NIRS features
        include_interactions: Include interaction features
        include_domain: Include domain knowledge features

    Returns:
        DataFrame with engineered features
    """
    df_eng = df.copy()

    print("Engineering features...")

    # Add interaction features
    if include_interactions:
        print("  - Creating interaction features")
        df_eng = create_interaction_features(df_eng)

    # Add domain knowledge features
    if include_domain:
        print("  - Creating domain knowledge features")
        df_eng = create_domain_features(df_eng)

    n_original = len(df.columns)
    n_engineered = len(df_eng.columns)
    print(f"  - Total features: {n_engineered} (added {n_engineered - n_original})")

    return df_eng
