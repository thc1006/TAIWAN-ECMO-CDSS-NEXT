# TAIWAN-ECMO-CDSS-NEXT

**臺灣主導的 ECMO 臨床決策支援（CDSS）開源專案：ELSO 對齊、SMART on FHIR、可解釋 AI、成本效益與 VR 訓練。**  

**Taiwan-led open-source ECMO CDSS: ELSO-aligned, SMART on FHIR, explainable AI, cost-effectiveness & VR training.**

> 三合一：**Navigator（床邊風險）＋ Planner（成本/容量）＋ VR Studio（團隊訓練）**  
> Standards: **ELSO Registry, SMART on FHIR, FDA Non-Device CDS, IMDRF SaMD, IEC 62304, ISO 14971**.

## Quick start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run econ/dashboard.py
````

## Layout

```
TAIWAN-ECMO-CDSS-NEXT/
├─ README.md
├─ CLAUDE.md
├─ GOVERNANCE.md
├─ TOPICS.md
├─ data_dictionary.yaml
├─ prompts/
├─ sql/
├─ etl/
├─ nirs/
├─ econ/
└─ vr-training/
```