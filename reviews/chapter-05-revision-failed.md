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
        'exp': datetime.utcnow() + timedelta(days=7),
        'aud': 'auth.example.com',
        'iss': 'auth.example.com',
        'type': 'refresh',
        'jti': secrets.token_urlsafe(32)  # Unique token ID for revocation
    }
    
    refresh_token = jwt.encode(
        refresh_payload,
        private_key,
        algorithm='RS256'
    )
    
    return access_token, refresh_token
```

**Token Validation**

```python
def validate_token(token, token_type='access'):
    """Validate JWT with comprehensive checks."""
    
    try:
        # Decode with explicit algorithm and claims validation
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],  # Explicitly specify algorithm
            audience='api.example.com',
            issuer='auth.example.com',
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_aud': True,
                'verify_iss': True
            }
        )
        
        # Verify token type
        if decoded.get('type') != token_type:
            raise ValueError(f'Invalid token type: {decoded.get("type")}')
        
        # Check revocation list (if using token blacklist)
        if is_token_revoked(decoded.get('jti')):
            raise ValueError('Token has been revoked')
        
        return decoded
        
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidAudienceError:
        raise ValueError('Invalid token audience')
    except jwt.InvalidIssuerError:
        raise ValueError('Invalid token issuer')
    except jwt.InvalidSignatureError:
        raise ValueError('Invalid token signature')
    except Exception as e:
        raise ValueError(f'Token validation failed: {str(e)}')
```

**Refresh Token Exchange**

```python
@app.route('/refresh', methods=['POST'])
def refresh_access_token():
    """Exchange refresh token for new access token."""
    
    refresh_token = request.json.get('refresh_token')
    
    if not refresh_token:
        return {'error': 'Refresh token required'}, 400
    
    try:
        # Validate refresh token
        decoded = validate_token(refresh_token, token_type='refresh')
        
        # Generate new access token
        access_token, _ = generate_tokens(
            decoded['sub'],
            decoded.get('email')
        )
        
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 900  # 15 minutes
        }, 200
        
    except ValueError as e:
        return {'error': str(e)}, 401
```

**Secure Token Storage (Web)**

For web applications, store tokens in memory or use HttpOnly cookies:

```javascript
// Store in memory (lost on page refresh)
let accessToken = null;

function setAccessToken(token) {
    accessToken = token;
}

function getAccessToken() {
    return accessToken;
}

// Or use HttpOnly cookie (set by server)
// Server response:
// Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/api
```

**Secure Token Storage (Mobile)**

For mobile applications, use platform-specific secure storage:

```swift
// iOS: Keychain
import Security

func storeToken(_ token: String) {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: "access_token",
        kSecValueData as String: token.data(using: .utf8)!,
        kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    ]
    
    SecItemAdd(query as CFDictionary, nil)
}
```

```kotlin
// Android: EncryptedSharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences

val encryptedSharedPreferences = EncryptedSharedPreferences.create(
    context,
    "secret_shared_prefs",
    MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

encryptedSharedPreferences.edit().putString("access_token", token).apply()
```

**Token Revocation Implementation**

```python
import redis

# Initialize Redis client
revocation_cache = redis.Redis(host='localhost', port=6379, db=0)

def revoke_token(jti, expiration_time):
    """Add token to revocation list."""
    # Store JTI with expiration matching token expiration
    revocation_cache.setex(
        f'revoked_token:{jti}',
        expiration_time,
        '1'
    )

def is_token_revoked(jti):
    """Check if token has been revoked."""
    return revocation_cache.exists(f'revoked_token:{jti}') > 0

def revoke_user_tokens(user_id):
    """Revoke all tokens for a user (password change, logout)."""
    # Increment user token version
    current_version = revocation_cache.incr(f'user_token_version:{user_id}')
    
    # Tokens with old version will be rejected
    return current_version
```

## Pentest Lens

Security assessments of JWT implementations should focus on:

**Token Inspection and Decoding**

Use tools like jwt.io or command-line utilities to decode tokens and examine claims:

```bash
# Decode JWT without verification
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | cut -d. -f2 | base64 -d | jq .
```

Examine:
- Expiration time (`exp`): Is it reasonable?
- Audience (`aud`): Is it specific to the service?
- Issuer (`iss`): Is it trusted?
- Custom claims: Do they contain sensitive data?

**Algorithm Confusion Testing**

Attempt to exploit algorithm confusion:

1. Obtain a valid token signed with RS256
2. Decode and modify the header to specify HS256
3. Re-sign using the public key as the HMAC secret
4. Submit the forged token

If accepted, the application is vulnerable.

```python
import jwt
import json
import base64

# Original token (RS256)
original_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Decode without verification
header = json.loads(base64.urlsafe_b64decode(original_token.split('.')[0] + '=='))
payload = json.loads(base64.urlsafe_b64decode(original_token.split('.')[1] + '=='))

# Modify header to use HS256
header['alg'] = 'HS256'

# Modify payload (e.g., change user ID)
payload['sub'] = 'admin'

# Re-encode and sign with public key as secret
forged_token = jwt.encode(
    payload,
    public_key,  # Using public key as HMAC secret
    algorithm='HS256',
    headers=header
)
```

**Signature Verification Testing**

Test whether signature verification is properly enforced:

1. Modify the payload (change user ID, permissions)
2. Keep the original signature
3. Submit the modified token

If accepted, signature verification is not enforced.

```python
# Modify payload without changing signature
parts = token.split('.')
modified_payload = base64.urlsafe_b64encode(
    json.dumps({'sub': 'admin', 'role': 'admin'}).encode()
).decode().rstrip('=')

forged_token = f"{parts[0]}.{modified_payload}.{parts[2]}"
```

**Testing for 'none' Algorithm**

Some JWT libraries support the `none` algorithm (no signature). Test if this is accepted:

```python
# Create token with 'none' algorithm
header = base64.urlsafe_b64encode(json.dumps({'alg': 'none', 'typ': 'JWT'}).encode()).decode().rstrip('=')
payload = base64.urlsafe_b64encode(json.dumps({'sub': 'admin'}).encode()).decode().rstrip('=')

token_with_none = f"{header}.{payload}."
```

If the application accepts this token, it is critically vulnerable.

**Testing Expiration Enforcement**

Obtain an expired token and attempt to use it. If accepted, expiration validation is not enforced. Check the token's `exp` claim and verify it is in the past.

**Testing Audience and Issuer Validation**

Modify the `aud` and `iss` claims in a token and attempt to use it against a different service. If accepted, audience or issuer validation is missing.

```python
# Modify audience claim
payload['aud'] = 'different-service.example.com'
```

**Testing Token Revocation**

After a user logs out or changes their password, attempt to use their old token. If accepted, revocation is not implemented. Check if the token's `jti` (JWT ID) is tracked in a revocation list.

**Key Confusion Testing**

If the application uses asymmetric algorithms (RS256), attempt to:
1. Obtain the public key from the JWKS endpoint or application configuration
2. Create a new token signed with HS256 using the public key as the HMAC secret
3. Submit the forged token

If accepted, the application is vulnerable to key confusion attacks.

**Testing Sensitive Data Exposure**

Decode the JWT payload and examine it for:
- Passwords or password hashes
- API keys or secrets
- Social security numbers or credit card numbers
- Personally identifiable information

If sensitive data is present, the token is vulnerable to disclosure attacks."
    },
    {## Algorithm Confusion and Misvalidation

**Finding**: Application accepts tokens with algorithm specified in the header without explicit validation of the expected algorithm.

**Risk**: Attackers can exploit algorithm confusion to forge tokens. By changing the algorithm from RS256 (asymmetric) to HS256 (symmetric) and re-signing with the public key as the HMAC secret, attackers bypass signature verification.

**Example**: A microservice validates JWTs using the issuer's public key but does not enforce RS256. An attacker obtains a valid token, modifies the header to `"alg": "HS256"`, and re-signs using the public key as the HMAC secret. The validation library accepts the forged token because the algorithm is taken from the untrusted header.

**Detection**: Review token validation code. Look for patterns where the algorithm is extracted from the token header or where multiple algorithms are accepted without explicit enforcement.

```python
# VULNERABLE PATTERN
decoded = jwt.decode(token, key, algorithms=jwt.get_unverified_header(token)['alg'])
```

**Remediation**: Explicitly specify the expected algorithm during validation. Use an allowlist of acceptable algorithms.

```python
# SECURE PATTERN
decoded = jwt.decode(token, key, algorithms=['RS256'], audience='api.example.com')
```

---

## Missing or Incomplete Signature Verification

**Finding**: Application decodes JWT payload without verifying the signature, or verification is performed with incorrect keys.

**Risk**: Attackers can forge arbitrary tokens by modifying claims and omitting the signature. Alternatively, if verification uses the wrong key (e.g., a test key in production), tokens can be forged.

**Example**: A web application extracts the payload from a JWT by base64-decoding the second component without validating the signature. An attacker modifies the `sub` claim to impersonate another user and submits the token. The application accepts it because no signature verification occurs.

**Detection**: Search for JWT handling code that:
- Splits the token and base64-decodes components without calling a validation function
- Uses `jwt.decode()` without the `verify` parameter set to `True`
- Catches and ignores signature verification exceptions
- Uses hardcoded or test keys in production

**Remediation**: Always verify the signature using the correct key and algorithm. Use well-maintained JWT libraries that enforce verification by default.

```python
# VULNERABLE: No verification
import base64, json
payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '=='))

# SECURE: Signature verification enforced
decoded = jwt.decode(token, public_key, algorithms=['RS256'])
```

---

## Expired Token Acceptance

**Finding**: Application does not validate the `exp` (expiration time) claim, or validation is disabled.

**Risk**: Attackers can use expired tokens indefinitely. If a user's account is compromised, an attacker can continue using the victim's old tokens even after the legitimate user changes their password.

**Example**: A resource server validates JWT signatures but disables expiration checking with `options={'verify_exp': False}`. An attacker obtains a token that expired six months ago and uses it to access the API. The server accepts it because expiration is not enforced.

**Detection**: Review validation code for:
- `options={'verify_exp': False}` or similar disable flags
- Absence of expiration time checks
- Catch blocks that ignore `ExpiredSignatureError`

**Remediation**: Enable expiration validation by default. Ensure the `exp` claim is present in all tokens and validated during verification.

```python
# VULNERABLE
decoded = jwt.decode(token, key, algorithms=['RS256'], options={'verify_exp': False})

# SECURE
decoded = jwt.decode(token, key, algorithms=['RS256'])  # Expiration checked by default
```

---

## Missing Audience Validation

**Finding**: Application does not validate the `aud` (audience) claim, allowing tokens issued for one service to be used against another.

**Risk**: In microservices architectures, a token intended for Service A can be used to access Service B if audience validation is absent. This enables privilege escalation and lateral movement.

**Example**: An authentication service issues tokens with `"aud": "api.example.com"` for the main API. A separate admin service does not validate the audience claim. An attacker uses a token intended for the main API to access the admin service, gaining unauthorized privileges.

**Detection**: Review validation code for:
- Absence of `audience` parameter in `jwt.decode()` calls
- Validation of audience against a hardcoded or incorrect value
- Audience validation only in some code paths

**Remediation**: Validate the audience claim against the service's expected audience. Each service should specify its own audience.

```python
# VULNERABLE: No audience validation
decoded = jwt.decode(token, key, algorithms=['RS256'])

# SECURE: Audience validated
decoded = jwt.decode(token, key, algorithms=['RS256'], audience='admin.example.com')
```

---

## Insufficient Token Revocation

**Finding**: No mechanism exists to revoke tokens before expiration. Revoked tokens remain valid until they expire.

**Risk**: When a user's password is compromised, permissions are revoked, or a user logs out, existing tokens cannot be invalidated. An attacker with a stolen token can continue accessing the system.

**Example**: A user logs out, but their JWT access token (valid for 24 hours) is not revoked. An attacker who obtained the token during the session can continue using it for the next 24 hours, accessing the user's data and performing actions on their behalf.

**Detection**: Review the logout and permission change workflows:
- Absence of token revocation logic
- No token blacklist or revocation cache
- Revocation only applied to new tokens, not existing ones

**Remediation**: Implement a revocation mechanism:
- Maintain a blacklist of revoked token IDs (`jti` claim)
- Use short token lifetimes (15-30 minutes) with refresh tokens
- Include a token version in the payload; increment on password change
- Store revocation information in a fast cache (Redis) for quick lookup

```python
# SECURE: Token revocation with Redis
def revoke_token(jti, expiration_seconds):
    revocation_cache.setex(f'revoked:{jti}', expiration_seconds, '1')

def is_revoked(jti):
    return revocation_cache.exists(f'revoked:{jti}') > 0
```

---

## Sensitive Data in Token Payload

**Finding**: Confidential information (passwords, API keys, PII, credit card numbers) is included in the JWT payload.

**Risk**: The JWT payload is base64url-encoded, not encrypted. Anyone with access to the token can decode it and extract sensitive data. This violates the principle of least privilege and exposes confidential information.

**Example**: A JWT payload contains `"password_hash": "bcrypt_hash_here"` and `"ssn": "123-45-6789"`. An attacker intercepts the token (via network sniffing, XSS, or logs) and decodes the payload to extract the SSN and password hash.

**Detection**: Decode tokens and examine the payload for:
- Passwords or password hashes
- API keys or secrets
- Social security numbers, credit card numbers, or other PII
- Personally identifiable information that should not be transmitted in plaintext

**Remediation**: Store only necessary claims in the token. Use the `sub` claim for user identification and custom claims for authorization data (roles, permissions). Retrieve sensitive data from a secure backend store when needed.

```python
# VULNERABLE: Sensitive data in payload
payload = {
    'sub': user_id,
    'password_hash': user.password_hash,
    'ssn': user.ssn,
    'credit_card': user.credit_card
}

# SECURE: Only necessary claims
payload = {
    'sub': user_id,
    'email': user.email,
    'roles': ['user', 'admin'],
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(minutes=15)
}
```

---

## Weak Key Management

**Finding**: Signing keys are weak, hardcoded, or not properly rotated.

**Risk**: Weak keys (short HMAC secrets, small RSA key sizes) can be brute-forced or factored. Hardcoded keys in source code are exposed if the repository is compromised. Keys that are never rotated become a single point of failure.

**Example**: An application uses a 32-character HMAC secret derived from a predictable pattern (e.g., the application name repeated). An attacker brute-forces the secret and forges arbitrary tokens.

**Detection**: Review key management practices:
- HMAC secrets shorter than 256 bits
- RSA keys smaller than 2048 bits
- Keys hardcoded in source code or configuration files
- No key rotation policy or mechanism
- Same key used across multiple environments (development, staging, production)

**Remediation**: Use strong keys and proper key management:
- HMAC secrets: At least 256 bits (32 bytes) of cryptographically random data
- RSA keys: At least 2048 bits (preferably 4096 bits)
- Store keys in secure vaults (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- Implement key rotation: Periodically generate new keys and publish them via JWKS endpoint
- Use different keys for different environments

```python
# VULNERABLE: Weak hardcoded secret
SECRET_KEY = 'my_secret_key'

# SECURE: Strong key from environment
import os
SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
# Ensure SECRET_KEY is at least 256 bits of random data

# SECURE: Key rotation with JWKS
# Publish public keys at /.well-known/jwks.json
# Include 'kid' (key ID) in token header to identify which key was used
```

---

## Insecure Token Storage (Client-Side)

**Finding**: Tokens are stored in localStorage or sessionStorage, making them vulnerable to XSS attacks.

**Risk**: JavaScript running in the browser (including malicious scripts injected via XSS) can access tokens stored in localStorage or sessionStorage and exfiltrate them to an attacker-controlled server.

**Example**: A reflected XSS vulnerability allows an attacker to inject JavaScript into the page. The injected script accesses `localStorage.getItem('access_token')` and sends it to the attacker's server. The attacker then uses the token to impersonate the user.

**Detection**: Review client-side code for:
- `localStorage.setItem('token', ...)` or `sessionStorage.setItem('token', ...)`
- Absence of HttpOnly cookie usage
- Tokens visible in browser DevTools

**Remediation**: Store tokens in HttpOnly cookies set by the server. HttpOnly cookies cannot be accessed by JavaScript, protecting them from XSS attacks.

```javascript
// VULNERABLE: Token in localStorage
localStorage.setItem('access_token', token);

// SECURE: Token in HttpOnly cookie (set by server)
// Server response header:
// Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/api
```

---

## Missing or Weak Issuer Validation

**Finding**: Application does not validate the `iss` (issuer) claim, or validation is performed against an incorrect value.

**Risk**: Tokens issued by untrusted parties are accepted. In federated authentication scenarios, an attacker can issue tokens from a malicious authorization server and use them to access the application.

**Example**: An application accepts tokens from multiple issuers but does not validate the `iss` claim. An attacker creates a malicious authorization server, issues a token with `"iss": "attacker.com"`, and uses it to access the application.

**Detection**: Review validation code for:
- Absence of `issuer` parameter in `jwt.decode()` calls
- Validation against a hardcoded or incorrect issuer
- Issuer validation only in some code paths

**Remediation**: Validate the issuer claim against the expected authorization server. Use an allowlist of trusted issuers if multiple are supported.

```python
# VULNERABLE: No issuer validation
decoded = jwt.decode(token, key, algorithms=['RS256'])

# SECURE: Issuer validated
decoded = jwt.decode(token, key, algorithms=['RS256'], issuer='auth.example.com')

# SECURE: Multiple trusted issuers
trusted_issuers = ['auth.example.com', 'auth-backup.example.com']
decoded = jwt.decode(token, key, algorithms=['RS256'], issuer=trusted_issuers)
```

---

## Lack of Token Binding

**Finding**: Tokens are not bound to a specific client, device, or session. A stolen token can be used by any attacker.

**Risk**: If a token is compromised (stolen from storage, intercepted, or leaked), an attacker can use it without restriction. Token binding techniques associate a token with a specific client, reducing the impact of token theft.

**Example**: An attacker steals a user's access token from a compromised device. The attacker uses the token from a different IP address and device to access the API. Without token binding, the API accepts the request because the token is valid.

**Detection**: Review token generation and validation:
- Absence of client-specific claims (IP address, device fingerprint, TLS certificate)
- No verification that the token is being used by the intended client

**Remediation**: Implement token binding by including client-specific information in the token and validating it during verification. Note that these techniques are imperfect and can cause legitimate access issues.

```python
# SECURE: Token binding with IP address (imperfect but helpful)
import hashlib

def generate_token_with_binding(user_id, client_ip):
    payload = {
        'sub': user_id,
        'ip_hash': hashlib.sha256(client_ip.encode()).hexdigest(),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def validate_token_with_binding(token, client_ip):
    decoded = jwt.decode(token, public_key, algorithms=['RS256'])
    expected_ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    if decoded.get('ip_hash') != expected_ip_hash:
        raise ValueError('Token IP binding mismatch')
    return decoded
```

---

## No Token Type Validation

**Finding**: Application does not distinguish between different token types (access token vs. refresh token) or validate the token type claim.

**Risk**: A refresh token (long-lived) can be used in place of an access token (short-lived), extending the window of exposure. An attacker with a refresh token can use it directly to access protected resources instead of exchanging it for an access token.

**Example**: An application issues both access tokens (15-minute lifetime) and refresh tokens (7-day lifetime) but does not include a `type` claim. An attacker obtains a refresh token and uses it directly in the Authorization header to access the API. The server accepts it because it does not validate the token type.

**Detection**: Review token generation and validation:
- Absence of `type` or `token_type` claim in tokens
- No validation of the token type during verification
- Same validation logic for access and refresh tokens

**Remediation**: Include a `type` claim in all tokens and validate it during verification. Use different validation rules for different token types.

```python
# SECURE: Token type claim and validation
def generate_tokens(user_id):
    access_payload = {
        'sub': user_id,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    refresh_payload = {
        'sub': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(access_payload, key, algorithm='RS256'), \
           jwt.encode(refresh_payload, key, algorithm='RS256')

def validate_access_token(token):
    decoded = jwt.decode(token, key, algorithms=['RS256'])
    if decoded.get('type') != 'access':
        raise ValueError('Invalid token type')
    return decoded
```

---

## Improper JWKS Endpoint Implementation

**Finding**: The JWKS (JSON Web Key Set) endpoint is not properly secured, or keys are not rotated.

**Risk**: If the JWKS endpoint is not authenticated or is accessible to unauthorized parties, an attacker can replace legitimate keys with their own. If keys are never rotated, a compromised key remains valid indefinitely.

**Example**: A JWKS endpoint at `/.well-known/jwks.json` is publicly accessible and accepts PUT requests. An attacker replaces the legitimate public key with their own and issues forged tokens that the application accepts.

**Detection**: Review JWKS endpoint implementation:
- Endpoint is writable by unauthorized users
- No rate limiting or access controls
- Keys are never rotated
- Old keys are not removed from the endpoint

**Remediation**: Secure the JWKS endpoint and implement key rotation:
- Make the endpoint read-only for clients
- Implement rate limiting to prevent abuse
- Rotate keys periodically (e.g., monthly)
- Publish multiple keys (current and previous) to allow for graceful rotation
- Include `kid` (key ID) in token headers to identify which key was used

```python
# SECURE: JWKS endpoint with key rotation
@app.route('/.well-known/jwks.json', methods=['GET'])
def jwks():
    # Return current and previous keys
    keys = [
        {
            'kty': 'RSA',
            'kid': 'current_key_id',
            'use': 'sig',
            'n': current_public_key_n,
            'e': current_public_key_e
        },
        {
            'kty': 'RSA',
            'kid': 'previous_key_id',
            'use': 'sig',
            'n': previous_public_key_n,
            'e': previous_public_key_e
        }
    ]
    return {'keys': keys}
```

---

# Secure Design Guidance

## Token Lifecycle Design

**Principle**: Design a complete token lifecycle that balances security and usability.

**Guidance**:

1. **Token Generation**: Issue tokens only after successful authentication. Include necessary claims (`sub`, `aud`, `iss`, `exp`, `iat`) and a unique token ID (`jti`) for revocation.

2. **Token Validation**: Validate all claims (signature, expiration, audience, issuer) on every request. Do not skip validation for performance reasons.

3. **Token Refresh**: Use short-lived access tokens (15-30 minutes) with longer-lived refresh tokens (7-30 days). Refresh tokens should be exchanged for new access tokens, not used directly for API access.

4. **Token Revocation**: Implement revocation for logout, password change, and permission revocation. Use a blacklist or token versioning approach.

5. **Token Expiration**: Set reasonable expiration times. Access tokens should expire quickly; refresh tokens can have longer lifetimes.

**Implementation Pattern**:

```python
# Token generation with complete lifecycle
def authenticate_user(username, password):
    user = authenticate(username, password)
    if not user:
        return None
    
    access_token, refresh_token = generate_tokens(user.id, user.email)
    
    # Store refresh token in database for revocation tracking
    store_refresh_token(user.id, refresh_token, expiration=timedelta(days=7))
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900  # 15 minutes
    }

def refresh_access_token(refresh_token):
    # Validate refresh token
    decoded = validate_token(refresh_token, token_type='refresh')
    
    # Check if refresh token has been revoked
    if is_refresh_token_revoked(decoded['jti']):
        raise ValueError('Refresh token has been revoked')
    
    # Generate new access token
    user = get_user(decoded['sub'])
    access_token, _ = generate_tokens(user.id, user.email)
    
    return {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 900
    }

def logout_user(user_id, refresh_token):
    # Revoke refresh token
    decoded = validate_token(refresh_token, token_type
```

## Interview Questions

- How would you test a JWT implementation for algorithm confusion vulnerabilities? What would you look for in the validation code?
- What claims should always be validated in a JWT, and why is each one important?
- Describe how you would design a token revocation system for a microservices architecture. What are the trade-offs between different approaches?
- What are the security trade-offs between short-lived access tokens (15 minutes) and long-lived refresh tokens (7 days)?
- How would you detect if a JWT implementation is missing audience validation? What would be the impact in a microservices environment?
- If you found that an application stores sensitive data (like SSN or API keys) in a JWT payload, how would you explain the risk to the development team?
- How should refresh tokens be stored and transmitted differently from access tokens? Why?
- What is the difference between JWTs and JWE, and when would you recommend using each?
- How would you verify that signature verification is actually being enforced in a JWT validation function?
- In a federated authentication scenario with multiple trusted issuers, how would you prevent tokens from one issuer being used against services that should only accept tokens from another issuer?"
    },
    {## Key Takeaways

- Authentication verifies identity; authorization decides what that identity can access.
- Strong authentication does not compensate for missing or inconsistent authorization checks.
- Authorization belongs on the server side and should be enforced close to protected resources.
- AppSec reviews should trace identity, session, role, permission, and object ownership decisions.
- Secure design requires clear access-control models, centralized policy logic, and repeatable tests.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]

## Secure Design Guidance

**Token Lifecycle Design**

**Principle**: Design a complete token lifecycle that balances security and usability.

**Guidance**:

1. **Token Generation**: Issue tokens only after successful authentication. Include necessary claims (`sub`, `aud`, `iss`, `exp`, `iat`) and a unique token ID (`jti`) for revocation.

2. **Token Validation**: Validate all claims (signature, expiration, audience, issuer) on every request. Do not skip validation for performance reasons.

3. **Token Refresh**: Use short-lived access tokens (15-30 minutes) with longer-lived refresh tokens (7-30 days). Refresh tokens should be exchanged for new access tokens, not used directly for API access.

4. **Token Revocation**: Implement revocation for logout, password change, and permission revocation. Use a blacklist or token versioning approach.

5. **Token Expiration**: Set reasonable expiration times. Access tokens should expire quickly; refresh tokens can have longer lifetimes.

**Implementation Pattern**:

```python
# Token generation with complete lifecycle
def authenticate_user(username, password):
    user = authenticate(username, password)
    if not user:
        return None
    
    access_token, refresh_token = generate_tokens(user.id, user.email)
    
    # Store refresh token in database for revocation tracking
    store_refresh_token(user.id, refresh_token, expiration=timedelta(days=7))
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900  # 15 minutes
    }

def refresh_access_token(refresh_token):
    # Validate refresh token
    decoded = validate_token(refresh_token, token_type='refresh')
    
    # Check if refresh token has been revoked
    if is_refresh_token_revoked(decoded['jti']):
        raise ValueError('Refresh token has been revoked')
    
    # Generate new access token
    user = get_user(decoded['sub'])
    access_token, _ = generate_tokens(user.id, user.email)
    
    return {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 900
    }

def logout_user(user_id, refresh_token):
    # Revoke refresh token
    decoded = validate_token(refresh_token, token_type='refresh')
    revoke_token(decoded['jti'], decoded['exp'])
    
    # Optionally: Increment user token version to invalidate all tokens
    increment_user_token_version(user_id)
```

**Token Lifecycle Edge Cases**

- **Permission Changes Mid-Session**: When a user's permissions change (role revocation, privilege escalation), existing tokens remain valid until expiration. Mitigate by using short token lifetimes and implementing token versioning. Increment the version when permissions change; tokens with old versions are rejected.

- **Password Change**: When a user changes their password, all existing tokens should be revoked. Implement this by incrementing a user-specific token version or maintaining a revocation list.

- **Account Lockout**: When an account is locked or suspended, all tokens should be immediately revoked. Use a revocation list or token version approach.

- **Device Logout**: In multi-device scenarios, allow users to revoke tokens for specific devices. Track device identifiers in the token and revocation list.

**Microservices Token Propagation**

When tokens are propagated through service-to-service calls:

- Validate the `aud` claim to ensure the token is intended for the receiving service
- Do not modify or re-sign tokens in intermediate services
- Propagate the original token to downstream services
- Log token usage for audit trails
- Consider using separate tokens for service-to-service communication (with different `aud` and `iss` claims)

**Key Management Best Practices**

- Use asymmetric algorithms (RS256, ES256) for distributed systems; symmetric algorithms (HS256) require secure key distribution
- Store private keys in secure vaults (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- Implement key rotation: Generate new keys periodically and publish them via JWKS endpoint
- Include `kid` (key ID) in token headers to identify which key was used
- Maintain multiple keys during rotation to allow graceful transitions
- Use different keys for different environments (development, staging, production)
- Audit key access and rotation events"
    },
    {

## Key Takeaways

- JWTs provide cryptographic integrity and non-repudiation but not confidentiality; use JWE (JSON Web Encryption) if the payload must be protected from disclosure.
- Algorithm confusion is a critical vulnerability; always explicitly specify the expected algorithm during validation rather than accepting the algorithm from the token header.
- Token revocation is essential for security but breaks the stateless model; design revocation mechanisms (blacklists, token versioning) that balance security and performance.
- Short-lived access tokens (15-30 minutes) with longer-lived refresh tokens (7-30 days) balance security and usability better than single long-lived tokens.
- Validate all claims (signature, expiration, audience, issuer) on every request; do not skip
