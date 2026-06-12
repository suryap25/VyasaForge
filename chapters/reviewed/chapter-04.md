# Chapter 04: OpenID Connect and User Information

## Learning Objectives

After completing this chapter, you will be able to:

- Explain the core concepts of OpenID Connect (OIDC) and how it extends OAuth 2.0 for authentication
- Identify the key differences between authentication and authorization in the context of OIDC
- Understand the UserInfo endpoint and the security implications of user information disclosure
- Design and implement OIDC flows securely in web and mobile applications
- Recognize common vulnerabilities in OIDC implementations and user information handling
- Assess OIDC implementations during security reviews and penetration tests
- Apply secure design patterns when integrating OIDC into applications

## Conceptual Foundation

OpenID Connect (OIDC) is an identity layer built on top of the OAuth 2.0 authorization framework. While OAuth 2.0 solves the delegation of authorization (granting access to resources), OIDC adds authentication—verifying who a user is. This distinction is critical: OAuth 2.0 answers "What can you access?" while OIDC answers "Who are you?"

OIDC introduces several key concepts that security professionals must understand:

**Identity Provider (IdP)**: The server that authenticates users and issues identity tokens. Examples include Okta, Auth0, Azure AD, Google, or self-hosted solutions like Keycloak.

**Relying Party (RP)**: The application requesting authentication. This is typically your web or mobile application that needs to know who the user is.

**ID Token**: A JSON Web Token (JWT) that contains claims about the authentication of an end user. Unlike access tokens, ID tokens are intended for the application and should never be sent to resource servers.

**UserInfo Endpoint**: An OIDC endpoint that returns claims about the authenticated end user. This endpoint requires a valid access token and returns user information in JSON format.

**Claims**: Assertions about a user, such as name, email, phone number, or custom attributes. Claims are the fundamental unit of information in OIDC.

**Scopes**: Permissions that determine what claims an application can request. The `openid` scope is mandatory for OIDC flows. Additional scopes like `profile`, `email`, and `address` request specific claim sets.

The OIDC specification defines three primary flows:

1. **Authorization Code Flow**: Used by web applications and native mobile apps. The application receives an authorization code that is exchanged for tokens at a secure backend.

2. **Implicit Flow**: Deprecated for new implementations. Tokens are returned directly from the authorization endpoint, which creates security risks.

3. **Hybrid Flow**: Combines elements of authorization code and implicit flows, returning some tokens from the authorization endpoint and others from the token endpoint.

For modern applications, the Authorization Code Flow with PKCE (Proof Key for Code Exchange) is the recommended approach for both web and mobile applications.

## Architecture Perspective

OIDC implementations involve multiple components that must work together securely. Understanding the architectural patterns helps identify where security controls must be implemented.

### Standard OIDC Authorization Code Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. User clicks "Login with [IdP]"                             │
│  2. Application redirects to IdP authorization endpoint        │
│  3. IdP authenticates user (username/password, MFA, etc.)      │
│  4. IdP redirects back with authorization code                 │
│  5. Application backend exchanges code for tokens              │
│  6. Application receives ID token and access token             │
│  7. Application optionally calls UserInfo endpoint             │
│  8. Application creates session and redirects user             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The critical architectural principle is that sensitive operations—particularly the code-to-token exchange—must occur on the application backend, never in the browser or mobile app frontend. This prevents exposure of tokens to malicious JavaScript or network interception.

### Token Storage and Transmission

**ID Tokens** contain authentication information and should be:
- Validated on the backend before trusting claims
- Stored securely (never in localStorage for web applications)
- Used only by the application that requested them
- Checked for expiration before use

**Access Tokens** are used to call the UserInfo endpoint and should be:
- Stored securely on the backend
- Transmitted only over HTTPS
- Included in Authorization headers (Bearer token format)
- Validated for scope and expiration before use

**Refresh Tokens** (if issued) should be:
- Stored securely on the backend only
- Never exposed to the frontend
- Rotated regularly
- Revoked when users log out

### UserInfo Endpoint Architecture

The UserInfo endpoint is a critical component that requires careful architectural consideration:

```
Application Backend
    │
    ├─ Stores access token securely
    ├─ Calls UserInfo endpoint with access token
    │
    └─> IdP UserInfo Endpoint
        ├─ Validates access token
        ├─ Returns user claims
        └─> Application Backend receives claims
            ├─ Validates claims
            ├─ Maps to local user record
            └─> Application session created
```

The UserInfo endpoint should only be called from the application backend, never from the frontend. The backend must validate that the access token is still valid and has the appropriate scope before making the request.

### Multi-Tenant and Federation Considerations

In enterprise environments, applications often support multiple identity providers. The architecture must handle:

- **IdP Discovery**: Determining which IdP to use based on email domain or explicit selection
- **Claim Mapping**: Translating claims from different IdPs to a common schema
- **Attribute Synchronization**: Keeping user attributes in sync across multiple IdPs
- **Logout Coordination**: Ensuring logout from the application also logs out from the IdP

## AppSec Lens

From an application security perspective, OIDC implementations present several categories of risk that must be addressed through design, implementation, and testing.

### Token Validation Vulnerabilities

One of the most common security failures is inadequate token validation. Applications must validate:

**Signature**: Verify that the ID token was signed by the IdP using the IdP's public key. This prevents token forgery.

**Expiration**: Check the `exp` claim to ensure the token has not expired. Accepting expired tokens allows attackers to reuse old tokens.

**Audience**: Verify the `aud` claim matches the application's client ID. This prevents tokens issued for one application from being used by another.

**Issuer**: Verify the `iss` claim matches the expected IdP. This prevents tokens from unauthorized IdPs.

**Nonce**: For certain flows, verify the `nonce` claim matches the value sent in the authorization request. This prevents token replay attacks.

A common failure is trusting claims without validation:

```
// INSECURE: Trusting claims without validation
const idToken = jwt.decode(tokenString); // No verification!
const userId = idToken.sub;
createSession(userId);

// SECURE: Validating token before trusting claims
const idToken = jwt.verify(tokenString, publicKey, {
  algorithms: ['RS256'],
  audience: clientId,
  issuer: expectedIssuer
});
const userId = idToken.sub;
createSession(userId);
```

### UserInfo Endpoint Risks

The UserInfo endpoint introduces specific security considerations:

**Access Token Leakage**: If the access token is exposed (through logs, error messages, or network interception), attackers can call the UserInfo endpoint to retrieve user information. Access tokens should be treated as sensitive as passwords.

**Scope Creep**: Applications requesting excessive scopes gain access to more user information than necessary. The principle of least privilege applies to OIDC scopes.

**Information Disclosure**: User information returned from the UserInfo endpoint may contain sensitive data. Applications must protect this data in transit and at rest.

**Token Expiration**: If an access token expires, the UserInfo endpoint will return an error. Applications must handle token refresh gracefully.

### Redirect URI Validation

The redirect URI is where the IdP sends the user after authentication. If not properly validated, attackers can redirect users to malicious sites:

**Open Redirect**: If the application accepts any redirect URI, attackers can craft authorization requests that redirect to attacker-controlled sites, potentially capturing authorization codes.

**Subdomain Takeover**: If the application allows broad redirect URIs (e.g., `https://*.example.com`), attackers who compromise a subdomain can intercept authorization codes.

**Secure Implementation**: Redirect URIs must be registered with the IdP and validated exactly. The application should never construct redirect URIs dynamically based on user input.

### State Parameter and CSRF Protection

The `state` parameter is essential for CSRF protection in OIDC flows:

```
// Authorization request includes state
const state = generateRandomString();
session.state = state;
redirectToIdP(`${idpAuthEndpoint}?client_id=${clientId}&state=${state}&...`);

// After IdP redirects back
if (request.query.state !== session.state) {
  throw new Error('State mismatch - possible CSRF attack');
}
```

Without proper state validation, attackers can trick users into authenticating with attacker-controlled accounts, leading to account takeover.

### PKCE for Mobile and SPAs

For applications without a secure backend (mobile apps and single-page applications), PKCE provides additional protection:

```
// Generate code verifier and challenge
const codeVerifier = generateRandomString(128);
const codeChallenge = base64url(sha256(codeVerifier));

// Include in authorization request
redirectToIdP(`${idpAuthEndpoint}?...&code_challenge=${codeChallenge}&code_challenge_method=S256`);

// When exchanging code for token, include verifier
const tokenResponse = await fetch(idpTokenEndpoint, {
  method: 'POST',
  body: {
    code: authorizationCode,
    code_verifier: codeVerifier,
    client_id: clientId,
    // Note: client_secret should NOT be included in mobile apps
  }
});
```

PKCE prevents authorization code interception attacks by requiring knowledge of the code verifier, which is never transmitted to the IdP.

## Developer Lens

Developers implementing OIDC must understand both the protocol mechanics and the security implications of their implementation choices.

### Choosing the Right Flow

**Web Applications with Backend**: Use Authorization Code Flow with PKCE. The backend securely stores tokens and handles all sensitive operations.

**Single-Page Applications (SPAs)**: Use Authorization Code Flow with PKCE. The backend-for-frontend (BFF) pattern is recommended, where a lightweight backend handles token exchange and stores tokens securely.

**Native Mobile Applications**: Use Authorization Code Flow with PKCE. Never use the Implicit Flow or store client secrets in mobile apps.

**Server-to-Server Communication**: Use Client Credentials Flow (OAuth 2.0, not OIDC). This is not for user authentication but for service-to-service authorization.

### Implementation Checklist

When implementing OIDC, developers should verify:

- [ ] Authorization Code Flow is used (not Implicit Flow)
- [ ] PKCE is implemented for all flows
- [ ] Redirect URIs are registered and validated exactly
- [ ] State parameter is generated, stored, and validated
- [ ] Nonce parameter is used and validated (for certain flows)
- [ ] ID token signature is verified using IdP's public key
- [ ] ID token expiration is checked
- [ ] ID token audience claim matches application's client ID
- [ ] ID token issuer claim matches expected IdP
- [ ] Access tokens are stored securely on the backend
- [ ] Access tokens are never logged or exposed in error messages
- [ ] UserInfo endpoint is called only from the backend
- [ ] UserInfo endpoint response is validated
- [ ] HTTPS is used for all communication
- [ ] Tokens are cleared on logout
- [ ] Token refresh is handled gracefully

### Practical Implementation Example

Here's a simplified example of a secure OIDC implementation in a Node.js/Express application:

```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const crypto = require('crypto');

const app = express();

// Configuration
const OIDC_CONFIG = {
  clientId: process.env.OIDC_CLIENT_ID,
  clientSecret: process.env.OIDC_CLIENT_SECRET,
  redirectUri: 'https://app.example.com/auth/callback',
  authorizationEndpoint: 'https://idp.example.com/authorize',
  tokenEndpoint: 'https://idp.example.com/token',
  userInfoEndpoint: 'https://idp.example.com/userinfo',
  jwksUri: 'https://idp.example.com/.well-known/jwks.json'
};

// Generate PKCE parameters
function generatePKCE() {
  const codeVerifier = crypto.randomBytes(32).toString('hex');
  const codeChallenge = crypto
    .createHash('sha256')
    .update(codeVerifier)
    .digest('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
  
  return { codeVerifier, codeChallenge };
}

// Generate state parameter
function generateState() {
  return crypto.randomBytes(32).toString('hex');
}

// Initiate login
app.get('/auth/login', (req, res) => {
  const { codeVerifier, codeChallenge } = generatePKCE();
  const state = generateState();
  const nonce = crypto.randomBytes(16).toString('hex');
  
  // Store in secure session
  req.session.codeVerifier = codeVerifier;
  req.session.state = state;
  req.session.nonce = nonce;
  
  const authUrl = new URL(OIDC_CONFIG.authorizationEndpoint);
  authUrl.searchParams.append('client_id', OIDC_CONFIG.clientId);
  authUrl.searchParams.append('redirect_uri', OIDC_CONFIG.redirectUri);
  authUrl.searchParams.append('response_type', 'code');
  authUrl.searchParams.append('scope', 'openid profile email');
  authUrl.searchParams.append('state', state);
  authUrl.searchParams.append('nonce', nonce);
  authUrl.searchParams.append('code_challenge', codeChallenge);
  authUrl.searchParams.append('code_challenge_method', 'S256');
  
  res.redirect(authUrl.toString());
});

// Handle callback
app.get('/auth/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    
    // Validate state
    if (state !== req.session.state) {
      return res.status(400).send('State mismatch');
    }
    
    // Exchange code for tokens
    const tokenResponse = await axios.post(OIDC_CONFIG.tokenEndpoint, {
      grant_type: 'authorization_code',
      code,
      redirect_uri: OIDC_CONFIG.redirectUri,
      client_id: OIDC_CONFIG.clientId,
      client_secret: OIDC_CONFIG.clientSecret,
      code_verifier: req.session.codeVerifier
    });
    
    const { id_token, access_token } = tokenResponse.data;
    
    // Fetch and verify ID token
    const jwksResponse = await axios.get(OIDC_CONFIG.jwksUri);
    const publicKey = jwksResponse.data.keys[0]; // Simplified
    
    const idTokenClaims = jwt.verify(id_token, publicKey, {
      algorithms: ['RS256'],
      audience: OIDC_CONFIG.clientId,
      issuer: 'https://idp.example.com'
    });
    
    // Validate nonce
    if (idTokenClaims.nonce !== req.session.nonce) {
      return res.status(400).send('Nonce mismatch');
    }
    
    // Fetch user info
    const userInfoResponse = await axios.get(
      OIDC_CONFIG.userInfoEndpoint,
      {
        headers: {
          'Authorization': `Bearer ${access_token}`
        }
      }
    );
    
    const userInfo = userInfoResponse.data;
    
    // Create session
    req.session.userId = idTokenClaims.sub;
    req.session.userEmail = userInfo.email;
    req.session.userName = userInfo.name;
    
    // Clear sensitive data
    delete req.session.codeVerifier;
    delete req.session.state;
    delete req.session.nonce;
    
    res.redirect('/dashboard');
  } catch (error) {
    console.error('Authentication error:', error.message);
    res.status(500).send('Authentication failed');
  }
});

// Logout
app.get('/auth/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});
```

### Common Implementation Mistakes

**Mistake 1: Storing tokens in localStorage**
```javascript
// INSECURE
localStorage.setItem('idToken', idToken);
localStorage.setItem('accessToken', accessToken);

// SECURE
// Store tokens in secure, httpOnly cookies or session storage
// Access tokens should be stored on the backend
```

**Mistake 2: Not validating token signature**
```javascript
// INSECURE
const claims = jwt.decode(idToken); // No verification!

// SECURE
const claims = jwt.verify(idToken, publicKey, {
  algorithms: ['RS256'],
  audience: clientId,
  issuer: expectedIssuer
});
```

**Mistake 3: Accepting any redirect URI**
```javascript
// INSECURE
const redirectUri = req.query.redirect_uri; // User-controlled!
res.redirect(redirectUri);

// SECURE
const allowedRedirectUris = [
  'https://app.example.com/auth/callback',
  'https://app.example.com/auth/callback2'
];
if (!allowedRedirectUris.includes(redirectUri)) {
  throw new Error('Invalid redirect URI');
}
```

## Pentest Lens

Security testers and penetration testers should focus on specific areas when assessing OIDC implementations.

### Token Validation Testing

**Test 1: Signature Verification**
- Obtain a valid ID token
- Modify the payload (e.g., change the `sub` claim)
- Attempt to use the modified token
- **Expected Result**: Application rejects the token
- **Failure**: Application accepts the modified token

**Test 2: Expiration Validation**
- Obtain an ID token
- Wait for it to expire (or modify the `exp` claim)
- Attempt to use the expired token
- **Expected Result**: Application rejects the token
- **Failure**: Application accepts the expired token

**Test 3: Audience Validation**
- Obtain an ID token issued for a different application
- Attempt to use it in the target application
- **Expected Result**: Application rejects the token
- **Failure**: Application accepts the token

**Test 4: Issuer Validation**
- Obtain an ID token from an unauthorized IdP
- Attempt to use it in the target application
- **Expected Result**: Application rejects the token
- **Failure**: Application accepts the token

### Authorization Code Interception

- Intercept the authorization code returned from the IdP
- Attempt to use the code from a different IP address or browser
- **Expected Result**: Token exchange fails or tokens are invalidated
- **Failure**: Attacker can exchange the code for tokens

### PKCE Validation

- Intercept an authorization request
- Attempt to exchange the authorization code without the code verifier
- **Expected Result**: Token exchange fails
- **Failure**: Attacker can exchange the code without the verifier

### State Parameter Testing

- Initiate a login flow and capture the state parameter
- Craft a malicious authorization request with a different state
- Trick a user into clicking the link
- **Expected Result**: Application rejects the callback due to state mismatch
- **Failure**: Application accepts the callback and logs in the attacker's account

### Redirect URI Validation

- Attempt to register a redirect URI that is not in the whitelist
- Attempt to use a redirect URI with a different scheme (http vs https)
- Attempt to use a redirect URI with a different domain
- **Expected Result**: IdP rejects the authorization request
- **Failure**: IdP accepts the unauthorized redirect URI

# Common Findings

## Token Validation Failures

**Finding**: ID tokens accepted without signature verification or with disabled verification.

**Risk**: Attackers forge ID tokens to impersonate any user, bypassing authentication entirely.

**Example**:
```javascript
// VULNERABLE: No signature verification
const decoded = jwt.decode(idToken);
userId = decoded.sub;

// VULNERABLE: Verification disabled
jwt.verify(idToken, key, { verify: false });
```

**Detection**: Review token handling code for `jwt.decode()` without `jwt.verify()`. Check for verification options set to false. Attempt to modify token payload and observe if application accepts it.

**Remediation**: Always use `jwt.verify()` with the IdP's public key. Validate signature, expiration, audience, and issuer claims before trusting any token claim.

---

## Missing Expiration Validation

**Finding**: ID tokens used without checking the `exp` claim.

**Risk**: Expired tokens can be replayed indefinitely, allowing attackers to reuse captured tokens long after they should have been invalidated.

**Example**:
```javascript
// VULNERABLE: No expiration check
const claims = jwt.verify(token, key);
createSession(claims.sub);

// SECURE: Expiration checked by verify()
const claims = jwt.verify(token, key, { ignoreExpiration: false });
```

**Detection**: Capture a valid ID token. Modify the `exp` claim to a past timestamp. Attempt to use the modified token. If accepted, expiration validation is missing.

**Remediation**: Ensure `ignoreExpiration: false` is set in verification options (this is typically the default). Implement server-side token expiration tracking for additional defense.

---

## Audience Claim Bypass

**Finding**: ID tokens accepted without validating the `aud` (audience) claim.

**Risk**: Tokens issued for one application can be used in another application, allowing cross-application token reuse attacks.

**Example**:
```javascript
// VULNERABLE: No audience validation
jwt.verify(token, key, { algorithms: ['RS256'] });

// SECURE: Audience validated
jwt.verify(token, key, {
  algorithms: ['RS256'],
  audience: expectedClientId
});
```

**Detection**: Obtain an ID token from one application. Attempt to use it in a different application. If accepted, audience validation is missing.

**Remediation**: Always validate the `aud` claim matches the application's client ID. Configure the JWT verification library to enforce audience validation.

---

## Issuer Validation Missing

**Finding**: ID tokens accepted from any issuer without validation.

**Risk**: Attackers can create their own identity provider or compromise an unauthorized IdP to issue tokens that the application accepts.

**Example**:
```javascript
// VULNERABLE: No issuer validation
jwt.verify(token, key);

// SECURE: Issuer validated
jwt.verify(token, key, {
  issuer: 'https://trusted-idp.example.com'
});
```

**Detection**: Obtain an ID token. Modify the `iss` claim to point to an attacker-controlled IdP. Attempt to use the modified token. If accepted, issuer validation is missing.

**Remediation**: Always validate the `iss` claim matches the expected IdP URL. Maintain a whitelist of trusted IdPs if supporting multiple providers.

---

## Access Token Exposure in Logs

**Finding**: Access tokens logged in application logs, error messages, or debug output.

**Risk**: Logs are often stored in centralized logging systems with broad access. Exposed access tokens allow attackers to call the UserInfo endpoint and retrieve user information.

**Example**:
```javascript
// VULNERABLE: Token logged
console.log('Token response:', tokenResponse);
logger.info(`Received token: ${accessToken}`);

// SECURE: Sensitive data excluded
console.log('Token received successfully');
logger.info('Authentication successful', { userId: claims.sub });
```

**Detection**: Review application logs for access tokens. Search logs for patterns like "Bearer ", "access_token", or token-like strings. Check error handling code for token exposure.

**Remediation**: Never log tokens. Implement log sanitization to redact tokens. Use structured logging with explicit fields rather than logging entire objects. Implement log access controls.

---

## Nonce Parameter Not Validated

**Finding**: ID tokens accepted without validating the `nonce` claim.

**Risk**: Attackers can replay captured ID tokens in different sessions, potentially gaining unauthorized access.

**Example**:
```javascript
// VULNERABLE: Nonce not validated
const claims = jwt.verify(idToken, key);
createSession(claims.sub);

// SECURE: Nonce validated
if (claims.nonce !== session.nonce) {
  throw new Error('Nonce mismatch');
}
createSession(claims.sub);
```

**Detection**: Capture an ID token from one authentication session. Attempt to use it in a different session. If accepted, nonce validation is missing.

**Remediation**: Generate a random nonce for each authorization request. Store it in the session. Validate the nonce claim in the ID token matches the stored value.

---

## State Parameter Not Validated

**Finding**: Authorization callback processed without validating the `state` parameter.

**Risk**: Attackers can perform CSRF attacks, tricking users into authenticating with attacker-controlled accounts, leading to account takeover.

**Example**:
```javascript
// VULNERABLE: State not validated
app.get('/auth/callback', (req, res) => {
  const { code } = req.query;
  exchangeCodeForToken(code);
});

// SECURE: State validated
app.get('/auth/callback', (req, res) => {
  if (req.query.state !== req.session.state) {
    throw new Error('State mismatch');
  }
  exchangeCodeForToken(req.query.code);
});
```

**Detection**: Initiate a login flow and capture the state parameter. Craft a malicious authorization request with a different state. Trick a user into clicking the link. If the application logs them in, state validation is missing.

**Remediation**: Generate a cryptographically random state parameter for each authorization request. Store it in the session. Validate it matches the state parameter in the callback.

---

## Redirect URI Open Redirect

**Finding**: Application accepts redirect URIs not registered with the IdP or constructs them dynamically.

**Risk**: Attackers can redirect users to malicious sites after authentication, potentially capturing authorization codes or performing phishing attacks.

**Example**:
```javascript
// VULNERABLE: Dynamic redirect URI
const redirectUri = req.query.redirect_uri;
res.redirect(redirectUri);

// VULNERABLE: Overly broad registration
// IdP allows: https://*.example.com/callback

// SECURE: Whitelist validation
const allowedUris = [
  'https://app.example.com/auth/callback',
  'https://app.example.com/auth/callback2'
];
if (!allowedUris.includes(redirectUri)) {
  throw new Error('Invalid redirect URI');
}
```

**Detection**: Attempt to register a redirect URI not in the whitelist. Attempt to use a redirect URI with a different domain, subdomain, or path. If accepted, validation is missing.

**Remediation**: Register redirect URIs with the IdP using exact matching. Validate redirect URIs against a whitelist before redirecting. Never construct redirect URIs dynamically based on user input.

---

## PKCE Not Implemented

**Finding**: Authorization Code Flow used without PKCE in mobile apps or SPAs.

**Risk**: Authorization codes can be intercepted and exchanged for tokens by attackers, especially in mobile apps where the code is transmitted through the system browser.

**Example**:
```javascript
// VULNERABLE: No PKCE
const authUrl = `${idpAuthEndpoint}?client_id=${clientId}&code=...`;

// SECURE: PKCE implemented
const codeChallenge = base64url(sha256(codeVerifier));
const authUrl = `${idpAuthEndpoint}?client_id=${clientId}&code_challenge=${codeChallenge}&code_challenge_method=S256`;
```

**Detection**: Intercept an authorization request. Capture the authorization code. Attempt to exchange it for tokens without the code verifier. If successful, PKCE is not implemented.

**Remediation**: Implement PKCE for all Authorization Code Flow implementations. Use S256 (SHA256) as the code challenge method. Generate a cryptographically random code verifier of at least 128 characters.

---

## Client Secret Exposed in Mobile Apps

**Finding**: Client secret hardcoded in mobile application code.

**Risk**: Client secrets can be extracted from mobile app binaries through reverse engineering. Attackers can use the secret to exchange authorization codes for tokens.

**Example**:
```javascript
// VULNERABLE: Secret in code
const clientSecret = 'super_secret_key_12345';

// VULNERABLE: Secret in config file
const config = require('./config.json'); // Contains secret
```

**Detection**: Decompile or reverse engineer the mobile app. Search for strings matching the client ID or secret format. Check configuration files and resources.

**Remediation**: Never include client secrets in mobile apps. Use PKCE instead of client secrets for mobile apps. If a secret is exposed, rotate it immediately and revoke all tokens issued with it.

---

## UserInfo Endpoint Called from Frontend

**Finding**: UserInfo endpoint called directly from browser JavaScript or mobile app frontend.

**Risk**: Access tokens are exposed to the frontend, increasing the attack surface. Tokens can be stolen through XSS attacks or network interception.

**Example**:
```javascript
// VULNERABLE: UserInfo called from frontend
fetch('https://idp.example.com/userinfo', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
}).then(r => r.json()).then(user => {
  localStorage.setItem('user', JSON.stringify(user));
});

// SECURE: UserInfo called from backend
// Frontend calls backend endpoint
fetch('/api/user', {
  credentials: 'include' // Uses secure session cookie
}).then(r => r.json()).then(user => {
  // User data from backend
});
```

**Detection**: Monitor network traffic from the frontend. Look for requests to the IdP's UserInfo endpoint. Check if access tokens are stored in localStorage or sessionStorage.

**Remediation**: Call the UserInfo endpoint only from the application backend. Store access tokens securely on the backend (in memory or secure storage). Return user information to the frontend through the application's own API.

---

## Tokens Stored in localStorage

**Finding**: ID tokens or access tokens stored in browser localStorage.

**Risk**: localStorage is vulnerable to XSS attacks. Any malicious JavaScript can access tokens and use them to impersonate the user.

**Example**:
```javascript
// VULNERABLE: Tokens in localStorage
localStorage.setItem('idToken', idToken);
localStorage.setItem('accessToken', accessToken);

// SECURE: Tokens in httpOnly cookies
// Set by backend with httpOnly, Secure, SameSite flags
// Not accessible to JavaScript
```

**Detection**: Open browser developer tools. Check localStorage for tokens. Search for patterns like "eyJ" (JWT prefix) or "Bearer".

**Remediation**: Store tokens in httpOnly, Secure, SameSite cookies set by the backend. If using a BFF pattern, the backend handles token storage and the frontend uses session cookies. Never store tokens in localStorage or sessionStorage.

---

## Missing HTTPS Enforcement

**Finding**: OIDC endpoints or redirect URIs use HTTP instead of HTTPS.

**Risk**: Tokens and authorization codes can be intercepted in transit. Attackers can perform man-in-the-middle attacks to steal credentials or tokens.

**Example**:
```javascript
// VULNERABLE: HTTP used
const authUrl = 'http://idp.example.com/authorize?...';

// SECURE: HTTPS enforced
const authUrl = 'https://idp.example.com/authorize?...';
```

**Detection**: Review OIDC configuration. Check redirect URIs, token endpoints, and UserInfo endpoints. Verify HTTPS is used for all endpoints.

**Remediation**: Use HTTPS for all OIDC endpoints. Enforce HTTPS in redirect URI registration. Implement HSTS headers to prevent downgrade attacks.

---

## Insufficient Scope Validation

**Finding**: Application requests excessive scopes or doesn't validate scope in access tokens.

**Risk**: Application gains access to more user information than necessary. If access tokens are compromised, attackers can access sensitive user data.

**Example**:
```javascript
// VULNERABLE: Requesting all scopes
const scopes = 'openid profile email phone address';

// VULNERABLE: Not validating scope
const userInfo = await callUserInfoEndpoint(accessToken);

// SECURE: Requesting only necessary scopes
const scopes = 'openid email';

// SECURE: Validating scope
const tokenClaims = jwt.verify(accessToken, key);
if (!tokenClaims.scope.includes('email')) {
  throw new Error('Insufficient scope');
}
```

**Detection**: Review authorization requests for requested scopes. Check if application uses all requested information. Verify scope validation in access token handling.

**Remediation**: Request only the scopes necessary for application functionality. Validate that access tokens have the required scope before calling protected endpoints. Implement scope-based access control.

---

## No Token Refresh Handling

**Finding**: Application doesn't handle access token expiration or refresh.

**Risk**: When access tokens expire, the application fails to refresh them, causing service disruption. Users may be logged out unexpectedly.

**Example**:
```javascript
// VULNERABLE: No refresh handling
const userInfo = await fetch(userInfoEndpoint, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});

// SECURE: Refresh token handling
try {
  const userInfo = await fetch(userInfoEndpoint, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
} catch (error) {
  if (error.status === 401) {
    // Token expired, refresh it
    const newTokens = await refreshAccessToken(refreshToken);
    accessToken = newTokens.access_token;
    // Retry request
  }
}
```

**Detection**: Allow an access token to expire. Attempt to use it. Observe if the application handles the error gracefully or fails.

**Remediation**: Implement token refresh logic. Store refresh tokens securely on the backend. When an access token expires, use the refresh token to obtain a new one. Implement automatic token refresh before expiration.

---

## Insufficient Logout Implementation

**Finding**: Logout doesn't clear tokens or invalidate sessions.

**Risk**: Tokens remain valid after logout. Attackers can use captured tokens to access the application even after the user logs out.

**Example**:
```javascript
// VULNERABLE: Incomplete logout
app.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
  // Tokens still valid at IdP!
});

// SECURE: Complete logout
app.get('/logout', (req, res) => {
  const idLogoutUrl = `${idpLogoutEndpoint}?id_token_hint=${idToken}&post_logout_redirect_uri=${appUrl}`;
  req.session.destroy();
  res.redirect(idLogoutUrl);
});
```

**Detection**: Log out from the application. Attempt to use captured access tokens to call the UserInfo endpoint. If successful, logout is incomplete.

**Remediation**: Clear all tokens from the backend session on logout. Implement IdP-initiated logout by redirecting to the IdP's logout endpoint. Implement token revocation to invalidate tokens at the IdP.

---

## Weak PKCE Implementation

**Finding**: PKCE implemented with weak code verifier or plain code challenge.

**Risk**: Weak code verifiers can be brute-forced. Plain code challenge method (not S256) is vulnerable to interception.

**Example**:
```javascript
// VULNERABLE: Weak code verifier
const codeVerifier = Math.random().toString(36).substring(7);

// VULNERABLE: Plain code challenge
const codeChallenge = codeVerifier; // No hashing!
authUrl.searchParams.append('code_challenge_method', 'plain');

// SECURE: Strong code verifier and S256
const codeVerifier = crypto.randomBytes(32).toString('hex');
const codeChallenge = base64url(sha256(codeVerifier));
authUrl.searchParams.append('code_challenge_method', 'S256');
```

**Detection**: Intercept authorization requests. Check code challenge method. If "plain" is used, verify that code challenge equals code verifier. Attempt to brute-force weak code verifiers.

**Remediation**: Generate code verifier using cryptographically secure random number generator. Use at least 128 characters. Always use S256 code challenge method. Never use plain method.

---

## Missing JWKS Caching and Validation

**Finding**: Application doesn't cache JWKS or validates keys incorrectly.

**Risk**: Attackers can perform key confusion attacks. Application may accept tokens signed with attacker-controlled keys.

**Example**:
```javascript
// VULNERABLE: No caching, accepts any key
const jwks = await fetch(jwksUri).then(r => r.json());
const key = jwks.keys[0]; // Accepts first key without validation

// VULNERABLE: No key ID validation
const decoded = jwt.decode(token, { complete: true });
const key = findKeyByKid(decoded.header.kid); // No validation

// SECURE: Caching and validation
const jwks = await getCachedJWKS(jwksUri, { ttl: 3600 });
const decoded = jwt.decode(token, { complete: true });
const key = jwks.keys.find(k => k.kid === decoded.header.kid);
if (!key) throw new Error('Key not found');
jwt.verify(token, key);
```

**Detection**: Obtain a valid token. Modify the `kid` (key ID) header to point to a non-existent key. Attempt to use the modified token. If accepted, key validation is missing.

**Remediation**: Cache JWKS with appropriate TTL. Validate that the key ID in the token header exists in the JWKS. Validate key algorithms match expected values. Implement key rotation handling.

---

## Insufficient Error Handling

**Finding**: Detailed error messages reveal OIDC implementation details.

**Risk**: Error messages can leak information about the OIDC configuration, IdP endpoints, or token validation logic, helping attackers craft targeted attacks.

**Example**:
```javascript
// VULNERABLE: Detailed error messages
catch (error) {
  res.status(400).send(`Token validation failed: ${error.message}`);
  // Reveals: "Invalid signature", "Token expired", "Invalid audience"
}

// SECURE: Generic error messages
catch (error) {
  logger.error('Authentication error', { error: error.message });
  res.status(401).send('Authentication failed');
}
```

**Detection**: Trigger various authentication failures. Observe error messages for detailed information about OIDC configuration or validation logic.

**Remediation**: Return generic error messages to users. Log detailed errors server-side for debugging. Don't expose token validation details, endpoint URLs, or configuration in error messages.

---

## Multiple IdP Claim Mapping Issues

**Finding**: Application doesn't properly map claims from multiple IdPs to consistent user identifiers.

**Risk**: Users can create multiple accounts by authenticating with different IdPs. Attackers can exploit claim mapping to impersonate other users.

**Example**:
```javascript
// VULNERABLE: Using email as user ID
const userId = userInfo.email; // Different IdPs may have different emails

// VULNERABLE: No claim mapping
const userId = idToken.sub; // Different IdPs use different subject formats

// SECURE: Consistent user identifier
const userId = `${idToken.iss}:${idToken.sub}`; // Includes issuer
// Or maintain mapping table: IdP + sub -> local user ID
```

**Detection**: Authenticate with multiple IdPs. Observe if the application creates separate accounts or links them. Check if claim values are consistent across IdPs.

**Remediation**: Maintain a mapping table linking IdP identifiers (issuer + subject) to local user accounts. Use consistent claim mapping across all supported IdPs. Implement account linking with user verification.

---

## Lack of Rate Limiting on Token Endpoints

**Finding**: Token endpoint or UserInfo endpoint not rate-limited.

**Risk**: Attackers can brute-force authorization codes or perform credential stuffing attacks against the token endpoint.

**Example**:
```javascript
// VULNERABLE: No rate limiting
app.post('/token', async (req, res) => {
  const tokens = await exchangeCodeForToken(req.body.code);
  res.json(tokens);
});

// SECURE: Rate limiting implemented
const rateLimit = require
```

## Secure Design Guidance

This section requires additional handbook content. Cover the topic with vendor-neutral guidance, practical AppSec examples, implementation considerations, and testing notes.

## Interview Questions

- How do authentication and authorization failures show up differently in application logs?
- What controls would you expect around session creation, token validation, and privilege checks?
- How would you review an API endpoint to confirm that authorization is enforced server-side?
- What is the risk of relying on client-side checks for access control?
- How should teams test for horizontal and vertical privilege escalation?

## Key Takeaways

- Authentication verifies identity; authorization decides what that identity can access.
- Strong authentication does not compensate for missing or inconsistent authorization checks.
- Authorization belongs on the server side and should be enforced close to protected resources.
- AppSec reviews should trace identity, session, role, permission, and object ownership decisions.
- Secure design requires clear access-control models, centralized policy logic, and repeatable tests.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]

## Common Findings

# Common Findings

## Token Validation Failures

**Finding**: ID tokens accepted without signature verification or with disabled verification.

**Risk**: Attackers forge ID tokens to impersonate any user, bypassing authentication entirely.

**Example**:
```javascript
// VULNERABLE: No signature verification
const decoded = jwt.decode(idToken);
userId = decoded.sub;

// VULNERABLE: Verification disabled
jwt.verify(idToken, key, { verify: false });
```

**Detection**: Review token handling code for `jwt.decode()` without `jwt.verify()`. Check for verification options set to false. Attempt to modify token payload and observe if application accepts it.

**Remediation**: Always use `jwt.verify()` with the IdP's public key. Validate signature, expiration, audience, and issuer claims before trusting any token claim.

---

## Missing Expiration Validation

**Finding**: ID tokens used without checking the `exp` claim.

**Risk**: Expired tokens can be replayed indefinitely, allowing attackers to reuse captured tokens long after they should have been invalidated.

**Example**:
```javascript
// VULNERABLE: No expiration check
const claims = jwt.verify(token, key);
createSess(claims.sub);

// SECURE: Expiration checked by verify()
const claims = jwt.verify(token, key, { ignoreExpiration: false });
```

**Detection**: Capture a valid ID token. Modify the `exp` claim to a past timestamp. Attempt to use the modified token. If accepted, expiration validation is missing.

**Remediation**: Ensure `ignoreExpiration: false` is set in verification options (this is typically the default). Implement server-side token expiration tracking for additional defense.

---

## Audience Claim Bypass

**Finding**: ID tokens accepted without validating the `aud` (audience) claim.

**Risk**: Tokens issued for one application can be used in another application, allowing cross-application token reuse attacks.

**Example**:
```javascript
// VULNERABLE: No audience validation
jwt.verify(token, key, { algorithms: ['RS256'] });

// SECURE: Audience validated
jwt.verify(token, key, {
  algorithms: ['RS256'],
  audience: expectedClientId
});
```

**Detection**: Obtain an ID token from one application. Attempt to use it in a different application. If accepted, audience validation is missing.

**Remediation**: Always validate the `aud` claim matches the application's client ID. Configure the JWT verification library to enforce audience validation.

---

## Issuer Validation Missing

**Finding**: ID tokens accepted from any issuer without validation.

**Risk**: Attackers can create their own identity provider or compromise an unauthorized IdP to issue tokens that the application accepts.

**Example**:
```javascript
// VULNERABLE: No issuer validation
jwt.verify(token, key);

// SECURE: Issuer validated
jwt.verify(token, key, {
  issuer: 'https://trusted-idp.example.com'
});
```

**Detection**: Obtain an ID token. Modify the `iss` claim to point to an attacker-controlled IdP. Attempt to use the modified token. If accepted, issuer validation is missing.

**Remediation**: Always validate the `iss` claim matches the expected IdP URL. Maintain a whitelist of trusted IdPs if supporting multiple providers.

---

## Access Token Exposure in Logs

**Finding**: Access tokens logged in application logs, error messages, or debug output.

**Risk**: Logs are often stored in centralized logging systems with broad access. Exposed access tokens allow attackers to call the UserInfo endpoint and retrieve user information.

**Example**:
```javascript
// VULNERABLE: Token logged
console.log('Token response:', tokenResponse);
logger.info(`Received token: ${accessToken}`);

// SECURE: Sensitive data excluded
console.log('Token received successfully');
logger.info('Authentication successful', { userId: claims.sub });
```

**Detection**: Review application logs for access tokens. Search logs for patterns like "Bearer ", "access_token", or token-like strings. Check error handling code for token exposure.

**Remediation**: Never log tokens. Implement log sanitization to redact tokens. Use structured logging with explicit fields rather than logging entire objects. Implement log access controls.

---

## Nonce Parameter Not Validated

**Finding**: ID tokens accepted without validating the `nonce` claim.

**Risk**: Attackers can replay captured ID tokens in different sessions, potentially gaining unauthorized access.

**Example**:
```javascript
// VULNERABLE: Nonce not validated
const claims = jwt.verify(idToken, key);
createSess(claims.sub);

// SECURE: Nonce validated
if (claims.nonce !== session.nonce) {
  throw new Error('Nonce mismatch');
}
createSess(claims.sub);
```

**Detection**: Capture an ID token from one authentication session. Attempt to use it in a different session. If accepted, nonce validation is missing.

**Remediation**: Generate a random nonce for each authorization request. Store it in the session. Validate the nonce claim in the ID token matches the stored value.

---

## State Parameter Not Validated

**Finding**: Authorization callback processed without validating the `state` parameter.

**Risk**: Attackers can perform CSRF attacks, tricking users into authenticating with attacker-controlled accounts, leading to account takeover.

**Example**:
```javascript
// VULNERABLE: State not validated
app.get('/auth/callback', (req, res) => {
  const { code } = req.query;
  exchangeCodeForToken(code);
});

// SECURE: State validated
app.get('/auth/callback', (req, res) => {
  if (req.query.state !== req.session.state) {
    throw new Error('State mismatch');
  }
  exchangeCodeForToken(req.query.code);
});
```

**Detection**: Initiate a login flow and capture the state parameter. Craft a malicious authorization request with a different state. Trick a user into clicking the link. If the application logs them in, state validation is missing.

**Remediation**: Generate a cryptographically random state parameter for each authorization request. Store it in the session. Validate it matches the state parameter in the callback.

---

## Redirect URI Open Redirect

**Finding**: Application accepts redirect URIs not registered with the IdP or constructs them dynamically.

**Risk**: Attackers can redirect users to malicious sites after authentication, potentially capturing authorization codes or performing phishing attacks.

**Example**:
```javascript
// VULNERABLE: Dynamic redirect URI
const redirectUri = req.query.redirect_uri;
res.redirect(redirectUri);

// VULNERABLE: Overly broad registration
// IdP allows: https://*.example.com/callback

// SECURE: Whitelist validation
const allowedUris = [
  'https://app.example.com/auth/callback',
  'https://app.example.com/auth/callback2'
];
if (!allowedUris.includes(redirectUri)) {
  throw new Error('Invalid redirect URI');
}
```

**Detection**: Attempt to register a redirect URI not in the whitelist. Attempt to use a redirect URI with a different domain, subdomain, or path. If accepted, validation is missing.

**Remediation**: Register redirect URIs with the IdP using exact matching. Validate redirect URIs against a whitelist before redirecting. Never construct redirect URIs dynamically based on user input.

---

## PKCE Not Implemented

**Finding**: Authorization Code Flow used without PKCE in mobile apps or SPAs.

**Risk**: Authorization codes can be intercepted and exchanged for tokens by attackers, especially in mobile apps where the code is transmitted through the system browser.

**Example**:
```javascript
// VULNERABLE: No PKCE
const authUrl = `${idpAuthEndpoint}?client_id=${clientId}&code=...`;

// SECURE: PKCE implemented
const codeChallenge = base64url(sha256(codeVerifier));
const authUrl = `${idpAuthEndpoint}?client_id=${clientId}&code_challenge=${codeChallenge}&code_challenge_method=S256`;
```

**Detection**: Intercept an authorization request. Capture the authorization code. Attempt to exchange it for tokens without the code verifier. If successful, PKCE is not implemented.

**Remediation**: Implement PKCE for all Authorization Code Flow implementations. Use S256 (SHA256) as the code challenge method. Generate a cryptographically random code verifier of at least 128 characters.

---

## Client Secret Exposed in Mobile Apps

**Finding**: Client secret hardcoded in mobile application code.

**Risk**: Client secrets can be extracted from mobile app binaries through reverse engineering. Attackers can use the secret to exchange authorization codes for tokens.

**Example**:
```javascript
// VULNERABLE: Secret in code
const clientSecret = 'super_secret_key_12345';

// VULNERABLE: Secret in config file
const config = require('./config.json'); // Contains secret
```

**Detection**: Decompile or reverse engineer the mobile app. Search for strings matching the client ID or secret format. Check configuration files and resources.

**Remediation**: Never include client secrets in mobile apps. Use PKCE instead of client secrets for mobile apps. If a secret is exposed, rotate it immediately and revoke all tokens issued with it.

---

## UserInfo Endpoint Called from Frontend

**Finding**: UserInfo endpoint called directly from browser JavaScript or mobile app frontend.

**Risk**: Access tokens are exposed to the frontend, increasing the attack surface. Tokens can be stolen through XSS attacks or network interception.

**Example**:
```javascript
// VULNERABLE: UserInfo called from frontend
fetch('https://idp.example.com/userinfo', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
}).then(r => r.json()).then(user => {
  localStorage.setItem('user', JSON.stringify(user));
});

// SECURE: UserInfo called from backend
fetch('/api/user', {
  credentials: 'include'
}).then(r => r.json()).then(user => {
  // User data from backend
});
```

**Detection**: Monitor network traffic from the frontend. Look for requests to the IdP's UserInfo endpoint. Check if access tokens are stored in localStorage or sessionStorage.

**Remediation**: Call the UserInfo endpoint only from the application backend. Store access tokens securely on the backend (in memory or secure storage). Return user information to the frontend through the application's own API.

---

## Tokens Stored in localStorage

**Finding**: ID tokens or access tokens stored in browser localStorage.

**Risk**: localStorage is vulnerable to XSS attacks. Any malicious JavaScript can access tokens and use them to impersonate the user.

**Example**:
```javascript
// VULNERABLE: Tokens in localStorage
localStorage.setItem('idToken', idToken);
localStorage.setItem('accessToken', accessToken);

// SECURE: Tokens in httpOnly cookies
// Set by backend with httpOnly, Secure, SameSite flags
// Not accessible to JavaScript
```
