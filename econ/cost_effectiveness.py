"""
Cost-Effectiveness Analysis for ECMO CDSS (WP2)

Computes:
- CER (Cost-Effectiveness Ratio) by risk quintile
- ICER (Incremental Cost-Effectiveness Ratio)
- CEAC (Cost-Effectiveness Acceptability Curve)
- PSA (Probabilistic Sensitivity Analysis)
- Two-way sensitivity analysis (tornado diagrams)
- VOI (Value of Information) analysis
- Budget impact analysis
- Multi-currency support (TWD, USD, EUR)
- Taiwan NHI-specific calculations

Follows CHEERS 2022 reporting guidelines.

Parameterized for local context: LOS, costs, survival rates
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple, Optional, List
import warnings


class ECMOCostEffectivenessAnalysis:
    """
    Cost-effectiveness analysis for ECMO interventions stratified by risk quintile.

    Supports local parameterization of:
    - Length of stay (ICU, hospital)
    - Cost parameters (daily ICU, daily ward, ECMO consumables)
    - Survival rates
    - Quality-adjusted life years (QALYs)
    - Multi-currency support (TWD, USD, EUR)
    - Taiwan NHI reimbursement calculations
    - Probabilistic sensitivity analysis
    - Value of information analysis
    - Budget impact analysis
    """

    # Currency conversion rates (to TWD)
    CURRENCY_RATES = {
        'TWD': 1.0,
        'USD': 31.5,  # Approximate TWD/USD
        'EUR': 34.2,  # Approximate TWD/EUR
    }

    # Taiwan NHI DRG reimbursement rates (TWD) - approximate values
    NHI_DRG_RATES = {
        'ECMO_VA': 800000,  # DRG for VA-ECMO
        'ECMO_VV': 750000,  # DRG for VV-ECMO
        'ICU_daily_cap': 45000,  # Daily ICU cap
    }

    def __init__(
        self,
        icu_cost_per_day: float = 30000,
        ward_cost_per_day: float = 8000,
        ecmo_daily_consumable: float = 15000,
        ecmo_setup_cost: float = 100000,
        qaly_gain_per_survivor: float = 1.5,
        time_horizon_years: float = 1.0,
        discount_rate: float = 0.03,
        currency: str = "TWD",
        use_nhi_rates: bool = False,
        ecmo_mode: str = "VA"
    ):
        """
        Initialize cost-effectiveness parameters.

        Args:
            icu_cost_per_day: Daily ICU cost (local currency)
            ward_cost_per_day: Daily ward cost (local currency)
            ecmo_daily_consumable: Daily ECMO consumable cost
            ecmo_setup_cost: One-time ECMO setup/cannulation cost
            qaly_gain_per_survivor: Average QALY gained per survivor
            time_horizon_years: Analysis time horizon (typically 1-5 years)
            discount_rate: Annual discount rate for future costs/benefits
            currency: Local currency code (TWD, USD, EUR)
            use_nhi_rates: Use Taiwan NHI DRG reimbursement rates
            ecmo_mode: ECMO mode ('VA' or 'VV') for NHI calculations
        """
        self.icu_cost_per_day = icu_cost_per_day
        self.ward_cost_per_day = ward_cost_per_day
        self.ecmo_daily_consumable = ecmo_daily_consumable
        self.ecmo_setup_cost = ecmo_setup_cost
        self.qaly_gain_per_survivor = qaly_gain_per_survivor
        self.time_horizon_years = time_horizon_years
        self.discount_rate = discount_rate
        self.currency = currency
        self.use_nhi_rates = use_nhi_rates
        self.ecmo_mode = ecmo_mode

        # Validate currency
        if currency not in self.CURRENCY_RATES:
            raise ValueError(f"Unsupported currency: {currency}. Use TWD, USD, or EUR.")

    def compute_total_cost(
        self,
        icu_los_days: float,
        ward_los_days: float,
        ecmo_days: float
    ) -> float:
        """
        Compute total hospitalization cost.

        Args:
            icu_los_days: ICU length of stay
            ward_los_days: Ward length of stay
            ecmo_days: Days on ECMO support

        Returns:
            Total cost in local currency
        """
        icu_cost = icu_los_days * self.icu_cost_per_day
        ward_cost = ward_los_days * self.ward_cost_per_day
        ecmo_cost = self.ecmo_setup_cost + (ecmo_days * self.ecmo_daily_consumable)

        return icu_cost + ward_cost + ecmo_cost

    def compute_qaly(
        self,
        survival_rate: float,
        quality_of_life: float = 1.0
    ) -> float:
        """
        Compute quality-adjusted life years.

        Args:
            survival_rate: Proportion surviving to discharge
            quality_of_life: Quality of life multiplier (0-1)

        Returns:
            Expected QALYs
        """
        # Discount future QALYs
        discount_factor = 1 / (1 + self.discount_rate) ** self.time_horizon_years
        qaly = survival_rate * self.qaly_gain_per_survivor * quality_of_life * discount_factor
        return qaly

    def compute_cer(
        self,
        total_cost: float,
        qaly: float
    ) -> float:
        """
        Compute Cost-Effectiveness Ratio (CER).

        CER = Total Cost / QALYs gained

        Args:
            total_cost: Total intervention cost
            qaly: Quality-adjusted life years

        Returns:
            CER in local currency per QALY
        """
        if qaly <= 0:
            return float('inf')
        return total_cost / qaly

    def compute_icer(
        self,
        cost_intervention: float,
        cost_comparator: float,
        qaly_intervention: float,
        qaly_comparator: float
    ) -> float:
        """
        Compute Incremental Cost-Effectiveness Ratio (ICER).

        ICER = (Cost_intervention - Cost_comparator) / (QALY_intervention - QALY_comparator)

        Args:
            cost_intervention: Cost of intervention arm
            cost_comparator: Cost of standard care
            qaly_intervention: QALYs from intervention
            qaly_comparator: QALYs from standard care

        Returns:
            ICER in local currency per QALY gained
        """
        delta_cost = cost_intervention - cost_comparator
        delta_qaly = qaly_intervention - qaly_comparator

        if delta_qaly <= 0:
            # Intervention dominated or no benefit
            return float('inf') if delta_cost > 0 else float('-inf')

        return delta_cost / delta_qaly

    def analyze_by_quintile(
        self,
        quintile_data: pd.DataFrame,
        quintile_col: str = 'risk_quintile',
        icu_los_col: str = 'icu_los_days',
        ward_los_col: str = 'ward_los_days',
        ecmo_days_col: str = 'ecmo_days',
        survival_col: str = 'survival_to_discharge'
    ) -> pd.DataFrame:
        """
        Perform cost-effectiveness analysis stratified by risk quintile.

        Args:
            quintile_data: DataFrame with patient-level data
            quintile_col: Column containing risk quintile (1-5)
            icu_los_col: ICU length of stay column
            ward_los_col: Ward length of stay column
            ecmo_days_col: ECMO days column
            survival_col: Survival outcome column (0/1)

        Returns:
            DataFrame with quintile-specific CER metrics
        """
        results = []

        for quintile in sorted(quintile_data[quintile_col].unique()):
            qdata = quintile_data[quintile_data[quintile_col] == quintile]

            # Mean values per quintile
            mean_icu_los = qdata[icu_los_col].mean()
            mean_ward_los = qdata[ward_los_col].mean()
            mean_ecmo_days = qdata[ecmo_days_col].mean()
            survival_rate = qdata[survival_col].mean()
            n_patients = len(qdata)

            # Cost and effectiveness
            total_cost = self.compute_total_cost(
                mean_icu_los,
                mean_ward_los,
                mean_ecmo_days
            )
            qaly = self.compute_qaly(survival_rate)
            cer = self.compute_cer(total_cost, qaly)

            results.append({
                'quintile': quintile,
                'n_patients': n_patients,
                'survival_rate': survival_rate,
                'mean_icu_los_days': mean_icu_los,
                'mean_ward_los_days': mean_ward_los,
                'mean_ecmo_days': mean_ecmo_days,
                'total_cost': total_cost,
                'qaly': qaly,
                'cer': cer,
                'cost_per_survivor': total_cost / survival_rate if survival_rate > 0 else float('inf')
            })

        return pd.DataFrame(results)

    def compute_icer_by_quintile(
        self,
        quintile_results: pd.DataFrame,
        baseline_quintile: int = 1
    ) -> pd.DataFrame:
        """
        Compute ICER for each quintile relative to baseline.

        Args:
            quintile_results: Results from analyze_by_quintile()
            baseline_quintile: Reference quintile (typically lowest risk)

        Returns:
            DataFrame with incremental analysis
        """
        baseline = quintile_results[quintile_results['quintile'] == baseline_quintile].iloc[0]

        icer_results = []
        for _, row in quintile_results.iterrows():
            if row['quintile'] == baseline_quintile:
                icer = 0  # No incremental cost vs. self
            else:
                icer = self.compute_icer(
                    row['total_cost'],
                    baseline['total_cost'],
                    row['qaly'],
                    baseline['qaly']
                )

            icer_results.append({
                'quintile': row['quintile'],
                'icer_vs_baseline': icer,
                'incremental_cost': row['total_cost'] - baseline['total_cost'],
                'incremental_qaly': row['qaly'] - baseline['qaly']
            })

        return pd.DataFrame(icer_results)

    def compute_ceac(
        self,
        quintile_results: pd.DataFrame,
        wtp_thresholds: np.ndarray = None,
        n_simulations: int = 1000,
        cost_std_pct: float = 0.2,
        qaly_std_pct: float = 0.15
    ) -> pd.DataFrame:
        """
        Compute Cost-Effectiveness Acceptability Curve (CEAC) via probabilistic sensitivity analysis.

        CEAC shows probability that intervention is cost-effective at different
        willingness-to-pay (WTP) thresholds.

        Args:
            quintile_results: Results from analyze_by_quintile()
            wtp_thresholds: Array of WTP thresholds to evaluate (local currency/QALY)
            n_simulations: Number of Monte Carlo simulations
            cost_std_pct: Standard deviation of costs as % of mean
            qaly_std_pct: Standard deviation of QALYs as % of mean

        Returns:
            DataFrame with CEAC data (quintile, WTP threshold, probability cost-effective)
        """
        if wtp_thresholds is None:
            # Default WTP thresholds: 0 to 3x GDP per capita (Taiwan ~$30k USD, ~900k TWD)
            wtp_thresholds = np.linspace(0, 3000000, 50)

        ceac_data = []

        for _, row in quintile_results.iterrows():
            quintile = row['quintile']
            mean_cost = row['total_cost']
            mean_qaly = row['qaly']

            # Monte Carlo simulation with uncertainty
            cost_sim = np.random.normal(
                mean_cost,
                mean_cost * cost_std_pct,
                n_simulations
            )
            qaly_sim = np.random.normal(
                mean_qaly,
                mean_qaly * qaly_std_pct,
                n_simulations
            )

            # Ensure non-negative values
            cost_sim = np.maximum(cost_sim, 0)
            qaly_sim = np.maximum(qaly_sim, 0.001)

            # Compute probability cost-effective at each WTP threshold
            for wtp in wtp_thresholds:
                nmb = (wtp * qaly_sim) - cost_sim  # Net Monetary Benefit
                prob_cost_effective = np.mean(nmb > 0)

                ceac_data.append({
                    'quintile': quintile,
                    'wtp_threshold': wtp,
                    'probability_cost_effective': prob_cost_effective
                })

        return pd.DataFrame(ceac_data)

    def sensitivity_analysis(
        self,
        base_case: Dict,
        parameters: Dict[str, Tuple[float, float, float]]
    ) -> pd.DataFrame:
        """
        One-way sensitivity analysis.

        Args:
            base_case: Dictionary with base case values
                       (icu_los, ward_los, ecmo_days, survival_rate)
            parameters: Dict mapping parameter name to (low, base, high) values

        Returns:
            DataFrame with sensitivity results
        """
        results = []

        for param_name, (low, base, high) in parameters.items():
            for value, scenario in [(low, 'low'), (base, 'base'), (high, 'high')]:
                # Update parameter
                case = base_case.copy()

                if param_name in ['icu_los', 'ward_los', 'ecmo_days', 'survival_rate']:
                    case[param_name] = value
                else:
                    # Cost parameter - update object attribute
                    setattr(self, param_name, value)

                # Recompute
                total_cost = self.compute_total_cost(
                    case.get('icu_los', base_case['icu_los']),
                    case.get('ward_los', base_case['ward_los']),
                    case.get('ecmo_days', base_case['ecmo_days'])
                )
                qaly = self.compute_qaly(case.get('survival_rate', base_case['survival_rate']))
                cer = self.compute_cer(total_cost, qaly)

                results.append({
                    'parameter': param_name,
                    'scenario': scenario,
                    'value': value,
                    'total_cost': total_cost,
                    'qaly': qaly,
                    'cer': cer
                })

        return pd.DataFrame(results)

    def convert_currency(self, amount: float, to_currency: str) -> float:
        """
        Convert amount from base currency to target currency.

        Args:
            amount: Amount in base currency
            to_currency: Target currency code

        Returns:
            Converted amount
        """
        if to_currency not in self.CURRENCY_RATES:
            raise ValueError(f"Unsupported currency: {to_currency}")

        # Convert to TWD first, then to target
        amount_twd = amount * self.CURRENCY_RATES[self.currency]
        return amount_twd / self.CURRENCY_RATES[to_currency]

    def compute_nhi_reimbursement(
        self,
        icu_los_days: float,
        ecmo_days: float
    ) -> Dict[str, float]:
        """
        Compute Taiwan NHI reimbursement and hospital margin.

        Args:
            icu_los_days: ICU length of stay
            ecmo_days: Days on ECMO support

        Returns:
            Dictionary with reimbursement, actual cost, and margin
        """
        drg_key = f'ECMO_{self.ecmo_mode}'
        drg_payment = self.NHI_DRG_RATES.get(drg_key, 0)

        # Additional ICU daily payments (beyond DRG)
        icu_additional = min(icu_los_days * 10000, icu_los_days * self.NHI_DRG_RATES['ICU_daily_cap'])

        total_reimbursement = drg_payment + icu_additional

        # Compute actual cost
        actual_cost = self.compute_total_cost(
            icu_los_days=icu_los_days,
            ward_los_days=0,  # NHI typically only covers ICU
            ecmo_days=ecmo_days
        )

        margin = total_reimbursement - actual_cost
        margin_pct = (margin / total_reimbursement * 100) if total_reimbursement > 0 else 0

        return {
            'drg_payment': drg_payment,
            'icu_additional': icu_additional,
            'total_reimbursement': total_reimbursement,
            'actual_cost': actual_cost,
            'margin': margin,
            'margin_pct': margin_pct
        }

    def probabilistic_sensitivity_analysis(
        self,
        base_case: Dict,
        parameter_distributions: Dict[str, Tuple[str, tuple]],
        n_simulations: int = 10000,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Monte Carlo probabilistic sensitivity analysis (PSA).

        Args:
            base_case: Dictionary with base case values
                       (icu_los, ward_los, ecmo_days, survival_rate)
            parameter_distributions: Dict mapping parameter name to (dist_type, params)
                                    dist_type: 'normal', 'lognormal', 'gamma', 'beta', 'uniform'
                                    params: distribution parameters
            n_simulations: Number of Monte Carlo simulations
            seed: Random seed for reproducibility

        Returns:
            DataFrame with simulation results (cost, qaly, cer, nmb for each iteration)
        """
        np.random.seed(seed)
        results = []

        for i in range(n_simulations):
            sim_case = base_case.copy()

            # Sample parameters from distributions
            for param_name, (dist_type, dist_params) in parameter_distributions.items():
                if dist_type == 'normal':
                    mean, std = dist_params
                    value = np.random.normal(mean, std)
                elif dist_type == 'lognormal':
                    mean, std = dist_params
                    value = np.random.lognormal(mean, std)
                elif dist_type == 'gamma':
                    shape, scale = dist_params
                    value = np.random.gamma(shape, scale)
                elif dist_type == 'beta':
                    alpha, beta = dist_params
                    value = np.random.beta(alpha, beta)
                elif dist_type == 'uniform':
                    low, high = dist_params
                    value = np.random.uniform(low, high)
                else:
                    warnings.warn(f"Unknown distribution type: {dist_type}")
                    continue

                # Ensure positive values for most parameters
                if param_name != 'survival_rate':
                    value = max(0.001, value)
                else:
                    value = np.clip(value, 0.001, 0.999)

                # Update parameter
                if param_name in sim_case:
                    sim_case[param_name] = value
                else:
                    setattr(self, param_name, value)

            # Compute outcomes
            total_cost = self.compute_total_cost(
                sim_case.get('icu_los', base_case['icu_los']),
                sim_case.get('ward_los', base_case['ward_los']),
                sim_case.get('ecmo_days', base_case['ecmo_days'])
            )
            qaly = self.compute_qaly(sim_case.get('survival_rate', base_case['survival_rate']))
            cer = self.compute_cer(total_cost, qaly)

            # Net Monetary Benefit at different WTP thresholds
            wtp_thresholds = [500000, 1000000, 1500000, 2000000, 3000000]
            nmb_values = {f'nmb_wtp_{wtp}': (wtp * qaly) - total_cost for wtp in wtp_thresholds}

            results.append({
                'iteration': i,
                'total_cost': total_cost,
                'qaly': qaly,
                'cer': cer,
                **nmb_values
            })

        return pd.DataFrame(results)

    def two_way_sensitivity_analysis(
        self,
        base_case: Dict,
        param1_name: str,
        param1_range: np.ndarray,
        param2_name: str,
        param2_range: np.ndarray
    ) -> pd.DataFrame:
        """
        Two-way sensitivity analysis for tornado diagrams and heat maps.

        Args:
            base_case: Dictionary with base case values
            param1_name: First parameter name
            param1_range: Array of values for first parameter
            param2_name: Second parameter name
            param2_range: Array of values for second parameter

        Returns:
            DataFrame with results for all combinations
        """
        results = []

        for p1_val in param1_range:
            for p2_val in param2_range:
                case = base_case.copy()

                # Update parameters
                if param1_name in case:
                    case[param1_name] = p1_val
                else:
                    setattr(self, param1_name, p1_val)

                if param2_name in case:
                    case[param2_name] = p2_val
                else:
                    setattr(self, param2_name, p2_val)

                # Compute outcomes
                total_cost = self.compute_total_cost(
                    case.get('icu_los', base_case['icu_los']),
                    case.get('ward_los', base_case['ward_los']),
                    case.get('ecmo_days', base_case['ecmo_days'])
                )
                qaly = self.compute_qaly(case.get('survival_rate', base_case['survival_rate']))
                cer = self.compute_cer(total_cost, qaly)

                results.append({
                    param1_name: p1_val,
                    param2_name: p2_val,
                    'total_cost': total_cost,
                    'qaly': qaly,
                    'cer': cer
                })

        return pd.DataFrame(results)

    def value_of_information_analysis(
        self,
        psa_results: pd.DataFrame,
        wtp_threshold: float = 1500000,
        population_size: int = 1000,
        time_horizon_years: int = 5
    ) -> Dict[str, float]:
        """
        Expected Value of Perfect Information (EVPI) analysis.

        EVPI represents the maximum amount worth paying for perfect information
        to eliminate decision uncertainty.

        Args:
            psa_results: Results from probabilistic_sensitivity_analysis()
            wtp_threshold: Willingness-to-pay threshold
            population_size: Relevant population per year
            time_horizon_years: Years over which decision is relevant

        Returns:
            Dictionary with EVPI metrics
        """
        nmb_col = f'nmb_wtp_{int(wtp_threshold)}'

        if nmb_col not in psa_results.columns:
            # Compute NMB
            nmb = (wtp_threshold * psa_results['qaly']) - psa_results['total_cost']
        else:
            nmb = psa_results[nmb_col]

        # Expected NMB under current uncertainty
        expected_nmb = nmb.mean()

        # Expected NMB with perfect information (max in each iteration)
        perfect_info_nmb = nmb.max()

        # EVPI per person
        evpi_per_person = max(0, perfect_info_nmb - expected_nmb)

        # EVPI for population over time horizon
        # Discount future population benefits
        discount_factor = sum([1 / (1 + self.discount_rate) ** t for t in range(time_horizon_years)])
        evpi_population = evpi_per_person * population_size * discount_factor

        return {
            'evpi_per_person': evpi_per_person,
            'evpi_population': evpi_population,
            'expected_nmb': expected_nmb,
            'perfect_info_nmb': perfect_info_nmb,
            'wtp_threshold': wtp_threshold,
            'population_size': population_size,
            'time_horizon_years': time_horizon_years
        }

    def budget_impact_analysis(
        self,
        current_scenario: Dict,
        new_scenario: Dict,
        population_size: int,
        uptake_rate: float = 1.0,
        years: int = 5
    ) -> pd.DataFrame:
        """
        Budget impact analysis comparing current practice to new intervention.

        Args:
            current_scenario: Dict with current practice parameters
                            (icu_los, ward_los, ecmo_days, survival_rate, n_patients)
            new_scenario: Dict with new intervention parameters
            population_size: Total eligible population per year
            uptake_rate: Proportion adopting new intervention (0-1)
            years: Number of years to project

        Returns:
            DataFrame with yearly budget impact
        """
        results = []

        for year in range(1, years + 1):
            # Linear uptake over time
            current_year_uptake = min(uptake_rate * (year / years), 1.0)
            n_current = int(population_size * (1 - current_year_uptake))
            n_new = int(population_size * current_year_uptake)

            # Current practice costs
            cost_current_per_patient = self.compute_total_cost(
                current_scenario['icu_los'],
                current_scenario['ward_los'],
                current_scenario['ecmo_days']
            )
            total_cost_current = cost_current_per_patient * n_current

            # New intervention costs
            cost_new_per_patient = self.compute_total_cost(
                new_scenario['icu_los'],
                new_scenario['ward_los'],
                new_scenario['ecmo_days']
            )
            total_cost_new = cost_new_per_patient * n_new

            # Total budget
            total_budget = total_cost_current + total_cost_new

            # Incremental budget impact
            incremental_cost = (cost_new_per_patient - cost_current_per_patient) * n_new

            # Discount future costs
            discount_factor = 1 / (1 + self.discount_rate) ** (year - 1)
            discounted_total = total_budget * discount_factor
            discounted_incremental = incremental_cost * discount_factor

            # QALYs
            qaly_current = self.compute_qaly(current_scenario['survival_rate']) * n_current
            qaly_new = self.compute_qaly(new_scenario['survival_rate']) * n_new
            total_qaly = qaly_current + qaly_new
            incremental_qaly = (
                self.compute_qaly(new_scenario['survival_rate']) -
                self.compute_qaly(current_scenario['survival_rate'])
            ) * n_new

            results.append({
                'year': year,
                'n_current_practice': n_current,
                'n_new_intervention': n_new,
                'uptake_rate': current_year_uptake,
                'total_budget': total_budget,
                'incremental_budget': incremental_cost,
                'discounted_total_budget': discounted_total,
                'discounted_incremental_budget': discounted_incremental,
                'total_qaly': total_qaly,
                'incremental_qaly': incremental_qaly,
                'icer': incremental_cost / incremental_qaly if incremental_qaly > 0 else float('inf')
            })

        return pd.DataFrame(results)


def generate_synthetic_quintile_data(
    n_patients: int = 500,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic patient data for demonstration.

    Quintile 1 (lowest risk): Better outcomes, shorter LOS
    Quintile 5 (highest risk): Worse outcomes, longer LOS

    Args:
        n_patients: Total number of patients
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic patient data
    """
    np.random.seed(seed)

    data = []
    patients_per_quintile = n_patients // 5

    for quintile in range(1, 6):
        # Risk-stratified outcomes
        # Higher quintile = higher risk = worse outcomes
        base_survival = 0.65 - (quintile - 1) * 0.10  # 65% → 25%
        base_icu_los = 10 + (quintile - 1) * 5        # 10 → 30 days
        base_ward_los = 5 + (quintile - 1) * 3        # 5 → 17 days
        base_ecmo_days = 5 + (quintile - 1) * 2       # 5 → 13 days

        for _ in range(patients_per_quintile):
            survival = int(np.random.random() < base_survival)

            # Survivors have shorter LOS
            icu_los = max(1, np.random.normal(
                base_icu_los * (0.8 if survival else 1.2),
                base_icu_los * 0.3
            ))
            ward_los = max(0, np.random.normal(
                base_ward_los * survival,  # Non-survivors don't go to ward
                base_ward_los * 0.4
            ))
            ecmo_days = max(1, np.random.normal(
                base_ecmo_days,
                base_ecmo_days * 0.25
            ))

            data.append({
                'patient_id': len(data) + 1,
                'risk_quintile': quintile,
                'survival_to_discharge': survival,
                'icu_los_days': icu_los,
                'ward_los_days': ward_los,
                'ecmo_days': ecmo_days
            })

    return pd.DataFrame(data)


if __name__ == '__main__':
    # Demonstration with synthetic data
    print("=" * 80)
    print("ECMO Cost-Effectiveness Analysis (WP2)")
    print("=" * 80)

    # Initialize analysis with Taiwan-specific parameters
    cea = ECMOCostEffectivenessAnalysis(
        icu_cost_per_day=30000,      # TWD
        ward_cost_per_day=8000,       # TWD
        ecmo_daily_consumable=15000,  # TWD
        ecmo_setup_cost=100000,       # TWD
        qaly_gain_per_survivor=1.5,
        time_horizon_years=1.0,
        discount_rate=0.03,
        currency="TWD"
    )

    # Generate synthetic data
    patient_data = generate_synthetic_quintile_data(n_patients=500)
    print(f"\nGenerated {len(patient_data)} synthetic patient records")
    print(f"Risk quintiles: {sorted(patient_data['risk_quintile'].unique())}")

    # Analyze by quintile
    print("\n" + "=" * 80)
    print("COST-EFFECTIVENESS RATIO (CER) BY RISK QUINTILE")
    print("=" * 80)
    quintile_results = cea.analyze_by_quintile(patient_data)
    print(quintile_results.to_string(index=False))

    # Incremental analysis
    print("\n" + "=" * 80)
    print("INCREMENTAL COST-EFFECTIVENESS RATIO (ICER)")
    print("=" * 80)
    icer_results = cea.compute_icer_by_quintile(quintile_results, baseline_quintile=1)
    print(icer_results.to_string(index=False))

    # CEAC
    print("\n" + "=" * 80)
    print("COST-EFFECTIVENESS ACCEPTABILITY CURVE (CEAC)")
    print("=" * 80)
    print("Computing probabilistic sensitivity analysis...")
    ceac_data = cea.compute_ceac(
        quintile_results,
        wtp_thresholds=np.array([500000, 1000000, 1500000, 2000000, 3000000]),
        n_simulations=1000
    )
    print("\nSample CEAC results (WTP thresholds in TWD/QALY):")
    print(ceac_data.head(15).to_string(index=False))

    # Sensitivity analysis
    print("\n" + "=" * 80)
    print("ONE-WAY SENSITIVITY ANALYSIS (Quintile 3)")
    print("=" * 80)
    q3_data = patient_data[patient_data['risk_quintile'] == 3]
    base_case = {
        'icu_los': q3_data['icu_los_days'].mean(),
        'ward_los': q3_data['ward_los_days'].mean(),
        'ecmo_days': q3_data['ecmo_days'].mean(),
        'survival_rate': q3_data['survival_to_discharge'].mean()
    }

    sensitivity_params = {
        'icu_cost_per_day': (20000, 30000, 40000),
        'survival_rate': (0.30, base_case['survival_rate'], 0.60)
    }

    sens_results = cea.sensitivity_analysis(base_case, sensitivity_params)
    print(sens_results.to_string(index=False))

    print("\n" + "=" * 80)
    print("Analysis complete. Use dashboard.py for interactive visualization.")
    print("=" * 80)
