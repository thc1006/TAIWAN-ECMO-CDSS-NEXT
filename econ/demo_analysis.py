"""
Comprehensive Cost-Effectiveness Analysis Demonstration (WP2)

Full workflow demonstration including:
1. Data integration (synthetic Taiwan ECMO data)
2. Risk stratification
3. Cost-effectiveness analysis
4. Sensitivity analyses (one-way, two-way, probabilistic)
5. Value of information analysis
6. Budget impact analysis
7. Publication-ready reporting

This demonstrates the complete CEA pipeline following CHEERS 2022 guidelines.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from econ.cost_effectiveness import ECMOCostEffectivenessAnalysis
from econ.data_integration import ECMODataIntegrator
from econ.reporting import CEAReportGenerator


def run_comprehensive_cea_demo(
    n_patients: int = 500,
    n_psa_simulations: int = 5000,
    output_dir: str = "./reports/demo",
    seed: int = 42
):
    """
    Run comprehensive cost-effectiveness analysis demonstration.

    Args:
        n_patients: Number of synthetic patients to generate
        n_psa_simulations: Number of PSA Monte Carlo simulations
        output_dir: Output directory for reports
        seed: Random seed for reproducibility

    Returns:
        Dictionary with all analysis results
    """
    print("=" * 100)
    print("TAIWAN ECMO CDSS - COMPREHENSIVE COST-EFFECTIVENESS ANALYSIS DEMONSTRATION (WP2)")
    print("=" * 100)
    print("")
    print("This demonstration follows CHEERS 2022 reporting guidelines and includes:")
    print("  1. Data integration and risk stratification")
    print("  2. Base case cost-effectiveness analysis")
    print("  3. Incremental analysis (ICER)")
    print("  4. Cost-effectiveness acceptability curve (CEAC)")
    print("  5. One-way sensitivity analysis")
    print("  6. Two-way sensitivity analysis")
    print("  7. Probabilistic sensitivity analysis (PSA)")
    print("  8. Value of information (EVPI) analysis")
    print("  9. Budget impact analysis")
    print("  10. Publication-ready reporting")
    print("")
    print("=" * 100)

    results = {}

    # ============================================================================
    # STEP 1: DATA INTEGRATION
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 1: DATA INTEGRATION AND RISK STRATIFICATION")
    print("=" * 100)

    integrator = ECMODataIntegrator(data_source="synthetic")

    # Generate synthetic data
    print("\nGenerating synthetic Taiwan ECMO patient data...")
    patient_data = integrator.load_patient_data()

    # Assign risk quintiles (using APACHE-II as proxy for demonstration)
    print("\nAssigning risk quintiles based on APACHE-II scores...")
    patient_data = integrator.assign_risk_quintiles()

    # Compute costs
    print("\nComputing costs (Taiwan NHI perspective)...")
    patient_data = integrator.compute_costs(
        icu_cost_per_day=30000,  # TWD
        ward_cost_per_day=8000,
        ecmo_daily_consumable=15000,
        ecmo_setup_cost=100000
    )

    # Prepare for CEA
    cea_data = integrator.prepare_for_cea()
    results['patient_data'] = cea_data

    print("\nQuintile Summary:")
    quintile_summary = integrator.get_quintile_summary()
    print(quintile_summary.to_string())

    # ============================================================================
    # STEP 2: COST-EFFECTIVENESS ANALYSIS (BASE CASE)
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 2: BASE CASE COST-EFFECTIVENESS ANALYSIS")
    print("=" * 100)

    # Initialize CEA
    cea = ECMOCostEffectivenessAnalysis(
        icu_cost_per_day=30000,
        ward_cost_per_day=8000,
        ecmo_daily_consumable=15000,
        ecmo_setup_cost=100000,
        qaly_gain_per_survivor=1.5,
        time_horizon_years=1.0,
        discount_rate=0.03,
        currency="TWD",
        use_nhi_rates=False,
        ecmo_mode="VA"
    )

    # Analyze by quintile
    print("\nComputing CER by risk quintile...")
    quintile_results = cea.analyze_by_quintile(cea_data)
    results['quintile_results'] = quintile_results

    print("\nCost-Effectiveness Ratio (CER) by Risk Quintile:")
    print(quintile_results.to_string(index=False))

    # ============================================================================
    # STEP 3: INCREMENTAL ANALYSIS (ICER)
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 3: INCREMENTAL COST-EFFECTIVENESS ANALYSIS (ICER)")
    print("=" * 100)

    icer_results = cea.compute_icer_by_quintile(quintile_results, baseline_quintile=1)
    results['icer_results'] = icer_results

    print("\nICER Analysis (vs. Quintile 1 - Lowest Risk):")
    print(icer_results.to_string(index=False))

    # ============================================================================
    # STEP 4: COST-EFFECTIVENESS ACCEPTABILITY CURVE (CEAC)
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 4: COST-EFFECTIVENESS ACCEPTABILITY CURVE (CEAC)")
    print("=" * 100)

    print("\nRunning Monte Carlo simulations for CEAC...")
    wtp_thresholds = np.linspace(0, 3000000, 50)
    ceac_data = cea.compute_ceac(
        quintile_results,
        wtp_thresholds=wtp_thresholds,
        n_simulations=1000
    )
    results['ceac_data'] = ceac_data

    # Summary at key thresholds
    key_wtp = [500000, 900000, 1500000, 2000000, 3000000]
    ceac_summary = ceac_data[ceac_data['wtp_threshold'].isin(key_wtp)].pivot(
        index='quintile',
        columns='wtp_threshold',
        values='probability_cost_effective'
    )

    print("\nProbability Cost-Effective at Key WTP Thresholds:")
    print(ceac_summary.to_string())

    # ============================================================================
    # STEP 5: ONE-WAY SENSITIVITY ANALYSIS
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 5: ONE-WAY SENSITIVITY ANALYSIS (TORNADO DIAGRAM)")
    print("=" * 100)

    # Base case from quintile 3 (median risk)
    q3_data = cea_data[cea_data['risk_quintile'] == 3]
    base_case = {
        'icu_los': q3_data['icu_los_days'].mean(),
        'ward_los': q3_data['ward_los_days'].mean(),
        'ecmo_days': q3_data['ecmo_days'].mean(),
        'survival_rate': q3_data['survival_to_discharge'].mean()
    }

    print(f"\nBase case (Quintile 3):")
    for key, val in base_case.items():
        print(f"  {key}: {val:.2f}")

    # Sensitivity parameters (±30% variation)
    sensitivity_params = {
        'icu_cost_per_day': (21000, 30000, 39000),
        'ward_cost_per_day': (5600, 8000, 10400),
        'ecmo_daily_consumable': (10500, 15000, 19500),
        'ecmo_setup_cost': (70000, 100000, 130000),
        'survival_rate': (
            max(0.2, base_case['survival_rate'] * 0.7),
            base_case['survival_rate'],
            min(0.9, base_case['survival_rate'] * 1.3)
        ),
        'qaly_gain_per_survivor': (1.05, 1.5, 1.95)
    }

    print("\nRunning one-way sensitivity analysis...")
    sens_results = cea.sensitivity_analysis(base_case, sensitivity_params)
    results['sensitivity_results'] = sens_results

    # Show range of variation
    print("\nSensitivity Analysis - Parameter Impact on CER:")
    for param in sens_results['parameter'].unique():
        pdata = sens_results[sens_results['parameter'] == param]
        base_cer = pdata[pdata['scenario'] == 'base']['cer'].values[0]
        low_cer = pdata[pdata['scenario'] == 'low']['cer'].values[0]
        high_cer = pdata[pdata['scenario'] == 'high']['cer'].values[0]
        range_cer = high_cer - low_cer

        print(f"  {param:30s}: {low_cer:>12,.0f} - {high_cer:>12,.0f} (Range: {range_cer:>12,.0f})")

    # ============================================================================
    # STEP 6: TWO-WAY SENSITIVITY ANALYSIS
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 6: TWO-WAY SENSITIVITY ANALYSIS (HEAT MAP)")
    print("=" * 100)

    print("\nTwo-way analysis: ICU cost vs. Survival rate...")
    icu_cost_range = np.linspace(20000, 40000, 10)
    survival_range = np.linspace(0.3, 0.7, 10)

    two_way_results = cea.two_way_sensitivity_analysis(
        base_case,
        'icu_cost_per_day',
        icu_cost_range,
        'survival_rate',
        survival_range
    )
    results['two_way_results'] = two_way_results

    print(f"Generated {len(two_way_results)} parameter combinations")
    print(f"CER range: {two_way_results['cer'].min():,.0f} - {two_way_results['cer'].max():,.0f}")

    # ============================================================================
    # STEP 7: PROBABILISTIC SENSITIVITY ANALYSIS (PSA)
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 7: PROBABILISTIC SENSITIVITY ANALYSIS (PSA)")
    print("=" * 100)

    # Define parameter distributions
    parameter_distributions = {
        'icu_los': ('gamma', (5, 3)),  # shape, scale
        'ward_los': ('gamma', (3, 2)),
        'ecmo_days': ('gamma', (3, 2)),
        'survival_rate': ('beta', (
            base_case['survival_rate'] * 10,
            (1 - base_case['survival_rate']) * 10
        )),
        'icu_cost_per_day': ('normal', (30000, 3000)),
        'ecmo_daily_consumable': ('normal', (15000, 2000)),
    }

    print(f"\nRunning {n_psa_simulations} Monte Carlo simulations...")
    psa_results = cea.probabilistic_sensitivity_analysis(
        base_case,
        parameter_distributions,
        n_simulations=n_psa_simulations,
        seed=seed
    )
    results['psa_results'] = psa_results

    # PSA summary statistics
    print("\nPSA Results (95% Confidence Intervals):")
    for col in ['total_cost', 'qaly', 'cer']:
        mean_val = psa_results[col].mean()
        ci_low = psa_results[col].quantile(0.025)
        ci_high = psa_results[col].quantile(0.975)
        print(f"  {col:15s}: {mean_val:>12,.2f} (95% CI: {ci_low:>12,.2f} - {ci_high:>12,.2f})")

    # ============================================================================
    # STEP 8: VALUE OF INFORMATION (EVPI) ANALYSIS
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 8: VALUE OF PERFECT INFORMATION (EVPI) ANALYSIS")
    print("=" * 100)

    print("\nComputing EVPI at WTP = 1,500,000 TWD/QALY...")
    evpi_results = cea.value_of_information_analysis(
        psa_results,
        wtp_threshold=1500000,
        population_size=1000,  # Annual ECMO cases in Taiwan (approximate)
        time_horizon_years=5
    )
    results['evpi_results'] = evpi_results

    print("\nEVPI Results:")
    print(f"  EVPI per person: {evpi_results['evpi_per_person']:,.0f} TWD")
    print(f"  EVPI for population (5 years): {evpi_results['evpi_population']:,.0f} TWD")
    print(f"  Expected NMB (current): {evpi_results['expected_nmb']:,.0f} TWD")
    print(f"  Expected NMB (perfect info): {evpi_results['perfect_info_nmb']:,.0f} TWD")

    print("\nInterpretation:")
    if evpi_results['evpi_population'] > 10000000:  # 10M TWD
        print("  -> High value of additional research (EVPI > 10M TWD)")
        print("  -> Consider funding additional studies to reduce uncertainty")
    else:
        print("  -> Low value of additional research (EVPI < 10M TWD)")
        print("  -> Current evidence may be sufficient for decision-making")

    # ============================================================================
    # STEP 9: BUDGET IMPACT ANALYSIS
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 9: BUDGET IMPACT ANALYSIS (5-YEAR PROJECTION)")
    print("=" * 100)

    # Current practice (standard ECMO)
    current_scenario = {
        'icu_los': 18,
        'ward_los': 6,
        'ecmo_days': 7,
        'survival_rate': 0.45
    }

    # New intervention (CDSS-guided ECMO)
    new_scenario = {
        'icu_los': 15,  # 15% reduction
        'ward_los': 7,  # Longer ward stay for survivors
        'ecmo_days': 6,  # Optimized ECMO duration
        'survival_rate': 0.52  # 7% absolute improvement
    }

    print("\nScenario Comparison:")
    print("  Current Practice:")
    for key, val in current_scenario.items():
        print(f"    {key}: {val}")
    print("\n  New Intervention (CDSS):")
    for key, val in new_scenario.items():
        print(f"    {key}: {val}")

    print("\nComputing budget impact over 5 years...")
    budget_results = cea.budget_impact_analysis(
        current_scenario,
        new_scenario,
        population_size=1000,  # Annual ECMO cases
        uptake_rate=0.8,  # 80% uptake by year 5
        years=5
    )
    results['budget_results'] = budget_results

    print("\nBudget Impact Analysis:")
    print(budget_results.to_string(index=False))

    # 5-year cumulative impact
    total_incremental = budget_results['discounted_incremental_budget'].sum()
    total_qaly_gain = budget_results['incremental_qaly'].sum()
    avg_icer = total_incremental / total_qaly_gain if total_qaly_gain > 0 else float('inf')

    print(f"\n5-Year Cumulative Impact:")
    print(f"  Total incremental budget: {total_incremental:,.0f} TWD")
    print(f"  Total QALY gain: {total_qaly_gain:.1f}")
    print(f"  Average ICER: {avg_icer:,.0f} TWD/QALY")

    # ============================================================================
    # STEP 10: GENERATE PUBLICATION-READY REPORTS
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("STEP 10: GENERATE PUBLICATION-READY REPORTS")
    print("=" * 100)

    # Initialize report generator
    reporter = CEAReportGenerator(
        study_title="Taiwan ECMO CDSS Cost-Effectiveness Analysis",
        perspective="Healthcare payer (Taiwan NHI)",
        time_horizon="1 year",
        discount_rate=0.03,
        currency="TWD",
        wtp_threshold=1500000,
        output_dir=output_dir
    )

    print(f"\nGenerating reports in: {output_dir}")

    # Executive summary
    print("\n1. Generating executive summary...")
    summary = reporter.generate_executive_summary(
        quintile_results,
        icer_results,
        psa_results
    )
    print(summary)

    # LaTeX table
    print("\n2. Generating LaTeX table...")
    latex_table = reporter.generate_cea_table_latex(
        quintile_results,
        icer_results
    )
    latex_file = Path(output_dir) / "cea_table.tex"
    latex_file.parent.mkdir(exist_ok=True, parents=True)
    with open(latex_file, 'w') as f:
        f.write(latex_table)
    print(f"   LaTeX table saved to: {latex_file}")

    # Excel tables
    print("\n3. Generating Excel tables...")
    excel_file = reporter.generate_cea_table_excel(
        quintile_results,
        icer_results,
        filename="cea_results.xlsx"
    )

    # Plots
    print("\n4. Generating cost-effectiveness plane...")
    ce_plane = reporter.plot_ce_plane(
        icer_results,
        quintile_results,
        filename="ce_plane.png"
    )

    print("\n5. Generating CEAC plot...")
    ceac_plot = reporter.plot_ceac(
        ceac_data,
        filename="ceac.png"
    )

    print("\n6. Generating tornado diagram...")
    base_cer = sens_results[sens_results['scenario'] == 'base']['cer'].iloc[0]
    tornado_plot = reporter.plot_tornado_diagram(
        sens_results,
        base_cer,
        filename="tornado.png"
    )

    print("\n7. Generating budget impact plot...")
    budget_plot = reporter.plot_budget_impact(
        budget_results,
        filename="budget_impact.png"
    )

    # Full report
    print("\n8. Generating comprehensive text report...")
    full_report = reporter.generate_full_report(
        quintile_results,
        icer_results,
        ceac_data,
        sensitivity_results=sens_results,
        psa_results=psa_results,
        budget_results=budget_results,
        filename="cea_full_report.txt"
    )

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n\n" + "=" * 100)
    print("ANALYSIS COMPLETE - SUMMARY")
    print("=" * 100)

    print("\nKey Findings:")
    print(f"  1. Total patients analyzed: {len(cea_data)}")
    print(f"  2. Risk quintiles: 5 (stratified by predicted mortality)")
    print(f"  3. CER range: {quintile_results['cer'].min():,.0f} - {quintile_results['cer'].max():,.0f} TWD/QALY")

    n_cost_effective = (quintile_results['cer'] < 1500000).sum()
    print(f"  4. Quintiles cost-effective at 1.5M TWD/QALY: {n_cost_effective}/5")

    print(f"  5. PSA simulations: {n_psa_simulations:,}")
    print(f"  6. EVPI (5-year population): {evpi_results['evpi_population']:,.0f} TWD")
    print(f"  7. 5-year budget impact: {total_incremental:,.0f} TWD")

    print(f"\nGenerated outputs in: {output_dir}")
    print("  - Executive summary (text)")
    print("  - LaTeX table (cea_table.tex)")
    print("  - Excel workbook (cea_results.xlsx)")
    print("  - Cost-effectiveness plane (ce_plane.png)")
    print("  - CEAC curve (ceac.png)")
    print("  - Tornado diagram (tornado.png)")
    print("  - Budget impact plot (budget_impact.png)")
    print("  - Full text report (cea_full_report.txt)")

    print("\n" + "=" * 100)
    print("CHEERS 2022-COMPLIANT ANALYSIS COMPLETE")
    print("=" * 100)

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Run comprehensive cost-effectiveness analysis for Taiwan ECMO CDSS'
    )
    parser.add_argument('--n-patients', type=int, default=500,
                       help='Number of synthetic patients (default: 500)')
    parser.add_argument('--n-psa-simulations', type=int, default=5000,
                       help='Number of PSA simulations (default: 5000)')
    parser.add_argument('--output-dir', type=str, default='./reports/demo',
                       help='Output directory (default: ./reports/demo)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')

    args = parser.parse_args()

    # Run comprehensive analysis
    results = run_comprehensive_cea_demo(
        n_patients=args.n_patients,
        n_psa_simulations=args.n_psa_simulations,
        output_dir=args.output_dir,
        seed=args.seed
    )

    print("\nAnalysis results stored in dictionary with keys:")
    for key in results.keys():
        print(f"  - {key}")
