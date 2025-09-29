# TAIWAN-ECMO-CDSS-NEXT

**臺灣主導的 ECMO 臨床決策支援（CDSS）開源專案：ELSO 對齊、SMART on FHIR、可解釋 AI、成本效益與 VR 訓練。**  
**Taiwan-led open-source ECMO Clinical Decision Support System: ELSO-aligned, SMART on FHIR, explainable AI, cost-effectiveness & VR training.**

> **三合一：Navigator（床邊風險）＋ Planner（成本/容量）＋ VR Studio（團隊訓練）**  
> **Standards:** ELSO Registry, SMART on FHIR, FDA Non-Device CDS, IMDRF SaMD, IEC 62304, ISO 14971

## 🎯 Overview

Taiwan ECMO CDSS is a comprehensive clinical decision support system designed to improve ECMO (Extracorporeal Membrane Oxygenation) outcomes through:

- **🔍 Navigator**: Bedside risk assessment with NIRS-enhanced models (VA/VV ECMO specific)
- **📈 Planner**: Cost-effectiveness analysis and capacity planning 
- **🥽 VR Studio**: Virtual reality training protocols and team metrics

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/thc1006/TAIWAN-ECMO-CDSS-NEXT.git
cd TAIWAN-ECMO-CDSS-NEXT

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run econ/dashboard.py
```

## 📁 Project Structure

```
TAIWAN-ECMO-CDSS-NEXT/
├─ README.md                    # This file
├─ data_dictionary.yaml         # ELSO-aligned data dictionary
├─ requirements.txt             # Python dependencies
├─ .env.example                # Environment variables template
├─ sql/
│  └─ identify_ecmo.sql         # MIMIC-IV ECMO identification query
├─ etl/
│  ├─ elso_processor.py         # ELSO-aligned ETL pipeline
│  └─ codes/
│     ├─ ecmo_procedures.yaml   # ECMO procedure codes (ICD-10, CPT, SNOMED)
│     └─ ecmo_diagnoses.yaml    # ECMO indication diagnoses
├─ nirs/
│  └─ risk_models.py            # NIRS + EHR risk models (VA/VV separated)
├─ econ/
│  ├─ cost_effectiveness.py     # Cost-effectiveness analytics
│  └─ dashboard.py              # Streamlit web dashboard
├─ vr-training/
│  └─ training_protocol.py      # VR training protocols and metrics
└─ prompts/
   └─ (AI prompts and templates)
```

## 🔬 Core Components

### 1. ELSO-Aligned ETL Pipeline (`etl/`)

- **Data Dictionary**: YAML-based data structure aligned with ELSO Registry v3.4
- **Code Lists**: Comprehensive procedure and diagnosis codes (ICD-10, CPT, SNOMED, Taiwan NHI)
- **Data Processor**: Validates and transforms ECMO data to ELSO standards
- **Quality Assurance**: Built-in validation and compliance checking

### 2. MIMIC-IV ECMO Identification (`sql/`)

- **Comprehensive Query**: Identifies ECMO episodes using multiple methods:
  - Procedure codes (ICD-10-PCS, CPT)
  - Medication administration patterns
  - Chart events and device parameters
  - Clinical note text mining
- **Validation Ready**: Includes confidence scoring and manual review flags

### 3. NIRS-Enhanced Risk Models (`nirs/`)

- **Separate Models**: VA-ECMO (cardiac) and VV-ECMO (respiratory) specific
- **NIRS Integration**: Near-infrared spectroscopy for enhanced prediction
- **Risk Scores**: Calculates SAVE-II, RESP, and PRESERvE scores
- **Model Calibration**: Isotonic regression for probability calibration
- **Explainable AI**: SHAP-based explanations for clinical transparency

### 4. Cost-Effectiveness Analytics (`econ/`)

- **Comprehensive Analysis**: ICER, budget impact, sensitivity analysis
- **QALY Calculations**: Quality-adjusted life years with health utilities
- **Taiwan Context**: Cost parameters adjusted for Taiwan healthcare system
- **Interactive Dashboard**: Streamlit-based web interface

### 5. VR Training Protocol (`vr-training/`)

- **Standardized Scenarios**: 6+ training scenarios (VA/VV/Complications)
- **Performance Metrics**: Technical, communication, and decision-making scores
- **Competency Assessment**: Evidence-based evaluation criteria
- **Learning Paths**: Personalized training recommendations
- **Progress Tracking**: Comprehensive competency reporting

## 🛡️ Clinical Guardrails

⚠️ **This system provides explanations and insights, not prescriptive orders.**

- All clinical decisions must be made by qualified healthcare professionals
- System exposes inputs and logic for complete transparency  
- No protected health information (PHI) enters the repository
- All secrets managed through environment variables (`.env`)

## 📊 Key Features

### Standards Compliance
- ✅ **ELSO Registry v3.4** alignment
- ✅ **SMART on FHIR** ready (future integration)
- ✅ **FDA Non-Device CDS** guidelines
- ✅ **IEC 62304 / ISO 14971** medical device standards

### Clinical Decision Support
- ✅ **Risk stratification** with confidence intervals
- ✅ **Model interpretability** using SHAP values
- ✅ **Real-time assessment** capability
- ✅ **Multi-modal data** integration (NIRS + EHR)

### Health Economics
- ✅ **Cost-effectiveness analysis** (ICER calculations)
- ✅ **Budget impact modeling** with sensitivity analysis
- ✅ **QALY-based outcomes** assessment
- ✅ **Resource optimization** recommendations

### Training & Education
- ✅ **Simulation protocols** for team training
- ✅ **Objective assessment** metrics
- ✅ **Competency tracking** and certification
- ✅ **Performance analytics** and improvement paths

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Git

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
# Do not commit secrets or PHI to the repository
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Lint code  
flake8 .

# Type checking
mypy .
```

## 📈 Usage Examples

### Risk Assessment
```python
from nirs.risk_models import NIRSECMORiskModel

# Initialize VA-ECMO model
model = NIRSECMORiskModel('VA')

# Assess patient risk
risk_prob = model.predict_risk(patient_data)
explanation = model.explain_prediction(patient_data)
```

### Cost Analysis
```python
from econ.cost_effectiveness import ECMOCostEffectivenessAnalyzer

# Initialize analyzer
analyzer = ECMOCostEffectivenessAnalyzer()

# Calculate costs and QALYs
costs = analyzer.calculate_ecmo_costs(patient_cohort)
qalys = analyzer.calculate_qaly_outcomes(patient_cohort)

# Budget impact analysis
budget_impact = analyzer.budget_impact_analysis(
    population_size=100000, 
    utilization_rate=0.001,
    years=5
)
```

### Training Assessment
```python
from vr_training.training_protocol import ECMOVRTrainingProtocol

# Initialize training system
protocol = ECMOVRTrainingProtocol()

# Assess trainee performance
performance = protocol.assess_performance(
    trainee_id='TRAINEE_001',
    scenario_id='VA001', 
    performance_data=session_data
)

# Generate competency report
report = protocol.generate_competency_report('TRAINEE_001')
```

## 🤝 Contributing

We welcome contributions from the global ECMO community! Please see our contributing guidelines for:

- Code standards and style guide
- Clinical validation requirements  
- Documentation standards
- Issue reporting and feature requests

## 📚 Documentation

- **Clinical Guidelines**: Based on ELSO, AHA/ACC, ESC recommendations
- **Technical Documentation**: API references and implementation guides
- **Training Materials**: User manuals and training protocols
- **Validation Studies**: Clinical validation and performance metrics

## 🏥 Clinical Validation

This system is designed for research and educational purposes. Clinical implementation requires:

- Institutional review and validation
- Local regulatory approval
- Clinical workflow integration
- Staff training and certification

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

This project is open-source and freely available for research, education, and clinical implementation.

## 🌟 Acknowledgments

- **ELSO (Extracorporeal Life Support Organization)** for data standards
- **MIMIC-IV** research database for development datasets
- **Taiwan Ministry of Health and Welfare** for healthcare system insights
- **International ECMO community** for clinical expertise and feedback

## 📞 Support & Contact

- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for general questions
- **Clinical Questions**: Contact through institutional channels
- **Technical Support**: See documentation or create an issue

---

**Disclaimer**: This software is provided for research and educational purposes only. It is not intended for direct clinical use without appropriate validation, regulatory approval, and clinical oversight. All clinical decisions should be made by qualified healthcare professionals.
