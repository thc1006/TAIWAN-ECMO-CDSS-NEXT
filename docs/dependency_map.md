# TAIWAN-ECMO-CDSS-NEXT: Dependency Map & Module Relationships

## Complete Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION ENTRY POINTS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  streamlit run econ/dashboard.py  ←── Main UI Entry Point                   │
│  python -m pytest tests/         ←── Test Runner                            │
│  python nirs/risk_models.py      ←── Model Training                         │
│  python econ/cost_effectiveness.py ←── Economic Analysis                    │
│  python vr-training/training_protocol.py ←── VR Training Demo               │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODULE DEPENDENCY TREE                                │
└─────────────────────────────────────────────────────────────────────────────┘

econ/dashboard.py (748 lines)
├─[INTERNAL]─> nirs.risk_models.NIRSECMORiskModel
├─[INTERNAL]─> nirs.risk_models.generate_demo_data
├─[INTERNAL]─> econ.cost_effectiveness.ECMOCostEffectivenessAnalyzer
├─[INTERNAL]─> econ.cost_effectiveness.generate_demo_economic_data
├─[INTERNAL]─> econ.cost_effectiveness.CostParameters
├─[EXTERNAL]─> streamlit (Web UI framework)
│              ├── st.set_page_config()
│              ├── st.sidebar
│              ├── st.form
│              ├── st.plotly_chart()
│              └── st.cache_data
├─[EXTERNAL]─> plotly.express (Interactive visualizations)
├─[EXTERNAL]─> plotly.graph_objects (Custom plots)
├─[EXTERNAL]─> plotly.subplots (Multi-panel charts)
├─[EXTERNAL]─> pandas (DataFrames)
├─[EXTERNAL]─> numpy (Numerical operations)
├─[EXTERNAL]─> joblib (Model loading - UNUSED in current code)
└─[EXTERNAL]─> yaml (Config loading)

nirs/risk_models.py (507 lines)
├─[EXTERNAL]─> pandas (Data manipulation)
├─[EXTERNAL]─> numpy (Numerical arrays)
├─[EXTERNAL]─> sklearn.ensemble
│              ├── RandomForestClassifier
│              └── GradientBoostingClassifier
├─[EXTERNAL]─> sklearn.linear_model.LogisticRegression
├─[EXTERNAL]─> sklearn.model_selection
│              ├── train_test_split
│              ├── cross_val_score
│              └── StratifiedKFold
├─[EXTERNAL]─> sklearn.preprocessing
│              ├── StandardScaler
│              └── LabelEncoder
├─[EXTERNAL]─> sklearn.calibration
│              ├── CalibratedClassifierCV
│              └── calibration_curve
├─[EXTERNAL]─> sklearn.metrics
│              ├── roc_auc_score
│              ├── brier_score_loss
│              ├── roc_curve
│              └── precision_recall_curve
├─[EXTERNAL]─> matplotlib.pyplot (Plotting)
├─[EXTERNAL]─> seaborn (Statistical visualizations)
├─[EXTERNAL]─> shap (Model explainability)
│              ├── LinearExplainer
│              └── TreeExplainer
├─[EXTERNAL]─> joblib (Model persistence)
└─[EXTERNAL]─> logging (Structured logging)

nirs/features.py (14 lines)
├─[EXTERNAL]─> pandas (Time-windowed data)
└─[EXTERNAL]─> numpy (Statistical calculations)

econ/cost_effectiveness.py (533 lines)
├─[EXTERNAL]─> pandas (Economic data)
├─[EXTERNAL]─> numpy (Financial calculations)
├─[EXTERNAL]─> matplotlib.pyplot (Cost-effectiveness plane)
├─[EXTERNAL]─> seaborn (Statistical plots)
├─[EXTERNAL]─> logging (Audit trail)
└─[EXTERNAL]─> dataclasses (Type-safe config)

vr-training/training_protocol.py (700 lines)
├─[EXTERNAL]─> pandas (Performance data)
├─[EXTERNAL]─> numpy (Score calculations)
├─[EXTERNAL]─> dataclasses (Scenario/Metrics models)
├─[EXTERNAL]─> datetime (Session timestamps)
├─[EXTERNAL]─> json (Data export)
└─[EXTERNAL]─> logging (Training events)

etl/elso_processor.py (216 lines)
├─[EXTERNAL]─> pandas (Data transformation)
├─[EXTERNAL]─> numpy (Validation logic)
├─[EXTERNAL]─> yaml (Data dictionary loading)
├─[EXTERNAL]─> datetime (Timestamp processing)
├─[EXTERNAL]─> logging (ETL audit)
└─[EXTERNAL]─> typing (Type hints)

etl/elso_mapper.py (21 lines)
└─[EXTERNAL]─> typing (Type hints only)

tests/test_basic_functionality.py (191 lines)
├─[INTERNAL]─> etl.elso_processor.ELSODataProcessor
├─[INTERNAL]─> nirs.risk_models.NIRSECMORiskModel
├─[INTERNAL]─> nirs.risk_models.generate_demo_data
├─[INTERNAL]─> econ.cost_effectiveness.ECMOCostEffectivenessAnalyzer
├─[INTERNAL]─> econ.cost_effectiveness.CostParameters
├─[INTERNAL]─> vr_training.training_protocol.ECMOVRTrainingProtocol
├─[EXTERNAL]─> pytest (Test framework)
├─[EXTERNAL]─> pandas (Test data)
├─[EXTERNAL]─> numpy (Assertions)
├─[EXTERNAL]─> yaml (Config validation)
└─[EXTERNAL]─> sys/os (File path operations)
```

## Dependency Categories & Usage

### Category 1: Core Data Science (Used in ALL modules)
```python
pandas>=1.5.0          # 8/8 modules (100%)
numpy>=1.21.0          # 8/8 modules (100%)
```

### Category 2: Machine Learning (Used in NIRS module)
```python
scikit-learn>=1.1.0    # nirs/risk_models.py
xgboost>=1.6.0         # nirs/risk_models.py (available, not actively used)
lightgbm>=3.3.0        # nirs/risk_models.py (available, not actively used)
shap>=0.41.0           # nirs/risk_models.py (explainability)
joblib>=1.1.0          # nirs/risk_models.py (model persistence)
scipy>=1.9.0           # Indirect via sklearn
```

### Category 3: Visualization (3 modules)
```python
matplotlib>=3.5.0      # nirs/risk_models.py, econ/cost_effectiveness.py
seaborn>=0.11.0        # nirs/risk_models.py, econ/cost_effectiveness.py
plotly>=5.10.0         # econ/dashboard.py
```

### Category 4: Web Framework (1 module)
```python
streamlit>=1.15.0      # econ/dashboard.py
fastapi>=0.85.0        # PLANNED (not yet implemented)
uvicorn>=0.18.0        # PLANNED (not yet implemented)
```

### Category 5: Data Validation (2 modules)
```python
pydantic>=1.9.0        # PLANNED (not yet used)
PyYAML>=6.0            # etl/elso_processor.py, econ/dashboard.py
yaml>=0.2.5            # etl/elso_processor.py
python-dotenv>=0.20.0  # PLANNED (not yet used)
```

### Category 6: Database (0 modules - NOT USED YET)
```python
sqlalchemy>=1.4.0      # PLANNED
psycopg2-binary>=2.9.0 # PLANNED
pymongo>=4.0.0         # PLANNED
```

### Category 7: Healthcare Standards (0 modules - NOT USED YET)
```python
fhir.resources>=6.5.0  # PLANNED (SMART on FHIR)
hl7apy>=1.3.0          # PLANNED
pydicom>=2.3.0         # PLANNED
```

### Category 8: Statistics (0 modules - NOT USED YET)
```python
statsmodels>=0.13.0    # PLANNED (advanced regression)
lifelines>=0.27.0      # PLANNED (survival analysis)
tslearn>=0.5.0         # PLANNED (time series for NIRS)
```

### Category 9: Testing (1 module)
```python
pytest>=7.0.0          # tests/test_basic_functionality.py
pytest-cov>=3.0.0      # PLANNED (coverage reports)
black>=22.0.0          # PLANNED (code formatting)
flake8>=5.0.0          # PLANNED (linting)
mypy>=0.991            # PLANNED (type checking)
```

### Category 10: Utilities (ALL modules)
```python
logging (built-in)     # All modules
datetime (built-in)    # etl/elso_processor.py, vr-training/training_protocol.py
dataclasses (built-in) # econ/cost_effectiveness.py, vr-training/training_protocol.py
typing (built-in)      # Most modules
json (built-in)        # vr-training/training_protocol.py
```

## Unused Dependencies (Candidates for Removal or Future Use)

```python
# HTTP Clients (not used in current codebase)
requests>=2.28.0       # UNUSED
httpx>=0.23.0          # UNUSED

# Geographic Analysis (not used)
geopy>=2.2.0           # UNUSED

# Documentation (not actively used)
sphinx>=5.0.0          # UNUSED
sphinx-rtd-theme>=1.0.0 # UNUSED

# Deployment (not used in code, only for ops)
gunicorn>=20.1.0       # UNUSED in Python code
docker>=6.0.0          # UNUSED in Python code

# Security (not yet implemented)
cryptography>=37.0.0   # UNUSED
pyjwt>=2.4.0           # UNUSED

# Monitoring (not yet implemented)
structlog>=22.1.0      # UNUSED

# Advanced ML (available but not actively used)
xgboost>=1.6.0         # AVAILABLE (imported but not primary model)
lightgbm>=3.3.0        # AVAILABLE (imported but not primary model)
```

## Import Patterns & Best Practices

### Pattern 1: Explicit Imports (Preferred)
```python
# ✅ GOOD: Clear what's being used
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
```

### Pattern 2: Namespace Imports (Acceptable)
```python
# ✅ ACCEPTABLE: Common convention
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

### Pattern 3: Star Imports (NOT USED)
```python
# ❌ AVOIDED: Not present in codebase
# from module import *
```

### Pattern 4: Conditional Imports (Present)
```python
# ✅ GOOD: Used in tests for optional modules
try:
    from nirs.risk_models import NIRSECMORiskModel
except ImportError as e:
    pytest.skip(f"Could not import NIRS risk models: {e}")
```

## Cross-Module Communication Patterns

### Pattern 1: Direct Import (Most Common)
```python
# econ/dashboard.py
from nirs.risk_models import NIRSECMORiskModel, generate_demo_data
from econ.cost_effectiveness import ECMOCostEffectivenessAnalyzer

# Usage
model = NIRSECMORiskModel('VA')
analyzer = ECMOCostEffectivenessAnalyzer()
```

### Pattern 2: Function-Based (Used for Demo Data)
```python
# nirs/risk_models.py
def generate_demo_data(n_patients: int = 1000, ecmo_type: str = 'VA') -> pd.DataFrame:
    # Returns DataFrame with demo patient data
    pass

# econ/dashboard.py
demo_data = generate_demo_data(100, 'VA')
```

### Pattern 3: Class-Based (Used for Core Logic)
```python
# nirs/risk_models.py
class NIRSECMORiskModel:
    def __init__(self, ecmo_type: str = 'VA'):
        self.ecmo_type = ecmo_type

    def train_model(self, X, y):
        # Training logic
        pass

# econ/dashboard.py
va_model = NIRSECMORiskModel('VA')
metrics = va_model.train_model(X_train, y_train)
```

## Missing Integrations (Gaps in Dependency Graph)

### API Layer ❌ (Planned but Not Implemented)
```python
# MISSING: api/main.py
from fastapi import FastAPI, Depends, HTTPException
from api.routes import risk, economics, vr_training
from api.auth import get_current_user

app = FastAPI(title="Taiwan ECMO CDSS API")
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(economics.router, prefix="/api/v1/economics", tags=["economics"])
app.include_router(vr_training.router, prefix="/api/v1/vr", tags=["vr-training"])
```

### Database Layer ❌ (Planned but Not Implemented)
```python
# MISSING: models/ecmo_episode.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base

class ECMOEpisode(Base):
    __tablename__ = "ecmo_episodes"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, index=True)
    ecmo_type = Column(String)  # VA, VV, VAV
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    survival = Column(Boolean)
    # ... more fields
```

### FHIR Integration ❌ (Planned but Not Implemented)
```python
# MISSING: integrations/fhir_client.py
from fhir.resources.patient import Patient
from fhir.resources.procedure import Procedure
from fhir.resources.observation import Observation

class FHIRClient:
    def get_patient(self, patient_id: str) -> Patient:
        # Fetch patient from FHIR server
        pass

    def get_ecmo_procedures(self, patient_id: str) -> list[Procedure]:
        # Fetch ECMO procedures
        pass
```

## Dependency Installation Strategy

### Step 1: Verify Python Version
```bash
python --version  # Should be 3.9+ for all dependencies
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Step 3: Install in Order (Resolve Dependency Conflicts)
```bash
# Core dependencies (no conflicts)
pip install pandas numpy scipy

# ML libraries (order matters - scikit-learn before xgboost)
pip install scikit-learn
pip install xgboost lightgbm shap joblib

# Visualization (matplotlib before seaborn)
pip install matplotlib
pip install seaborn plotly

# Web frameworks
pip install streamlit fastapi uvicorn

# All remaining dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import pandas, numpy, sklearn, streamlit; print('Core imports OK')"
pytest tests/test_basic_functionality.py -v
```

## Dependency Update Strategy

### Current Approach: Minimum Version (`>=`)
```txt
pandas>=1.5.0  # Allows 1.5.0, 1.5.1, 1.6.0, 2.0.0, etc.
```

### Recommended Production Approach: Exact Pinning
```bash
# Generate locked requirements
pip freeze > requirements-lock.txt

# Example output:
# pandas==1.5.3
# numpy==1.21.6
# scikit-learn==1.1.3
```

### Dependency Update Workflow
```bash
# 1. Test with latest versions
pip install --upgrade pandas numpy scikit-learn
pytest tests/

# 2. If tests pass, update requirements.txt
pip freeze > requirements-lock.txt

# 3. Commit both files
git add requirements.txt requirements-lock.txt
git commit -m "Update dependencies to latest compatible versions"
```

---

**Last Updated:** 2025-09-30
**Dependencies Tracked:** 89
**Dependencies Actively Used:** 20-25
**Unused Dependencies:** 15-20 (planned for future features)