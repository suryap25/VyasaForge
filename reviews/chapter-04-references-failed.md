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
  tokenEndpoint: 'https://id