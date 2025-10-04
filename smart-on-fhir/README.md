# Taiwan ECMO CDSS - SMART on FHIR Integration

A SMART on FHIR application for integrating ECMO Clinical Decision Support System with Electronic Health Records (EHR).

## Overview

This application provides real-time ECMO candidacy assessment and risk stratification by:
- Fetching patient data from FHIR-compliant EHR systems
- Extracting clinical features (vitals, labs, NIRS monitoring)
- Computing survival predictions using ML-based risk models
- Displaying actionable insights through an interactive dashboard

## Features

- **SMART App Launch**: EHR-initiated and standalone launch modes
- **OAuth2/PKCE**: Secure authentication with FHIR servers
- **FHIR R4 Compliance**: Reads Patient, Observation, Procedure, Condition, MedicationRequest resources
- **Risk Assessment**: ML-based survival prediction (integrates with `nirs/risk_models.py`)
- **NIRS Monitoring**: Real-time cerebral/somatic oxygen saturation visualization
- **Interactive Dashboard**: Bootstrap 5 UI with tabs, charts, and clinical recommendations

## Architecture

```
smart-on-fhir/
├── app.py                 # Flask application with SMART launch endpoints
├── fhir_client.py        # FHIR resource fetching and parsing utilities
├── templates/
│   ├── index.html        # Landing page with launch options
│   └── dashboard.html    # Clinical dashboard with risk assessment
├── .env.example          # Environment variable template
└── README.md             # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd smart-on-fhir
pip install flask requests python-dotenv
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here

# SMART on FHIR Configuration
FHIR_BASE_URL=https://launch.smarthealthit.org/v/r4/fhir
SMART_CLIENT_ID=your-client-id
SMART_CLIENT_SECRET=  # Optional for public apps
SMART_REDIRECT_URI=http://localhost:5000/callback
```

### 3. Run the Application

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Testing with SMART Health IT Launcher

### Option 1: Standalone Launch

1. Visit `http://localhost:5000`
2. Click "Launch Standalone"
3. Application will redirect to SMART authorization
4. Select a patient from the test server
5. View the ECMO risk dashboard

### Option 2: EHR-Initiated Launch (Simulated)

1. Go to [SMART Health IT Launcher](https://launch.smarthealthit.org/)
2. Configure launch parameters:
   - **Launch Type**: Provider EHR Launch
   - **FHIR Server**: R4 (FHIR 4.0.1)
   - **App Launch URL**: `http://localhost:5000/launch`
   - **Patient**: Select any test patient
3. Click "Launch"
4. Review requested scopes and authorize
5. Dashboard will load with patient data

## Required FHIR Scopes

The application requires the following SMART scopes:

| Scope | Purpose |
|-------|---------|
| `launch` | SMART launch context |
| `openid` | OpenID Connect authentication |
| `fhirUser` | Current user identity |
| `patient/Patient.read` | Patient demographics (age, gender, MRN) |
| `patient/Observation.read` | Vitals, labs, NIRS values |
| `patient/Procedure.read` | ECMO procedures, CRRT |
| `patient/Condition.read` | Diagnoses (cardiac arrest, ARDS, sepsis) |
| `patient/MedicationRequest.read` | Medications (vasopressors, anticoagulation) |
| `patient/DiagnosticReport.read` | Imaging, echo results |
| `patient/Device.read` | ECMO device information |

## FHIR Resource Mappings

### Key LOINC Codes Used

| Code | Description | Use in Model |
|------|-------------|--------------|
| `59452-7` | Cerebral oxygen saturation (rSO2) | Primary NIRS feature |
| `59453-5` | Somatic oxygen saturation | Secondary NIRS feature |
| `2524-7` | Lactate (serum/plasma) | Critical outcome predictor |
| `2744-1` | pH (arterial blood) | Acid-base status |
| `2703-7` | PaO2 (arterial blood) | Oxygenation assessment |
| `8867-4` | Heart rate | Vital sign monitoring |
| `8480-6` / `8462-4` | Systolic/Diastolic BP | MAP calculation |
| `718-7` | Hemoglobin | Oxygen carrying capacity |
| `777-3` | Platelets | Coagulation status |

### SNOMED Procedure Codes

| Code | Description |
|------|-------------|
| `233573008` | Extracorporeal membrane oxygenation |
| `233574002` | VA ECMO |
| `233575001` | VV ECMO |
| `265764009` | Renal dialysis |

### SNOMED Condition Codes

| Code | Description |
|------|-------------|
| `410429000` | Cardiac arrest |
| `429007001` | Cardiogenic shock |
| `67782005` | ARDS |
| `91302008` | Sepsis |
| `76571007` | Septic shock |

## Integration with Risk Models

The FHIR client (`fhir_client.py`) extracts features compatible with the ML models in `nirs/risk_models.py`:

```python
from fhir_client import FHIRClient

# Initialize client
client = FHIRClient(fhir_base_url, access_token)

# Fetch all ECMO-relevant data
clinical_data = client.get_ecmo_clinical_data(patient_id)

# Extract features for risk model
features = client.extract_ecmo_features(clinical_data)

# Features include:
# - age, gender
# - cerebral_rso2_mean, cerebral_rso2_latest
# - lactate_mmol_l
# - abg_ph, abg_pao2_mmHg
# - heart_rate, map_mmHg
# - hemoglobin_g_dl, platelets_10e9_l
# - cardiac_arrest (boolean)
# - on_ecmo (boolean)
```

### Integrating Production Models

To use trained models from `nirs/risk_models.py`:

1. **Load trained model**:
```python
import pickle
from nirs.risk_models import ECMORiskModel

# Load saved model
with open('path/to/va_ecmo_model.pkl', 'rb') as f:
    va_model = pickle.load(f)
```

2. **Update `/api/ecmo-risk` endpoint**:
```python
# In app.py
from nirs.risk_models import ECMORiskModel

# Prepare feature vector
X = prepare_feature_vector(features)

# Predict
survival_prob = va_model.predict_proba(X, calibrated=True)[0, 1]
explanation = va_model.explain_prediction(X, index=0)
```

3. **Return predictions**:
```python
return jsonify({
    'survival_probability': float(survival_prob),
    'prediction': explanation,
    'features': features
})
```

## Deployment Considerations

### Production Deployment

1. **Security**:
   - Use HTTPS (required by SMART specification)
   - Set secure session cookies
   - Store client secrets securely (e.g., AWS Secrets Manager)
   - Implement rate limiting
   - Add CORS configuration if needed

2. **Environment Variables**:
```bash
FLASK_ENV=production
FLASK_SECRET_KEY=$(openssl rand -hex 32)
FHIR_BASE_URL=https://fhir.your-hospital.org
SMART_CLIENT_ID=your-production-client-id
SMART_REDIRECT_URI=https://ecmo-cdss.your-hospital.org/callback
```

3. **WSGI Server** (e.g., Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Reverse Proxy** (Nginx):
```nginx
server {
    listen 443 ssl;
    server_name ecmo-cdss.your-hospital.org;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### EHR Registration

To register this app with your EHR system:

1. **Epic**:
   - Log into Epic's App Orchard
   - Register new SMART app
   - Configure redirect URI: `https://ecmo-cdss.your-hospital.org/callback`
   - Request required scopes
   - Obtain client ID (and secret if confidential)

2. **Cerner**:
   - Access Cerner Code Console
   - Create new SMART application
   - Set launch URL: `https://ecmo-cdss.your-hospital.org/launch`
   - Configure OAuth2 settings
   - Get client credentials

3. **Other FHIR Servers**:
   - Follow vendor-specific SMART app registration process
   - Ensure FHIR R4 compatibility
   - Verify scope support

### Error Handling

The application includes comprehensive error handling:

- **Authentication errors**: Redirects to login
- **Missing data**: Graceful fallbacks with user-friendly messages
- **FHIR server errors**: Logged and displayed to user
- **Token expiration**: Automatic refresh or re-authentication

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/launch` | GET | EHR-initiated SMART launch |
| `/standalone-launch` | GET | Standalone launch (user-initiated) |
| `/callback` | GET | OAuth2 callback |
| `/dashboard` | GET | Clinical dashboard |
| `/api/patient-data` | GET | Fetch FHIR resources |
| `/api/ecmo-risk` | GET | Calculate ECMO risk assessment |
| `/refresh-token` | GET | Refresh expired access token |
| `/logout` | GET | Clear session and logout |

## Troubleshooting

### Common Issues

1. **"Failed to retrieve SMART configuration"**
   - Check FHIR server URL is correct
   - Ensure server supports `/.well-known/smart-configuration`
   - Try `/metadata` endpoint as fallback

2. **"Invalid state parameter"**
   - Session cookie not persisted (enable secure cookies)
   - CSRF protection triggered (check redirect URI)

3. **"No patient context"**
   - EHR didn't provide patient ID in token response
   - Use standalone launch and manually select patient

4. **"Failed to fetch patient data"**
   - Check access token is valid
   - Verify scopes were granted
   - Ensure patient ID is correct

5. **"Risk assessment service unavailable"**
   - Missing required FHIR resources
   - Feature extraction failed (check LOINC codes)
   - ML model not loaded (check integration)

### Debug Mode

Enable debug logging:

```python
# In app.py
import logging

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

## Development Roadmap

- [ ] Integrate production ML models from `nirs/risk_models.py`
- [ ] Add model versioning and A/B testing
- [ ] Implement real-time NIRS streaming (WebSocket)
- [ ] Add intervention tracking and outcome feedback loop
- [ ] Support FHIR write operations (create Observation resources)
- [ ] Multi-language support (English, Chinese)
- [ ] Mobile-responsive design improvements
- [ ] Offline mode with local data caching

## References

- [SMART App Launch Framework](http://www.hl7.org/fhir/smart-app-launch/)
- [FHIR R4 Specification](http://hl7.org/fhir/R4/)
- [SMART Health IT Launcher](https://launch.smarthealthit.org/)
- [LOINC Database](https://loinc.org/)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)

## License

See main project LICENSE file.

## Support

For issues or questions:
- Open a GitHub issue
- Contact: [your-email@hospital.org]
- Documentation: [project wiki URL]
