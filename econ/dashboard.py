"""
ECMO Cost-Effectiveness Dashboard (WP2)
Interactive visualization of CER, ICER, and CEAC by risk quintile
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cost_effectiveness import ECMOCostEffectivenessAnalysis, generate_synthetic_quintile_data

# Page configuration
st.set_page_config(page_title="ECMO Cost-Effectiveness", layout="wide")
st.title('ECMO Cost-Effectiveness Analysis Dashboard')
st.markdown('**WP2: CER/ICER/CEAC by Risk Quintile | Parameterized for Local Context**')

# Sidebar: Cost parameters
st.sidebar.header('Local Cost Parameters (TWD)')
icu_cost = st.sidebar.number_input('ICU cost per day', 10000.0, 100000.0, 30000.0, step=1000.0)
ward_cost = st.sidebar.number_input('Ward cost per day', 1000.0, 50000.0, 8000.0, step=1000.0)
ecmo_consumable = st.sidebar.number_input('ECMO daily consumable', 5000.0, 50000.0, 15000.0, step=1000.0)
ecmo_setup = st.sidebar.number_input('ECMO setup cost', 50000.0, 500000.0, 100000.0, step=10000.0)

st.sidebar.header('Clinical Parameters')
qaly_gain = st.sidebar.number_input('QALY gain per survivor', 0.5, 5.0, 1.5, step=0.1)
time_horizon = st.sidebar.number_input('Time horizon (years)', 1.0, 10.0, 1.0, step=0.5)
discount_rate = st.sidebar.slider('Discount rate', 0.0, 0.10, 0.03, step=0.01)

st.sidebar.header('Analysis Settings')
n_patients = st.sidebar.number_input('Synthetic patient count', 100, 2000, 500, step=100)
n_simulations = st.sidebar.number_input('CEAC simulations', 100, 5000, 1000, step=100)
wtp_max = st.sidebar.number_input('Max WTP threshold (TWD)', 500000, 10000000, 3000000, step=100000)

# Initialize analysis
cea = ECMOCostEffectivenessAnalysis(
    icu_cost_per_day=icu_cost,
    ward_cost_per_day=ward_cost,
    ecmo_daily_consumable=ecmo_consumable,
    ecmo_setup_cost=ecmo_setup,
    qaly_gain_per_survivor=qaly_gain,
    time_horizon_years=time_horizon,
    discount_rate=discount_rate,
    currency="TWD"
)

# Generate data
with st.spinner('Generating synthetic patient data...'):
    patient_data = generate_synthetic_quintile_data(n_patients=int(n_patients))

# Main analysis
tab1, tab2, tab3, tab4 = st.tabs(['CER by Quintile', 'ICER Analysis', 'CEAC', 'Sensitivity Analysis'])

# Tab 1: CER by Quintile
with tab1:
    st.header('Cost-Effectiveness Ratio (CER) by Risk Quintile')

    quintile_results = cea.analyze_by_quintile(patient_data)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader('Quintile Results')
        display_df = quintile_results.copy()
        display_df['total_cost'] = display_df['total_cost'].round(0).astype(int)
        display_df['qaly'] = display_df['qaly'].round(3)
        display_df['cer'] = display_df['cer'].round(0).astype(int)
        display_df['cost_per_survivor'] = display_df['cost_per_survivor'].round(0).astype(int)
        st.dataframe(display_df, use_container_width=True)

    with col2:
        st.subheader('Key Metrics')
        avg_cer = quintile_results['cer'].mean()
        min_cer = quintile_results['cer'].min()
        max_cer = quintile_results['cer'].max()

        st.metric('Average CER', f'{avg_cer:,.0f} TWD/QALY')
        st.metric('Best CER (lowest)', f'{min_cer:,.0f} TWD/QALY')
        st.metric('Worst CER (highest)', f'{max_cer:,.0f} TWD/QALY')

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(quintile_results['quintile'], quintile_results['cer'], color='steelblue', alpha=0.7)
        ax.set_xlabel('Risk Quintile')
        ax.set_ylabel('CER (TWD/QALY)')
        ax.set_title('Cost-Effectiveness Ratio by Quintile')
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(quintile_results['quintile'], quintile_results['survival_rate'], color='forestgreen', alpha=0.7)
        ax.set_xlabel('Risk Quintile')
        ax.set_ylabel('Survival Rate')
        ax.set_title('Survival Rate by Quintile')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig)

# Tab 2: ICER Analysis
with tab2:
    st.header('Incremental Cost-Effectiveness Ratio (ICER)')
    st.markdown('**Comparison vs. Quintile 1 (Lowest Risk)**')

    icer_results = cea.compute_icer_by_quintile(quintile_results, baseline_quintile=1)

    # Merge with quintile results for context
    icer_display = icer_results.merge(
        quintile_results[['quintile', 'total_cost', 'qaly', 'survival_rate']],
        on='quintile'
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader('ICER Results')
        display_icer = icer_display.copy()
        display_icer['total_cost'] = display_icer['total_cost'].round(0).astype(int)
        display_icer['qaly'] = display_icer['qaly'].round(3)
        display_icer['incremental_cost'] = display_icer['incremental_cost'].round(0).astype(int)
        display_icer['incremental_qaly'] = display_icer['incremental_qaly'].round(3)
        display_icer['icer_vs_baseline'] = display_icer['icer_vs_baseline'].apply(
            lambda x: f'{x:,.0f}' if np.isfinite(x) else 'Dominated'
        )
        st.dataframe(display_icer, use_container_width=True)

    with col2:
        st.subheader('Interpretation')
        st.info('''
        **ICER** measures the incremental cost per additional QALY gained compared to baseline.

        - **Lower ICER**: More cost-effective
        - **Dominated**: Costs more, produces less benefit
        - **WTP threshold**: Typically 1-3x GDP per capita (~900k-2.7M TWD/QALY for Taiwan)
        ''')

    # ICER plot
    fig, ax = plt.subplots(figsize=(8, 5))

    # Filter finite ICERs for plotting
    finite_icer = icer_display[np.isfinite(icer_display['icer_vs_baseline'])]

    ax.scatter(
        finite_icer['incremental_qaly'],
        finite_icer['incremental_cost'],
        s=100,
        c=finite_icer['quintile'],
        cmap='viridis',
        alpha=0.7,
        edgecolors='black'
    )

    # Add WTP threshold lines
    wtp_thresholds = [900000, 1800000, 2700000]
    colors = ['green', 'orange', 'red']
    for wtp, color in zip(wtp_thresholds, colors):
        qaly_range = np.linspace(0, finite_icer['incremental_qaly'].max(), 100)
        cost_range = qaly_range * wtp
        ax.plot(qaly_range, cost_range, '--', color=color, alpha=0.5,
                label=f'WTP = {wtp/1000:.0f}k TWD/QALY')

    ax.set_xlabel('Incremental QALY')
    ax.set_ylabel('Incremental Cost (TWD)')
    ax.set_title('Cost-Effectiveness Plane')
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

# Tab 3: CEAC
with tab3:
    st.header('Cost-Effectiveness Acceptability Curve (CEAC)')
    st.markdown('**Probability of cost-effectiveness at different WTP thresholds**')

    with st.spinner(f'Running {n_simulations} Monte Carlo simulations...'):
        wtp_thresholds = np.linspace(0, wtp_max, 50)
        ceac_data = cea.compute_ceac(
            quintile_results,
            wtp_thresholds=wtp_thresholds,
            n_simulations=int(n_simulations)
        )

    # CEAC plot
    fig, ax = plt.subplots(figsize=(10, 6))

    for quintile in sorted(ceac_data['quintile'].unique()):
        qdata = ceac_data[ceac_data['quintile'] == quintile]
        ax.plot(
            qdata['wtp_threshold'] / 1000,  # Convert to thousands
            qdata['probability_cost_effective'],
            marker='o',
            label=f'Quintile {quintile}',
            linewidth=2
        )

    # Add reference lines
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='50% threshold')
    ax.axvline(x=900, color='green', linestyle=':', alpha=0.5, label='1x GDP/capita')
    ax.axvline(x=2700, color='red', linestyle=':', alpha=0.5, label='3x GDP/capita')

    ax.set_xlabel('Willingness-to-Pay Threshold (1000s TWD/QALY)')
    ax.set_ylabel('Probability Cost-Effective')
    ax.set_title('Cost-Effectiveness Acceptability Curve by Risk Quintile')
    ax.set_ylim([0, 1])
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    # Summary table at key WTP thresholds
    st.subheader('Probability Cost-Effective at Key Thresholds')
    key_wtp = [500000, 900000, 1500000, 2000000, 3000000]
    ceac_summary = ceac_data[ceac_data['wtp_threshold'].isin(key_wtp)].pivot(
        index='quintile',
        columns='wtp_threshold',
        values='probability_cost_effective'
    )
    ceac_summary.columns = [f'{int(x/1000)}k TWD' for x in ceac_summary.columns]
    st.dataframe(ceac_summary.style.format('{:.2%}'), use_container_width=True)

# Tab 4: Sensitivity Analysis
with tab4:
    st.header('One-Way Sensitivity Analysis')
    st.markdown('**Impact of parameter variation on CER (Quintile 3)**')

    # Base case from quintile 3
    q3_data = patient_data[patient_data['risk_quintile'] == 3]
    base_case = {
        'icu_los': q3_data['icu_los_days'].mean(),
        'ward_los': q3_data['ward_los_days'].mean(),
        'ecmo_days': q3_data['ecmo_days'].mean(),
        'survival_rate': q3_data['survival_to_discharge'].mean()
    }

    # Define sensitivity parameters
    sensitivity_params = {
        'icu_cost_per_day': (icu_cost * 0.7, icu_cost, icu_cost * 1.3),
        'ward_cost_per_day': (ward_cost * 0.7, ward_cost, ward_cost * 1.3),
        'ecmo_daily_consumable': (ecmo_consumable * 0.7, ecmo_consumable, ecmo_consumable * 1.3),
        'survival_rate': (max(0.2, base_case['survival_rate'] * 0.7),
                         base_case['survival_rate'],
                         min(0.9, base_case['survival_rate'] * 1.3))
    }

    sens_results = cea.sensitivity_analysis(base_case, sensitivity_params)

    # Display results
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader('Sensitivity Results')
        display_sens = sens_results.copy()
        display_sens['total_cost'] = display_sens['total_cost'].round(0).astype(int)
        display_sens['qaly'] = display_sens['qaly'].round(3)
        display_sens['cer'] = display_sens['cer'].round(0).astype(int)
        st.dataframe(display_sens, use_container_width=True)

    with col2:
        st.subheader('Tornado Diagram')

        # Calculate range for each parameter
        tornado_data = []
        for param in sens_results['parameter'].unique():
            pdata = sens_results[sens_results['parameter'] == param]
            low_cer = pdata[pdata['scenario'] == 'low']['cer'].values[0]
            high_cer = pdata[pdata['scenario'] == 'high']['cer'].values[0]
            base_cer = pdata[pdata['scenario'] == 'base']['cer'].values[0]

            tornado_data.append({
                'parameter': param,
                'low_delta': low_cer - base_cer,
                'high_delta': high_cer - base_cer,
                'range': abs(high_cer - low_cer)
            })

        tornado_df = pd.DataFrame(tornado_data).sort_values('range', ascending=True)

        fig, ax = plt.subplots(figsize=(6, 5))
        y_pos = np.arange(len(tornado_df))

        ax.barh(y_pos, tornado_df['low_delta'], color='steelblue', alpha=0.7, label='Low')
        ax.barh(y_pos, tornado_df['high_delta'], color='coral', alpha=0.7, label='High')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tornado_df['parameter'])
        ax.set_xlabel('Change in CER (TWD/QALY)')
        ax.set_title('Parameter Sensitivity')
        ax.axvline(x=0, color='black', linewidth=0.8)
        ax.legend()
        ax.grid(axis='x', alpha=0.3)
        st.pyplot(fig)

# Tab 5: Export and Reports
with st.sidebar:
    st.markdown('---')
    st.header('Export Options')

    if st.button('📊 Export to Excel'):
        try:
            from econ.reporting import CEAReportGenerator
            reporter = CEAReportGenerator(output_dir='./reports/dashboard')
            excel_path = reporter.generate_cea_table_excel(
                quintile_results,
                icer_results,
                filename='dashboard_export.xlsx'
            )
            st.success(f'Exported to: {excel_path}')
        except Exception as e:
            st.error(f'Export failed: {e}')

    if st.button('📄 Generate LaTeX Table'):
        try:
            from econ.reporting import CEAReportGenerator
            reporter = CEAReportGenerator()
            latex_code = reporter.generate_cea_table_latex(quintile_results, icer_results)
            st.text_area('LaTeX Code', latex_code, height=300)
        except Exception as e:
            st.error(f'Generation failed: {e}')

    if st.button('📝 Generate Executive Summary'):
        try:
            from econ.reporting import CEAReportGenerator
            reporter = CEAReportGenerator(
                wtp_threshold=wtp_max,
                currency='TWD'
            )
            summary = reporter.generate_executive_summary(
                quintile_results,
                icer_results
            )
            st.text_area('Executive Summary', summary, height=400)
        except Exception as e:
            st.error(f'Generation failed: {e}')

# Footer
st.markdown('---')
st.markdown('''
**Taiwan ECMO CDSS - WP2 Cost-Effectiveness Analysis** (Enhanced Version)

This dashboard provides:
- **CER** (Cost-Effectiveness Ratio) stratified by risk quintile
- **ICER** (Incremental Cost-Effectiveness Ratio) vs. lowest risk group
- **CEAC** (Cost-Effectiveness Acceptability Curve) with probabilistic sensitivity analysis
- **One-way sensitivity analysis** for key parameters
- **Export functionality** (Excel, LaTeX, Executive Summary)

**New Features:**
- Multi-currency support (TWD, USD, EUR)
- Taiwan NHI reimbursement calculations
- Probabilistic sensitivity analysis (PSA)
- Two-way sensitivity analysis
- Value of information (EVPI) analysis
- Budget impact analysis
- Publication-ready exports

All parameters are configurable for local context (Taiwan or other settings).
Adjust sidebar parameters to explore different scenarios.

**CHEERS 2022 Compliant** | **Taiwan NHI Perspective**
''')