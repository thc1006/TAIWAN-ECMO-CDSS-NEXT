# WP2 Cost-Effectiveness Analysis - Enhancement Summary

## Overview

This document summarizes the comprehensive enhancements made to the Taiwan ECMO CDSS cost-effectiveness analysis tools (WP2), following CHEERS 2022 reporting guidelines and Taiwan NHI-specific requirements.

---

## Files Enhanced/Created

### 1. **cost_effectiveness.py** (Enhanced)
**Location:** `D:\dev\TAIWAN-ECMO-CDSS-NEXT\econ\cost_effectiveness.py`

#### New Features Added:
- **Multi-currency support** (TWD, USD, EUR)
  - Automatic currency conversion
  - Currency rate configuration

- **Taiwan NHI-specific calculations**
  - DRG reimbursement rates (VA/VV ECMO)
  - Hospital margin calculations
  - ICU daily payment caps

- **Probabilistic Sensitivity Analysis (PSA)**
  - Monte Carlo simulations (configurable iterations)
  - Multiple parameter distributions (normal, lognormal, gamma, beta, uniform)
  - Net Monetary Benefit (NMB) at multiple WTP thresholds
  - 95% confidence intervals

- **Two-way sensitivity analysis**
  - Heat map data generation
  - Parameter interaction analysis
  - Complete grid search over parameter ranges

- **Value of Information (VOI) analysis**
  - Expected Value of Perfect Information (EVPI)
  - Per-person and population-level estimates
  - Discounted future benefits
  - Research prioritization guidance

- **Budget Impact Analysis**
  - 5-year projections
  - Gradual uptake modeling
  - Discounted costs and QALYs
  - Incremental budget calculations

#### Methods Added:
```python
ECMOCostEffectivenessAnalysis:
  - convert_currency(amount, to_currency)
  - compute_nhi_reimbursement(icu_los_days, ecmo_days)
  - probabilistic_sensitivity_analysis(base_case, distributions, n_simulations)
  - two_way_sensitivity_analysis(base_case, param1, param2, ranges)
  - value_of_information_analysis(psa_results, wtp_threshold, population)
  - budget_impact_analysis(current_scenario, new_scenario, population, years)
```

---

### 2. **data_integration.py** (New)
**Location:** `D:\dev\TAIWAN-ECMO-CDSS-NEXT\econ\data_integration.py`

#### Purpose:
Integrate patient data from multiple sources with risk predictions and cost calculations.

#### Key Features:
- **Multiple data source support**
  - Synthetic data generation (for testing/demonstration)
  - CSV file loading
  - SQL database queries
  - MIMIC-IV database integration

- **Risk stratification**
  - Integration with NIRS risk models (from WP1)
  - APACHE-II score proxy
  - Equal-frequency or equal-width quintile assignment

- **Cost computation**
  - Per-patient cost calculations
  - ICU, ward, and ECMO cost components
  - Customizable cost parameters

- **Data preparation for CEA**
  - Validation of required columns
  - Summary statistics by quintile
  - Missing value handling

#### Classes:
```python
ECMODataIntegrator:
  - load_patient_data(file_path, sql_query, connection_string)
  - assign_risk_quintiles(risk_scores, method)
  - compute_costs(icu_cost_per_day, ward_cost_per_day, ...)
  - integrate_risk_predictions(va_model, vv_model)
  - prepare_for_cea()
  - get_quintile_summary()
```

#### Synthetic Data Generation:
Generates realistic synthetic ECMO patient data with:
- VA/VV mode distribution (60/40)
- Risk-stratified outcomes
- NIRS features (HbO2, HbT)
- EHR features (vitals, labs, ECMO settings)
- Correlated survival and length of stay

---

### 3. **reporting.py** (New)
**Location:** `D:\dev\TAIWAN-ECMO-CDSS-NEXT\econ\reporting.py`

#### Purpose:
Generate publication-ready reports following CHEERS 2022 guidelines.

#### Output Formats:
1. **Executive Summary** (text)
   - Study characteristics
   - Patient demographics
   - Key findings
   - Cost-effectiveness conclusions

2. **LaTeX Tables**
   - Publication-ready formatting
   - Combined CER/ICER tables
   - Customizable captions

3. **Excel Workbooks**
   - Multiple sheets (Quintile Results, ICER, Combined)
   - Formatted tables
   - Easy data sharing

4. **Visualizations** (PNG, 300 DPI)
   - Cost-effectiveness plane
   - CEAC curves
   - Tornado diagrams
   - Budget impact plots

5. **Comprehensive Text Report**
   - All tables and summaries
   - Integrated analysis
   - CHEERS 2022-compliant structure

#### Classes:
```python
CEAReportGenerator:
  - generate_executive_summary(quintile_results, icer_results, psa_results)
  - generate_cea_table_latex(quintile_results, icer_results)
  - generate_cea_table_excel(quintile_results, icer_results)
  - plot_ce_plane(icer_results, quintile_results, wtp_thresholds)
  - plot_ceac(ceac_data)
  - plot_tornado_diagram(sensitivity_results, base_cer)
  - plot_budget_impact(budget_results)
  - generate_full_report(all_results)
```

---

### 4. **demo_analysis.py** (New)
**Location:** `D:\dev\TAIWAN-ECMO-CDSS-NEXT\econ\demo_analysis.py`

#### Purpose:
Comprehensive demonstration of entire CEA workflow.

#### Workflow (10 Steps):
1. **Data Integration** - Generate/load patient data
2. **Base Case CEA** - CER by risk quintile
3. **Incremental Analysis** - ICER calculations
4. **CEAC** - Probabilistic acceptability curves
5. **One-way Sensitivity** - Tornado diagrams
6. **Two-way Sensitivity** - Heat maps
7. **PSA** - Monte Carlo simulations
8. **EVPI** - Value of information analysis
9. **Budget Impact** - 5-year projections
10. **Reporting** - Generate all outputs

#### Command-line Interface:
```bash
python econ/demo_analysis.py --n-patients 500 --n-psa-simulations 5000 --output-dir ./reports/demo
```

#### Outputs Generated:
- Executive summary (text)
- LaTeX table (cea_table.tex)
- Excel workbook (cea_results.xlsx)
- Cost-effectiveness plane (ce_plane.png)
- CEAC curve (ceac.png)
- Tornado diagram (tornado.png)
- Budget impact plot (budget_impact.png)
- Full text report (cea_full_report.txt)

---

### 5. **dashboard.py** (Enhanced)
**Location:** `D:\dev\TAIWAN-ECMO-CDSS-NEXT\econ\dashboard.py`

#### New Features:
- **Export functionality**
  - Export to Excel (via sidebar button)
  - Generate LaTeX tables (copy to clipboard)
  - Generate executive summaries (in-app display)

- **Enhanced footer**
  - Feature list
  - CHEERS 2022 compliance badge
  - Taiwan NHI perspective indication

#### Usage:
```bash
streamlit run econ/dashboard.py
```

---

## CEA Methodology Decisions

### 1. **Economic Perspective**
- **Primary:** Healthcare payer (Taiwan NHI)
- **Alternative:** Societal perspective (configurable)

### 2. **Time Horizon**
- **Base case:** 1 year
- **Configurable:** 1-10 years
- **Rationale:** Short-term outcomes most relevant for ECMO

### 3. **Discount Rate**
- **Base case:** 3% (Taiwan standard)
- **Sensitivity:** 0-5%
- **Applied to:** Future costs and QALYs

### 4. **Willingness-to-Pay Threshold**
- **Primary:** 1,500,000 TWD/QALY (≈1.67x GDP/capita)
- **Range:** 500k - 3M TWD/QALY
- **Reference:** WHO guideline (1-3x GDP/capita)

### 5. **Cost Parameters (Taiwan)**
- ICU cost per day: 30,000 TWD
- Ward cost per day: 8,000 TWD
- ECMO daily consumable: 15,000 TWD
- ECMO setup cost: 100,000 TWD

### 6. **NHI DRG Reimbursement (Approximate)**
- VA-ECMO: 800,000 TWD
- VV-ECMO: 750,000 TWD
- ICU daily cap: 45,000 TWD

### 7. **QALY Estimation**
- Base: 1.5 QALYs per survivor (1-year horizon)
- Quality of life multiplier: Configurable (0-1)
- Discounted for future years

### 8. **Risk Stratification**
- **Method:** Risk quintiles (5 groups)
- **Basis:** Predicted mortality from NIRS models (WP1)
- **Proxy:** APACHE-II scores (when models unavailable)

### 9. **Uncertainty Handling**
- **One-way sensitivity:** ±30% parameter variation
- **Two-way sensitivity:** Full grid search
- **PSA:** 5,000-10,000 Monte Carlo iterations
- **Distributions:**
  - Costs: Normal/Gamma
  - Survival: Beta
  - Length of stay: Gamma

### 10. **Budget Impact Assumptions**
- Population: 1,000 annual ECMO cases (Taiwan estimate)
- Uptake: Linear increase to 80% by year 5
- Scenarios:
  - Current: Standard ECMO (45% survival)
  - New: CDSS-guided ECMO (52% survival, optimized LOS)

---

## Key CEA Outputs

### 1. **Cost-Effectiveness Ratio (CER)**
- Cost per QALY gained
- Stratified by risk quintile
- Compared to WTP threshold

### 2. **Incremental Cost-Effectiveness Ratio (ICER)**
- Incremental cost per additional QALY
- Compared to baseline (lowest risk quintile)
- Identifies dominated strategies

### 3. **Cost-Effectiveness Acceptability Curve (CEAC)**
- Probability cost-effective at various WTP thresholds
- Accounts for parameter uncertainty
- Supports decision-making under uncertainty

### 4. **Expected Value of Perfect Information (EVPI)**
- Maximum value of eliminating uncertainty
- Guides research investment decisions
- Population-level over time horizon

### 5. **Budget Impact**
- Total and incremental costs
- 5-year projections
- Discounted estimates
- Uptake modeling

---

## Example Output Formats

### LaTeX Table Example:
```latex
\begin{table}[htbp]
\centering
\caption{Cost-Effectiveness Analysis Results by Risk Quintile}
\label{tab:cea_results}
\begin{tabular}{lrrrrrrr}
\hline
Risk & N & Survival & Cost & QALY & CER & $\Delta$Cost & ICER \\
Quintile & & Rate (\%) & (TWD) & & (TWD/QALY) & (TWD) & (TWD/QALY) \\
\hline
Q1 & 100 & 64.0 & 537,746 & 0.932 & 576,957 & Ref & Ref \\
Q2 & 100 & 53.0 & 486,492 & 0.772 & 630,298 & -51,254 & Dom \\
...
\hline
\end{tabular}
\end{table}
```

### Executive Summary Example:
```
EXECUTIVE SUMMARY: Taiwan ECMO CDSS Cost-Effectiveness Analysis
================================================================================

Study Characteristics:
  Perspective: Healthcare payer (Taiwan NHI)
  Time Horizon: 1 year
  Discount Rate: 3.0%
  Currency: TWD
  WTP Threshold: 1,500,000 TWD/QALY

Cost-Effectiveness Results:
  CER Range: 576,957 - 834,945 TWD/QALY
  Mean CER: 686,635 TWD/QALY

Conclusions:
  5 of 5 risk quintiles are cost-effective at WTP threshold of 1,500,000 TWD/QALY
  Most cost-effective group: Quintile 1 (CER=576,957)
```

---

## Integration with Other WP Components

### WP1 (NIRS Risk Models)
- **File:** `nirs/risk_models.py`
- **Integration:** `data_integration.py` calls risk model predictions
- **Usage:**
  ```python
  from nirs.risk_models import train_va_vv_models
  va_model, vv_model, _ = train_va_vv_models(data)
  integrator.integrate_risk_predictions(va_model, vv_model)
  ```

### WP3 (VR Training)
- Cost of training program can be added as fixed cost
- Training effectiveness can modify survival rates

### WP4 (SMART on FHIR)
- Real-time data integration from EHR
- Cost tracking via FHIR resources
- Automated CEA updates

---

## Dependencies

### New Requirements Added:
```
openpyxl>=3.1         # Excel file generation
sqlalchemy>=2.0       # SQL database support
imbalanced-learn>=0.11  # Model class weighting
shap>=0.43             # Model explainability
psycopg2-binary>=2.9   # PostgreSQL for MIMIC-IV
```

### Install:
```bash
pip install -r requirements.txt
```

---

## Usage Examples

### 1. Quick Demo (Synthetic Data):
```bash
python econ/demo_analysis.py
```

### 2. Custom Analysis:
```python
from econ.cost_effectiveness import ECMOCostEffectivenessAnalysis
from econ.data_integration import ECMODataIntegrator

# Load data
integrator = ECMODataIntegrator(data_source="csv")
data = integrator.load_patient_data(file_path="ecmo_data.csv")
data = integrator.integrate_risk_predictions()
cea_data = integrator.prepare_for_cea()

# Run CEA
cea = ECMOCostEffectivenessAnalysis(
    icu_cost_per_day=30000,
    currency="TWD"
)
results = cea.analyze_by_quintile(cea_data)
```

### 3. Interactive Dashboard:
```bash
streamlit run econ/dashboard.py
```

### 4. Generate Reports:
```python
from econ.reporting import CEAReportGenerator

reporter = CEAReportGenerator(output_dir="./reports")
reporter.generate_full_report(
    quintile_results,
    icer_results,
    ceac_data,
    sensitivity_results,
    psa_results,
    budget_results
)
```

---

## CHEERS 2022 Compliance Checklist

✅ **Title and Abstract**
- Clear identification of study as economic evaluation
- Interventions compared
- Target population

✅ **Introduction**
- Health problem and interventions
- Economic importance
- Perspective and rationale

✅ **Methods**
- Target population and subgroups (risk quintiles)
- Setting and location (Taiwan)
- Study perspective (NHI payer)
- Comparators (quintile 1 baseline)
- Time horizon (1 year, configurable)
- Discount rate (3%)
- Selection of outcomes (QALYs)
- Measurement of effectiveness (survival data)
- Measurement and valuation of costs (NHI perspective)
- Currency and price date (TWD, current)
- Analytical methods (decision tree, Markov model)

✅ **Results**
- Study parameters (fully documented)
- Incremental costs and outcomes
- Characterizing uncertainty (PSA, sensitivity analyses)
- Characterizing heterogeneity (risk quintiles)

✅ **Discussion**
- Study findings and limitations
- Generalizability
- Current knowledge

✅ **Other Information**
- Funding sources
- Conflicts of interest

---

## File Structure

```
econ/
├── cost_effectiveness.py    # Core CEA engine (enhanced)
├── data_integration.py       # Data loading and integration (new)
├── reporting.py              # Publication-ready outputs (new)
├── demo_analysis.py          # Complete workflow demo (new)
├── dashboard.py              # Interactive Streamlit app (enhanced)
└── README_WP2_ENHANCEMENTS.md  # This file

reports/
├── demo/                     # Demo analysis outputs
│   ├── cea_table.tex
│   ├── cea_results.xlsx
│   ├── ce_plane.png
│   ├── ceac.png
│   ├── tornado.png
│   ├── budget_impact.png
│   └── cea_full_report.txt
└── dashboard/                # Dashboard exports
    └── dashboard_export.xlsx
```

---

## Testing

### Run Demo Analysis:
```bash
# Quick test (100 patients, 100 PSA iterations)
python econ/demo_analysis.py --n-patients 100 --n-psa-simulations 100

# Full analysis (500 patients, 5000 PSA iterations)
python econ/demo_analysis.py --n-patients 500 --n-psa-simulations 5000
```

### Run Dashboard:
```bash
streamlit run econ/dashboard.py
```

### Test Data Integration:
```bash
python econ/data_integration.py
```

### Test Reporting:
```bash
python econ/reporting.py
```

---

## Future Enhancements

### Potential Additions:
1. **Real-world data integration**
   - MIMIC-IV database queries
   - Taiwan NHIRD data
   - Local hospital EHR integration

2. **Advanced analyses**
   - Cost-effectiveness efficiency frontier
   - Multi-way sensitivity analysis
   - Scenario analysis
   - Threshold analysis

3. **Additional perspectives**
   - Societal costs (productivity loss)
   - Patient out-of-pocket costs
   - Hospital perspective

4. **Enhanced reporting**
   - PDF report generation
   - Word document export
   - Interactive HTML reports
   - CHEERS checklist auto-generation

5. **Machine learning integration**
   - Predicted cost trajectories
   - Personalized cost-effectiveness
   - Treatment optimization

---

## Contact & Support

For questions or issues:
1. Review this documentation
2. Check inline code comments
3. Run demo with `--help` flag
4. Examine example outputs in `reports/demo/`

---

## References

1. Husereau D, et al. Consolidated Health Economic Evaluation Reporting Standards 2022 (CHEERS 2022). JAMA. 2022.

2. Taiwan National Health Insurance Administration. DRG Payment Standards. 2024.

3. WHO-CHOICE. Cost-effectiveness thresholds. 2023.

4. Briggs A, Claxton K, Sculpher M. Decision Modelling for Health Economic Evaluation. Oxford University Press, 2006.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-05
**Author:** Taiwan ECMO CDSS Development Team
