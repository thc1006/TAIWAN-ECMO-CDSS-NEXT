"""
Unit Tests for Cost-Effectiveness Analysis Module (WP2)
Tests CER/ICER calculations, CEAC generation, NHI calculations, PSA/VOI analysis.
"""

import pytest
import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from econ.cost_effectiveness import (
    ECMOCostEffectivenessAnalysis,
    generate_synthetic_quintile_data
)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestInitialization:
    """Test ECMOCostEffectivenessAnalysis initialization."""

    def test_default_initialization(self):
        """Test default TWD parameters."""
        cea = ECMOCostEffectivenessAnalysis()

        assert cea.icu_cost_per_day == 30000
        assert cea.currency == "TWD"
        assert cea.use_nhi_rates is False

    def test_custom_initialization(self):
        """Test custom parameters."""
        cea = ECMOCostEffectivenessAnalysis(
            icu_cost_per_day=50000,
            currency="USD",
            discount_rate=0.05
        )

        assert cea.icu_cost_per_day == 50000
        assert cea.currency == "USD"
        assert cea.discount_rate == 0.05

    def test_invalid_currency(self):
        """Test invalid currency raises error."""
        with pytest.raises(ValueError, match="Unsupported currency"):
            ECMOCostEffectivenessAnalysis(currency="INVALID")

    @pytest.mark.parametrize("currency", ["TWD", "USD", "EUR"])
    def test_supported_currencies(self, currency):
        """Test all supported currencies."""
        cea = ECMOCostEffectivenessAnalysis(currency=currency)
        assert cea.currency == currency


# ============================================================================
# COST CALCULATION TESTS
# ============================================================================

class TestCostCalculations:
    """Test cost computation methods."""

    def test_compute_total_cost_basic(self):
        """Test basic cost computation."""
        cea = ECMOCostEffectivenessAnalysis(
            icu_cost_per_day=30000,
            ward_cost_per_day=8000,
            ecmo_daily_consumable=15000,
            ecmo_setup_cost=100000
        )

        total_cost = cea.compute_total_cost(
            icu_los_days=10,
            ward_los_days=5,
            ecmo_days=7
        )

        expected = (10 * 30000) + (5 * 8000) + 100000 + (7 * 15000)
        assert total_cost == expected

    def test_compute_total_cost_zero_ward(self):
        """Test cost with zero ward days."""
        cea = ECMOCostEffectivenessAnalysis()

        total_cost = cea.compute_total_cost(
            icu_los_days=10,
            ward_los_days=0,
            ecmo_days=5
        )

        assert total_cost > 0

    def test_cost_scales_with_los(self):
        """Test that cost scales linearly with LOS."""
        cea = ECMOCostEffectivenessAnalysis()

        cost_1 = cea.compute_total_cost(10, 5, 5)
        cost_2 = cea.compute_total_cost(20, 10, 10)

        # Cost should roughly double
        assert cost_2 > cost_1


# ============================================================================
# QALY CALCULATION TESTS
# ============================================================================

class TestQALYCalculations:
    """Test QALY computation methods."""

    def test_compute_qaly_full_survival(self):
        """Test QALY with 100% survival."""
        cea = ECMOCostEffectivenessAnalysis(
            qaly_gain_per_survivor=1.5,
            time_horizon_years=1.0,
            discount_rate=0.0  # No discounting
        )

        qaly = cea.compute_qaly(survival_rate=1.0, quality_of_life=1.0)

        assert qaly == 1.5

    def test_compute_qaly_with_discounting(self):
        """Test QALY with time discounting."""
        cea = ECMOCostEffectivenessAnalysis(
            qaly_gain_per_survivor=1.5,
            time_horizon_years=5.0,
            discount_rate=0.03
        )

        qaly = cea.compute_qaly(survival_rate=1.0)

        # Should be less than undiscounted
        assert qaly < 1.5

    def test_compute_qaly_reduced_qol(self):
        """Test QALY with reduced quality of life."""
        cea = ECMOCostEffectivenessAnalysis(qaly_gain_per_survivor=1.5)

        qaly_full = cea.compute_qaly(1.0, quality_of_life=1.0)
        qaly_reduced = cea.compute_qaly(1.0, quality_of_life=0.7)

        assert qaly_reduced < qaly_full
        assert abs(qaly_reduced / qaly_full - 0.7) < 0.01


# ============================================================================
# CER CALCULATION TESTS
# ============================================================================

class TestCER:
    """Test Cost-Effectiveness Ratio calculations."""

    def test_compute_cer_basic(self):
        """Test basic CER computation."""
        cea = ECMOCostEffectivenessAnalysis()

        cer = cea.compute_cer(total_cost=500000, qaly=1.0)

        assert cer == 500000

    def test_compute_cer_zero_qaly(self):
        """Test CER with zero QALYs."""
        cea = ECMOCostEffectivenessAnalysis()

        cer = cea.compute_cer(total_cost=500000, qaly=0.0)

        assert cer == float('inf')

    def test_cer_decreases_with_effectiveness(self):
        """Test that CER decreases as effectiveness increases."""
        cea = ECMOCostEffectivenessAnalysis()

        cer_low = cea.compute_cer(500000, 0.5)
        cer_high = cea.compute_cer(500000, 1.5)

        assert cer_high < cer_low


# ============================================================================
# ICER CALCULATION TESTS
# ============================================================================

class TestICER:
    """Test Incremental Cost-Effectiveness Ratio calculations."""

    def test_compute_icer_basic(self):
        """Test basic ICER computation."""
        cea = ECMOCostEffectivenessAnalysis()

        icer = cea.compute_icer(
            cost_intervention=600000,
            cost_comparator=400000,
            qaly_intervention=1.2,
            qaly_comparator=0.8
        )

        expected_icer = (600000 - 400000) / (1.2 - 0.8)
        assert icer == expected_icer

    def test_icer_dominated_intervention(self):
        """Test ICER when intervention is dominated (more costly, less effective)."""
        cea = ECMOCostEffectivenessAnalysis()

        icer = cea.compute_icer(
            cost_intervention=600000,
            cost_comparator=400000,
            qaly_intervention=0.8,
            qaly_comparator=1.2
        )

        # Should be infinity (dominated)
        assert icer == float('inf')

    def test_icer_dominant_intervention(self):
        """Test ICER when intervention is dominant (less costly, more effective)."""
        cea = ECMOCostEffectivenessAnalysis()

        icer = cea.compute_icer(
            cost_intervention=400000,
            cost_comparator=600000,
            qaly_intervention=1.5,
            qaly_comparator=1.0
        )

        # Should be negative (dominant)
        assert icer < 0


# ============================================================================
# QUINTILE ANALYSIS TESTS
# ============================================================================

class TestQuintileAnalysis:
    """Test risk quintile stratified analysis."""

    def test_analyze_by_quintile(self, synthetic_cea_data):
        """Test quintile-stratified analysis."""
        cea = ECMOCostEffectivenessAnalysis()

        results = cea.analyze_by_quintile(synthetic_cea_data)

        # Check structure
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 5  # 5 quintiles

        # Check columns
        required_cols = ['quintile', 'n_patients', 'survival_rate',
                        'total_cost', 'qaly', 'cer']
        for col in required_cols:
            assert col in results.columns

    def test_quintile_survival_gradient(self, synthetic_cea_data):
        """Test that survival decreases across quintiles."""
        cea = ECMOCostEffectivenessAnalysis()

        results = cea.analyze_by_quintile(synthetic_cea_data)

        # Survival should generally decrease from Q1 to Q5
        survival_rates = results['survival_rate'].values
        # Allow for some noise, but overall trend should be decreasing
        assert survival_rates[0] > survival_rates[-1]

    def test_quintile_cost_gradient(self, synthetic_cea_data):
        """Test that costs increase across quintiles."""
        cea = ECMOCostEffectivenessAnalysis()

        results = cea.analyze_by_quintile(synthetic_cea_data)

        # Costs should generally increase from Q1 to Q5
        costs = results['total_cost'].values
        assert costs[-1] > costs[0]

    def test_compute_icer_by_quintile(self, synthetic_cea_data):
        """Test incremental analysis by quintile."""
        cea = ECMOCostEffectivenessAnalysis()

        quintile_results = cea.analyze_by_quintile(synthetic_cea_data)
        icer_results = cea.compute_icer_by_quintile(quintile_results)

        # Check structure
        assert isinstance(icer_results, pd.DataFrame)
        assert len(icer_results) == 5

        # Baseline quintile should have ICER of 0
        baseline_row = icer_results[icer_results['quintile'] == 1].iloc[0]
        assert baseline_row['icer_vs_baseline'] == 0


# ============================================================================
# CEAC TESTS
# ============================================================================

class TestCEAC:
    """Test Cost-Effectiveness Acceptability Curve."""

    def test_compute_ceac_basic(self, synthetic_cea_data):
        """Test basic CEAC computation."""
        cea = ECMOCostEffectivenessAnalysis()

        quintile_results = cea.analyze_by_quintile(synthetic_cea_data)
        ceac_data = cea.compute_ceac(
            quintile_results,
            wtp_thresholds=np.array([500000, 1000000, 2000000]),
            n_simulations=100  # Small for speed
        )

        # Check structure
        assert isinstance(ceac_data, pd.DataFrame)
        assert 'quintile' in ceac_data.columns
        assert 'wtp_threshold' in ceac_data.columns
        assert 'probability_cost_effective' in ceac_data.columns

        # Probabilities should be between 0 and 1
        probs = ceac_data['probability_cost_effective'].values
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

    def test_ceac_monotonic_with_wtp(self, synthetic_cea_data):
        """Test that probability increases with WTP threshold."""
        cea = ECMOCostEffectivenessAnalysis()

        quintile_results = cea.analyze_by_quintile(synthetic_cea_data)
        ceac_data = cea.compute_ceac(
            quintile_results,
            wtp_thresholds=np.array([500000, 1500000, 3000000]),
            n_simulations=100
        )

        # For each quintile, probability should generally increase with WTP
        for quintile in [1, 2, 3, 4, 5]:
            q_data = ceac_data[ceac_data['quintile'] == quintile]
            probs = q_data['probability_cost_effective'].values

            # Should be weakly increasing
            # (Allow for Monte Carlo noise)
            assert probs[-1] >= probs[0] - 0.2


# ============================================================================
# SENSITIVITY ANALYSIS TESTS
# ============================================================================

class TestSensitivityAnalysis:
    """Test sensitivity analysis methods."""

    def test_one_way_sensitivity(self):
        """Test one-way sensitivity analysis."""
        cea = ECMOCostEffectivenessAnalysis()

        base_case = {
            'icu_los': 15,
            'ward_los': 7,
            'ecmo_days': 8,
            'survival_rate': 0.55
        }

        parameters = {
            'icu_cost_per_day': (20000, 30000, 40000),
            'survival_rate': (0.40, 0.55, 0.70)
        }

        results = cea.sensitivity_analysis(base_case, parameters)

        # Check structure
        assert isinstance(results, pd.DataFrame)
        assert 'parameter' in results.columns
        assert 'scenario' in results.columns
        assert 'cer' in results.columns

    def test_two_way_sensitivity(self):
        """Test two-way sensitivity analysis."""
        cea = ECMOCostEffectivenessAnalysis()

        base_case = {
            'icu_los': 15,
            'ward_los': 7,
            'ecmo_days': 8,
            'survival_rate': 0.55
        }

        results = cea.two_way_sensitivity_analysis(
            base_case,
            'icu_los',
            np.array([10, 15, 20]),
            'survival_rate',
            np.array([0.4, 0.55, 0.7])
        )

        # Check structure
        assert isinstance(results, pd.DataFrame)
        assert 'icu_los' in results.columns
        assert 'survival_rate' in results.columns
        assert 'cer' in results.columns
        assert len(results) == 9  # 3x3 grid


# ============================================================================
# PSA TESTS
# ============================================================================

class TestPSA:
    """Test Probabilistic Sensitivity Analysis."""

    def test_psa_basic(self):
        """Test basic PSA."""
        cea = ECMOCostEffectivenessAnalysis()

        base_case = {
            'icu_los': 15,
            'ward_los': 7,
            'ecmo_days': 8,
            'survival_rate': 0.55
        }

        parameter_distributions = {
            'icu_los': ('normal', (15, 3)),
            'survival_rate': ('beta', (55, 45))  # Beta distribution for proportions
        }

        psa_results = cea.probabilistic_sensitivity_analysis(
            base_case,
            parameter_distributions,
            n_simulations=100,
            seed=42
        )

        # Check structure
        assert isinstance(psa_results, pd.DataFrame)
        assert len(psa_results) == 100
        assert 'total_cost' in psa_results.columns
        assert 'qaly' in psa_results.columns
        assert 'cer' in psa_results.columns

    def test_psa_reproducibility(self):
        """Test that PSA is reproducible with seed."""
        cea1 = ECMOCostEffectivenessAnalysis()
        cea2 = ECMOCostEffectivenessAnalysis()

        base_case = {
            'icu_los': 15,
            'ward_los': 7,
            'ecmo_days': 8,
            'survival_rate': 0.55
        }

        parameter_distributions = {
            'icu_los': ('normal', (15, 3)),
        }

        psa1 = cea1.probabilistic_sensitivity_analysis(
            base_case, parameter_distributions, n_simulations=50, seed=42
        )
        psa2 = cea2.probabilistic_sensitivity_analysis(
            base_case, parameter_distributions, n_simulations=50, seed=42
        )

        # Should be identical
        pd.testing.assert_frame_equal(psa1, psa2)


# ============================================================================
# VOI ANALYSIS TESTS
# ============================================================================

class TestVOI:
    """Test Value of Information analysis."""

    def test_evpi_calculation(self):
        """Test EVPI calculation."""
        cea = ECMOCostEffectivenessAnalysis()

        # Create mock PSA results
        psa_results = pd.DataFrame({
            'iteration': range(100),
            'total_cost': np.random.normal(500000, 50000, 100),
            'qaly': np.random.normal(1.0, 0.2, 100),
            'cer': np.random.normal(500000, 100000, 100)
        })

        voi_results = cea.value_of_information_analysis(
            psa_results,
            wtp_threshold=1500000,
            population_size=1000,
            time_horizon_years=5
        )

        # Check structure
        assert 'evpi_per_person' in voi_results
        assert 'evpi_population' in voi_results
        assert 'expected_nmb' in voi_results

        # EVPI should be non-negative
        assert voi_results['evpi_per_person'] >= 0
        assert voi_results['evpi_population'] >= 0


# ============================================================================
# BUDGET IMPACT TESTS
# ============================================================================

class TestBudgetImpact:
    """Test Budget Impact Analysis."""

    def test_budget_impact_basic(self):
        """Test basic budget impact analysis."""
        cea = ECMOCostEffectivenessAnalysis()

        current_scenario = {
            'icu_los': 20,
            'ward_los': 5,
            'ecmo_days': 10,
            'survival_rate': 0.5
        }

        new_scenario = {
            'icu_los': 15,
            'ward_los': 8,
            'ecmo_days': 7,
            'survival_rate': 0.65
        }

        results = cea.budget_impact_analysis(
            current_scenario,
            new_scenario,
            population_size=100,
            uptake_rate=1.0,
            years=5
        )

        # Check structure
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 5
        assert 'year' in results.columns
        assert 'total_budget' in results.columns
        assert 'incremental_budget' in results.columns
        assert 'icer' in results.columns

    def test_budget_impact_uptake_increases(self):
        """Test that uptake increases over years."""
        cea = ECMOCostEffectivenessAnalysis()

        current_scenario = {
            'icu_los': 20,
            'ward_los': 5,
            'ecmo_days': 10,
            'survival_rate': 0.5
        }

        new_scenario = {
            'icu_los': 15,
            'ward_los': 8,
            'ecmo_days': 7,
            'survival_rate': 0.65
        }

        results = cea.budget_impact_analysis(
            current_scenario,
            new_scenario,
            population_size=100,
            uptake_rate=1.0,
            years=5
        )

        # Uptake should increase
        uptake_rates = results['uptake_rate'].values
        assert uptake_rates[0] < uptake_rates[-1]


# ============================================================================
# NHI CALCULATIONS TESTS
# ============================================================================

class TestNHICalculations:
    """Test Taiwan NHI-specific calculations."""

    def test_nhi_reimbursement_va_ecmo(self):
        """Test NHI reimbursement for VA-ECMO."""
        cea = ECMOCostEffectivenessAnalysis(
            use_nhi_rates=True,
            ecmo_mode='VA'
        )

        nhi_results = cea.compute_nhi_reimbursement(
            icu_los_days=10,
            ecmo_days=7
        )

        # Check structure
        assert 'drg_payment' in nhi_results
        assert 'total_reimbursement' in nhi_results
        assert 'actual_cost' in nhi_results
        assert 'margin' in nhi_results
        assert 'margin_pct' in nhi_results

        # DRG payment should match expected
        assert nhi_results['drg_payment'] == cea.NHI_DRG_RATES['ECMO_VA']

    def test_nhi_reimbursement_vv_ecmo(self):
        """Test NHI reimbursement for VV-ECMO."""
        cea = ECMOCostEffectivenessAnalysis(
            use_nhi_rates=True,
            ecmo_mode='VV'
        )

        nhi_results = cea.compute_nhi_reimbursement(
            icu_los_days=10,
            ecmo_days=7
        )

        assert nhi_results['drg_payment'] == cea.NHI_DRG_RATES['ECMO_VV']


# ============================================================================
# CURRENCY CONVERSION TESTS
# ============================================================================

class TestCurrencyConversion:
    """Test currency conversion."""

    def test_convert_twd_to_usd(self):
        """Test TWD to USD conversion."""
        cea = ECMOCostEffectivenessAnalysis(currency='TWD')

        usd_amount = cea.convert_currency(31500, 'USD')

        # Should be approximately 1000 USD
        assert abs(usd_amount - 1000) < 10

    def test_convert_usd_to_twd(self):
        """Test USD to TWD conversion."""
        cea = ECMOCostEffectivenessAnalysis(currency='USD')

        twd_amount = cea.convert_currency(1000, 'TWD')

        # Should be approximately 31500 TWD
        assert abs(twd_amount - 31500) < 500


# ============================================================================
# SYNTHETIC DATA GENERATION TESTS
# ============================================================================

class TestSyntheticDataGeneration:
    """Test synthetic data generation utility."""

    def test_generate_synthetic_quintile_data(self):
        """Test synthetic data generation."""
        data = generate_synthetic_quintile_data(n_patients=500, seed=42)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 500
        assert set(data['risk_quintile'].unique()) == {1, 2, 3, 4, 5}

    def test_synthetic_data_survival_gradient(self):
        """Test that synthetic data has survival gradient."""
        data = generate_synthetic_quintile_data(n_patients=500, seed=42)

        # Group by quintile and check survival rates
        survival_by_q = data.groupby('risk_quintile')['survival_to_discharge'].mean()

        # Q1 should have higher survival than Q5
        assert survival_by_q[1] > survival_by_q[5]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
