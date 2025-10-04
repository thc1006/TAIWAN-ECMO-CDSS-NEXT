"""
SMART on FHIR App Stub for Taiwan ECMO CDSS
=============================================

Minimal SMART App Launch implementation for EHR integration.
Implements OAuth2 authorization code flow with PKCE.

References:
- SMART App Launch: http://www.hl7.org/fhir/smart-app-launch/
- FHIR R4: http://hl7.org/fhir/R4/
"""

import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs
from datetime import datetime, timedelta

from flask import Flask, request, redirect, session, render_template, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# SMART on FHIR Configuration
FHIR_BASE_URL = os.getenv('FHIR_BASE_URL', 'https://launch.smarthealthit.org/v/r4/fhir')
CLIENT_ID = os.getenv('SMART_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('SMART_CLIENT_SECRET', '')  # Optional for public apps
REDIRECT_URI = os.getenv('SMART_REDIRECT_URI', 'http://localhost:5000/callback')

# Required FHIR scopes for ECMO CDSS
REQUIRED_SCOPES = [
    'launch',                          # SMART launch context
    'openid',                          # OpenID Connect
    'fhirUser',                        # Current user identity
    'patient/*.read',                  # Read all patient data
    'patient/Patient.read',            # Patient demographics
    'patient/Observation.read',        # Lab values, vitals (NIRS, lactate, etc.)
    'patient/Procedure.read',          # ECMO procedures
    'patient/Condition.read',          # Diagnoses (cardiac arrest, sepsis, etc.)
    'patient/MedicationRequest.read',  # Medications (vasopressors, anticoagulation)
    'patient/DiagnosticReport.read',   # Imaging, echo results
    'patient/Device.read',             # ECMO device information
]


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge for enhanced security."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def get_smart_configuration(fhir_base_url):
    """
    Retrieve SMART configuration from FHIR server's .well-known endpoint.

    Returns authorization and token endpoints.
    """
    try:
        response = requests.get(f"{fhir_base_url}/.well-known/smart-configuration")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        app.logger.error(f"Failed to retrieve SMART configuration: {e}")
        # Fallback to capability statement
        try:
            response = requests.get(f"{fhir_base_url}/metadata")
            response.raise_for_status()
            metadata = response.json()
            # Extract OAuth2 URLs from CapabilityStatement
            for rest in metadata.get('rest', []):
                for security in rest.get('security', {}).get('extension', []):
                    if 'oauth-uris' in security.get('url', ''):
                        for ext in security.get('extension', []):
                            if ext.get('url') == 'authorize':
                                auth_url = ext.get('valueUri')
                            if ext.get('url') == 'token':
                                token_url = ext.get('valueUri')
                        return {'authorization_endpoint': auth_url, 'token_endpoint': token_url}
        except Exception as e2:
            app.logger.error(f"Failed to retrieve metadata: {e2}")
    return None


@app.route('/')
def index():
    """Landing page with SMART launch instructions."""
    return render_template('index.html',
                         client_id=CLIENT_ID,
                         redirect_uri=REDIRECT_URI,
                         scopes=' '.join(REQUIRED_SCOPES))


@app.route('/launch')
def launch():
    """
    SMART App Launch endpoint (EHR-initiated launch).

    Query parameters from EHR:
    - iss: FHIR server base URL
    - launch: Launch context token
    """
    iss = request.args.get('iss')
    launch_token = request.args.get('launch')

    if not iss or not launch_token:
        return jsonify({'error': 'Missing iss or launch parameter'}), 400

    # Store launch context in session
    session['iss'] = iss
    session['launch'] = launch_token

    # Get SMART configuration from FHIR server
    smart_config = get_smart_configuration(iss)
    if not smart_config:
        return jsonify({'error': 'Failed to retrieve SMART configuration'}), 500

    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()
    session['code_verifier'] = code_verifier

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['state'] = state

    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(REQUIRED_SCOPES),
        'state': state,
        'aud': iss,
        'launch': launch_token,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }

    auth_url = f"{smart_config['authorization_endpoint']}?{urlencode(auth_params)}"
    return redirect(auth_url)


@app.route('/standalone-launch')
def standalone_launch():
    """
    Standalone launch (user-initiated from outside EHR).

    Requires manual FHIR server selection.
    """
    fhir_server = request.args.get('fhir_server', FHIR_BASE_URL)
    session['iss'] = fhir_server

    smart_config = get_smart_configuration(fhir_server)
    if not smart_config:
        return jsonify({'error': 'Failed to retrieve SMART configuration'}), 500

    code_verifier, code_challenge = generate_pkce_pair()
    session['code_verifier'] = code_verifier

    state = secrets.token_urlsafe(32)
    session['state'] = state

    # Standalone launch without launch token
    scopes = [s for s in REQUIRED_SCOPES if s != 'launch']

    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(scopes),
        'state': state,
        'aud': fhir_server,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }

    auth_url = f"{smart_config['authorization_endpoint']}?{urlencode(auth_params)}"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    OAuth2 callback endpoint.

    Receives authorization code and exchanges it for access token.
    """
    # Validate state for CSRF protection
    returned_state = request.args.get('state')
    if returned_state != session.get('state'):
        return jsonify({'error': 'Invalid state parameter'}), 400

    # Check for authorization errors
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')
        return jsonify({'error': error, 'description': error_description}), 400

    # Get authorization code
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    # Retrieve FHIR server and SMART configuration
    iss = session.get('iss')
    smart_config = get_smart_configuration(iss)

    # Exchange code for access token
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': session.get('code_verifier'),
    }

    # Add client secret if configured (confidential client)
    if CLIENT_SECRET:
        token_params['client_secret'] = CLIENT_SECRET

    try:
        response = requests.post(smart_config['token_endpoint'], data=token_params)
        response.raise_for_status()
        token_response = response.json()

        # Store tokens in session
        session['access_token'] = token_response['access_token']
        session['refresh_token'] = token_response.get('refresh_token')
        session['expires_at'] = datetime.now() + timedelta(seconds=token_response.get('expires_in', 3600))
        session['patient_id'] = token_response.get('patient')
        session['encounter_id'] = token_response.get('encounter')

        return redirect('/dashboard')

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Token exchange failed: {e}")
        return jsonify({'error': 'Token exchange failed', 'details': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """
    Main ECMO CDSS dashboard.

    Displays patient data and ECMO risk predictions.
    """
    if 'access_token' not in session:
        return redirect('/')

    # Check token expiration
    if datetime.now() >= session.get('expires_at', datetime.now()):
        return redirect('/refresh-token')

    patient_id = session.get('patient_id')

    return render_template('dashboard.html',
                         patient_id=patient_id,
                         fhir_server=session.get('iss'))


@app.route('/api/patient-data')
def get_patient_data():
    """
    Fetch patient data from FHIR server using FHIRClient.

    Returns aggregated data needed for ECMO risk assessment.
    """
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    patient_id = session.get('patient_id')
    access_token = session['access_token']
    fhir_base = session.get('iss')

    if not patient_id:
        return jsonify({'error': 'No patient context'}), 400

    try:
        from fhir_client import FHIRClient

        # Initialize FHIR client
        client = FHIRClient(fhir_base, access_token)

        # Use basic requests for compatibility with FHIR servers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json',
        }

        # Fetch patient demographics
        patient = requests.get(f"{fhir_base}/Patient/{patient_id}", headers=headers).json()

        # Fetch recent observations (vitals, labs)
        observations = requests.get(
            f"{fhir_base}/Observation",
            params={'patient': patient_id, '_count': 100, '_sort': '-date'},
            headers=headers
        ).json()

        # Fetch procedures (ECMO, CRRT)
        procedures = requests.get(
            f"{fhir_base}/Procedure",
            params={'patient': patient_id, '_count': 50},
            headers=headers
        ).json()

        # Fetch conditions (diagnoses)
        conditions = requests.get(
            f"{fhir_base}/Condition",
            params={'patient': patient_id},
            headers=headers
        ).json()

        # Store clinical data in session for risk assessment
        session['clinical_data'] = {
            'patient': patient,
            'observations': observations,
            'procedures': procedures,
            'conditions': conditions,
        }

        return jsonify({
            'patient': patient,
            'observations': observations,
            'procedures': procedures,
            'conditions': conditions,
        })

    except Exception as e:
        app.logger.error(f"Failed to fetch patient data: {e}")
        return jsonify({'error': 'Failed to fetch patient data', 'details': str(e)}), 500


@app.route('/api/ecmo-risk')
def ecmo_risk_assessment():
    """
    Calculate ECMO candidacy and risk scores.

    Integrates with nirs/risk_models.py via FHIRClient feature extraction.
    """
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    patient_id = session.get('patient_id')
    access_token = session['access_token']
    fhir_base = session.get('iss')

    if not patient_id:
        return jsonify({'error': 'No patient context'}), 400

    try:
        from fhir_client import FHIRClient

        # Initialize FHIR client
        client = FHIRClient(fhir_base, access_token)

        # Fetch all ECMO-relevant clinical data
        clinical_data = client.get_ecmo_clinical_data(patient_id)

        # Extract features for risk model
        features = client.extract_ecmo_features(clinical_data)

        # Mock risk prediction (would integrate with actual trained model)
        # In production, this would load a trained model and make predictions
        # For now, return extracted features and mock prediction

        # Simple heuristic for demonstration:
        # High lactate, low MAP, cardiac arrest -> higher risk
        risk_score = 0.5  # Default medium risk

        if features.get('lactate_mmol_l', 0) > 4:
            risk_score += 0.2
        if features.get('map_mmHg', 70) < 60:
            risk_score += 0.15
        if features.get('cardiac_arrest', False):
            risk_score += 0.15
        if features.get('cerebral_rso2_latest', 70) < 50:
            risk_score += 0.2

        risk_score = min(risk_score, 0.95)
        survival_probability = 1 - risk_score

        # Mock feature importance (would come from trained model)
        feature_importance = [
            {'feature': 'lactate_mmol_l', 'importance': 0.25},
            {'feature': 'cerebral_rso2_mean', 'importance': 0.20},
            {'feature': 'map_mmHg', 'importance': 0.18},
            {'feature': 'age', 'importance': 0.12},
            {'feature': 'cardiac_arrest', 'importance': 0.10},
            {'feature': 'abg_ph', 'importance': 0.08},
            {'feature': 'heart_rate', 'importance': 0.07},
        ]

        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'survival_probability': survival_probability,
            'risk_score': risk_score,
            'features': features,
            'feature_importance': feature_importance,
            'model_info': {
                'type': 'demonstration',
                'note': 'This is a demonstration. In production, integrate with trained models from nirs/risk_models.py'
            },
            'recommendations': generate_recommendations(features, survival_probability)
        })

    except Exception as e:
        app.logger.error(f"Risk assessment failed: {e}")
        return jsonify({
            'error': 'Risk assessment failed',
            'details': str(e),
            'message': 'Unable to calculate risk. Please ensure all required clinical data is available.'
        }), 500


def generate_recommendations(features: dict, survival_prob: float) -> list:
    """Generate clinical recommendations based on risk assessment."""
    recommendations = []

    if survival_prob < 0.4:
        recommendations.append({
            'priority': 'high',
            'message': 'High mortality risk. Consider ECMO consultation and optimization of supportive care.'
        })

    if features.get('lactate_mmol_l', 0) > 4:
        recommendations.append({
            'priority': 'high',
            'message': 'Elevated lactate detected. Ensure adequate resuscitation and consider metabolic causes.'
        })

    if features.get('map_mmHg', 70) < 60:
        recommendations.append({
            'priority': 'high',
            'message': 'Low MAP. Consider vasopressor titration and fluid optimization.'
        })

    if features.get('cerebral_rso2_latest', 70) < 50:
        recommendations.append({
            'priority': 'medium',
            'message': 'Low cerebral oxygen saturation. Optimize cardiac output and hemoglobin.'
        })

    if not features.get('on_ecmo', False) and survival_prob < 0.3:
        recommendations.append({
            'priority': 'high',
            'message': 'Patient not on ECMO with very high risk. Urgent ECMO team consultation recommended.'
        })

    if len(recommendations) == 0:
        recommendations.append({
            'priority': 'low',
            'message': 'Continue current supportive care and monitor closely.'
        })

    return recommendations


@app.route('/refresh-token')
def refresh_token():
    """Refresh expired access token using refresh token."""
    if 'refresh_token' not in session:
        return redirect('/')

    iss = session.get('iss')
    smart_config = get_smart_configuration(iss)

    token_params = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
    }

    if CLIENT_SECRET:
        token_params['client_secret'] = CLIENT_SECRET

    try:
        response = requests.post(smart_config['token_endpoint'], data=token_params)
        response.raise_for_status()
        token_response = response.json()

        session['access_token'] = token_response['access_token']
        session['expires_at'] = datetime.now() + timedelta(seconds=token_response.get('expires_in', 3600))

        return redirect('/dashboard')

    except Exception as e:
        app.logger.error(f"Token refresh failed: {e}")
        session.clear()
        return redirect('/')


@app.route('/logout')
def logout():
    """Clear session and logout."""
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
