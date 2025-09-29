# WP4: SMART on FHIR Stub - Architecture Design

## System Overview

Minimal viable SMART App Launch implementation for embedding in EHR systems to access ECMO patient data via FHIR R4.

---

## Component Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   SMART App (Node.js/Express)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           Frontend (Minimal HTML/JS)                      │ │
│  │  - Launch page                                            │ │
│  │  - OAuth callback handler                                 │ │
│  │  - Patient data viewer (ECMO context)                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           Backend API (Express.js)                        │ │
│  │                                                            │ │
│  │  ┌────────────────┐  ┌────────────────┐                  │ │
│  │  │ Launch Handler │  │ Auth Manager   │                  │ │
│  │  │ /launch        │  │ - PKCE         │                  │ │
│  │  │ /callback      │  │ - Token mgmt   │                  │ │
│  │  └────────────────┘  └────────────────┘                  │ │
│  │                                                            │ │
│  │  ┌────────────────┐  ┌────────────────┐                  │ │
│  │  │ FHIR Client    │  │ Token Store    │                  │ │
│  │  │ - Patient      │  │ - In-memory    │                  │ │
│  │  │ - Observation  │  │ - Session mgmt │                  │ │
│  │  │ - MedicationRx │  │ - Refresh      │                  │ │
│  │  └────────────────┘  └────────────────┘                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    EHR Authorization Server                     │
│  (SMART-compliant OAuth2 provider)                             │
├────────────────────────────────────────────────────────────────┤
│  /.well-known/smart-configuration                              │
│  /authorize (user consent)                                     │
│  /token (code exchange, refresh)                               │
└────────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      FHIR R4 Server                             │
│  (Patient data repository)                                      │
├────────────────────────────────────────────────────────────────┤
│  GET /Patient/:id                                              │
│  GET /Observation?patient=:id&category=vital-signs            │
│  GET /MedicationRequest?patient=:id&status=active             │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Standalone Launch Flow

```
┌──────┐                ┌──────────┐              ┌──────────┐         ┌──────────┐
│ User │                │ SMART    │              │   EHR    │         │  FHIR    │
│      │                │   App    │              │  OAuth   │         │  Server  │
└──┬───┘                └────┬─────┘              └────┬─────┘         └────┬─────┘
   │                          │                        │                     │
   │ 1. Launch App            │                        │                     │
   ├─────────────────────────>│                        │                     │
   │                          │                        │                     │
   │                          │ 2. Discover Config     │                     │
   │                          ├───────────────────────>│                     │
   │                          │ GET /.well-known/...   │                     │
   │                          │                        │                     │
   │                          │<───────────────────────┤                     │
   │                          │ 3. Config (endpoints)  │                     │
   │                          │                        │                     │
   │                          │ 4. Generate PKCE       │                     │
   │                          │    code_challenge      │                     │
   │                          │                        │                     │
   │                          │ 5. Redirect to /authorize                    │
   │                          ├───────────────────────>│                     │
   │                          │ ?response_type=code    │                     │
   │                          │ &code_challenge=...    │                     │
   │                          │                        │                     │
   │<─────────────────────────┤                        │                     │
   │ 6. Consent Screen        │                        │                     │
   │                          │                        │                     │
   │ 7. User Approves         │                        │                     │
   ├─────────────────────────────────────────────────>│                     │
   │                          │                        │                     │
   │                          │ 8. Redirect to callback│                     │
   │<─────────────────────────┼────────────────────────┤                     │
   │ ?code=xyz&state=abc      │                        │                     │
   │                          │                        │                     │
   │                          │ 9. POST /token         │                     │
   │                          ├───────────────────────>│                     │
   │                          │ grant_type=auth_code   │                     │
   │                          │ code_verifier=...      │                     │
   │                          │                        │                     │
   │                          │<───────────────────────┤                     │
   │                          │ 10. access_token       │                     │
   │                          │     patient=Patient/123│                     │
   │                          │                        │                     │
   │                          │ 11. GET /Patient/123                         │
   │                          ├─────────────────────────────────────────────>│
   │                          │ Authorization: Bearer <token>                │
   │                          │                                              │
   │                          │<─────────────────────────────────────────────┤
   │                          │ 12. Patient resource (FHIR R4)               │
   │                          │                                              │
   │<─────────────────────────┤                                              │
   │ 13. Display Patient Data │                                              │
   │                          │                                              │
```

---

## API Endpoints

### SMART App Endpoints

#### `GET /launch`
**Purpose**: Standalone launch entry point
**Query Params**:
- `iss` (optional): FHIR server base URL
- `launch` (optional): EHR launch token

**Response**: Redirect to authorization endpoint

---

#### `GET /callback`
**Purpose**: OAuth2 callback handler
**Query Params**:
- `code`: Authorization code
- `state`: CSRF protection token
- `error` (optional): Error code if authorization failed

**Response**:
- Success: Redirect to patient viewer
- Error: Display error message

---

#### `GET /patient/:id`
**Purpose**: Fetch and display patient data
**Auth**: Session-based (token in server session)

**Response**: HTML page with patient demographics + ECMO-relevant data

---

#### `POST /logout`
**Purpose**: Revoke tokens and clear session

**Response**: Redirect to landing page

---

## Security Architecture

### 1. PKCE Implementation

```javascript
// PKCE Generation
import crypto from 'crypto';

function generatePKCE() {
  // code_verifier: 43-128 characters, base64url encoded
  const codeVerifier = crypto.randomBytes(64).toString('base64url');

  // code_challenge: SHA256(code_verifier)
  const codeChallenge = crypto
    .createHash('sha256')
    .update(codeVerifier)
    .digest('base64url');

  return {
    codeVerifier,
    codeChallenge,
    codeChallengeMethod: 'S256'
  };
}
```

### 2. State Parameter (CSRF Protection)

```javascript
// Generate state
function generateState() {
  return crypto.randomBytes(32).toString('base64url');
}

// Store in session
req.session.oauthState = generateState();

// Validate on callback
if (req.query.state !== req.session.oauthState) {
  throw new Error('Invalid state parameter - possible CSRF attack');
}
```

### 3. Token Storage

**Approach**: Server-side session storage (NOT client-side)

```javascript
// Store tokens in session (in-memory or Redis)
req.session.tokens = {
  accessToken: tokenResponse.access_token,
  refreshToken: tokenResponse.refresh_token,
  expiresAt: Date.now() + (tokenResponse.expires_in * 1000),
  scope: tokenResponse.scope,
  patient: tokenResponse.patient
};

// Automatic refresh before expiration
async function getValidAccessToken(session) {
  if (Date.now() >= session.tokens.expiresAt - 60000) {
    // Refresh 1 minute before expiration
    const newTokens = await refreshAccessToken(session.tokens.refreshToken);
    session.tokens = { ...newTokens };
  }
  return session.tokens.accessToken;
}
```

### 4. HTTPS Enforcement

```javascript
// Production middleware
app.use((req, res, next) => {
  if (process.env.NODE_ENV === 'production' && !req.secure) {
    return res.redirect(301, `https://${req.headers.host}${req.url}`);
  }
  next();
});
```

---

## FHIR Client Implementation

### Patient Resource Fetcher

```javascript
import axios from 'axios';

class FHIRClient {
  constructor(baseUrl, accessToken) {
    this.baseUrl = baseUrl;
    this.accessToken = accessToken;
  }

  async getPatient(patientId) {
    const response = await axios.get(
      `${this.baseUrl}/Patient/${patientId}`,
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'application/fhir+json'
        }
      }
    );
    return response.data;
  }

  async getObservations(patientId, category = 'vital-signs') {
    const response = await axios.get(
      `${this.baseUrl}/Observation`,
      {
        params: {
          patient: patientId,
          category: category,
          _sort: '-date',
          _count: 50
        },
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'application/fhir+json'
        }
      }
    );
    return response.data; // Bundle
  }

  async getMedicationRequests(patientId) {
    const response = await axios.get(
      `${this.baseUrl}/MedicationRequest`,
      {
        params: {
          patient: patientId,
          status: 'active'
        },
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'application/fhir+json'
        }
      }
    );
    return response.data; // Bundle
  }
}
```

---

## Configuration

### Environment Variables

```bash
# .env (development)
NODE_ENV=development
PORT=3000

# SMART App Registration
CLIENT_ID=ecmo-cdss-smart-app
CLIENT_SECRET=your-client-secret-for-confidential-client
REDIRECT_URI=http://localhost:3000/callback

# FHIR Server (default for standalone launch)
FHIR_BASE_URL=https://fhir-server.example.org

# Session
SESSION_SECRET=your-session-secret-min-32-chars

# Security
HTTPS_ONLY=false  # Set to true in production
```

### SMART App Registration (with EHR)

**App Manifest**:
```json
{
  "client_name": "Taiwan ECMO CDSS",
  "client_uri": "https://ecmo-cdss.taiwan.health",
  "redirect_uris": [
    "https://ecmo-cdss.taiwan.health/callback",
    "http://localhost:3000/callback"
  ],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic",
  "scope": "openid fhirUser patient/Patient.read patient/Observation.read patient/MedicationRequest.read offline_access",
  "logo_uri": "https://ecmo-cdss.taiwan.health/logo.png",
  "contacts": ["admin@taiwan.health"]
}
```

---

## Deployment Architecture

### Development
```
Local Node.js server (port 3000)
→ Mock EHR OAuth (MSW for tests)
→ Public HAPI FHIR test server
```

### Production
```
Azure App Service / AWS ECS
→ Load Balancer (HTTPS termination)
→ Node.js container (Express app)
→ Redis (session storage)
→ Taiwan EHR OAuth Server (production)
→ Taiwan FHIR Server (production PHI)
```

---

## Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Backend | Node.js 18+ + Express | SMART reference implementations use Node |
| HTTP Client | axios | Robust, well-tested, FHIR-friendly |
| OAuth2 | Native crypto (PKCE) | No external dependencies for security |
| JWT | jose | Lightweight, spec-compliant JWT/JWK |
| Session | express-session + Redis | Secure server-side token storage |
| Testing | Jest + Supertest + MSW | Industry standard, mock-friendly |
| Logging | winston | Structured logging for audit trail |
| Validation | ajv | JSON Schema validation for FHIR |

---

## Error Handling Strategy

### 1. OAuth Errors

```javascript
// Callback error handling
app.get('/callback', (req, res) => {
  if (req.query.error) {
    const errorMap = {
      'access_denied': 'User denied authorization',
      'invalid_request': 'Invalid authorization request',
      'server_error': 'EHR authorization server error'
    };

    return res.render('error', {
      message: errorMap[req.query.error] || 'Authorization failed',
      description: req.query.error_description
    });
  }

  // Continue with code exchange...
});
```

### 2. FHIR Errors

```javascript
// Handle FHIR OperationOutcome
async function handleFHIRResponse(response) {
  if (response.data.resourceType === 'OperationOutcome') {
    const issues = response.data.issue
      .map(i => `${i.severity}: ${i.diagnostics}`)
      .join('; ');
    throw new FHIRError(issues, response.status);
  }
  return response.data;
}
```

### 3. Token Expiration

```javascript
// Automatic retry with refresh
async function fetchWithRefresh(fetchFn, session) {
  try {
    return await fetchFn(session.tokens.accessToken);
  } catch (error) {
    if (error.response?.status === 401) {
      // Token expired, attempt refresh
      const newTokens = await refreshAccessToken(session.tokens.refreshToken);
      session.tokens = newTokens;
      return await fetchFn(newTokens.accessToken);
    }
    throw error;
  }
}
```

---

## Monitoring and Logging

### Audit Events

```javascript
// Log all security-relevant events
logger.info('oauth.authorization_requested', {
  clientId: CLIENT_ID,
  scope: requestedScope,
  timestamp: new Date().toISOString()
});

logger.info('oauth.token_obtained', {
  patient: tokenResponse.patient,
  scope: tokenResponse.scope,
  expiresIn: tokenResponse.expires_in
});

logger.warn('oauth.token_refresh_failed', {
  error: error.message,
  refreshTokenExpired: true
});
```

### Metrics

- Authorization request count
- Token exchange success rate
- Token refresh count
- FHIR API call latency
- Error rate by type

---

## Compliance and Standards

### SMART App Launch v2.2.0
- [x] Standalone launch
- [x] PKCE (RFC 7636)
- [x] State parameter (CSRF protection)
- [x] Scopes: patient/*.read
- [x] Launch context (patient parameter)
- [ ] EHR launch (future)
- [ ] Backend services (future)

### FHIR R4
- [x] Patient resource
- [x] Observation resource
- [x] MedicationRequest resource
- [x] Bundle (search results)
- [x] OperationOutcome (errors)

### Security
- [x] HTTPS enforced (production)
- [x] Server-side token storage
- [x] Authorization code single-use
- [x] Refresh token rotation
- [x] Rate limiting (future)

---

## Future Enhancements

### Phase 2 (Optional)
- EHR launch support (launch parameter)
- Multi-patient picker UI
- Context banner integration
- SMART Web Messaging

### Phase 3 (Advanced)
- Backend services for automated data sync
- Bulk FHIR export for analytics
- FHIR Subscriptions for real-time updates
- GraphQL facade over FHIR

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Author**: Senior Clinical ML + Health IT Engineer
**Status**: Architecture Approved