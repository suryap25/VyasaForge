# Chapter 05: JSON Web Tokens and Token Management

## Learning Objectives

After completing this chapter, you will be able to:

- Understand the structure, composition, and cryptographic properties of JSON Web Tokens (JWTs)
- Identify security risks inherent in JWT implementation and token lifecycle management
- Design and implement secure token generation, validation, and revocation strategies
- Evaluate JWT claims and signature verification mechanisms from an AppSec perspective
- Conduct security assessments of JWT implementations in web and mobile applications
- Recognize common JWT vulnerabilities and implement compensating controls
- Apply secure token management practices across distributed systems and microservices architectures

## Conceptual Foundation

JSON Web Tokens represent a stateless approach to authentication and authorization in modern distributed systems. Unlike traditional session-based authentication where server-side state is maintained, JWTs encode claims directly within the token itself, allowing services to validate tokens without querying a central session store.

A JWT consists of three base64url-encoded components separated by periods:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header** (first component) contains metadata about the token:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

The `alg` field specifies the signing algorithm. Common algorithms include HMAC variants (HS256, HS384, HS512), RSA variants (RS256, RS384, RS512), and ECDSA variants (ES256, ES384, ES512).

**Payload** (second component) contains claims—statements about the entity and additional metadata:
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022,
  "exp": 1516242622,
  "aud": "api.example.com",
  "iss": "auth.example.com"
}
```

Standard registered claims include:
- `iss` (issuer): Entity that created the token
- `sub` (subject): Principal the token represents
- `aud` (audience): Intended recipient(s) of the token
- `exp` (expiration time): Unix timestamp when token expires
- `iat` (issued at): Unix timestamp when token was created
- `nbf` (not before): Unix timestamp before which token is invalid
- `jti` (JWT ID): Unique identifier for the token

Applications can define custom claims for domain-specific data.

**Signature** (third component) is computed over the header and payload using the specified algorithm and a secret key. This ensures the token has not been tampered with and was issued by a trusted party.

The fundamental security model of JWTs relies on:

1. **Cryptographic integrity**: The signature proves the token was not modified after issuance
2. **Non-repudiation**: The issuer cannot deny creating the token (with asymmetric algorithms)
3. **Statelessness**: Validation requires only the public key or shared secret, not server-side state

However, JWTs do not provide confidentiality by default. The payload is merely base64url-encoded, not encrypted. Anyone with access to the token can read the claims. If sensitive data must be protected from disclosure, additional encryption (JWE—JSON Web Encryption) is required.

## Architecture Perspective

JWT-based authentication architectures typically follow these patterns:

**Centralized Token Issuance with Distributed Validation**

A dedicated authentication service (authorization server) issues tokens after validating credentials. Multiple resource servers validate tokens independently using the issuer's public key or shared secret. This architecture scales well because resource servers do not need to contact the authentication service for every request.

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. POST /login (credentials)
       ▼
┌──────────────────────┐
│ Authentication       │
│ Service              │
│ (Issues JWT)         │
└──────┬───────────────┘
       │ 2. JWT Token
       ▼
┌─────────────┐
│   Client    │
│ (stores JWT)│
└──────┬──────┘
       │ 3. GET /api/resource (JWT in Authorization header)
       ▼
┌──────────────────────┐
│ Resource Server 1    │
│ (Validates JWT)      │
└──────────────────────┘
       │ 4. GET /api/resource (JWT in Authorization header)
       ▼
┌──────────────────────┐
│ Resource Server 2    │
│ (Validates JWT)      │
└──────────────────────┘
```

**Token Refresh Pattern**

Short-lived access tokens reduce the window of exposure if a token is compromised. Refresh tokens, stored securely on the client, are exchanged for new access tokens when the original expires. This pattern balances security and user experience.

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. POST /login
       ▼
┌──────────────────────┐
│ Authentication       │
│ Service              │
└──────┬───────────────┘
       │ 2. {access_token, refresh_token}
       ▼
┌─────────────┐
│   Client    │
│ access_token: 15 min │
│ refresh_token: 7 day │
└──────┬──────┘
       │ 3. Use access_token for API calls
       ▼
┌──────────────────────┐
│ Resource Server      │
└──────────────────────┘
       │ 4. access_token expires
       ▼
┌─────────────┐
│   Client    │
│ POST /refresh
│ (refresh_token)
└──────┬──────┘
       │ 5. New access_token
       ▼
┌──────────────────────┐
│ Authentication       │
│ Service              │
└──────────────────────┘
```

**Microservices Token Propagation**

In microservices architectures, the client's JWT is propagated through service-to-service calls. Each service validates the token independently. This requires careful consideration of token scope and audience claims to prevent privilege escalation.

**Key Distribution Strategies**

For asymmetric algorithms (RS256, ES256), the authentication service signs tokens with a private key. Resource servers obtain the public key through:
- Static configuration (embedded in application)
- JWKS (JSON Web Key Set) endpoint: The issuer publishes public keys at a well-known URL
- Key rotation: Issuers periodically rotate keys; servers fetch updated keys from the JWKS endpoint

For symmetric algorithms (HS256), the shared secret must be securely distributed to all validating services. This is operationally complex and creates a single point of compromise.

## AppSec Lens

From an application security perspective, JWT implementations introduce several categories of risk:

**Algorithm Confusion Attacks**

A critical vulnerability occurs when an application accepts multiple algorithms without proper validation. An attacker can exploit this by:

1. Obtaining a valid JWT signed with RS256 (asymmetric)
2. Modifying the header to specify HS256 (symmetric)
3. Re-signing the token using the public key as the HMAC secret
4. Submitting the forged token

The vulnerability arises because the public key (intended only for verification) becomes the HMAC secret. If the application's validation logic does not enforce a specific algorithm, it will accept the forged token.

**Mitigation**: Explicitly specify the expected algorithm during validation. Do not accept the algorithm from the token header without verification.

```python
# VULNERABLE: Algorithm taken from token header
decoded = jwt.decode(token, key, algorithms=jwt.get_unverified_header(token)['alg'])

# SECURE: Algorithm explicitly specified
decoded = jwt.decode(token, key, algorithms=['RS256'])
```

**Weak or Missing Signature Verification**

Some implementations skip signature verification entirely or use weak verification logic:

```python
# VULNERABLE: No signature verification
import json
import base64
header, payload, signature = token.split('.')
claims = json.loads(base64.urlsafe_b64decode(payload + '=='))

# VULNERABLE: Signature verification with wrong key
decoded = jwt.decode(token, 'wrong_secret', algorithms=['HS256'])

# SECURE: Proper signature verification
decoded = jwt.decode(token, public_key, algorithms=['RS256'], audience='api.example.com')
```

**Token Expiration Not Enforced**

If the `exp` claim is not validated, an attacker can use an expired token indefinitely. Similarly, the `nbf` (not before) claim should be checked to prevent premature token usage.

**Missing Audience Validation**

The `aud` claim specifies the intended recipient. Without validating this claim, a token issued for one service can be used against another service. This is particularly dangerous in microservices architectures.

```python
# VULNERABLE: No audience validation
decoded = jwt.decode(token, key, algorithms=['RS256'])

# SECURE: Audience validation
decoded = jwt.decode(token, key, algorithms=['RS256'], audience='api.example.com')
```

**Insufficient Token Revocation**

JWTs are stateless, making revocation difficult. If a user's password is compromised or permissions change, existing tokens remain valid until expiration. Strategies to address this include:

- Short token lifetimes (15-30 minutes)
- Token blacklist: Maintain a list of revoked tokens (reduces statelessness benefit)
- Token versioning: Include a version number in the token; increment on password change
- Distributed cache: Store revocation information in Redis or similar for fast lookup

**Sensitive Data in Token Payload**

The payload is base64url-encoded, not encrypted. Sensitive information (passwords, API keys, PII) should never be included in the payload. An attacker with network access can decode the token and extract this data.

**Key Compromise**

If the signing key is compromised, an attacker can forge arbitrary tokens. For symmetric algorithms (HS256), this is particularly dangerous because the same key is used for both signing and verification. Asymmetric algorithms (RS256) are more resilient because only the private key can sign tokens.

**Token Storage Vulnerabilities**

Client-side token storage introduces risks:
- **LocalStorage**: Vulnerable to XSS attacks; JavaScript can access and exfiltrate tokens
- **SessionStorage**: Similar XSS vulnerability
- **Cookies**: Can be protected with HttpOnly and Secure flags, but vulnerable to CSRF if not properly configured

**Lack of Token Binding**

A token stolen from one user can be used by an attacker. Token binding techniques associate a token with a specific client (e.g., IP address, device fingerprint, TLS certificate). However, these are imperfect and can cause legitimate access issues.

## Developer Lens

From a developer implementation perspective, secure JWT handling requires attention to multiple concerns:

**Token Generation**

```python
import jwt
from datetime import datetime, timedelta
import secrets

def generate_tokens(user_id, email):
    """Generate access and refresh tokens with proper claims."""
    
    # Generate access token (short-lived)
    access_payload = {
        'sub': user_id,
        'email': email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'aud': 'api.example.com',
        'iss': 'auth.example.com',
        'type': 'access'
    }
    
    access_token = jwt.encode(
        access_payload,
        private_key,
        algorithm='RS256'
    )
    
    # Generate refresh token (long-lived)
    refresh_payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=7