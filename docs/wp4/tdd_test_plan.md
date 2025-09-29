# WP4: SMART on FHIR Stub - TDD Test Plan

## Executive Summary

This document provides a comprehensive Test-Driven Development (TDD) plan for implementing a minimal viable SMART App Launch application following the HL7 SMART on FHIR v2.2.0 specification (STU2.2) with FHIR R4.

**Target Coverage**: 100% of OAuth2 authorization flow
**Testing Framework**: Jest + Supertest + MSW (Mock Service Worker)
**Architecture Pattern**: Standalone Launch with PKCE

---

## 1. System Architecture Overview

### 1.1 Application Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SMART App (Client)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Launch Handler  │  │  Auth Manager    │                │
│  │  - Parse launch  │  │  - PKCE flow     │                │
│  │  - Build auth    │  │  - Token mgmt    │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  FHIR Client     │  │  Token Storage   │                │
│  │  - Patient       │  │  - Secure cache  │                │
│  │  - Observation   │  │  - Refresh logic │                │
│  │  - MedicationRx  │  └──────────────────┘                │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Mock EHR Authorization Server                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  SMART Configuration Endpoint                         │  │
│  │  GET /.well-known/smart-configuration                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authorization Endpoint                               │  │
│  │  GET /authorize?response_type=code&...               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Token Endpoint                                        │  │
│  │  POST /token (code, refresh_token grant types)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Mock FHIR R4 Server                           │
├─────────────────────────────────────────────────────────────┤
│  GET /Patient/:id                                            │
│  GET /Observation?patient=:id&category=vital-signs          │
│  GET /MedicationRequest?patient=:id&status=active           │
│  Capability Statement                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

**Backend (Node.js/Express)**
- Express.js for HTTP server
- axios for HTTP client
- jose for JWT/JWK handling
- crypto (Node.js native) for PKCE

**Testing Stack**
- Jest: Test runner
- Supertest: HTTP assertions
- MSW (Mock Service Worker): API mocking
- @faker-js/faker: Test data generation

**Security**
- PKCE (Proof Key for Code Exchange) - RFC 7636
- State parameter for CSRF protection
- TLS 1.2+ (enforced in production)

---

## 2. SMART App Launch Flow - Test Scenarios

### 2.1 Discovery Phase Tests

#### Test Suite: `discovery.test.js`

```javascript
describe('SMART Configuration Discovery', () => {

  test('TC-D-001: Retrieve .well-known/smart-configuration successfully', async () => {
    // GIVEN: Mock FHIR server URL
    // WHEN: GET /.well-known/smart-configuration
    // THEN: Returns 200 with valid SMART config
    // ASSERT: Contains authorization_endpoint, token_endpoint, capabilities
  });

  test('TC-D-002: Validate required SMART capabilities present', async () => {
    // ASSERT: capabilities include "launch-standalone", "sso-openid-connect"
    // ASSERT: scopes_supported includes "patient/*.read", "openid", "fhirUser"
  });

  test('TC-D-003: Handle missing .well-known endpoint gracefully', async () => {
    // GIVEN: FHIR server without SMART support
    // WHEN: Discovery fails
    // THEN: Returns meaningful error message
  });

  test('TC-D-004: Validate endpoint URLs are absolute HTTPS', async () => {
    // ASSERT: authorization_endpoint starts with https://
    // ASSERT: token_endpoint starts with https://
  });

  test('TC-D-005: Cache discovery document with 24hr TTL', async () => {
    // GIVEN: Successful discovery
    // WHEN: Second request within TTL
    // THEN: Uses cached config without HTTP call
  });

});
```

**Mock Data**: SMART Configuration JSON
```json
{
  "authorization_endpoint": "https://mock-ehr.test/authorize",
  "token_endpoint": "https://mock-ehr.test/token",
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "private_key_jwt"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "scopes_supported": [
    "openid", "fhirUser", "launch", "offline_access",
    "patient/*.read", "patient/Patient.read", "patient/Observation.read",
    "patient/MedicationRequest.read"
  ],
  "response_types_supported": ["code"],
  "capabilities": ["launch-standalone", "context-banner", "sso-openid-connect"],
  "code_challenge_methods_supported": ["S256"]
}
```

---

### 2.2 Authorization Request Tests

#### Test Suite: `authorization.test.js`

```javascript
describe('OAuth2 Authorization Request', () => {

  test('TC-A-001: Generate PKCE code_verifier and code_challenge', async () => {
    // WHEN: Generate PKCE parameters
    // THEN: code_verifier is 43-128 chars, base64url encoded
    // THEN: code_challenge = base64url(SHA256(code_verifier))
    // ASSERT: code_challenge_method = "S256"
  });

  test('TC-A-002: Build authorization URL with required parameters', async () => {
    // GIVEN: client_id, redirect_uri, scope
    // WHEN: Build authorization URL
    // THEN: Contains response_type=code
    // THEN: Contains client_id, redirect_uri, scope, state, aud
    // THEN: Contains code_challenge and code_challenge_method
  });

  test('TC-A-003: Generate cryptographically random state parameter', async () => {
    // WHEN: Generate state parameter (min 32 bytes entropy)
    // THEN: State is unique per request
    // THEN: State is stored in session for validation
  });

  test('TC-A-004: Validate redirect_uri matches registered URI', async () => {
    // GIVEN: Registered redirect_uri = "http://localhost:3000/callback"
    // WHEN: Authorization request with different URI
    // THEN: Reject with error
  });

  test('TC-A-005: Handle scope parameter formatting', async () => {
    // GIVEN: Scopes array ["openid", "fhirUser", "patient/Patient.read"]
    // WHEN: Build authorization URL
    // THEN: Scope parameter is space-separated string
  });

  test('TC-A-006: Include aud parameter with FHIR base URL', async () => {
    // GIVEN: FHIR base URL "https://fhir.example.org"
    // WHEN: Build authorization URL
    // THEN: aud parameter equals FHIR base URL
  });

  test('TC-A-007: Handle launch parameter for EHR launch', async () => {
    // GIVEN: EHR launch with launch token
    // WHEN: Build authorization URL
    // THEN: Includes launch=<opaque-token>
  });

});
```

**Test Data Generation**:
```javascript
// Helper function for test data
function generateMockAuthParams() {
  return {
    client_id: 'test-app-client-id',
    redirect_uri: 'http://localhost:3000/callback',
    scope: 'openid fhirUser patient/Patient.read patient/Observation.read patient/MedicationRequest.read',
    state: crypto.randomBytes(32).toString('base64url'),
    aud: 'https://fhir-server.test',
    code_challenge: 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
    code_challenge_method: 'S256'
  };
}
```

---

### 2.3 Token Exchange Tests

#### Test Suite: `token-exchange.test.js`

```javascript
describe('OAuth2 Token Exchange', () => {

  test('TC-T-001: Exchange authorization code for access token', async () => {
    // GIVEN: Valid authorization code, code_verifier
    // WHEN: POST /token with grant_type=authorization_code
    // THEN: Returns 200 with access_token, token_type, expires_in
    // ASSERT: token_type = "Bearer"
  });

  test('TC-T-002: Validate code_verifier against code_challenge', async () => {
    // GIVEN: Authorization code issued with PKCE challenge
    // WHEN: Token request with incorrect code_verifier
    // THEN: Returns 400 with error "invalid_grant"
  });

  test('TC-T-003: Include client authentication for confidential clients', async () => {
    // GIVEN: Confidential client with client_secret
    // WHEN: POST /token with Authorization: Basic header
    // THEN: Successfully authenticates
  });

  test('TC-T-004: Handle invalid authorization code', async () => {
    // GIVEN: Invalid/expired authorization code
    // WHEN: POST /token
    // THEN: Returns 400 with error "invalid_grant"
  });

  test('TC-T-005: Parse token response and extract scopes', async () => {
    // GIVEN: Successful token response
    // THEN: Extract access_token, scope, patient, fhirUser
    // THEN: Store tokens securely
  });

  test('TC-T-006: Handle authorization code used twice (replay attack)', async () => {
    // GIVEN: Authorization code already exchanged
    // WHEN: Attempt to exchange same code again
    // THEN: Returns 400 with error "invalid_grant"
    // THEN: Revoke all tokens issued with that code
  });

  test('TC-T-007: Validate redirect_uri matches authorization request', async () => {
    // GIVEN: Authorization with redirect_uri A
    // WHEN: Token exchange with redirect_uri B
    // THEN: Returns 400 with error "invalid_grant"
  });

  test('TC-T-008: Parse launch context from token response', async () => {
    // GIVEN: Token response with patient context
    // THEN: Extract patient: "Patient/123"
    // THEN: Extract fhirUser, encounter, etc.
  });

});
```

**Mock Token Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid fhirUser patient/Patient.read patient/Observation.read",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh-token-opaque-value",
  "patient": "Patient/example-patient-123",
  "fhirUser": "Practitioner/example-practitioner-456"
}
```

---

### 2.4 Refresh Token Tests

#### Test Suite: `token-refresh.test.js`

```javascript
describe('Token Refresh Flow', () => {

  test('TC-R-001: Refresh access token using refresh_token', async () => {
    // GIVEN: Valid refresh_token from initial auth
    // WHEN: POST /token with grant_type=refresh_token
    // THEN: Returns new access_token with same or reduced scope
  });

  test('TC-R-002: Detect refresh token reuse (security)', async () => {
    // GIVEN: Refresh token used once
    // WHEN: Attempt to use same refresh token again
    // THEN: Returns 400 and revokes all tokens in family
  });

  test('TC-R-003: Handle expired refresh token', async () => {
    // GIVEN: Expired refresh_token
    // WHEN: POST /token
    // THEN: Returns 400 with error "invalid_grant"
    // THEN: Prompt user to re-authenticate
  });

  test('TC-R-004: Maintain or reduce scope during refresh', async () => {
    // GIVEN: Original scope "patient/*.read offline_access"
    // WHEN: Refresh with scope "patient/Patient.read"
    // THEN: New token has reduced scope
  });

  test('TC-R-005: Update token storage with new credentials', async () => {
    // GIVEN: Successful refresh
    // WHEN: Store new access_token and refresh_token
    // THEN: Old tokens are invalidated
  });

  test('TC-R-006: Handle network failure during refresh', async () => {
    // GIVEN: Refresh token valid but network timeout
    // WHEN: Retry with exponential backoff
    // THEN: Eventually succeeds or fails gracefully
  });

});
```

---

### 2.5 Scope Validation Tests

#### Test Suite: `scope-validation.test.js`

```javascript
describe('Scope Authorization and Validation', () => {

  test('TC-S-001: Request patient/*.read wildcard scope', async () => {
    // GIVEN: App requests "patient/*.read"
    // WHEN: Authorization flow completes
    // THEN: Can access all patient-scoped resources
  });

  test('TC-S-002: Request fine-grained resource scopes', async () => {
    // GIVEN: App requests "patient/Patient.read patient/Observation.rs"
    // WHEN: Authorization flow completes
    // THEN: Can read Patient, read/search Observations
  });

  test('TC-S-003: Validate insufficient scope returns 403', async () => {
    // GIVEN: Token with scope "patient/Patient.read"
    // WHEN: Request GET /MedicationRequest?patient=123
    // THEN: FHIR server returns 403 Forbidden
  });

  test('TC-S-004: Request openid and fhirUser for identity', async () => {
    // GIVEN: Scope includes "openid fhirUser"
    // WHEN: Token response received
    // THEN: Includes id_token with user identity
    // THEN: fhirUser claim is FHIR resource reference
  });

  test('TC-S-005: Validate offline_access for refresh token', async () => {
    // GIVEN: Scope includes "offline_access"
    // WHEN: Token response received
    // THEN: Includes refresh_token
  });

  test('TC-S-006: Handle user denying requested scopes', async () => {
    // GIVEN: User approves only subset of requested scopes
    // WHEN: Token response received
    // THEN: scope field reflects approved scopes only
    // THEN: App handles gracefully
  });

  test('TC-S-007: Parse scope interactions (read vs search)', async () => {
    // GIVEN: Scope "patient/Observation.rs"
    // THEN: .r = read by id, .s = search
    // THEN: Both operations allowed
  });

});
```

**Scope Test Matrix**:
| Scope | Resource | Interaction | Expected Result |
|-------|----------|-------------|-----------------|
| `patient/*.read` | Patient | GET /Patient/123 | 200 OK |
| `patient/*.read` | Observation | GET /Observation?patient=123 | 200 OK |
| `patient/Patient.read` | Patient | GET /Patient/123 | 200 OK |
| `patient/Patient.read` | Observation | GET /Observation/456 | 403 Forbidden |
| `patient/Observation.rs` | Observation | GET /Observation/456 | 200 OK |
| `patient/Observation.rs` | Observation | GET /Observation?category=vital-signs | 200 OK |

---

### 2.6 FHIR Resource Access Tests

#### Test Suite: `fhir-resource-access.test.js`

```javascript
describe('FHIR R4 Resource Access', () => {

  test('TC-F-001: Fetch Patient resource with valid token', async () => {
    // GIVEN: Access token with scope "patient/Patient.read"
    // WHEN: GET /Patient/example-patient-123
    // THEN: Returns 200 with FHIR Patient resource (R4)
    // ASSERT: Resource.resourceType = "Patient"
  });

  test('TC-F-002: Fetch Observation resources (vital signs)', async () => {
    // GIVEN: Access token with scope "patient/Observation.read"
    // WHEN: GET /Observation?patient=123&category=vital-signs
    // THEN: Returns Bundle with Observations
    // ASSERT: Bundle.type = "searchset"
  });

  test('TC-F-003: Fetch active MedicationRequests', async () => {
    // GIVEN: Access token with scope "patient/MedicationRequest.read"
    // WHEN: GET /MedicationRequest?patient=123&status=active
    // THEN: Returns Bundle with active medication orders
  });

  test('TC-F-004: Handle 401 Unauthorized (missing token)', async () => {
    // GIVEN: No Authorization header
    // WHEN: GET /Patient/123
    // THEN: Returns 401 with WWW-Authenticate header
  });

  test('TC-F-005: Handle 401 Unauthorized (expired token)', async () => {
    // GIVEN: Expired access token
    // WHEN: GET /Patient/123
    // THEN: Returns 401
    // THEN: Attempt token refresh automatically
  });

  test('TC-F-006: Handle 403 Forbidden (insufficient scope)', async () => {
    // GIVEN: Token without patient/MedicationRequest.read
    // WHEN: GET /MedicationRequest?patient=123
    // THEN: Returns 403 with OperationOutcome
  });

  test('TC-F-007: Handle 404 Not Found (resource does not exist)', async () => {
    // GIVEN: Valid token
    // WHEN: GET /Patient/nonexistent-id
    // THEN: Returns 404
  });

  test('TC-F-008: Validate Bearer token format in Authorization header', async () => {
    // GIVEN: Access token
    // WHEN: Make FHIR request
    // THEN: Authorization header = "Bearer <access_token>"
  });

  test('TC-F-009: Parse FHIR Bundle and extract entries', async () => {
    // GIVEN: Search returns Bundle
    // THEN: Iterate Bundle.entry[]
    // THEN: Extract resource from entry.resource
  });

  test('TC-F-010: Handle rate limiting (429 Too Many Requests)', async () => {
    // GIVEN: Exceeded rate limit
    // WHEN: FHIR request
    // THEN: Returns 429 with Retry-After header
    // THEN: Implement exponential backoff
  });

});
```

**Mock FHIR Resources**:

*Patient Resource (R4)*:
```json
{
  "resourceType": "Patient",
  "id": "example-patient-123",
  "meta": { "versionId": "1", "lastUpdated": "2025-09-29T10:00:00Z" },
  "identifier": [
    { "system": "urn:oid:2.16.886.101.20003.20001", "value": "A123456789" }
  ],
  "active": true,
  "name": [{ "use": "official", "family": "Chen", "given": ["Wei"] }],
  "gender": "male",
  "birthDate": "1985-03-15"
}
```

*Observation Resource (Vital Signs)*:
```json
{
  "resourceType": "Observation",
  "id": "obs-hr-001",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8867-4",
      "display": "Heart rate"
    }]
  },
  "subject": { "reference": "Patient/example-patient-123" },
  "effectiveDateTime": "2025-09-29T08:30:00Z",
  "valueQuantity": { "value": 72, "unit": "bpm", "system": "http://unitsofmeasure.org", "code": "/min" }
}
```

*MedicationRequest Resource*:
```json
{
  "resourceType": "MedicationRequest",
  "id": "medrx-001",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "1049621",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  },
  "subject": { "reference": "Patient/example-patient-123" },
  "authoredOn": "2025-09-20",
  "dosageInstruction": [{
    "text": "Take 1 tablet daily",
    "timing": { "repeat": { "frequency": 1, "period": 1, "periodUnit": "d" } }
  }]
}
```

---

### 2.7 Security Tests

#### Test Suite: `security.test.js`

```javascript
describe('Security Requirements', () => {

  test('TC-SEC-001: Enforce HTTPS for all endpoints (production)', async () => {
    // GIVEN: Production environment
    // WHEN: Attempt HTTP request
    // THEN: Reject or redirect to HTTPS
  });

  test('TC-SEC-002: Validate state parameter to prevent CSRF', async () => {
    // GIVEN: Authorization callback with state parameter
    // WHEN: State does not match stored value
    // THEN: Reject with error
  });

  test('TC-SEC-003: Implement PKCE code_challenge validation', async () => {
    // GIVEN: Token exchange with code_verifier
    // WHEN: SHA256(code_verifier) != code_challenge
    // THEN: Reject with error "invalid_grant"
  });

  test('TC-SEC-004: Store tokens in secure storage (not localStorage)', async () => {
    // GIVEN: Token received
    // WHEN: Store in memory or httpOnly cookie
    // THEN: Not accessible via JavaScript (XSS protection)
  });

  test('TC-SEC-005: Implement token expiration and auto-refresh', async () => {
    // GIVEN: Token with expires_in = 3600
    // WHEN: 3600 seconds elapsed
    // THEN: Automatically attempt refresh before expiration
  });

  test('TC-SEC-006: Validate redirect_uri prevents open redirect', async () => {
    // GIVEN: Authorization with untrusted redirect_uri
    // WHEN: Redirect_uri not in whitelist
    // THEN: Reject with error
  });

  test('TC-SEC-007: Implement rate limiting on token endpoint', async () => {
    // GIVEN: Multiple failed token requests
    // WHEN: Exceed rate limit threshold
    // THEN: Return 429 and block IP temporarily
  });

  test('TC-SEC-008: Revoke tokens on logout', async () => {
    // GIVEN: User initiates logout
    // WHEN: Call token revocation endpoint
    // THEN: All tokens invalidated
  });

  test('TC-SEC-009: Validate JWT id_token signature', async () => {
    // GIVEN: id_token in token response
    // WHEN: Verify signature with JWKS
    // THEN: Accept only if signature valid
  });

  test('TC-SEC-010: Implement token binding (optional)', async () => {
    // GIVEN: Token bound to device/session
    // WHEN: Token used from different context
    // THEN: Reject request
  });

});
```

---

### 2.8 Error Handling Tests

#### Test Suite: `error-handling.test.js`

```javascript
describe('Error Handling and Edge Cases', () => {

  test('TC-E-001: Handle network timeout during authorization', async () => {
    // GIVEN: Authorization server unreachable
    // WHEN: Request timeout
    // THEN: Display user-friendly error message
  });

  test('TC-E-002: Handle user denies authorization', async () => {
    // GIVEN: User clicks "Deny" on consent screen
    // WHEN: Redirect to app with error=access_denied
    // THEN: Handle gracefully, display message
  });

  test('TC-E-003: Handle malformed token response', async () => {
    // GIVEN: Token endpoint returns invalid JSON
    // WHEN: Parse response
    // THEN: Catch error and log details
  });

  test('TC-E-004: Handle missing patient context in token response', async () => {
    // GIVEN: Token response without patient field
    // WHEN: App requires patient context
    // THEN: Prompt user to select patient or re-authorize
  });

  test('TC-E-005: Handle FHIR server returns OperationOutcome', async () => {
    // GIVEN: FHIR request with errors
    // WHEN: Server returns OperationOutcome resource
    // THEN: Parse and display error details
  });

  test('TC-E-006: Handle invalid FHIR resource format', async () => {
    // GIVEN: FHIR server returns invalid JSON
    // WHEN: Parse resource
    // THEN: Validate against FHIR R4 schema
  });

  test('TC-E-007: Handle authorization server downtime', async () => {
    // GIVEN: Authorization endpoint returns 503
    // WHEN: Detect service unavailable
    // THEN: Implement retry with backoff
  });

  test('TC-E-008: Implement circuit breaker for repeated failures', async () => {
    // GIVEN: Multiple consecutive API failures
    // WHEN: Failure threshold exceeded
    // THEN: Open circuit, return cached data or error
  });

});
```

---

## 3. Mock Server Implementation

### 3.1 Mock Authorization Server

**File**: `tests/mocks/mock-auth-server.js`

```javascript
import { rest } from 'msw';
import crypto from 'crypto';

const authCodes = new Map(); // code -> { code_challenge, redirect_uri, scope }
const accessTokens = new Map(); // token -> { scope, patient, expires_at }
const refreshTokens = new Map(); // refresh -> { access_token_id }

export const authServerHandlers = [

  // Discovery endpoint
  rest.get('https://mock-ehr.test/.well-known/smart-configuration', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({
      authorization_endpoint: 'https://mock-ehr.test/authorize',
      token_endpoint: 'https://mock-ehr.test/token',
      token_endpoint_auth_methods_supported: ['client_secret_basic', 'private_key_jwt'],
      grant_types_supported: ['authorization_code', 'refresh_token'],
      scopes_supported: [
        'openid', 'fhirUser', 'launch', 'offline_access',
        'patient/*.read', 'patient/Patient.read', 'patient/Observation.read'
      ],
      response_types_supported: ['code'],
      capabilities: ['launch-standalone', 'sso-openid-connect'],
      code_challenge_methods_supported: ['S256']
    }));
  }),

  // Authorization endpoint (simplified for tests)
  rest.get('https://mock-ehr.test/authorize', (req, res, ctx) => {
    const { code_challenge, redirect_uri, scope, state } = req.url.searchParams;

    // Generate auth code
    const code = crypto.randomBytes(32).toString('base64url');
    authCodes.set(code, { code_challenge, redirect_uri, scope });

    // Redirect back with code
    const redirectUrl = new URL(redirect_uri);
    redirectUrl.searchParams.set('code', code);
    redirectUrl.searchParams.set('state', state);

    return res(ctx.status(302), ctx.set('Location', redirectUrl.toString()));
  }),

  // Token endpoint
  rest.post('https://mock-ehr.test/token', async (req, res, ctx) => {
    const body = await req.json();

    if (body.grant_type === 'authorization_code') {
      const authData = authCodes.get(body.code);
      if (!authData) {
        return res(ctx.status(400), ctx.json({ error: 'invalid_grant' }));
      }

      // Validate PKCE
      const computed = crypto.createHash('sha256')
        .update(body.code_verifier)
        .digest('base64url');
      if (computed !== authData.code_challenge) {
        return res(ctx.status(400), ctx.json({ error: 'invalid_grant' }));
      }

      // Generate tokens
      const accessToken = crypto.randomBytes(32).toString('base64url');
      const refreshToken = crypto.randomBytes(32).toString('base64url');

      accessTokens.set(accessToken, {
        scope: authData.scope,
        patient: 'Patient/example-patient-123',
        expires_at: Date.now() + 3600000
      });

      refreshTokens.set(refreshToken, { access_token_id: accessToken });
      authCodes.delete(body.code); // One-time use

      return res(ctx.status(200), ctx.json({
        access_token: accessToken,
        token_type: 'Bearer',
        expires_in: 3600,
        scope: authData.scope,
        refresh_token: refreshToken,
        patient: 'Patient/example-patient-123'
      }));
    }

    return res(ctx.status(400), ctx.json({ error: 'unsupported_grant_type' }));
  })
];
```

### 3.2 Mock FHIR Server

**File**: `tests/mocks/mock-fhir-server.js`

```javascript
import { rest } from 'msw';

const mockPatient = {
  resourceType: 'Patient',
  id: 'example-patient-123',
  identifier: [{ system: 'urn:oid:2.16.886.101.20003.20001', value: 'A123456789' }],
  name: [{ family: 'Chen', given: ['Wei'] }],
  gender: 'male',
  birthDate: '1985-03-15'
};

const mockObservations = [
  {
    resourceType: 'Observation',
    id: 'obs-hr-001',
    status: 'final',
    category: [{ coding: [{ system: 'http://terminology.hl7.org/CodeSystem/observation-category', code: 'vital-signs' }] }],
    code: { coding: [{ system: 'http://loinc.org', code: '8867-4', display: 'Heart rate' }] },
    subject: { reference: 'Patient/example-patient-123' },
    valueQuantity: { value: 72, unit: 'bpm' }
  }
];

export const fhirServerHandlers = [

  // Patient resource
  rest.get('https://fhir-server.test/Patient/:id', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(ctx.status(401), ctx.set('WWW-Authenticate', 'Bearer'));
    }

    if (req.params.id === 'example-patient-123') {
      return res(ctx.status(200), ctx.json(mockPatient));
    }

    return res(ctx.status(404), ctx.json({
      resourceType: 'OperationOutcome',
      issue: [{ severity: 'error', code: 'not-found' }]
    }));
  }),

  // Observation search
  rest.get('https://fhir-server.test/Observation', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return res(ctx.status(401));
    }

    return res(ctx.status(200), ctx.json({
      resourceType: 'Bundle',
      type: 'searchset',
      total: mockObservations.length,
      entry: mockObservations.map(obs => ({ resource: obs }))
    }));
  }),

  // MedicationRequest search
  rest.get('https://fhir-server.test/MedicationRequest', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return res(ctx.status(401));
    }

    return res(ctx.status(200), ctx.json({
      resourceType: 'Bundle',
      type: 'searchset',
      total: 0,
      entry: []
    }));
  })
];
```

---

## 4. Integration Test Scenarios

### 4.1 End-to-End Happy Path

**Test**: `e2e-happy-path.test.js`

```javascript
describe('E2E: Complete SMART App Launch Flow', () => {

  test('TC-E2E-001: Standalone launch with patient data access', async () => {
    // 1. Discover SMART configuration
    const config = await discoverSmartConfig('https://mock-ehr.test');
    expect(config.authorization_endpoint).toBeDefined();

    // 2. Generate PKCE parameters
    const { codeVerifier, codeChallenge } = generatePKCE();
    const state = generateState();

    // 3. Build authorization URL
    const authUrl = buildAuthorizationUrl({
      authorizationEndpoint: config.authorization_endpoint,
      clientId: 'test-client',
      redirectUri: 'http://localhost:3000/callback',
      scope: 'openid fhirUser patient/Patient.read patient/Observation.read',
      state,
      codeChallenge
    });

    // 4. Simulate authorization (mock redirect)
    const callbackUrl = await simulateUserAuthorization(authUrl);
    const { code, state: returnedState } = parseCallback(callbackUrl);

    // 5. Validate state
    expect(returnedState).toBe(state);

    // 6. Exchange code for token
    const tokenResponse = await exchangeCodeForToken({
      tokenEndpoint: config.token_endpoint,
      code,
      codeVerifier,
      redirectUri: 'http://localhost:3000/callback',
      clientId: 'test-client'
    });

    expect(tokenResponse.access_token).toBeDefined();
    expect(tokenResponse.patient).toBe('Patient/example-patient-123');

    // 7. Fetch patient data
    const patient = await fetchPatient({
      fhirBaseUrl: 'https://fhir-server.test',
      patientId: 'example-patient-123',
      accessToken: tokenResponse.access_token
    });

    expect(patient.resourceType).toBe('Patient');
    expect(patient.id).toBe('example-patient-123');

    // 8. Fetch observations
    const observations = await fetchObservations({
      fhirBaseUrl: 'https://fhir-server.test',
      patientId: 'example-patient-123',
      accessToken: tokenResponse.access_token
    });

    expect(observations.resourceType).toBe('Bundle');
    expect(observations.total).toBeGreaterThan(0);
  });

});
```

### 4.2 Error Recovery Scenario

**Test**: `e2e-error-recovery.test.js`

```javascript
describe('E2E: Error Handling and Recovery', () => {

  test('TC-E2E-002: Handle token expiration and auto-refresh', async () => {
    // 1. Complete initial authorization
    const { accessToken, refreshToken } = await completeAuthorization();

    // 2. Simulate token expiration
    await sleep(3610000); // Wait > 3600s (mock time travel)

    // 3. Attempt FHIR request with expired token
    const response1 = await fetchPatient({ accessToken });
    expect(response1.status).toBe(401);

    // 4. Auto-refresh token
    const newTokens = await refreshAccessToken({ refreshToken });

    // 5. Retry FHIR request with new token
    const response2 = await fetchPatient({ accessToken: newTokens.accessToken });
    expect(response2.status).toBe(200);
  });

  test('TC-E2E-003: Handle user denies authorization', async () => {
    // 1. Initiate authorization
    const authUrl = buildAuthorizationUrl({ /* ... */ });

    // 2. Simulate user denial
    const callbackUrl = 'http://localhost:3000/callback?error=access_denied&state=abc123';
    const { error } = parseCallback(callbackUrl);

    expect(error).toBe('access_denied');

    // 3. Display appropriate message to user
    // (Verify app does not crash)
  });

});
```

---

## 5. Test Coverage Metrics

### 5.1 Coverage Targets

| Category | Target | Priority |
|----------|--------|----------|
| OAuth2 Authorization Flow | 100% | Critical |
| Token Exchange | 100% | Critical |
| PKCE Validation | 100% | Critical |
| State Parameter Validation | 100% | Critical |
| Scope Handling | 95% | High |
| FHIR Resource Access | 90% | High |
| Error Handling | 85% | Medium |
| Token Refresh | 95% | High |
| Security Tests | 100% | Critical |

### 5.2 Test Execution Strategy

**Phase 1: Unit Tests** (Week 1)
- Discovery tests
- PKCE generation
- URL building
- Token parsing
- Scope validation

**Phase 2: Integration Tests** (Week 2)
- Authorization flow with mock server
- Token exchange
- FHIR resource access
- Error scenarios

**Phase 3: E2E Tests** (Week 3)
- Complete happy path
- Error recovery
- Security validation

**Phase 4: Security Audit** (Week 4)
- Penetration testing
- OWASP Top 10 validation
- Threat modeling

---

## 6. Implementation Roadmap

### 6.1 Test-First Development Sequence

**Step 1**: Write discovery tests → Implement discovery client
**Step 2**: Write PKCE tests → Implement PKCE generator
**Step 3**: Write authorization URL tests → Implement URL builder
**Step 4**: Write token exchange tests → Implement token client
**Step 5**: Write FHIR client tests → Implement FHIR client
**Step 6**: Write security tests → Implement security measures
**Step 7**: Write E2E tests → Integrate all components

### 6.2 Dependencies

**NPM Packages**:
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.6.0",
    "jose": "^5.2.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "msw": "^2.0.0",
    "@faker-js/faker": "^8.3.1"
  }
}
```

---

## 7. Test Data Management

### 7.1 Test Fixtures

**File**: `tests/fixtures/fhir-resources.json`

Contains:
- 5 example Patient resources
- 20 Observation resources (vital signs, labs)
- 10 MedicationRequest resources
- 5 Practitioner resources
- OperationOutcome examples (errors)

### 7.2 Environment Configuration

**File**: `tests/config/test.env`

```bash
FHIR_BASE_URL=https://fhir-server.test
AUTH_BASE_URL=https://mock-ehr.test
CLIENT_ID=test-app-client-id
REDIRECT_URI=http://localhost:3000/callback
SCOPES=openid fhirUser patient/Patient.read patient/Observation.read patient/MedicationRequest.read
```

---

## 8. Continuous Integration

### 8.1 CI Pipeline

```yaml
# .github/workflows/test.yml
name: SMART App Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test -- --coverage
      - run: npm run test:security
      - uses: codecov/codecov-action@v3
```

### 8.2 Quality Gates

- Minimum 90% code coverage
- All critical tests passing
- No security vulnerabilities (npm audit)
- ESLint with no errors

---

## 9. Security Testing Checklist

- [ ] PKCE validation prevents code interception
- [ ] State parameter prevents CSRF attacks
- [ ] Tokens stored securely (not localStorage)
- [ ] HTTPS enforced in production
- [ ] Redirect URI validated against whitelist
- [ ] Authorization code single-use enforced
- [ ] Refresh token reuse detection working
- [ ] Token expiration enforced
- [ ] Rate limiting on token endpoint
- [ ] JWT signature validation (id_token)

---

## 10. Documentation Requirements

Each test file must include:
1. **Purpose**: What is being tested
2. **Setup**: Test fixtures and mocks required
3. **Assertions**: Expected outcomes
4. **References**: Link to SMART specification section

Example:
```javascript
/**
 * TC-T-001: Exchange authorization code for access token
 *
 * Purpose: Validates OAuth2 authorization code grant flow
 * Spec: https://build.fhir.org/ig/HL7/smart-app-launch/app-launch.html#step-4-app-exchanges-authorization-code-for-access-token
 *
 * Setup:
 * - Mock authorization server with /token endpoint
 * - Valid authorization code with PKCE challenge
 *
 * Assertions:
 * - Returns 200 status
 * - Response contains access_token, token_type, expires_in
 * - token_type equals "Bearer"
 * - scope matches requested scope
 */
test('TC-T-001: Exchange authorization code for access token', async () => {
  // ...
});
```

---

## 11. Success Criteria

✅ **Definition of Done for WP4**:

1. All 60+ test cases implemented and passing
2. 100% coverage of OAuth2 authorization flow
3. Mock server handles all SMART endpoints
4. Security tests validate PKCE, state, token handling
5. E2E tests demonstrate complete happy path
6. Error handling tests cover all failure modes
7. Documentation complete with references to SMART spec
8. CI pipeline running all tests automatically
9. Code review completed by security engineer
10. Demo ready: Launch app, authorize, fetch ECMO patient data

---

## Appendix A: SMART Specification References

1. **SMART App Launch v2.2.0**: https://build.fhir.org/ig/HL7/smart-app-launch/
2. **App Launch Flow**: https://build.fhir.org/ig/HL7/smart-app-launch/app-launch.html
3. **Scopes and Launch Context**: https://www.hl7.org/fhir/smart-app-launch/scopes-and-launch-context/
4. **Best Practices**: https://www.hl7.org/fhir/smart-app-launch/best-practices.html
5. **Inferno Test Kit**: https://inferno.healthit.gov/test-kits/smart-app-launch/

## Appendix B: Testing Tools

- **Jest**: https://jestjs.io/
- **Supertest**: https://github.com/ladjs/supertest
- **MSW**: https://mswjs.io/
- **HAPI FHIR Test Server**: https://hapi.fhir.org/
- **Inferno**: https://inferno.healthit.gov/

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Author**: Senior Clinical ML + Health IT Engineer (Backend API Developer)
**Status**: Ready for Implementation