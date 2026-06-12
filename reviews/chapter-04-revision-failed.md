# Chapter 04: OpenID Connect and User Information

## Learning Objectives

After completing this chapter, you will be able to:

- Explain the core components of OpenID Connect (OIDC) and how it extends OAuth 2.0 for authentication
- Identify the three primary OIDC flows and determine which is appropriate for different application architectures
- Recognize security risks associated with user information handling in OIDC implementations
- Implement secure UserInfo endpoint access patterns and token validation procedures
- Design and review OIDC integrations to prevent common vulnerabilities including token leakage, claim injection, and user enumeration
- Conduct security assessments of OIDC implementations using practical testing methodologies
- Evaluate third-party identity provider integrations for compliance with security best practices

## Conceptual Foundation

OpenID Connect (OIDC) is an authentication layer built on top of OAuth 2.0 that enables applications to verify the identity of end users and obtain basic profile information about them. While OAuth 2.0 focuses on authorization and delegated access to resources, OIDC adds an identity verification mechanism through the introduction of ID tokens and standardized user information endpoints.

The fundamental distinction between OAuth 2.0 and OIDC is critical for security practitioners. OAuth 2.0 access tokens are opaque to the application—they represent authorization to access resources but do not inherently contain identity information. OIDC introduces the ID token, a JSON Web Token (JWT) that contains claims about the authentication of an end user by an authorization server. This ID token is cryptographically signed and can be validated by the relying party (the application requesting authentication).

OIDC operates through the concept of an OpenID Provider (OP), which is the authorization server that performs authentication and issues ID tokens. The Relying Party (RP) is the application that relies on the OP to authenticate users. The Resource Owner is the end user whose identity is being verified.

The core user information in OIDC flows through multiple channels. The ID token contains claims about the user—such as subject identifier (sub), name, email, and email verification status. Additionally, OIDC defines a UserInfo endpoint that the RP can call to retrieve additional user attributes beyond what is included in the ID token. This separation of concerns creates both flexibility and security considerations that must be carefully managed.

OIDC defines several standard scopes that control what information is returned:
- **openid**: Required scope that indicates OIDC authentication is requested
- **profile**: Returns name, family_name, given_name, middle_name, nickname, preferred_username, profile, picture, website, gender, birthdate, zoneinfo, locale, updated_at
- **email**: Returns email and email_verified
- **address**: Returns address claim with street_address, locality, region, postal_code, country
- **phone**: Returns phone_number and phone_number_verified

Understanding these scopes is essential because they define the attack surface for user information disclosure and the legitimate data flows within your application.

## Architecture Perspective

OIDC implementations follow three primary flows, each suited to different application architectures and security contexts.

### Authorization Code Flow

The Authorization Code Flow is the most secure and recommended flow for traditional web applications and native mobile applications with secure backend servers. In this flow:

1. The user initiates login on the RP application
2. The RP redirects the user to the OP's authorization endpoint with parameters including client_id, redirect_uri, scope, and state
3. The user authenticates with the OP and grants consent
4. The OP redirects the user back to the RP's redirect_uri with an authorization code
5. The RP's backend server exchanges the authorization code for tokens by making a direct backend-to-backend call to the OP's token endpoint, including the client_secret
6. The OP returns an ID token and access token
7. The RP validates the ID token and establishes a session with the user

The critical security advantage of this flow is that the access token and ID token never pass through the user's browser—they are exchanged directly between backend servers. The authorization code is short-lived and single-use, limiting its value if intercepted.

### Implicit Flow

The Implicit Flow was designed for browser-based single-page applications (SPAs) without a backend server. In this flow:

1. The user initiates login on the SPA
2. The SPA redirects the user to the OP's authorization endpoint
3. The user authenticates and grants consent
4. The OP redirects the user back with tokens in the URL fragment

The Implicit Flow has significant security limitations. Tokens are exposed in the browser history, referrer headers, and server logs. This flow is now considered legacy and should not be used for new implementations. The OAuth 2.0 Security Best Current Practice explicitly recommends against the Implicit Flow.

### Authorization Code Flow with PKCE

The Authorization Code Flow with Proof Key for Code Exchange (PKCE) is the modern approach for SPAs and native mobile applications. PKCE adds an additional layer of security by requiring the client to generate a code_challenge and code_verifier:

1. The SPA generates a random code_verifier and derives a code_challenge from it
2. The SPA redirects to the authorization endpoint with the code_challenge
3. After receiving the authorization code, the SPA exchanges it for tokens by including the code_verifier
4. The OP verifies that the code_verifier matches the code_challenge, ensuring the same client that initiated the request is exchanging the code

PKCE protects against authorization code interception attacks, particularly in mobile applications where the authorization code could be intercepted by malicious applications on the same device.

### Hybrid Flow

The Hybrid Flow combines elements of Authorization Code and Implicit flows, returning some tokens directly and others through the backend. This flow is less commonly used in modern implementations and introduces complexity that often leads to security misconfigurations.

### Architecture Considerations for User Information

The architectural decision of where to store and access user information significantly impacts security. Several patterns exist:

**Pattern 1: Information in ID Token Only**
The RP relies entirely on claims within the ID token for user information. This minimizes backend calls but limits the freshness of user data. If user attributes change on the OP, the RP will not reflect those changes until the user re-authenticates.

**Pattern 2: ID Token Plus UserInfo Endpoint**
The RP uses claims from the ID token for immediate needs and calls the UserInfo endpoint to retrieve additional or updated information. This requires the RP to maintain the access token and make authenticated requests to the UserInfo endpoint.

**Pattern 3: UserInfo Endpoint Only**
The RP uses the ID token only for validation and retrieves all user information from the UserInfo endpoint. This ensures information freshness but increases latency and backend dependencies.

The choice depends on your application's requirements for data freshness, performance, and the sensitivity of the information being accessed.

## AppSec Lens

From an application security perspective, OIDC implementations introduce several categories of risk that require careful attention.

### Token Validation Failures

One of the most critical security requirements in OIDC is proper validation of the ID token. The ID token is a JWT that must be validated before being trusted. Validation includes:

1. **Signature Verification**: The token must be signed by the OP using a key that the RP can obtain from the OP's JWKS (JSON Web Key Set) endpoint. The RP must verify that the signature is valid using the correct public key.

2. **Issuer Validation**: The "iss" claim in the token must match the expected issuer URL. This prevents an attacker from substituting tokens from a different OP.

3. **Audience Validation**: The "aud" claim must contain the RP's client_id. This ensures the token was issued for your application, not another application.

4. **Expiration Validation**: The "exp" claim must indicate the token has not expired. Accepting expired tokens allows attackers to replay old tokens.

5. **Not Before Validation**: The "nbf" claim, if present, must indicate the token is not being used before its valid time.

A common failure is implementing partial validation. For example, an application might verify the signature but fail to validate the issuer or audience. This creates a vulnerability where tokens from other OPs or intended for other applications could be accepted.

### UserInfo Endpoint Security

The UserInfo endpoint is an OAuth 2.0 protected resource that requires a valid access token. Security considerations include:

1. **Access Token Validation**: The UserInfo endpoint must validate that the access token is valid, not expired, and has the appropriate scope (typically "openid" or "profile").

2. **Token Binding**: Some implementations use token binding or sender-constrained tokens to ensure the access token can only be used by the client that obtained it. This prevents token theft from being immediately exploitable.

3. **HTTPS Enforcement**: All communication with the UserInfo endpoint must use HTTPS. Unencrypted communication allows token interception.

4. **Rate Limiting**: The UserInfo endpoint should implement rate limiting to prevent enumeration attacks where an attacker attempts to retrieve information about many users.

### User Enumeration Risks

OIDC implementations can inadvertently enable user enumeration attacks. Consider these scenarios:

- An authorization endpoint that returns different error messages for "user not found" versus "invalid password" allows attackers to enumerate valid usernames
- A UserInfo endpoint that returns 404 for non-existent users but 200 for existing users enables enumeration
- Redirect URI validation that differs based on whether a user exists creates an enumeration vector

Secure implementations return consistent responses regardless of whether a user exists in the system.

### Redirect URI Validation

The redirect_uri parameter is critical to OIDC security. After authentication, the OP redirects the user back to the RP's application. If the RP does not properly validate the redirect_uri, an attacker can redirect authenticated users to a malicious site.

Redirect URI validation must be exact matching, not prefix matching. For example, if the registered redirect URI is `https://app.example.com/callback`, the OP should not accept `https://app.example.com/callback.evil.com` or `https://app.example.com/callback?attacker=true`.

### State Parameter and CSRF Protection

The state parameter is a critical CSRF protection mechanism in OIDC. The RP generates a random state value, includes it in the authorization request, and validates that the same state value is returned in the authorization response. This ensures the response corresponds to the request the RP initiated.

Failures in state parameter handling include:
- Not generating a cryptographically random state value
- Not validating the state parameter in the response
- Reusing state values across multiple requests
- Storing state values without expiration, allowing old states to be replayed

### Nonce Parameter for Replay Protection

The nonce parameter provides additional protection against token replay attacks. The RP includes a nonce in the authorization request, and the OP includes the same nonce in the ID token. The RP validates that the nonce in the token matches the nonce it sent.

The nonce is particularly important in flows where the ID token is returned directly to the browser (Implicit and Hybrid flows) because it prevents an attacker from replaying a token obtained from another user's session.

### Client Secret Management

In flows that use a client_secret (Authorization Code Flow), the secret must be protected as a credential. Common failures include:

- Storing the client_secret in client-side code (JavaScript, mobile apps)
- Committing the client_secret to version control
- Using the same client_secret across multiple environments
- Not rotating the client_secret regularly
- Transmitting the client_secret over unencrypted connections

### Token Leakage Vectors

ID tokens and access tokens can leak through multiple channels:

1. **Browser History**: Tokens in URL fragments or query parameters are stored in browser history
2. **Server Logs**: Tokens in query parameters or request bodies are logged by web servers
3. **Referrer Headers**: Tokens in URLs cause referrer headers to include tokens when navigating to external sites
4. **Proxy Logs**: Intermediate proxies may log tokens
5. **Error Messages**: Verbose error messages may include token information
6. **Local Storage**: Tokens stored in browser local storage are vulnerable to XSS attacks

Secure implementations use HTTPS, avoid including tokens in URLs, implement Content Security Policy to prevent XSS, and carefully manage token storage.

## Developer Lens

From a developer implementation perspective, OIDC requires careful attention to several areas.

### Choosing the Right Flow

The first decision is selecting the appropriate OIDC flow for your application architecture:

- **Traditional Web Application with Backend**: Use Authorization Code Flow
- **Single-Page Application (SPA)**: Use Authorization Code Flow with PKCE
- **Native Mobile Application**: Use Authorization Code Flow with PKCE
- **Legacy Browser-Only Application**: Use Authorization Code Flow with PKCE (do not use Implicit Flow)

### Implementation Example: Authorization Code Flow with PKCE

Here is a practical example of implementing OIDC Authorization Code Flow with PKCE in a Node.js/Express web application:

```javascript
const express = require('express');
const crypto = require('crypto');
const axios = require('axios');
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

const app = express();
const session = require('express-session');

// Configuration
const OIDC_CONFIG = {
  clientId: process.env.OIDC_CLIENT_ID,
  clientSecret: process.env.OIDC_CLIENT_SECRET,
  redirectUri: 'https://app.example.com/callback',
  authorizationEndpoint: 'https://idp.example.com/authorize',
  tokenEndpoint: 'https://idp.example.com/token',
  userInfoEndpoint: 'https://idp.example.com/userinfo',
  jwksUri: 'https://idp.example.com/.well-known/jwks.json',
  issuer: 'https://idp.example.com'
};

// Initialize JWKS client for signature verification
const jwksClientInstance = jwksClient({
  jwksUri: OIDC_CONFIG.jwksUri,
  cache: true,
  cacheMaxAge: 600000 // 10 minutes
});

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: true,
  cookie: {
    secure: true,
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 3600000 // 1 hour
  }
}));

// Helper function to generate PKCE code challenge
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

// Helper function to generate state parameter
function generateState() {
  return crypto.randomBytes(32).toString('hex');
}

// Login endpoint
app.get('/login', (req, res) => {
  const { codeVerifier, codeChallenge } = generatePKCE();
  const state = generateState();
  
  // Store in session for later validation
  req.session.codeVerifier = codeVerifier;
  req.session.state = state;
  req.session.save();
  
  const authUrl = new URL(OIDC_CONFIG.authorizationEndpoint);
  authUrl.searchParams.append('client_id', OIDC_CONFIG.clientId);
  authUrl.searchParams.append('redirect_uri', OIDC_CONFIG.redirectUri);
  authUrl.searchParams.append('response_type', 'code');
  authUrl.searchParams.append('scope', 'openid profile email');
  authUrl.searchParams.append('state', state);
  authUrl.searchParams.append('code_challenge', codeChallenge);
  authUrl.searchParams.append('code_challenge_method', 'S256');
  
  res.redirect(authUrl.toString());
});

// Callback endpoint
app.get('/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    
    // Validate state parameter
    if (!state || state !== req.session.state) {
      return res.status(400).send('Invalid state parameter');
    }
    
    if (!code) {
      return res.status(400).send('No authorization code received');
    }
    
    // Exchange authorization code for tokens
    const tokenResponse = await axios.post(
      OIDC_CONFIG.tokenEndpoint,
      {
        grant_type: 'authorization_code',
        code: code,
        client_id: OIDC_CONFIG.clientId,
        client_secret: OIDC_CONFIG.clientSecret,
        redirect_uri: OIDC_CONFIG.redirectUri,
        code_verifier: req.session.codeVerifier
      },
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      }
    );
    
    const { id_token, access_token } = tokenResponse.data;
    
    // Validate ID token
    const decodedToken = jwt.decode(id_token, { complete: true });
    
    if (!decodedToken) {
      return res.status(400).send('Invalid ID token format');
    }
    
    // Get the signing key
    const key = await jwksClientInstance.getSigningKey(decodedToken.header.kid);
    const signingKey = key.getPublicKey();
    
    // Verify token signature and claims
    const verified = jwt.verify(id_token, signingKey, {
      algorithms: ['RS256'],
      issuer: OIDC_CONFIG.issuer,
      audience: OIDC_CONFIG.clientId,
      clockTolerance: 10 // 10 seconds tolerance for clock skew
    });
    
    // Retrieve user information from UserInfo endpoint
    const userInfoResponse = await axios.get(
      OIDC_CONFIG.userInfoEndpoint,
      {
        headers: {
          'Authorization': `Bearer ${access_token}`
        }
      }
    );
    
    const userInfo = userInfoResponse.data;
    
    // Verify that the sub claim matches
    if (verified.sub !== userInfo.sub) {
      return res.status(400).send('Subject mismatch between ID token and UserInfo');
    }
    
    // Store user information in session
    req.session.user = {
      sub: verified.sub,
      email: userInfo.email,
      name: userInfo.name,
      emailVerified: userInfo.email_verified
    };
    
    // Clear sensitive data from session
    delete req.session.codeVerifier;
    delete req.session.state;
    
    req.session.save();
    
    res.redirect('/dashboard');
  } catch (error) {
    console.error('Authentication error:', error.message);
    res.status(500).send('Authentication failed');
  }
});

// Protected route
app.get('/dashboard', (req, res) => {
  if (!req.session.user) {
    return res.redirect('/login');
  }
  
  res.send(`Welcome, ${req.session.user.name}`);
});

// Logout endpoint
app.get('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).send('Logout failed');
    }
    res.redirect('/');
  });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

This implementation demonstrates several security best practices:

1. **PKCE Implementation**: Generates a code_verifier and code_challenge, stores the verifier in the session, and includes it in the token exchange
2. **State Parameter**: Generates a random state, stores it in the session, and validates it in the callback
3. **Token Validation**: Verifies the signature using the JWKS endpoint, validates the issuer and audience claims, and checks expiration
4. **UserInfo Endpoint**: Calls the UserInfo endpoint with the access token and validates that the subject matches
5. **Session Security**: Uses secure, httpOnly, sameSite cookies for session management
6. **Error Handling**: Returns generic error messages to prevent information disclosure

### Common Implementation Mistakes

**Mistake 1: Skipping Token Validation**
Some developers trust the ID token without validating the signature. This is dangerous because an attacker could forge a token or substitute a token from a different OP. Always verify the signature using the OP's public key from the JWKS endpoint, and validate the issuer and audience claims.

**Mistake 2: Not Validating Issuer and Audience**
Even if the signature is valid, the token might be from a different OP or intended for a different application. Always validate that the `iss` claim matches your expected issuer URL and the `aud` claim contains your application's client_id. This prevents token substitution attacks.

**Mistake 3: Storing Tokens in Local Storage**
Storing access tokens or ID tokens in browser local storage makes them vulnerable to XSS attacks. Any JavaScript on the page can access local storage, so a single XSS vulnerability exposes all tokens. Use secure, httpOnly cookies instead, which are inaccessible to JavaScript and provide better protection against token theft.

**Mistake 4: Including Tokens in URLs**
Tokens included in query parameters or URL fragments are logged by web servers, proxies, and browser history. Never pass tokens as URL parameters. Instead, use POST requests with tokens in the Authorization header or in secure cookies. This prevents accidental token exposure through logs and referrer headers.

**Mistake 5: Not Implementing PKCE for SPAs and Mobile Apps**
Applications without a secure backend should use PKCE to protect authorization codes from interception. Without PKCE, an attacker who intercepts the authorization code can exchange it for tokens. PKCE requires the client to prove it initiated the authorization request by including a code_verifier that matches the code_challenge sent earlier.

### Library Selection Best Practices

When selecting OIDC libraries, prioritize:

- **Active Maintenance**: Choose libraries with recent updates and active security patching
- **Comprehensive Validation**: Ensure the library enforces all required token validation checks (signature, issuer, audience, expiration)
- **PKCE Support**: Verify the library supports PKCE for modern application architectures
- **Security Defaults**: Look for libraries that default to secure configurations (e.g., HTTPS enforcement, secure cookie flags)
- **Community Trust**: Use libraries with established track records and community adoption
- **Clear Documentation**: Select libraries with clear security guidance and examples

Popular, well-maintained libraries include `passport-openidconnect`, `oidc-client-ts`, and `next-auth.js` for JavaScript/Node.js environments.

### Testing Strategies for Developers

Developers should implement automated tests to verify OIDC security:

- **Token Validation Tests**: Mock JWKS endpoints and test that## Reconnaissance and Discovery

When assessing an OIDC implementation, begin by identifying the OpenID Provider and gathering configuration information:

1. **Discover OIDC Endpoints**: Access the `.well-known/openid-configuration` endpoint to retrieve the authorization endpoint, token endpoint, UserInfo endpoint, and JWKS URI. Compare discovered endpoints against documented configuration to identify discrepancies.

2. **Enumerate Registered Redirect URIs**: Test various redirect URI patterns to identify which ones are accepted. Document the validation logic—whether it uses exact matching, prefix matching, or regex patterns.

3. **Identify Supported Flows**: The discovery endpoint reveals which response types are supported (code, token, id_token, etc.). This indicates which flows the OP allows.

4. **Examine JWKS Endpoint**: Retrieve the public keys used for token signing. Verify that key rotation is implemented and that old keys are eventually removed.

5. **Test Client Registration**: If dynamic client registration is enabled, attempt to register a client and observe what parameters are required and validated.

## Authorization Endpoint Testing

**State Parameter Validation**
- Submit authorization requests without a state parameter and verify the OP requires it
- Submit requests with an empty state value
- Submit requests with a state value that differs from the callback response
- Attempt to reuse state values across multiple sessions
- Test whether state values expire or can be replayed after extended periods

**Redirect URI Validation**
- Test exact redirect URI matching by attempting variations:
  - `https://app.example.com/callback` vs `https://app.example.com/callback/`
  - `https://app.example.com/callback` vs `https://app.example.com/callback?param=value`
  - `https://app.example.com/callback` vs `https://app.example.com/callback#fragment`
  - `https://app.example.com/callback` vs `https://app.example.com/callback.attacker.com`
  - `https://app.example.com/callback` vs `https://app.example.com/callback@attacker.com`
- Test open redirect vulnerabilities by attempting to register wildcard or overly broad redirect URIs
- Test subdomain takeover scenarios if subdomains are registered as redirect URIs

**Nonce Parameter Testing**
- Submit authorization requests without a nonce and verify it's not required (or is required if the OP enforces it)
- Submit requests with a nonce and verify it appears in the ID token
- Attempt to use the same nonce across multiple requests
- Test whether nonce validation is enforced by the RP

**Response Type Testing**
- Test unsupported response types to identify error handling
- Test response type combinations (e.g., `code id_token`, `code token`) to identify which flows are supported
- Verify that response types return appropriate token types

**Scope Testing**
- Request scopes that should not be available to your client
- Request scopes that reveal sensitive information (e.g., admin scopes)
- Test scope downgrade attacks where requested scopes differ from granted scopes
- Verify that the OP enforces scope restrictions

**User Enumeration via Authorization Endpoint**
- Attempt authentication with valid and invalid usernames
- Observe whether error messages, response times, or HTTP status codes differ
- Test whether the authorization endpoint reveals whether a user exists before authentication
- Attempt to enumerate users through redirect URI validation differences

## Token Endpoint Testing

**Authorization Code Validation**
- Attempt to reuse authorization codes
- Attempt to use authorization codes from different clients
- Attempt to use expired authorization codes
- Attempt to exchange authorization codes without the client_secret
- Test whether authorization codes are single-use and short-lived

**PKCE Validation**
- Submit token requests without code_verifier when code_challenge was provided
- Submit token requests with incorrect code_verifier values
- Test whether code_challenge_method is properly validated (S256 vs plain)
- Attempt to use PKCE with clients that don't support it

**Client Authentication**
- Test client authentication methods (client_secret_basic, client_secret_post, none)
- Attempt to authenticate without credentials
- Attempt to use incorrect client credentials
- Test whether the OP enforces client authentication for confidential clients

**Token Response Validation**
- Examine the token response for sensitive information in logs or error messages
- Test whether tokens are returned over HTTPS
- Verify that tokens are not cached by intermediate proxies
- Test whether token response includes appropriate cache-control headers

## ID Token Validation Testing

**Signature Verification**
- Modify the ID token payload and verify the RP rejects it
- Modify the ID token signature and verify the RP rejects it
- Attempt to use tokens signed with different algorithms (e.g., HS256 instead of RS256)
- Test algorithm confusion attacks by attempting to use symmetric key algorithms with public keys

**Claim Validation**
- Verify that the RP validates the `iss` (issuer) claim
- Verify that the RP validates the `aud` (audience) claim
- Verify that the RP validates the `exp` (expiration) claim
- Verify that the RP validates the `iat` (issued at) claim
- Test whether the RP accepts tokens with missing required claims
- Test whether the RP accepts tokens with unexpected additional claims

**Token Expiration**
- Attempt to use expired ID tokens
- Test clock skew tolerance by using tokens with future `iat` values
- Verify that the RP properly handles tokens with very long expiration times

**Nonce Validation**
- Verify that the RP validates the nonce claim when nonce was included in the authorization request
- Attempt to use tokens with missing nonce claims when nonce was requested
- Attempt to use tokens with incorrect nonce values

## UserInfo Endpoint Testing

**Access Token Validation**
- Call the UserInfo endpoint without an access token
- Call the UserInfo endpoint with an invalid or expired access token
- Call the UserInfo endpoint with an access token from a different client
- Call the UserInfo endpoint with an access token from a different OP
- Verify that the endpoint validates token scope (typically requires "openid" or "profile")

**User Enumeration**
- Attempt to retrieve information for non-existent users
- Observe whether the endpoint returns 404, 401, or other status codes for invalid tokens
- Test whether response times differ for valid vs. invalid tokens
- Attempt to enumerate users through timing attacks

**Information Disclosure**
- Verify what user attributes are returned by the UserInfo endpoint
- Test whether the endpoint returns more information than expected
- Verify that sensitive information (passwords, internal IDs) is not exposed
- Test whether the endpoint respects scope restrictions

**Rate Limiting**
- Attempt to make rapid requests to the UserInfo endpoint
- Verify that rate limiting is implemented
- Test whether rate limiting is per-token, per-IP, or per-user

## Token Storage and Leakage Testing

**Browser Storage Analysis**
- Examine browser local storage, session storage, and cookies for tokens
- Verify that tokens are not stored in local storage (vulnerable to XSS)
- Verify that tokens in cookies use secure, httpOnly, and sameSite flags
- Test whether tokens appear in browser history

**Network Traffic Analysis**
- Capture HTTP traffic and verify all OIDC communication uses HTTPS
- Verify that tokens do not appear in query parameters (which are logged)
- Verify that tokens do not appear in referrer headers
- Test whether tokens are included in error messages or logs

**XSS and Token Theft**
- Identify XSS vulnerabilities in the RP application
- Verify that XSS cannot be used to steal tokens from secure storage
- Test whether Content Security Policy prevents token exfiltration
- Verify that tokens are not accessible to injected scripts

## Session and State Management Testing

**Session Fixation**
- Attempt to set a session cookie before authentication
- Verify that a new session is created after authentication
- Test whether the old session is invalidated after authentication

**Session Hijacking**
- Verify that session cookies use secure, httpOnly, and sameSite flags
- Test whether session tokens are cryptographically random
- Verify that session tokens are not predictable

**Logout and Token Revocation**
- Verify that logout invalidates the session
- Test whether tokens can be used after logout
- Verify that the RP calls the OP's logout endpoint if available
- Test whether refresh tokens are revoked on logout

## Third-Party Identity Provider Testing

**Provider Configuration Validation**
- Verify that the OP's certificate is valid and not expired
- Verify that the OP's certificate is issued by a trusted CA
- Test whether certificate pinning is implemented for critical connections
- Verify that the OP's endpoints use HTTPS with strong TLS configuration

**Provider Compromise Scenarios**
- Test how the RP responds if the OP's JWKS endpoint is compromised
- Test whether the RP validates JWKS responses
- Verify that the RP does not accept arbitrary keys from the JWKS endpoint

## Practical Testing Workflow

1. **Baseline Configuration**: Document the OIDC configuration, flows supported, and endpoints used
2. **Authorization Flow**: Test the authorization endpoint for state, nonce, redirect URI, and scope validation
3. **Token Exchange**: Test the token endpoint for authorization code and PKCE validation
4. **Token Validation**: Analyze ID tokens for proper signature, issuer, audience, and expiration validation
5. **UserInfo Access**: Test the UserInfo endpoint for access control and information disclosure
6. **Session Management**: Verify session creation, validation, and invalidation
7. **Integration Points**: Test how the RP handles errors, timeouts, and provider unavailability
8. **Data Flow**: Trace user information from authorization through UserInfo endpoint to application storage

---

# Common Findings

## Finding 1: Missing or Incomplete ID Token Validation

**Severity**: Critical

**Description**: The application accepts ID tokens without validating the signature, issuer, audience, or expiration claims. This allows attackers to forge tokens or use tokens from other OPs.

**Example Scenario**: A Node.js application decodes the ID token using `jwt.decode()` without verification, trusting the claims without cryptographic validation.

```javascript
// VULNERABLE CODE
const token = req.query.id_token;
const decoded = jwt.decode(token); // No verification!
req.session.user = decoded;
```

**Impact**: An attacker can create arbitrary ID tokens, impersonate any user, and gain unauthorized access to the application.

**Remediation**:
- Always verify the ID token signature using the OP's public key from the JWKS endpoint
- Validate the `iss` claim matches the expected issuer
- Validate the `aud` claim contains the application's client_id
- Validate the `exp` claim to ensure the token is not expired
- Use a well-maintained JWT library that enforces validation

```javascript
// SECURE CODE
const key = await jwksClient.getSigningKey(decodedToken.header.kid);
const verified = jwt.verify(id_token, key.getPublicKey(), {
  algorithms: ['RS256'],
  issuer: EXPECTED_ISSUER,
  audience: CLIENT_ID
});
```

## Finding 2: Redirect URI Validation Bypass

**Severity**: Critical

**Description**: The OP or RP does not properly validate redirect URIs, allowing attackers to redirect authenticated users to malicious sites.

**Example Scenario**: An OP accepts redirect URIs with prefix matching instead of exact matching. A registered URI of `https://app.example.com/callback` also accepts `https://app.example.com/callback.attacker.com`.

**Impact**: Attackers can redirect users to phishing sites after authentication, capturing credentials or performing further attacks.

**Remediation**:
- Implement exact string matching for redirect URI validation
- Reject redirect URIs with query parameters or fragments that differ from registered values
- Use allowlists of explicitly registered redirect URIs
- Validate redirect URIs on both the OP and RP sides
- For OPs: Provide clear error messages when redirect URIs don't match

## Finding 3: State Parameter Not Validated

**Severity**: High

**Description**: The application does not validate the state parameter returned from the OP, or generates predictable state values.

**Example Scenario**: An application generates state as `state=1`, `state=2`, etc., or does not check that the returned state matches the sent state.

**Impact**: CSRF attacks where an attacker tricks a user into clicking a link that initiates authentication with the attacker's account, potentially linking the user's account to the attacker's identity.

**Remediation**:
- Generate cryptographically random state values using a secure random number generator
- Store the state value in the session before redirecting to the OP
- Validate that the returned state matches the stored state
- Invalidate state values after use
- Implement state value expiration (typically 5-10 minutes)

```javascript
// SECURE CODE
const state = crypto.randomBytes(32).toString('hex');
req.session.state = state;
// ... later in callback
if (req.query.state !== req.session.state) {
  throw new Error('State mismatch');
}
delete req.session.state;
```

## Finding 4: PKCE Not Implemented for SPAs and Mobile Apps

**Severity**: High

**Description**: Single-page applications or mobile applications use the Authorization Code Flow without PKCE, making authorization codes vulnerable to interception.

**Example Scenario**: A React SPA exchanges an authorization code for tokens without including a code_verifier, allowing an attacker who intercepts the code to exchange it for tokens.

**Impact**: Authorization code interception attacks where an attacker on the same network or controlling a malicious app can steal authorization codes and exchange them for tokens.

**Remediation**:
- Implement PKCE for all SPAs and mobile applications
- Generate a cryptographically random code_verifier (43-128 characters)
- Derive the code_challenge using SHA256 of the code_verifier
- Include code_challenge in the authorization request
- Include code_verifier in the token request
- Use code_challenge_method=S256 (SHA256) instead of plain

## Finding 5: Implicit Flow Still in Use

**Severity**: High

**Description**: The application uses the Implicit Flow for authentication, which returns tokens directly in the URL fragment.

**Example Scenario**: An older SPA uses `response_type=token id_token` and receives tokens in the URL fragment.

**Impact**: Tokens are exposed in browser history, referrer headers, and server logs. XSS vulnerabilities can steal tokens from the URL.

**Remediation**:
- Migrate to Authorization Code Flow with PKCE
- Disable the Implicit Flow on the OP
- Update all applications to use Authorization Code Flow with PKCE
- If legacy applications must use Implicit Flow, implement additional protections like token binding

## Finding 6: Client Secret Exposed in Client-Side Code

**Severity**: Critical

**Description**: The application includes the client_secret in JavaScript, mobile app code, or configuration files that are accessible to users.

**Example Scenario**: A React application includes `const CLIENT_SECRET = "secret123"` in the source code, or a mobile app hardcodes the secret.

**Impact**: Attackers can use the exposed client_secret to impersonate the application, exchange authorization codes for tokens, or call protected endpoints.

**Remediation**:
- Never include client_secret in client-side code
- For SPAs and mobile apps, use the Authorization Code Flow with PKCE and omit the client_secret (use public clients)
- If a backend is required, keep the client_secret on the backend only
- Use environment variables or secure configuration management for secrets
- Rotate client_secrets regularly
- Monitor for exposed secrets in version control

## Finding 7: UserInfo Endpoint Called Without Access Token

**Severity**: High

**Description**: The application calls the UserInfo endpoint without including the access token, or the OP accepts requests without valid tokens.

**Example Scenario**: An application makes a request to the UserInfo endpoint without an Authorization header, and the OP returns user information.

**Impact**: Attackers can retrieve user information without authentication, enabling user enumeration and information disclosure.

**Remediation**:
- Always include a valid access token in the Authorization header when calling UserInfo
- Verify that the access token has the appropriate scope (openid, profile, email, etc.)
- On the OP side, reject UserInfo requests without valid access tokens
- Implement rate limiting on the UserInfo endpoint to prevent enumeration

## Finding 8: Nonce Parameter Not Validated

**Severity**: Medium

**Description**: The application does not validate the nonce parameter in the ID token, or does not include nonce in the authorization request.

**Example Scenario**: An application requests authentication with a nonce but does not verify that the returned ID token contains the same nonce.

**Impact**: Token replay attacks where an attacker captures an ID token and replays it in a different session or application.

**Remediation**:
- Include a nonce in the authorization request
- Store the nonce in the session
- Verify that the ID token contains the same nonce
- Invalidate nonce values after use
- Implement nonce expiration

## Finding 9: Tokens Stored in Local Storage

**Severity**: High

**Description**: The application stores ID tokens or access tokens in browser local storage, making them vulnerable to XSS attacks.

**Example Scenario**: A React application stores the access token in `localStorage.setItem('access_token', token)`.

**Impact**: XSS vulnerabilities allow attackers to steal tokens from local storage and use them to access protected resources.

**Remediation**:
- Store tokens in secure, httpOnly cookies instead of local storage
- If tokens must be stored in memory, clear them when the page is closed
- Implement Content Security Policy to prevent XSS
- Use token binding or sender-constrained tokens to limit token usability
- Consider using refresh token rotation to limit token lifetime

## Finding 10: Insufficient Scope Validation

**Severity**: Medium

**Description**: The application requests or accepts scopes that grant access to more information than necessary, or does not validate that granted scopes match requested scopes.

**Example Scenario**: An application requests the "profile" scope but only needs the user's email, or accepts tokens with admin scopes when the user should only have user scopes.

**Impact**: Privilege escalation or information disclosure if scopes are not properly restricted.

**Remediation**:
- Request only the minimum scopes necessary for the application's functionality
- Validate that granted scopes match requested scopes
- Implement scope-based access control in the application
- Regularly audit scope usage and remove unnecessary scopes
- Document why each scope is required

## Finding 11: No HTTPS Enforcement

**Severity**: Critical

**Description**: OIDC communication occurs over unencrypted HTTP instead of HTTPS.

**Example Scenario**: An application redirects to an authorization endpoint using HTTP, or the token endpoint accepts HTTP connections.

**Impact**: Man-in-the-middle attacks where attackers intercept tokens, authorization codes, or credentials.

**Remediation**:
- Enforce HTTPS for all OIDC endpoints
- Use HSTS headers to prevent downgrade attacks
- Implement certificate pinning for critical connections
- Verify that all redirects use HTTPS
- Test for mixed content (HTTP resources loaded from HTTPS pages)

## Finding 12: User Enumeration via Authorization Endpoint

**Severity**: Medium

**Description**: The authorization endpoint returns different responses based on whether a user exists, enabling attackers to enumerate valid usernames.

**Example Scenario**: The OP returns "user not found" for invalid usernames but "invalid password" for valid usernames, or returns different HTTP status codes.

**Impact**: Attackers can enumerate valid usernames and use them for targeted attacks.

**Remediation**:
- Return consistent error messages regardless of whether a user exists
- Use the same HTTP status code for all authentication failures
- Avoid revealing whether a user exists in error messages
- Implement rate limiting to prevent enumeration attacks
- Log enumeration attempts for security monitoring

---

# Secure Design Guidance

## Principle 1: Minimize Token Exposure

**Guidance**: Design the application to minimize the exposure of tokens to potential attackers.

**Implementation**:
- Use Authorization Code Flow with PKCE for all new applications
- Store tokens in secure, httpOnly, sameSite cookies
- Never include tokens in URLs or query parameters
- Implement token rotation to limit the window of exposure if a token is compromised
- Use short-lived access tokens (5-15 minutes) with refresh tokens for longer-lived sessions
- Clear tokens from memory when they are no longer needed

**Example Architecture**:
```
User Browser → Application Backend → OIDC Provider
                    ↓
              Session Cookie (secure, httpOnly)
              Access Token (in memory or secure storage)
              Refresh Token (secure storage)
```

## Principle 2: Implement Defense in Depth for Token Validation

**Guidance**: Validate tokens at multiple layers to catch attacks at different points.

**Implementation**:
- Validate token signature using the OP's public key
- Validate issuer claim to ensure the token came from the expected OP
- Validate audience claim to ensure the token was issued for your application
- Validate expiration to ensure the token is still valid
-

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
