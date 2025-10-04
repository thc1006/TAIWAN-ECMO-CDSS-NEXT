"""
Publication-Ready Reporting for Cost-Effectiveness Analysis (WP2)

Generates CHEERS 2022-compliant reports including:
- Cost-effectiveness tables (LaTeX, Word, Excel)
- Cost-effectiveness plane plots
- CEAC curves
- Incremental analysis tables
- Executive summaries
- Budget impact projections
- Sensitivity analysis tornado diagrams

Formats:
- LaTeX tables for academic publications
- Word documents for reports
- Excel workbooks for data sharing
- PDF reports with visualizations
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import warnings


class CEAReportGenerator:
    """
    Generate publication-ready cost-effectiveness analysis reports.

    Follows CHEERS 2022 reporting guidelines:
    - Clear perspective statement
    - Time horizon specification
    - Discount rate documentation
    - Uncertainty characterization
    - Incremental analysis
    - Sensitivity analysis
    """

    def __init__(
        self,
        study_title: str = "Taiwan ECMO CDSS Cost-Effectiveness Analysis",
        perspective: str = "Healthcare payer (Taiwan NHI)",
        time_horizon: str = "1 year",
        discount_rate: float = 0.03,
        currency: str = "TWD",
        wtp_threshold: float = 1500000,
        output_dir: str = "./reports"
    ):
        """
        Initialize report generator.

        Args:
            study_title: Study title
            perspective: Economic perspective
            time_horizon: Time horizon for analysis
            discount_rate: Annual discount rate
            currency: Currency code
            wtp_threshold: Willingness-to-pay threshold
            output_dir: Output directory for reports
        """
        self.study_title = study_title
        self.perspective = perspective
        self.time_horizon = time_horizon
        self.discount_rate = discount_rate
        self.currency = currency
        self.wtp_threshold = wtp_threshold
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def generate_executive_summary(
        self,
        quintile_results: pd.DataFrame,
        icer_results: pd.DataFrame,
        psa_results: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Generate executive summary text.

        Args:
            quintile_results: Results from analyze_by_quintile()
            icer_results: Results from compute_icer_by_quintile()
            psa_results: Results from probabilistic_sensitivity_analysis()

        Returns:
            Executive summary text
        """
        summary = []
        summary.append(f"EXECUTIVE SUMMARY: {self.study_title}")
        summary.append("=" * 80)
        summary.append("")

        # Study characteristics
        summary.append("Study Characteristics:")
        summary.append(f"  Perspective: {self.perspective}")
        summary.append(f"  Time Horizon: {self.time_horizon}")
        summary.append(f"  Discount Rate: {self.discount_rate*100:.1f}%")
        summary.append(f"  Currency: {self.currency}")
        summary.append(f"  WTP Threshold: {self.wtp_threshold:,.0f} {self.currency}/QALY")
        summary.append("")

        # Sample characteristics
        n_total = quintile_results['n_patients'].sum()
        overall_survival = (
            quintile_results['survival_rate'] * quintile_results['n_patients']
        ).sum() / n_total

        summary.append("Patient Characteristics:")
        summary.append(f"  Total Patients: {n_total}")
        summary.append(f"  Overall Survival Rate: {overall_survival*100:.1f}%")
        summary.append(f"  Risk Quintiles: 5 (stratified by predicted mortality)")
        summary.append("")

        # Cost-effectiveness results
        summary.append("Cost-Effectiveness Results:")
        summary.append("")

        # Overall CER range
        min_cer = quintile_results['cer'].min()
        max_cer = quintile_results['cer'].max()
        mean_cer = quintile_results['cer'].mean()

        summary.append(f"  CER Range: {min_cer:,.0f} - {max_cer:,.0f} {self.currency}/QALY")
        summary.append(f"  Mean CER: {mean_cer:,.0f} {self.currency}/QALY")
        summary.append("")

        # Quintile-specific results
        summary.append("  By Risk Quintile:")
        for _, row in quintile_results.iterrows():
            q = int(row['quintile'])
            cer = row['cer']
            survival = row['survival_rate']
            cost = row['total_cost']
            cost_effective = "Yes" if cer < self.wtp_threshold else "No"

            summary.append(f"    Q{q}: CER={cer:,.0f}, Survival={survival*100:.1f}%, "
                         f"Cost={cost:,.0f}, Cost-Effective={cost_effective}")
        summary.append("")

        # ICER results
        summary.append("Incremental Analysis (vs. Quintile 1):")
        for _, row in icer_results.iterrows():
            if row['quintile'] == 1:
                continue
            q = int(row['quintile'])
            icer = row['icer_vs_baseline']
            inc_cost = row['incremental_cost']
            inc_qaly = row['incremental_qaly']

            if np.isfinite(icer):
                icer_str = f"{icer:,.0f}"
                cost_effective = "Yes" if icer < self.wtp_threshold else "No"
            else:
                icer_str = "Dominated"
                cost_effective = "No"

            summary.append(f"    Q{q}: ICER={icer_str}, ΔCost={inc_cost:,.0f}, "
                         f"ΔQALY={inc_qaly:.3f}, Cost-Effective={cost_effective}")
        summary.append("")

        # PSA results (if available)
        if psa_results is not None:
            summary.append("Probabilistic Sensitivity Analysis:")
            mean_cost = psa_results['total_cost'].mean()
            ci_cost = psa_results['total_cost'].quantile([0.025, 0.975])
            mean_qaly = psa_results['qaly'].mean()
            ci_qaly = psa_results['qaly'].quantile([0.025, 0.975])

            summary.append(f"  Mean Cost: {mean_cost:,.0f} {self.currency} "
                         f"(95% CI: {ci_cost.iloc[0]:,.0f} - {ci_cost.iloc[1]:,.0f})")
            summary.append(f"  Mean QALY: {mean_qaly:.3f} "
                         f"(95% CI: {ci_qaly.iloc[0]:.3f} - {ci_qaly.iloc[1]:.3f})")

            # Probability cost-effective
            nmb_col = f'nmb_wtp_{int(self.wtp_threshold)}'
            if nmb_col in psa_results.columns:
                prob_ce = (psa_results[nmb_col] > 0).mean()
                summary.append(f"  Probability Cost-Effective (WTP={self.wtp_threshold:,.0f}): {prob_ce*100:.1f}%")
            summary.append("")

        # Conclusions
        summary.append("Conclusions:")
        n_cost_effective = (quintile_results['cer'] < self.wtp_threshold).sum()
        summary.append(f"  {n_cost_effective} of 5 risk quintiles are cost-effective "
                     f"at WTP threshold of {self.wtp_threshold:,.0f} {self.currency}/QALY")

        best_quintile = quintile_results.loc[quintile_results['cer'].idxmin()]
        summary.append(f"  Most cost-effective group: Quintile {int(best_quintile['quintile'])} "
                     f"(CER={best_quintile['cer']:,.0f})")

        summary.append("")
        summary.append("=" * 80)

        return "\n".join(summary)

    def generate_cea_table_latex(
        self,
        quintile_results: pd.DataFrame,
        icer_results: pd.DataFrame,
        caption: str = "Cost-Effectiveness Analysis Results by Risk Quintile"
    ) -> str:
        """
        Generate LaTeX table for publication.

        Args:
            quintile_results: Results from analyze_by_quintile()
            icer_results: Results from compute_icer_by_quintile()
            caption: Table caption

        Returns:
            LaTeX table code
        """
        # Merge results
        merged = quintile_results.merge(icer_results, on='quintile')

        latex = []
        latex.append("\\begin{table}[htbp]")
        latex.append("\\centering")
        latex.append(f"\\caption{{{caption}}}")
        latex.append("\\label{tab:cea_results}")
        latex.append("\\begin{tabular}{lrrrrrrr}")
        latex.append("\\hline")
        latex.append("Risk & N & Survival & Cost & QALY & CER & $\\Delta$Cost & ICER \\\\")
        latex.append("Quintile & & Rate (\\%) & (TWD) & & (TWD/QALY) & (TWD) & (TWD/QALY) \\\\")
        latex.append("\\hline")

        for _, row in merged.iterrows():
            q = int(row['quintile'])
            n = int(row['n_patients'])
            survival = row['survival_rate'] * 100
            cost = row['total_cost']
            qaly = row['qaly']
            cer = row['cer']
            inc_cost = row['incremental_cost']
            icer = row['icer_vs_baseline']

            if q == 1:
                icer_str = "Ref"
                inc_cost_str = "Ref"
            elif np.isfinite(icer):
                icer_str = f"{icer:,.0f}"
                inc_cost_str = f"{inc_cost:,.0f}"
            else:
                icer_str = "Dom"
                inc_cost_str = f"{inc_cost:,.0f}"

            latex.append(f"Q{q} & {n} & {survival:.1f} & {cost:,.0f} & {qaly:.3f} & "
                        f"{cer:,.0f} & {inc_cost_str} & {icer_str} \\\\")

        latex.append("\\hline")
        latex.append("\\end{tabular}")
        latex.append("\\end{table}")

        return "\n".join(latex)

    def generate_cea_table_excel(
        self,
        quintile_results: pd.DataFrame,
        icer_results: pd.DataFrame,
        filename: str = "cea_results.xlsx"
    ) -> str:
        """
        Generate Excel table with multiple sheets.

        Args:
            quintile_results: Results from analyze_by_quintile()
            icer_results: Results from compute_icer_by_quintile()
            filename: Output filename

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / filename

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Quintile results
            quintile_results.to_excel(writer, sheet_name='Quintile_Results', index=False)

            # Sheet 2: ICER results
            icer_results.to_excel(writer, sheet_name='ICER_Analysis', index=False)

            # Sheet 3: Merged
            merged = quintile_results.merge(icer_results, on='quintile')
            merged.to_excel(writer, sheet_name='Combined', index=False)

        print(f"Excel report saved to: {output_path}")
        return str(output_path)

    def plot_ce_plane(
        self,
        icer_results: pd.DataFrame,
        quintile_results: pd.DataFrame,
        wtp_thresholds: Optional[List[float]] = None,
        filename: str = "ce_plane.png",
        figsize: Tuple[int, int] = (10, 8)
    ) -> str:
        """
        Plot cost-effectiveness plane.

        Args:
            icer_results: Results from compute_icer_by_quintile()
            quintile_results: Results from analyze_by_quintile()
            wtp_thresholds: WTP threshold lines to plot
            filename: Output filename
            figsize: Figure size

        Returns:
            Path to generated file
        """
        if wtp_thresholds is None:
            wtp_thresholds = [900000, 1500000, 2700000]  # 1x, 1.67x, 3x GDP/capita

        fig, ax = plt.subplots(figsize=figsize)

        # Plot points
        merged = icer_results.merge(quintile_results[['quintile', 'survival_rate']], on='quintile')

        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, 5))

        for i, (_, row) in enumerate(merged.iterrows()):
            if row['quintile'] == 1:
                # Reference point at origin
                ax.scatter(0, 0, s=200, c=[colors[i]], marker='*',
                          edgecolors='black', linewidths=2, label=f"Q{int(row['quintile'])} (Ref)",
                          zorder=5)
            else:
                ax.scatter(row['incremental_qaly'], row['incremental_cost'],
                          s=150, c=[colors[i]], marker='o',
                          edgecolors='black', linewidths=1.5, label=f"Q{int(row['quintile'])}",
                          alpha=0.8, zorder=5)

        # WTP threshold lines
        max_qaly = max(merged['incremental_qaly'].max(), 0.1)
        qaly_range = np.linspace(0, max_qaly * 1.2, 100)

        wtp_colors = ['green', 'orange', 'red']
        wtp_labels = ['1x GDP/capita', '1.67x GDP/capita', '3x GDP/capita']

        for wtp, color, label in zip(wtp_thresholds, wtp_colors, wtp_labels):
            cost_range = qaly_range * wtp
            ax.plot(qaly_range, cost_range, '--', color=color, alpha=0.6,
                   linewidth=2, label=f'{label}: {wtp/1000:.0f}k TWD/QALY')

        # Quadrant labels
        max_cost = merged['incremental_cost'].max()
        ax.text(max_qaly * 0.6, max_cost * 0.8, 'More effective,\nMore costly',
               fontsize=10, alpha=0.5, ha='center')
        ax.text(max_qaly * 0.6, -max_cost * 0.3, 'More effective,\nLess costly\n(Dominant)',
               fontsize=10, alpha=0.5, ha='center')

        # Labels and formatting
        ax.set_xlabel('Incremental QALY', fontsize=12, fontweight='bold')
        ax.set_ylabel('Incremental Cost (TWD)', fontsize=12, fontweight='bold')
        ax.set_title('Cost-Effectiveness Plane\nECMO CDSS by Risk Quintile',
                    fontsize=14, fontweight='bold', pad=20)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.2)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"CE plane saved to: {output_path}")
        return str(output_path)

    def plot_ceac(
        self,
        ceac_data: pd.DataFrame,
        filename: str = "ceac.png",
        figsize: Tuple[int, int] = (10, 6)
    ) -> str:
        """
        Plot cost-effectiveness acceptability curve.

        Args:
            ceac_data: Results from compute_ceac()
            filename: Output filename
            figsize: Figure size

        Returns:
            Path to generated file
        """
        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.Set2(np.linspace(0, 1, 5))

        for i, quintile in enumerate(sorted(ceac_data['quintile'].unique())):
            qdata = ceac_data[ceac_data['quintile'] == quintile]
            ax.plot(qdata['wtp_threshold'] / 1000,  # Convert to thousands
                   qdata['probability_cost_effective'],
                   marker='o', markersize=4, linewidth=2.5,
                   color=colors[i], label=f'Quintile {quintile}',
                   alpha=0.8)

        # Reference lines
        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1,
                  label='50% threshold')
        ax.axvline(x=900, color='green', linestyle=':', alpha=0.5, linewidth=2,
                  label='1x GDP/capita (900k)')
        ax.axvline(x=2700, color='red', linestyle=':', alpha=0.5, linewidth=2,
                  label='3x GDP/capita (2.7M)')

        # Labels and formatting
        ax.set_xlabel('Willingness-to-Pay Threshold (1000s TWD/QALY)',
                     fontsize=12, fontweight='bold')
        ax.set_ylabel('Probability Cost-Effective', fontsize=12, fontweight='bold')
        ax.set_title('Cost-Effectiveness Acceptability Curve (CEAC)\nECMO CDSS by Risk Quintile',
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim([0, 1])
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"CEAC plot saved to: {output_path}")
        return str(output_path)

    def plot_tornado_diagram(
        self,
        sensitivity_results: pd.DataFrame,
        base_cer: float,
        filename: str = "tornado.png",
        figsize: Tuple[int, int] = (10, 6)
    ) -> str:
        """
        Plot tornado diagram for sensitivity analysis.

        Args:
            sensitivity_results: Results from sensitivity_analysis()
            base_cer: Base case CER value
            filename: Output filename
            figsize: Figure size

        Returns:
            Path to generated file
        """
        # Calculate ranges for each parameter
        tornado_data = []
        for param in sensitivity_results['parameter'].unique():
            pdata = sensitivity_results[sensitivity_results['parameter'] == param]
            low_cer = pdata[pdata['scenario'] == 'low']['cer'].values[0]
            high_cer = pdata[pdata['scenario'] == 'high']['cer'].values[0]

            tornado_data.append({
                'parameter': param,
                'low_delta': low_cer - base_cer,
                'high_delta': high_cer - base_cer,
                'range': abs(high_cer - low_cer)
            })

        tornado_df = pd.DataFrame(tornado_data).sort_values('range', ascending=True)

        # Plot
        fig, ax = plt.subplots(figsize=figsize)
        y_pos = np.arange(len(tornado_df))

        # Bars
        ax.barh(y_pos, tornado_df['low_delta'], color='steelblue', alpha=0.7,
               label='Low value', height=0.7)
        ax.barh(y_pos, tornado_df['high_delta'], color='coral', alpha=0.7,
               label='High value', height=0.7)

        # Reference line
        ax.axvline(x=0, color='black', linewidth=2)

        # Labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tornado_df['parameter'])
        ax.set_xlabel('Change in CER (TWD/QALY)', fontsize=12, fontweight='bold')
        ax.set_title('Tornado Diagram: One-Way Sensitivity Analysis\nECMO CDSS Cost-Effectiveness',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Tornado diagram saved to: {output_path}")
        return str(output_path)

    def plot_budget_impact(
        self,
        budget_results: pd.DataFrame,
        filename: str = "budget_impact.png",
        figsize: Tuple[int, int] = (12, 6)
    ) -> str:
        """
        Plot budget impact analysis over time.

        Args:
            budget_results: Results from budget_impact_analysis()
            filename: Output filename
            figsize: Figure size

        Returns:
            Path to generated file
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        years = budget_results['year']

        # Plot 1: Budget over time
        ax1.plot(years, budget_results['total_budget'] / 1e6, 'o-',
                linewidth=2.5, markersize=8, color='steelblue',
                label='Total Budget')
        ax1.plot(years, budget_results['incremental_budget'] / 1e6, 's--',
                linewidth=2, markersize=7, color='coral',
                label='Incremental Budget')
        ax1.fill_between(years,
                         budget_results['incremental_budget'] / 1e6,
                         alpha=0.3, color='coral')

        ax1.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Budget (Millions TWD)', fontsize=11, fontweight='bold')
        ax1.set_title('Budget Impact Over Time', fontsize=12, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(years)

        # Plot 2: Uptake and QALY
        ax2_qaly = ax2.twinx()

        ax2.bar(years, budget_results['uptake_rate'], alpha=0.5,
               color='lightblue', label='Uptake Rate')
        ax2_qaly.plot(years, budget_results['total_qaly'], 'o-',
                     linewidth=2.5, markersize=8, color='green',
                     label='Total QALYs')

        ax2.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Uptake Rate', fontsize=11, fontweight='bold', color='steelblue')
        ax2_qaly.set_ylabel('Total QALYs', fontsize=11, fontweight='bold', color='green')
        ax2.set_title('Intervention Uptake and Health Outcomes', fontsize=12, fontweight='bold')
        ax2.set_ylim([0, 1.1])
        ax2.set_xticks(years)
        ax2.tick_params(axis='y', labelcolor='steelblue')
        ax2_qaly.tick_params(axis='y', labelcolor='green')
        ax2.grid(True, alpha=0.3)

        # Combined legend
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_qaly.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Budget impact plot saved to: {output_path}")
        return str(output_path)

    def generate_full_report(
        self,
        quintile_results: pd.DataFrame,
        icer_results: pd.DataFrame,
        ceac_data: pd.DataFrame,
        sensitivity_results: Optional[pd.DataFrame] = None,
        psa_results: Optional[pd.DataFrame] = None,
        budget_results: Optional[pd.DataFrame] = None,
        filename: str = "cea_full_report.txt"
    ) -> str:
        """
        Generate comprehensive text report.

        Args:
            quintile_results: Results from analyze_by_quintile()
            icer_results: Results from compute_icer_by_quintile()
            ceac_data: Results from compute_ceac()
            sensitivity_results: Results from sensitivity_analysis()
            psa_results: Results from probabilistic_sensitivity_analysis()
            budget_results: Results from budget_impact_analysis()
            filename: Output filename

        Returns:
            Path to generated file
        """
        report = []

        # Executive summary
        report.append(self.generate_executive_summary(
            quintile_results, icer_results, psa_results
        ))
        report.append("\n\n")

        # Detailed results
        report.append("=" * 80)
        report.append("DETAILED RESULTS")
        report.append("=" * 80)
        report.append("")

        report.append("Table 1: Cost-Effectiveness Analysis by Risk Quintile")
        report.append("-" * 80)
        report.append(quintile_results.to_string(index=False))
        report.append("")

        report.append("Table 2: Incremental Cost-Effectiveness Analysis")
        report.append("-" * 80)
        merged = quintile_results.merge(icer_results, on='quintile')
        report.append(merged.to_string(index=False))
        report.append("")

        # CEAC summary
        key_wtp = [500000, 1000000, 1500000, 2000000, 3000000]
        ceac_summary = ceac_data[ceac_data['wtp_threshold'].isin(key_wtp)].pivot(
            index='quintile',
            columns='wtp_threshold',
            values='probability_cost_effective'
        )
        report.append("Table 3: Cost-Effectiveness Acceptability (Probability)")
        report.append("-" * 80)
        report.append(ceac_summary.to_string())
        report.append("")

        # Sensitivity analysis
        if sensitivity_results is not None:
            report.append("Table 4: One-Way Sensitivity Analysis Results")
            report.append("-" * 80)
            report.append(sensitivity_results.to_string(index=False))
            report.append("")

        # Budget impact
        if budget_results is not None:
            report.append("Table 5: Budget Impact Analysis (5-Year Projection)")
            report.append("-" * 80)
            report.append(budget_results.to_string(index=False))
            report.append("")

        # Save report
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            f.write("\n".join(report))

        print(f"Full report saved to: {output_path}")
        return str(output_path)


if __name__ == '__main__':
    print("=" * 80)
    print("CEA Report Generator - Example Usage")
    print("=" * 80)
    print("")
    print("This module generates publication-ready reports for CEA.")
    print("See demo_analysis.py for complete workflow example.")
    print("")
    print("Example usage:")
    print("  generator = CEAReportGenerator()")
    print("  generator.generate_executive_summary(quintile_results, icer_results)")
    print("  generator.generate_cea_table_latex(quintile_results, icer_results)")
    print("  generator.plot_ce_plane(icer_results, quintile_results)")
    print("  generator.plot_ceac(ceac_data)")
    print("  generator.generate_full_report(...)")
