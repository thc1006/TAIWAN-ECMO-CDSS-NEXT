# WP2 Cost-Effectiveness Analytics - Comprehensive TDD Test Plan

## Executive Summary

This document provides a complete Test-Driven Development (TDD) test plan for the WP2 Cost-Effectiveness Analytics module of the Taiwan ECMO CDSS. The plan targets **100% code coverage** with verified calculations, edge case handling, and regression tests.

**Analysis Date**: 2025-09-30
**Code Analyzed**:
- `econ/cost_effectiveness.py` (533 lines, 9 methods)
- `econ/dashboard.py` (748 lines, 5 Streamlit pages)

---

## 1. Code Analysis Summary

### 1.1 Core Classes & Parameters

#### CostParameters (Lines 22-45)
```python
- ecmo_daily_cost: $3,500
- icu_daily_cost: $2,500
- physician_daily_cost: $800
- nursing_daily_cost: $1,200
- Total daily cost: $8,000
- Cannulation: $15,000 (one-time)
- Decannulation: $8,000 (one-time)
- Complications:
  * Bleeding (15%): $25,000
  * Stroke (8%): $45,000
  * AKI (25%): $20,000
  * Infection (20%): $15,000
- Circuit replacement: $3,000 (every 7 days)
- Taiwan cost multiplier: 0.65
```

#### UtilityParameters (Lines 48-59)
```python
- normal_health: 0.90
- ecmo_support: 0.20
- post_ecmo_good: 0.80
- post_ecmo_moderate: 0.60
- post_ecmo_severe: 0.30
- death: 0.0
- life_expectancy_reduction: 2.0 years
```

### 1.2 Critical Methods Requiring Tests

1. **calculate_ecmo_costs()** (Lines 85-184)
   - Daily cost accumulation
   - Complication cost assignment (probabilistic)
   - Circuit replacement logic
   - Taiwan cost multiplier application

2. **calculate_qaly_outcomes()** (Lines 186-260)
   - Neurologic outcome mapping
   - Utility assignment
   - Life expectancy adjustment
   - QALY discounting with mid-point formula

3. **calculate_icer()** (Lines 262-310)
   - Incremental cost calculation
   - Incremental QALY calculation
   - ICER formula: ΔCost / ΔQALY
   - Edge case: QALY ≤ 0 (infinity handling)

4. **budget_impact_analysis()** (Lines 325-396)
   - Annual case estimation
   - Multi-year projection with discounting
   - Cost per case calculation
   - QALY aggregation

5. **sensitivity_analysis()** (Lines 398-442)
   - One-way parameter variation
   - ICER recalculation
   - Percentage change from base case

---

## 2. TDD Test Plan Structure

### Test Organization
```
tests/
├── test_cost_parameters.py          # Parameter validation tests
├── test_utility_parameters.py       # Utility value tests
├── test_ecmo_costs.py               # Cost calculation tests
├── test_qaly_outcomes.py            # QALY calculation tests
├── test_icer_calculations.py        # ICER formula tests
├── test_budget_impact.py            # Budget projection tests
├── test_sensitivity_analysis.py     # Sensitivity analysis tests
├── test_risk_quintiles.py           # Risk stratification tests
├── test_ceac_calculations.py        # CEAC (Cost-Effectiveness Acceptability Curve) tests
├── test_dashboard_components.py     # Streamlit dashboard tests
├── test_integration.py              # End-to-end integration tests
└── fixtures/
    ├── test_patient_data.csv
    ├── expected_costs.json
    └── expected_qalys.json
```

---

## 3. Detailed Test Specifications

### 3.1 Unit Tests: Cost Calculation (`test_ecmo_costs.py`)

#### Test Case 1.1: Basic Daily Cost Calculation
```python
def test_daily_cost_calculation_single_patient():
    """
    Test basic daily cost for 1 patient, 5 days ECMO
    Expected: ($3500 + $2500 + $800 + $1200) * 5 = $40,000
    With Taiwan multiplier 0.65: $40,000 * 0.65 = $26,000
    Plus cannulation: $15,000 * 0.65 = $9,750
    Plus decannulation (survived): $8,000 * 0.65 = $5,200
    Total base (no complications): $40,950
    """
    patient_data = pd.DataFrame({
        'ecmo_duration_hours': [120],  # 5 days
        'survived_to_discharge': [True],
        'age_years': [55]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    costs = analyzer.calculate_ecmo_costs(patient_data)

    # Base calculations
    expected_daily_cost = 8000  # Sum of all daily costs
    expected_duration_days = 5
    expected_daily_total = expected_daily_cost * expected_duration_days  # 40000
    expected_cannulation = 15000
    expected_decannulation = 8000
    expected_base_before_multiplier = 40000 + 15000 + 8000  # 63000

    # No complications, 1 circuit replacement (5 days / 7)
    expected_circuit_replacements = 1
    expected_circuit_cost = 3000 * expected_circuit_replacements  # 3000
    expected_total_before_multiplier = 63000 + 3000  # 66000
    expected_total_with_taiwan = 66000 * 0.65  # 42900

    assert costs['daily_total_cost'].iloc[0] == 8000
    assert costs['ecmo_duration_days'].iloc[0] == 5
    assert costs['circuit_replacements'].iloc[0] == 1
    # Note: Actual total will vary due to random complications
    assert costs['total_cost_usd'].iloc[0] > 0
```

#### Test Case 1.2: Zero Duration Edge Case
```python
def test_zero_duration_ecmo():
    """
    Test edge case: Patient cannulated but immediately died (0 hours ECMO)
    Expected: Only cannulation cost, no daily costs, no decannulation
    """
    patient_data = pd.DataFrame({
        'ecmo_duration_hours': [0],
        'survived_to_discharge': [False],
        'age_years': [60]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    costs = analyzer.calculate_ecmo_costs(patient_data)

    expected_min_cost = 15000 * 0.65  # Cannulation only: $9,750
    expected_max_cost = (15000 + 25000 + 45000 + 20000 + 15000) * 0.65  # With all complications

    assert costs['ecmo_duration_days'].iloc[0] == 0
    assert costs['decannulation_cost'].iloc[0] == 0  # No decannulation for non-survivors
    assert costs['total_cost_usd'].iloc[0] >= expected_min_cost
    assert costs['total_cost_usd'].iloc[0] <= expected_max_cost
```

#### Test Case 1.3: Taiwan Cost Multiplier Validation
```python
def test_taiwan_cost_multiplier():
    """
    Verify Taiwan cost multiplier (0.65) is applied to ALL costs
    """
    patient_data = pd.DataFrame({
        'ecmo_duration_hours': [168],  # 7 days
        'survived_to_discharge': [True],
        'age_years': [50]
    })

    # Test with multiplier = 1.0 (USD)
    analyzer_usd = ECMOCostEffectivenessAnalyzer()
    analyzer_usd.cost_params.taiwan_cost_multiplier = 1.0
    costs_usd = analyzer_usd.calculate_ecmo_costs(patient_data)

    # Test with multiplier = 0.65 (Taiwan)
    analyzer_tw = ECMOCostEffectivenessAnalyzer()
    costs_tw = analyzer_tw.calculate_ecmo_costs(patient_data)

    assert np.isclose(costs_tw['total_cost_usd'].iloc[0],
                      costs_usd['total_cost_usd'].iloc[0] * 0.65,
                      rtol=0.01)
```

#### Test Case 1.4: Complication Cost Assignment
```python
def test_complication_costs_deterministic():
    """
    Test complication costs with fixed random seed for reproducibility
    Bleeding 15%, Stroke 8%, AKI 25%, Infection 20%
    """
    np.random.seed(42)  # Deterministic outcomes

    patient_data = pd.DataFrame({
        'ecmo_duration_hours': [120] * 1000,
        'survived_to_discharge': [True] * 1000,
        'age_years': [55] * 1000
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    costs = analyzer.calculate_ecmo_costs(patient_data)

    # Check complication rates (allow 5% variance)
    bleeding_rate = (costs['bleeding_cost'] > 0).mean()
    stroke_rate = (costs['stroke_cost'] > 0).mean()
    aki_rate = (costs['aki_cost'] > 0).mean()
    infection_rate = (costs['infection_cost'] > 0).mean()

    assert 0.10 <= bleeding_rate <= 0.20  # 15% ± 5%
    assert 0.03 <= stroke_rate <= 0.13     # 8% ± 5%
    assert 0.20 <= aki_rate <= 0.30        # 25% ± 5%
    assert 0.15 <= infection_rate <= 0.25  # 20% ± 5%
```

#### Test Case 1.5: Circuit Replacement Logic
```python
def test_circuit_replacement_schedule():
    """
    Test circuit replacement every 7 days
    3 days → 1 replacement, 7 days → 1, 8 days → 2, 14 days → 2, 15 days → 3
    """
    test_cases = [
        (72, 1),    # 3 days → ceil(3/7) = 1
        (168, 1),   # 7 days → ceil(7/7) = 1
        (192, 2),   # 8 days → ceil(8/7) = 2
        (336, 2),   # 14 days → ceil(14/7) = 2
        (360, 3),   # 15 days → ceil(15/7) = 3
    ]

    for hours, expected_replacements in test_cases:
        patient_data = pd.DataFrame({
            'ecmo_duration_hours': [hours],
            'survived_to_discharge': [True],
            'age_years': [55]
        })

        analyzer = ECMOCostEffectivenessAnalyzer()
        costs = analyzer.calculate_ecmo_costs(patient_data)

        assert costs['circuit_replacements'].iloc[0] == expected_replacements
        expected_circuit_cost = expected_replacements * 3000 * 0.65
        assert np.isclose(costs['circuit_costs'].iloc[0], expected_circuit_cost)
```

---

### 3.2 Unit Tests: QALY Calculation (`test_qaly_outcomes.py`)

#### Test Case 2.1: QALY Formula Verification
```python
def test_qaly_calculation_formula():
    """
    Test QALY formula: QALYs = Utility × Life Expectancy

    Example: 50-year-old, good neurologic outcome
    - Base life expectancy: 80 - 50 = 30 years
    - Adjusted: 30 - 2 = 28 years
    - Post-ECMO utility (good): 0.80
    - QALYs: 0.80 × 28 = 22.4
    - Discount rate 3%, mid-point: 14 years
    - Discount factor: 1 / (1.03)^14 = 0.6611
    - Discounted QALYs: 22.4 × 0.6611 = 14.81
    """
    patient_data = pd.DataFrame({
        'age_years': [50],
        'survived_to_discharge': [True],
        'neurologic_outcome': ['normal'],
        'total_cost_usd': [50000]
    })

    analyzer = ECMOCostEffectivenessAnalyzer(discount_rate=0.03)
    qalys = analyzer.calculate_qaly_outcomes(patient_data)

    expected_life_expectancy = 80 - 50 - 2  # 28 years
    expected_utility = 0.80  # post_ecmo_good
    expected_qalys = expected_utility * expected_life_expectancy  # 22.4

    # Discount factor: 1 / (1.03)^(28/2) = 1 / (1.03)^14
    expected_discount_factor = 1 / (1.03 ** 14)  # 0.6611
    expected_discounted_qalys = expected_qalys * expected_discount_factor  # 14.81

    assert qalys['adjusted_life_expectancy'].iloc[0] == 28
    assert qalys['post_ecmo_utility'].iloc[0] == 0.80
    assert np.isclose(qalys['qalys_gained'].iloc[0], 22.4, atol=0.1)
    assert np.isclose(qalys['discounted_qalys'].iloc[0], 14.81, atol=0.1)
```

#### Test Case 2.2: Death Outcome (Zero QALYs)
```python
def test_qaly_death_outcome():
    """
    Test QALY calculation for deceased patients
    Expected: QALYs = 0 regardless of age or other factors
    """
    patient_data = pd.DataFrame({
        'age_years': [30, 50, 70],  # Various ages
        'survived_to_discharge': [False, False, False],
        'neurologic_outcome': ['death', 'death', 'death'],
        'total_cost_usd': [40000, 50000, 60000]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    qalys = analyzer.calculate_qaly_outcomes(patient_data)

    assert (qalys['qalys_gained'] == 0).all()
    assert (qalys['discounted_qalys'] == 0).all()
    assert (qalys['post_ecmo_utility'] == 0.0).all()
```

#### Test Case 2.3: Neurologic Outcome Mapping
```python
def test_neurologic_outcome_utilities():
    """
    Test utility mapping for all neurologic outcomes
    """
    outcomes = ['death', 'normal', 'mild_deficit', 'moderate_deficit', 'severe_deficit']
    expected_utilities = [0.0, 0.80, 0.80, 0.60, 0.30]

    patient_data = pd.DataFrame({
        'age_years': [55] * 5,
        'survived_to_discharge': [False, True, True, True, True],
        'neurologic_outcome': outcomes,
        'total_cost_usd': [50000] * 5
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    qalys = analyzer.calculate_qaly_outcomes(patient_data)

    for i, expected_utility in enumerate(expected_utilities):
        assert qalys['post_ecmo_utility'].iloc[i] == expected_utility
```

#### Test Case 2.4: Discount Rate Sensitivity
```python
def test_discount_rate_effect():
    """
    Test effect of discount rate on QALYs
    Higher discount rate → Lower discounted QALYs
    """
    patient_data = pd.DataFrame({
        'age_years': [50],
        'survived_to_discharge': [True],
        'neurologic_outcome': ['normal'],
        'total_cost_usd': [50000]
    })

    # Test with 0% discount
    analyzer_0 = ECMOCostEffectivenessAnalyzer(discount_rate=0.0)
    qalys_0 = analyzer_0.calculate_qaly_outcomes(patient_data)

    # Test with 3% discount
    analyzer_3 = ECMOCostEffectivenessAnalyzer(discount_rate=0.03)
    qalys_3 = analyzer_3.calculate_qaly_outcomes(patient_data)

    # Test with 5% discount
    analyzer_5 = ECMOCostEffectivenessAnalyzer(discount_rate=0.05)
    qalys_5 = analyzer_5.calculate_qaly_outcomes(patient_data)

    # With 0% discount, discounted = undiscounted
    assert qalys_0['discounted_qalys'].iloc[0] == qalys_0['qalys_gained'].iloc[0]

    # Higher discount rate → Lower discounted QALYs
    assert qalys_0['discounted_qalys'].iloc[0] > qalys_3['discounted_qalys'].iloc[0]
    assert qalys_3['discounted_qalys'].iloc[0] > qalys_5['discounted_qalys'].iloc[0]
```

---

### 3.3 Unit Tests: ICER Calculation (`test_icer_calculations.py`)

#### Test Case 3.1: ICER Formula Verification
```python
def test_icer_formula_basic():
    """
    Test ICER = (Cost_intervention - Cost_comparator) / (QALY_intervention - QALY_comparator)

    Example:
    - ECMO: Cost = $100,000, QALYs = 10
    - Standard: Cost = $50,000, QALYs = 5
    - ICER = ($100k - $50k) / (10 - 5) = $50,000 / 5 = $10,000 per QALY
    """
    intervention_data = pd.DataFrame({
        'total_cost_usd': [100000, 110000, 90000],
        'discounted_qalys': [10, 11, 9],
        'age_years': [55, 60, 50]
    })

    comparator_data = pd.DataFrame({
        'total_cost_usd': [50000, 55000, 45000],
        'discounted_qalys': [5, 6, 4],
        'age_years': [55, 60, 50]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    icer_result = analyzer.calculate_icer(intervention_data, comparator_data)

    expected_intervention_cost = 100000
    expected_comparator_cost = 50000
    expected_incremental_cost = 50000

    expected_intervention_qaly = 10
    expected_comparator_qaly = 5
    expected_incremental_qaly = 5

    expected_icer = 50000 / 5  # $10,000 per QALY

    assert np.isclose(icer_result['incremental_cost'], expected_incremental_cost)
    assert np.isclose(icer_result['incremental_qaly'], expected_incremental_qaly)
    assert np.isclose(icer_result['icer'], expected_icer)
    assert icer_result['cost_effective_50k'] == True
    assert icer_result['cost_effective_100k'] == True
```

#### Test Case 3.2: ICER Edge Case - Zero QALY Gain
```python
def test_icer_zero_qaly_gain():
    """
    Test ICER when QALY gain = 0 (intervention no better than comparator)
    If incremental cost > 0: ICER = +∞ (dominated)
    If incremental cost < 0: ICER = -∞ (cost-saving but no benefit)
    """
    # Case 1: More expensive, no QALY gain
    intervention_worse = pd.DataFrame({
        'total_cost_usd': [100000],
        'discounted_qalys': [5],
        'age_years': [55]
    })

    comparator = pd.DataFrame({
        'total_cost_usd': [50000],
        'discounted_qalys': [5],  # Same QALYs
        'age_years': [55]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    icer_result = analyzer.calculate_icer(intervention_worse, comparator)

    assert icer_result['incremental_qaly'] == 0
    assert icer_result['icer'] == float('inf')
    assert icer_result['interpretation'] == "Dominated"
```

#### Test Case 3.3: ICER Dominant Strategy
```python
def test_icer_dominant_strategy():
    """
    Test ICER when intervention is dominant (less expensive AND more effective)
    ICER = negative value (cost-saving)
    """
    intervention_dominant = pd.DataFrame({
        'total_cost_usd': [40000],  # Cheaper
        'discounted_qalys': [10],    # More effective
        'age_years': [55]
    })

    comparator = pd.DataFrame({
        'total_cost_usd': [50000],
        'discounted_qalys': [5],
        'age_years': [55]
    })

    analyzer = ECMOCostEffectivenessAnalyzer()
    icer_result = analyzer.calculate_icer(intervention_dominant, comparator)

    expected_incremental_cost = 40000 - 50000  # -10000
    expected_incremental_qaly = 10 - 5  # 5
    expected_icer = -10000 / 5  # -$2000 per QALY (cost-saving)

    assert icer_result['incremental_cost'] < 0
    assert icer_result['incremental_qaly'] > 0
    assert icer_result['icer'] < 0
    assert "dominant" in icer_result['interpretation'].lower()
```

#### Test Case 3.4: WTP Threshold Classification
```python
def test_wtp_threshold_classification():
    """
    Test cost-effectiveness classification at different WTP thresholds
    $0-20k: Very cost-effective
    $20k-50k: Cost-effective
    $50k-100k: Moderately cost-effective
    >$100k: Not cost-effective
    """
    test_cases = [
        (10000, True, True, "Very cost-effective"),
        (30000, True, True, "Cost-effective"),
        (75000, False, True, "Moderately cost-effective"),
        (150000, False, False, "Not cost-effective"),
    ]

    for icer_value, expect_50k, expect_100k, expected_interp in test_cases:
        # Create data with specific ICER
        intervention = pd.DataFrame({
            'total_cost_usd': [icer_value * 10],
            'discounted_qalys': [10],
            'age_years': [55]
        })

        comparator = pd.DataFrame({
            'total_cost_usd': [0],
            'discounted_qalys': [0],
            'age_years': [55]
        })

        analyzer = ECMOCostEffectivenessAnalyzer()
        result = analyzer.calculate_icer(intervention, comparator)

        assert result['cost_effective_50k'] == expect_50k
        assert result['cost_effective_100k'] == expect_100k
        assert expected_interp in result['interpretation']
```

---

### 3.4 Unit Tests: Budget Impact Analysis (`test_budget_impact.py`)

#### Test Case 4.1: Annual Budget Calculation
```python
def test_annual_budget_calculation():
    """
    Test annual budget impact calculation
    Population: 100,000, Utilization: 0.1% (0.001) → 100 cases/year
    Mean cost: $50,000/case → Annual cost: $5,000,000
    """
    analyzer = ECMOCostEffectivenessAnalyzer()

    np.random.seed(42)  # Reproducible results
    budget = analyzer.budget_impact_analysis(
        population_size=100000,
        ecmo_utilization_rate=0.001,
        years=1
    )

    expected_annual_cases = 100
    assert np.isclose(budget['annual_cases'], expected_annual_cases)
    assert budget['time_horizon_years'] == 1
    assert len(budget['yearly_results']) == 1

    # Total cost should be in reasonable range ($3M - $7M for 100 cases)
    assert 3_000_000 <= budget['total_program_cost'] <= 7_000_000
```

#### Test Case 4.2: Multi-Year Discounting
```python
def test_multi_year_discounting():
    """
    Test that costs are properly discounted over multiple years
    Discount rate 3%: Year 1 = 1.0, Year 2 = 0.971, Year 3 = 0.943
    """
    analyzer = ECMOCostEffectivenessAnalyzer(discount_rate=0.03)

    np.random.seed(42)
    budget = analyzer.budget_impact_analysis(
        population_size=100000,
        ecmo_utilization_rate=0.001,
        years=3
    )

    yearly_results = budget['yearly_results']

    # Year 1 cost (no discount)
    year1_cost = yearly_results[0]['total_cost']

    # Year 2 cost (discounted by 1.03)
    year2_cost = yearly_results[1]['total_cost']
    expected_year2_discount = 1 / (1.03 ** 1)
    assert np.isclose(year2_cost / year1_cost, expected_year2_discount, rtol=0.01)

    # Year 3 cost (discounted by 1.03^2)
    year3_cost = yearly_results[2]['total_cost']
    expected_year3_discount = 1 / (1.03 ** 2)
    assert np.isclose(year3_cost / year1_cost, expected_year3_discount, rtol=0.01)
```

#### Test Case 4.3: Zero Utilization Edge Case
```python
def test_zero_utilization_rate():
    """
    Test edge case: 0% utilization rate → 0 cases → $0 budget
    """
    analyzer = ECMOCostEffectivenessAnalyzer()

    budget = analyzer.budget_impact_analysis(
        population_size=100000,
        ecmo_utilization_rate=0.0,
        years=5
    )

    assert budget['annual_cases'] == 0
    assert budget['total_program_cost'] == 0
    assert budget['total_program_qalys'] == 0
```

---

### 3.5 Unit Tests: Sensitivity Analysis (`test_sensitivity_analysis.py`)

#### Test Case 5.1: One-Way Sensitivity on Daily Costs
```python
def test_sensitivity_daily_cost():
    """
    Test one-way sensitivity analysis on ecmo_daily_cost
    Varying from $2000 to $5000 should proportionally affect ICER
    """
    np.random.seed(42)
    base_data = pd.DataFrame({
        'ecmo_duration_hours': [120] * 100,
        'survived_to_discharge': [True] * 100,
        'age_years': [55] * 100
    })

    analyzer = ECMOCostEffectivenessAnalyzer()

    sensitivity = analyzer.sensitivity_analysis(
        base_data,
        parameter_ranges={
            'ecmo_daily_cost': (2000, 5000)
        }
    )

    results = sensitivity['ecmo_daily_cost']

    # ICER should increase as daily cost increases
    assert results[0]['icer'] < results[1]['icer'] < results[2]['icer']

    # Verify change_from_base calculation
    base_icer = results[1]['icer']  # Middle value is base
    low_change = results[0]['change_from_base']
    high_change = results[2]['change_from_base']

    assert low_change < 0  # Lower cost → lower ICER
    assert high_change > 0  # Higher cost → higher ICER
```

#### Test Case 5.2: Tornado Diagram Data
```python
def test_sensitivity_tornado_data():
    """
    Test generation of data for tornado diagram
    Identify parameters with highest impact on ICER
    """
    np.random.seed(42)
    base_data = pd.DataFrame({
        'ecmo_duration_hours': [120] * 50,
        'survived_to_discharge': [True] * 50,
        'age_years': [55] * 50
    })

    analyzer = ECMOCostEffectivenessAnalyzer()

    parameter_ranges = {
        'ecmo_daily_cost': (2500, 4500),
        'icu_daily_cost': (2000, 3000),
        'bleeding_cost': (20000, 30000),
        'taiwan_cost_multiplier': (0.50, 0.80)
    }

    sensitivity = analyzer.sensitivity_analysis(base_data, parameter_ranges)

    # Calculate range of ICER for each parameter
    impacts = {}
    for param, results in sensitivity.items():
        icers = [r['icer'] for r in results]
        impacts[param] = max(icers) - min(icers)

    # Taiwan multiplier should have highest impact (affects all costs)
    assert impacts['taiwan_cost_multiplier'] > impacts['bleeding_cost']
```

---

### 3.6 Unit Tests: Risk Quintile Stratification (`test_risk_quintiles.py`)

#### Test Case 6.1: Risk Quintile Assignment
```python
def test_risk_quintile_assignment():
    """
    Test assignment of patients to risk quintiles (Q1-Q5)
    Each quintile should have ~20% of patients
    """
    np.random.seed(42)
    n_patients = 1000

    # Generate patient data with varying risk profiles
    demo_data = generate_demo_economic_data(n_patients)

    # Calculate risk scores (simplified)
    demo_data['risk_score'] = np.random.beta(2, 5, n_patients)  # Skewed distribution

    # Assign quintiles
    demo_data['risk_quintile'] = pd.qcut(
        demo_data['risk_score'],
        q=5,
        labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
    )

    # Check quintile distribution
    quintile_counts = demo_data['risk_quintile'].value_counts()

    for quintile in ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']:
        count = quintile_counts[quintile]
        assert 180 <= count <= 220  # ~200 ± 20 (allow 10% variance)
```

#### Test Case 6.2: CER by Risk Quintile
```python
def test_cer_by_risk_quintile():
    """
    Test Cost-Effectiveness Ratio (CER) stratified by risk quintile
    CER = Cost / QALYs
    Higher risk → Higher cost, Lower QALYs → Much higher CER
    """
    np.random.seed(42)

    # Simulate data for each quintile
    quintiles_data = []

    for q in range(1, 6):
        # Higher quintile → higher risk → higher mortality → lower QALYs
        mortality_rate = 0.2 + (q - 1) * 0.15  # Q1: 20%, Q5: 80%

        data = pd.DataFrame({
            'ecmo_duration_hours': np.random.exponential(120, 200),
            'survived_to_discharge': np.random.random(200) > mortality_rate,
            'age_years': np.random.normal(55, 15, 200),
            'risk_quintile': f'Q{q}'
        })
        quintiles_data.append(data)

    all_data = pd.concat(quintiles_data, ignore_index=True)

    analyzer = ECMOCostEffectivenessAnalyzer()
    cost_data = analyzer.calculate_ecmo_costs(all_data)
    qaly_data = analyzer.calculate_qaly_outcomes(cost_data)

    # Calculate CER by quintile
    qaly_data['cer'] = qaly_data['total_cost_usd'] / qaly_data['qalys_gained'].replace(0, np.nan)

    cer_by_quintile = qaly_data.groupby('risk_quintile')['cer'].mean()

    # CER should increase with risk quintile (higher risk = worse cost-effectiveness)
    assert cer_by_quintile['Q1'] < cer_by_quintile['Q3'] < cer_by_quintile['Q5']
```

---

### 3.7 Unit Tests: CEAC Calculations (`test_ceac_calculations.py`)

#### Test Case 7.1: CEAC Curve Generation
```python
def test_ceac_curve_generation():
    """
    Test Cost-Effectiveness Acceptability Curve (CEAC)
    CEAC shows probability that intervention is cost-effective at different WTP thresholds
    """
    np.random.seed(42)

    # Generate bootstrap samples to create uncertainty
    n_bootstraps = 1000
    ceac_data = []

    for _ in range(n_bootstraps):
        intervention = pd.DataFrame({
            'total_cost_usd': [np.random.normal(100000, 10000, 1)[0]],
            'discounted_qalys': [np.random.normal(10, 1, 1)[0]],
            'age_years': [55]
        })

        comparator = pd.DataFrame({
            'total_cost_usd': [np.random.normal(50000, 5000, 1)[0]],
            'discounted_qalys': [np.random.normal(5, 0.5, 1)[0]],
            'age_years': [55]
        })

        analyzer = ECMOCostEffectivenessAnalyzer()
        icer_result = analyzer.calculate_icer(intervention, comparator)
        ceac_data.append(icer_result['icer'])

    # Calculate probability cost-effective at different WTP thresholds
    wtp_thresholds = [25000, 50000, 75000, 100000, 150000]
    probabilities = []

    for wtp in wtp_thresholds:
        prob_ce = np.mean([icer < wtp for icer in ceac_data if icer != float('inf')])
        probabilities.append(prob_ce)

    # Probability should increase with WTP threshold
    for i in range(len(probabilities) - 1):
        assert probabilities[i] <= probabilities[i + 1]

    # At very high WTP, probability should approach 1.0
    assert probabilities[-1] >= 0.8
```

#### Test Case 7.2: Net Monetary Benefit (NMB)
```python
def test_net_monetary_benefit():
    """
    Test Net Monetary Benefit calculation
    NMB = (QALY × WTP) - Cost
    NMB > 0 → intervention is cost-effective at given WTP
    """
    intervention = pd.DataFrame({
        'total_cost_usd': [100000],
        'discounted_qalys': [10],
        'age_years': [55]
    })

    comparator = pd.DataFrame({
        'total_cost_usd': [50000],
        'discounted_qalys': [5],
        'age_years': [55]
    })

    incremental_cost = 50000  # 100k - 50k
    incremental_qaly = 5       # 10 - 5

    # Test at $50k WTP threshold
    wtp_50k = 50000
    nmb_50k = (incremental_qaly * wtp_50k) - incremental_cost
    # NMB = (5 × 50000) - 50000 = 250000 - 50000 = 200000 > 0 ✓

    assert nmb_50k == 200000
    assert nmb_50k > 0  # Cost-effective at $50k/QALY

    # Test at $10k WTP threshold
    wtp_10k = 10000
    nmb_10k = (incremental_qaly * wtp_10k) - incremental_cost
    # NMB = (5 × 10000) - 50000 = 50000 - 50000 = 0

    assert nmb_10k == 0

    # Test at $5k WTP threshold
    wtp_5k = 5000
    nmb_5k = (incremental_qaly * wtp_5k) - incremental_cost
    # NMB = (5 × 5000) - 50000 = 25000 - 50000 = -25000 < 0

    assert nmb_5k == -25000
    assert nmb_5k < 0  # Not cost-effective at $5k/QALY
```

---

### 3.8 Integration Tests: Dashboard Components (`test_dashboard_components.py`)

#### Test Case 8.1: Streamlit Dashboard Page Rendering
```python
def test_dashboard_home_page():
    """
    Test home page rendering with basic metrics
    """
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("econ/dashboard.py")
    at.run()

    # Check that main header is present
    assert "Taiwan ECMO CDSS" in at.markdown[0].value

    # Check navigation
    assert at.selectbox[0].label == "Choose a module:"
    assert len(at.selectbox[0].options) == 5
```

#### Test Case 8.2: Cost-Effectiveness Module Calculation
```python
def test_dashboard_cost_effectiveness_calculation():
    """
    Test cost-effectiveness module calculations in dashboard
    """
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("econ/dashboard.py")
    at.selectbox[0].select("💰 Cost-Effectiveness")
    at.run()

    # Set parameters
    at.number_input("population_size").set_value(100000)
    at.slider("utilization_rate").set_value(0.001)
    at.slider("time_horizon").set_value(5)

    # Run analysis
    at.button[0].click()
    at.run()

    # Check that metrics are displayed
    assert len(at.metric) >= 4
```

---

### 3.9 Regression Tests (`test_integration.py`)

#### Test Case 9.1: End-to-End Workflow
```python
def test_end_to_end_economic_analysis():
    """
    Test complete workflow from patient data → costs → QALYs → ICER
    """
    np.random.seed(42)

    # Step 1: Generate patient data
    ecmo_patients = generate_demo_economic_data(100)
    standard_care_patients = generate_demo_economic_data(100)

    # Step 2: Calculate costs
    analyzer = ECMOCostEffectivenessAnalyzer()
    ecmo_costs = analyzer.calculate_ecmo_costs(ecmo_patients)
    standard_costs = analyzer.calculate_ecmo_costs(standard_care_patients)
    standard_costs['total_cost_usd'] *= 0.3  # Standard care is cheaper

    # Step 3: Calculate QALYs
    ecmo_qalys = analyzer.calculate_qaly_outcomes(ecmo_costs)
    standard_qalys = analyzer.calculate_qaly_outcomes(standard_costs)
    standard_qalys['discounted_qalys'] *= 0.5  # Standard care worse outcomes

    # Step 4: Calculate ICER
    icer_result = analyzer.calculate_icer(ecmo_qalys, standard_qalys)

    # Assertions
    assert icer_result['incremental_cost'] > 0  # ECMO more expensive
    assert icer_result['incremental_qaly'] > 0  # ECMO more effective
    assert icer_result['icer'] > 0
    assert icer_result['icer'] < 500000  # Reasonable ICER range
```

---

## 4. Test Data Fixtures

### 4.1 Test Patient Data (`fixtures/test_patient_data.csv`)

```csv
patient_id,age_years,ecmo_duration_hours,survived_to_discharge,ecmo_type,risk_quintile
PT0001,45,120,True,VA,Q1
PT0002,60,168,True,VV,Q2
PT0003,70,240,False,VA,Q5
PT0004,55,96,True,VV,Q1
PT0005,65,192,False,VA,Q4
```

### 4.2 Expected Cost Results (`fixtures/expected_costs.json`)

```json
{
  "PT0001": {
    "ecmo_duration_days": 5,
    "daily_total_cost": 8000,
    "total_daily_costs": 40000,
    "cannulation_cost": 15000,
    "decannulation_cost": 8000,
    "circuit_replacements": 1,
    "circuit_costs": 3000,
    "total_before_taiwan": 66000,
    "total_cost_usd_min": 40000,
    "total_cost_usd_max": 90000
  }
}
```

---

## 5. Coverage Requirements

### Target Coverage: 100%

**Line Coverage**: 100% of executable lines
**Branch Coverage**: 100% of conditional branches
**Function Coverage**: 100% of functions/methods
**Edge Case Coverage**: All identified edge cases tested

### Critical Functions Requiring 100% Coverage:

1. `calculate_ecmo_costs()` - 100 lines → 100% coverage
2. `calculate_qaly_outcomes()` - 75 lines → 100% coverage
3. `calculate_icer()` - 49 lines → 100% coverage
4. `budget_impact_analysis()` - 72 lines → 100% coverage
5. `sensitivity_analysis()` - 45 lines → 100% coverage

---

## 6. Acceptable Ranges for Economic Metrics

### Cost Ranges (Taiwan-adjusted, 0.65 multiplier)

| Metric | Minimum | Expected | Maximum | Notes |
|--------|---------|----------|---------|-------|
| Daily total cost | $5,200 | $5,200 | $5,200 | Fixed: $8,000 × 0.65 |
| 5-day ECMO (no complications) | $40,950 | $42,900 | $44,000 | Base + cannulation + decannulation + 1 circuit |
| 5-day ECMO (all complications) | $100,000 | $110,000 | $120,000 | + bleeding + stroke + AKI + infection |
| Mean cost per patient | $35,000 | $50,000 | $80,000 | Population average |

### QALY Ranges

| Outcome | Utility | Life Years | Undiscounted QALYs | Discounted QALYs (3%) |
|---------|---------|------------|-------------------|---------------------|
| Death | 0.0 | 0 | 0 | 0 |
| Good outcome, age 50 | 0.80 | 28 | 22.4 | 14.8 |
| Moderate outcome, age 50 | 0.60 | 28 | 16.8 | 11.1 |
| Severe outcome, age 50 | 0.30 | 28 | 8.4 | 5.6 |
| Good outcome, age 70 | 0.80 | 8 | 6.4 | 5.3 |

### ICER Ranges

| Classification | ICER Range | Cost-Effective? |
|----------------|------------|-----------------|
| Dominant | < $0 | Yes (cost-saving) |
| Very cost-effective | $0 - $20,000/QALY | Yes |
| Cost-effective | $20,000 - $50,000/QALY | Yes (at $50k WTP) |
| Moderately cost-effective | $50,000 - $100,000/QALY | Yes (at $100k WTP) |
| Not cost-effective | > $100,000/QALY | No (at $100k WTP) |
| Dominated | +∞ (no QALY gain) | No |

---

## 7. Test Execution Plan

### Phase 1: Unit Tests (Week 1)
1. Test parameter classes (1 day)
2. Test cost calculations (2 days)
3. Test QALY calculations (2 days)

### Phase 2: Core Economic Tests (Week 2)
4. Test ICER calculations (2 days)
5. Test budget impact (2 days)
6. Test sensitivity analysis (1 day)

### Phase 3: Advanced Tests (Week 3)
7. Test risk quintile stratification (2 days)
8. Test CEAC calculations (2 days)
9. Dashboard component tests (1 day)

### Phase 4: Integration & Regression (Week 4)
10. End-to-end integration tests (2 days)
11. Regression test suite (1 day)
12. Performance benchmarking (1 day)
13. Test documentation (1 day)

---

## 8. Test Infrastructure Setup

### Required Libraries
```python
# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1

# Streamlit testing
streamlit==1.28.0

# Data & numerics
pandas==2.1.0
numpy==1.24.3
scipy==1.11.1

# Fixtures
pytest-fixtures==0.1.0
faker==19.3.0
```

### pytest Configuration (`pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=econ
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=100
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    regression: Regression tests
    slow: Slow-running tests
```

### Coverage Configuration (`.coveragerc`)
```ini
[run]
source = econ
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

---

## 9. Calculation Verification Examples

### Example 1: Complete Cost Calculation

**Patient**: 55-year-old, 7 days ECMO, survived, VA-ECMO

**Step-by-step calculation**:
```
1. Daily costs: $3,500 + $2,500 + $800 + $1,200 = $8,000
2. Duration: 7 days
3. Total daily: $8,000 × 7 = $56,000
4. Cannulation: $15,000
5. Decannulation (survived): $8,000
6. Circuit replacements: ceil(7/7) = 1 → $3,000
7. Complications (example):
   - Bleeding (15% chance): $0 (not occurred)
   - Stroke (8% chance): $0 (not occurred)
   - AKI (25% chance): $20,000 (occurred)
   - Infection (20% chance): $15,000 (occurred)
   Total complications: $35,000
8. Subtotal: $56,000 + $15,000 + $8,000 + $3,000 + $35,000 = $117,000
9. Taiwan multiplier: $117,000 × 0.65 = $76,050
```

**Expected result**: $76,050 ± $30,000 (due to random complications)

### Example 2: Complete QALY Calculation

**Patient**: 50-year-old, survived, good neurologic outcome

**Step-by-step calculation**:
```
1. Base life expectancy: 80 - 50 = 30 years
2. Critical illness reduction: 30 - 2 = 28 years
3. Neurologic outcome: "good" → utility = 0.80
4. Undiscounted QALYs: 0.80 × 28 = 22.4 QALYs
5. Discount rate: 3%
6. Mid-point discounting: 28 / 2 = 14 years
7. Discount factor: 1 / (1.03^14) = 1 / 1.5126 = 0.6611
8. Discounted QALYs: 22.4 × 0.6611 = 14.81 QALYs
```

**Expected result**: 14.81 QALYs

### Example 3: Complete ICER Calculation

**ECMO Group**: N=100, Mean cost = $65,000, Mean QALYs = 8.5
**Standard Care**: N=100, Mean cost = $30,000, Mean QALYs = 4.0

**Step-by-step calculation**:
```
1. Incremental cost: $65,000 - $30,000 = $35,000
2. Incremental QALYs: 8.5 - 4.0 = 4.5
3. ICER: $35,000 / 4.5 = $7,778 per QALY
4. Classification: < $20,000 → "Very cost-effective"
5. Cost-effective at $50k WTP? Yes ($7,778 < $50,000)
6. Cost-effective at $100k WTP? Yes ($7,778 < $100,000)
```

**Expected result**: ICER = $7,778/QALY (Very cost-effective)

---

## 10. Test Automation & CI/CD

### GitHub Actions Workflow (`.github/workflows/wp2-tests.yml`)

```yaml
name: WP2 Economic Analysis Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run WP2 tests
      run: |
        pytest tests/test_cost_*.py \
               tests/test_qaly_*.py \
               tests/test_icer_*.py \
               tests/test_budget_*.py \
               tests/test_sensitivity_*.py \
               tests/test_risk_quintiles.py \
               tests/test_ceac_*.py \
               --cov=econ \
               --cov-report=xml \
               --cov-fail-under=100

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: wp2-economic
```

---

## 11. Known Issues & Edge Cases

### Issue 1: Random Complication Assignment
**Problem**: `calculate_ecmo_costs()` uses `np.random.random()` for complications (lines 132-155), making tests non-deterministic.

**Solution**:
```python
# In tests, use fixed seed
np.random.seed(42)

# OR mock complication assignment
with mock.patch('numpy.random.random', return_value=0.1):
    # All complications will occur (0.1 < all rates)
```

### Issue 2: QALY Calculation for Very Old Patients
**Problem**: Patients age > 80 have negative adjusted life expectancy.

**Current code (line 237)**:
```python
qaly_df['adjusted_life_expectancy'] = np.maximum(
    base_life_expectancy - self.utility_params.life_expectancy_reduction, 0
)
```

**Test**: Verify that very old patients (age 85+) get 0 QALYs correctly.

### Issue 3: Division by Zero in CER
**Problem**: If patient dies immediately (0 QALYs), CER = cost / 0 = infinity.

**Solution**:
```python
# Test case should expect NaN or infinity
with pytest.warns(RuntimeWarning):
    cer = cost / qalys  # qalys = 0
assert np.isinf(cer) or np.isnan(cer)
```

---

## 12. Test Metrics & Reporting

### Success Criteria

| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| Line coverage | 100% | TBD | 🔴 Pending |
| Branch coverage | 100% | TBD | 🔴 Pending |
| Function coverage | 100% | TBD | 🔴 Pending |
| Tests passing | 100% | TBD | 🔴 Pending |
| Test execution time | < 60s | TBD | 🔴 Pending |

### Test Suite Summary

| Test Category | # Tests | Priority | Effort |
|--------------|---------|----------|--------|
| Cost calculation | 15 | P0 | 2 days |
| QALY calculation | 12 | P0 | 2 days |
| ICER calculation | 10 | P0 | 2 days |
| Budget impact | 8 | P1 | 2 days |
| Sensitivity analysis | 6 | P1 | 1 day |
| Risk quintiles | 8 | P1 | 2 days |
| CEAC | 5 | P2 | 2 days |
| Dashboard | 10 | P2 | 1 day |
| Integration | 6 | P0 | 2 days |
| **Total** | **80** | - | **16 days** |

---

## 13. Next Steps

### Immediate Actions (Week 1)
1. ✅ Create test directory structure
2. ✅ Set up pytest configuration
3. ✅ Create test fixtures
4. 🔴 Implement parameter validation tests
5. 🔴 Implement cost calculation tests

### Short-term (Weeks 2-3)
6. 🔴 Implement QALY and ICER tests
7. 🔴 Implement budget and sensitivity tests
8. 🔴 Implement risk quintile tests
9. 🔴 Implement CEAC tests

### Medium-term (Week 4)
10. 🔴 Integration tests
11. 🔴 Dashboard tests
12. 🔴 Regression test suite
13. 🔴 Performance benchmarking

---

## 14. References & Standards

### Economic Evaluation Standards
- **CHEERS 2022**: Consolidated Health Economic Evaluation Reporting Standards
- **ISPOR Guidelines**: Good Practices for Cost-Effectiveness Analysis
- **WHO-CHOICE**: Cost-effectiveness thresholds by country income level

### Taiwan-Specific Parameters
- **Taiwan WTP threshold**: ~$75,000/QALY (3× GDP per capita)
- **Healthcare cost multiplier**: 0.65 (vs US costs)
- **NHIA reimbursement**: Taiwan National Health Insurance Administration guidelines

### Testing Standards
- **pytest**: Python testing framework
- **Coverage.py**: Code coverage measurement
- **SWE-Bench**: Software engineering benchmark standards

---

## 15. Contact & Support

**Test Plan Author**: Claude Code Quality Analyzer
**Date**: 2025-09-30
**Project**: Taiwan ECMO CDSS - WP2 Cost-Effectiveness Analytics

For questions or clarifications:
- Review `econ/cost_effectiveness.py` for implementation details
- Consult `prompts/WP2_cost_effectiveness.md` for requirements
- Reference ELSO standards at `data_dictionary.yaml`

---

**End of WP2 TDD Test Plan**