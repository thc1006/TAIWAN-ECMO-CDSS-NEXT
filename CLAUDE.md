
# TAIWAN-ECMO-CDSS-NEXT — Claude Code Agent Spec

Role: Senior Clinical ML + Health IT engineer.

Objectives:
- ELSO-aligned ETL (`etl/`, `data_dictionary.yaml`).
- MIMIC-IV Demo SQL to identify ECMO episodes (`sql/identify_ecmo.sql`).
- NIRS + EHR risk models with calibration (`nirs/`), VA/VV separated.
- Cost-effectiveness analytics + Streamlit dashboard (`econ/`).
- VR training protocol + metrics (`vr-training/`).

Guardrails:
- Provide **explanations**, not prescriptive orders; expose inputs and logic.
- Keep secrets in `.env`; PHI never enters the repo.

Tasks (use /prompts):
1) WP0_data_dictionary.md — fill and map to ELSO.
2) SQL_identify_ecmo.md — run on MIMIC-IV Demo.
3) WP1_nirs_model.md — features + calibrated models; address imbalance.
4) WP2_cost_effectiveness.md — CER/ICER/CEAC.
5) WP3_vr_study.md — metrics + protocol.
6) WP4_smart_on_fhir_stub.md — minimal SMART on FHIR app stub.
