# Chapter 1: Authentication vs Authorization

## Learning Objectives

After completing this chapter, you will be able to:

- **Distinguish** between authentication and authorization and explain why both are essential to application security
- **Design** authentication mechanisms that verify user identity with appropriate strength for your threat model
- **Implement** authorization controls that enforce access policies consistently across your application
- **Identify** common authentication and authorization failures in code review and penetration testing
- **Evaluate** authentication and authorization architectures for security gaps and design flaws
- **Apply** secure design patterns for both authentication and authorization in web applications and APIs
- **Assess** whether your organization's authentication and authorization controls meet security requirements

---

## Conceptual Foundation

Authentication and authorization are foundational security concepts that are frequently confused, conflated, or implemented incorrectly. Understanding the distinction between them is critical to building secure applications.

### Authentication: Proving Identity

**Authentication** is the process of verifying that a user is who they claim to be. It answers the question: "Who are you?"

When you log into your email account, you provide credentials—typically a username and password. The authentication system verifies that the password matches the account, confirming your identity. Authentication establishes a verified identity that the application can trust for the duration of a session or request.

Authentication mechanisms include:

- **Password-based authentication**: User provides a secret (password) that only they should know
- **Multi-factor authentication (MFA)**: User provides multiple independent factors (something you know, something you have, something you are)
- **Certificate-based authentication**: User proves possession of a private key corresponding to a trusted certificate
- **Token-based authentication**: User exchanges credentials for a token (JWT, OAuth token) that represents their authenticated identity
- **Biometric authentication**: User provides a biological characteristic (fingerprint, face recognition)
- **Social authentication**: User authenticates through a trusted third party (OAuth 2.0 with Google, GitHub, etc.)

The strength of authentication depends on the mechanism used and how well it resists attacks. A password-only system is weaker than a system requiring both a password and a time-based one-time password (TOTP). A system vulnerable to credential stuffing attacks is weaker than one with rate limiting and account lockout.

### Authorization: Enforcing Access Policy

**Authorization** is the process of determining what an authenticated user is allowed to do. It answers the question: "What are you allowed to access?"

After authentication establishes your identity, authorization controls determine which resources you can access and what actions you can perform. If you authenticate as a regular user in a banking application, authorization prevents you from viewing other customers' accounts or transferring funds from accounts you don't own.

Authorization mechanisms include:

- **Role-based access control (RBAC)**: Users are assigned roles (admin, user, viewer), and roles have permissions
- **Attribute-based access control (ABAC)**: Access decisions based on attributes of the user, resource, action, and environment
- **Access control lists (ACLs)**: Explicit lists defining which users or groups can access specific resources
- **Policy-based access control**: Formal policies define who can do what under what conditions

Authorization is enforced at multiple layers:

- **API level**: The backend service checks permissions before returning data or performing actions
- **Database level**: Row-level security or views restrict which records a user can access
- **UI level**: The frontend hides or disables features the user cannot access (this is not a security control, only a UX improvement)
- **Business logic level**: Application code enforces domain-specific rules about what actions are permitted

### The Relationship Between Authentication and Authorization

Authentication and authorization are sequential and interdependent:

1. **Authentication first**: The application must verify the user's identity before making any authorization decisions
2. **Authorization second**: Once identity is established, the application checks permissions
3. **Both required**: An application that authenticates users but fails to authorize access is insecure. An application that authorizes without authenticating is also insecure.

A common failure is treating authentication as sufficient for security. For example, an application might correctly authenticate a user but then fail to check whether that user owns the resource they're requesting. This is a **broken object-level authorization** vulnerability—the user is authenticated, but authorization is missing.

---

## Architecture Perspective

### Authentication Architecture Patterns

Modern applications use several authentication architecture patterns, each with different security and operational characteristics.

#### Centralized Authentication Service

In this pattern, a dedicated authentication service handles all identity verification. Applications delegate authentication to this service rather than implementing it themselves.

```
User → Application → Auth Service → Identity Provider
                          ↓
                    Session/Token
                          ↓
                    Application
```

**Advantages:**
- Single implementation reduces bugs and inconsistencies
- Easier to update authentication mechanisms globally
- Centralized audit logging of authentication events
- Supports single sign-on (SSO) across multiple applications

**Considerations:**
- The auth service becomes a critical dependency
- Network latency for every authentication check
- Requires secure communication between application and auth service
- Token validation must be fast and reliable

#### Distributed Token-Based Authentication

Applications validate tokens (JWTs, OAuth tokens) locally without contacting a central service for every request.

```
User → Auth Service → Token (JWT)
                          ↓
User + Token → Application (validates locally)
```

**Advantages:**
- No dependency on auth service for every request
- Scales horizontally—each application validates independently
- Reduced latency for request processing
- Stateless—no session storage required

**Considerations:**
- Token revocation is difficult (tokens remain valid until expiration)
- Clock skew between servers can cause validation failures
- Token compromise affects all applications until expiration
- Requires secure token signing and validation

#### Hybrid Approach

Many organizations use both patterns: centralized authentication for login, distributed token validation for requests.

```
User → Auth Service (login) → Token
                                  ↓
User + Token → Application (validates token locally)
                                  ↓
            (Optional: periodic validation with auth service)
```

### Authorization Architecture Patterns

#### Centralized Policy Engine

A dedicated service evaluates all authorization decisions.

```
Application → Policy Engine → Decision (Allow/Deny)
```

**Advantages:**
- Consistent policy enforcement across all applications
- Easier to audit and modify policies
- Supports complex policy languages (XACML, Rego)
- Separation of policy from application logic

**Considerations:**
- Every authorization check requires a network call
- Policy engine becomes a critical dependency
- Latency impact on application performance
- Requires caching for acceptable performance

#### Distributed Authorization

Applications make authorization decisions locally using policies distributed to them.

```
Policy Distribution → Application (evaluates locally)
```

**Advantages:**
- No network dependency for authorization checks
- Low latency
- Scales horizontally
- Applications can make decisions offline

**Considerations:**
- Policy updates have propagation delay
- Inconsistent enforcement if policies diverge
- Harder to audit across applications
- Requires careful policy versioning

#### Attribute-Based Access Control (ABAC)

Authorization decisions based on attributes of the user, resource, action, and environment.

```
User Attributes + Resource Attributes + Action + Environment
                          ↓
                    Policy Engine
                          ↓
                    Decision (Allow/Deny)
```

ABAC is more flexible than RBAC but requires careful policy design to avoid complexity and security gaps.

---

## AppSec Lens

### Authentication Security Risks

#### Weak Credential Storage

**Risk**: Passwords stored in plaintext or with weak hashing allow attackers to compromise accounts.

**Example failure**:
```python
# INSECURE: Storing password in plaintext
def create_user(username, password):
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
```

**Secure approach**:
```python
# SECURE: Using bcrypt with proper salt and cost factor
import bcrypt

def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()
```

#### Credential Stuffing and Brute Force

**Risk**: Attackers use lists of compromised credentials or attempt many password guesses to gain access.

**Mitigation strategies**:
- Implement rate limiting on login endpoints (e.g., 5 failed attempts per 15 minutes)
- Use account lockout after repeated failures (temporary, not permanent)
- Implement CAPTCHA after failed attempts
- Monitor for unusual login patterns
- Require MFA to reduce impact of compromised passwords

#### Session Fixation

**Risk**: Attacker forces a user to use a known session ID, then hijacks the session after authentication.

**Secure approach**:
- Generate a new session ID after successful authentication
- Invalidate the pre-authentication session ID
- Use secure, random session IDs (cryptographically strong)
- Set secure flags on session cookies (HttpOnly, Secure, SameSite)

#### Insecure Token Handling

**Risk**: Tokens stored insecurely, transmitted over unencrypted channels, or not validated properly.

**Secure approach**:
- Store tokens in secure, HttpOnly cookies or secure storage
- Transmit tokens only over HTTPS
- Validate token signature and expiration on every request
- Use short expiration times for access tokens
- Implement token refresh mechanisms

### Authorization Security Risks

#### Broken Object-Level Authorization (BOLA)

**Risk**: User can access or modify resources belonging to other users by manipulating object identifiers.

**Example failure**:
```python
# INSECURE: No authorization check
@app.route('/api/accounts/<account_id>/balance')
def get_balance(account_id):
    account = Account.query.get(account_id)
    return {'balance': account.balance}
```

An authenticated user can request `/api/accounts/999/balance` and retrieve another user's balance.

**Secure approach**:
```python
# SECURE: Verify user owns the account
@app.route('/api/accounts/<account_id>/balance')
def get_balance(account_id):
    account = Account.query.get(account_id)
    
    # Authorization check
    if account.user_id != current_user.id:
        abort(403)  # Forbidden
    
    return {'balance': account.balance}
```

#### Privilege Escalation

**Risk**: User gains access to higher-privilege functions or data.

**Example failure**:
```python
# INSECURE: Role check only on frontend
@app.route('/api/admin/users', methods=['DELETE'])
def delete_user(user_id):
    # No backend authorization check
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return {'status': 'deleted'}
```

An attacker can call this endpoint directly, bypassing frontend role checks.

**Secure approach**:
```python
# SECURE: Backend authorization check
from functools import wraps

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/admin/users', methods=['DELETE'])
@require_role('admin')
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return {'status': 'deleted'}
```

#### Insecure Direct Object References (IDOR)

**Risk**: Application uses user-supplied input directly to access objects without proper authorization.

**Example failure**:
```python
# INSECURE: Direct use of user input
@app.route('/documents/<doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    return render_template('document.html', doc=document)
```

**Secure approach**:
```python
# SECURE: Verify user has access
@app.route('/documents/<doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    
    # Check if user has access to this document
    if document.owner_id != current_user.id and \
       current_user.id not in [s.user_id for s in document.shared_with]:
        abort(403)
    
    return render_template('document.html', doc=document)
```

#### Missing Authorization Checks

**Risk**: Sensitive operations lack authorization checks entirely.

**Example failure**:
```python
# INSECURE: No authorization check
@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    settings = request.json
    current_user.email = settings['email']
    current_user.role = settings['role']  # User can set their own role!
    db.session.commit()
    return {'status': 'updated'}
```

**Secure approach**:
```python
# SECURE: Separate endpoints with proper authorization
@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    settings = request.json
    # Only allow user to update their own email
    current_user.email = settings['email']
    db.session.commit()
    return {'status': 'updated'}

@app.route('/api/admin/users/<user_id>/role', methods=['POST'])
@require_role('admin')
def update_user_role(user_id):
    user = User.query.get(user_id)
    user.role = request.json['role']
    db.session.commit()
    return {'status': 'updated'}
```

---

## Developer Lens

### Implementing Authentication

#### Password-Based Authentication

When implementing password-based authentication, follow these principles:

1. **Hash passwords with a strong algorithm**: Use bcrypt, scrypt, or Argon2 with appropriate cost factors
2. **Never store plaintext passwords**: Hash passwords before storing
3. **Use unique salts**: Modern algorithms (bcrypt, Argon2) handle this automatically
4. **Implement rate limiting**: Prevent brute force attacks
5. **Require strong passwords**: Enforce minimum length and complexity
6. **Implement account lockout**: Temporarily lock accounts after failed attempts
7. **Log authentication events**: Track successful and failed login attempts

**Implementation example** (Python with Flask and bcrypt):

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuthLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event = db.Column(db.String(50))  # 'login_success', 'login_failure', 'account_locked'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

def hash_password(password):
    """Hash password using bcrypt with cost factor 12"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate input
    if not username or not password:
        return {'error': 'Username and password required'}, 400
    
    if len(password) < 12:
        return {'error': 'Password must be at least 12 characters'}, 400
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        return {'error': 'Username already exists'}, 409
    
    # Create user with hashed password
    user = User(
        username=username,
        password_hash=hash_password(password)
    )
    db.session.add(user)
    db.session.commit()
    
    return {'status': 'User created successfully'}, 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    client_ip = request.remote_addr
    
    user = User.query.filter_by(username=username).first()
    
    # Check if account is locked
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        AuthLog.create(user.id, 'login_attempt_locked', client_ip)
        return {'error': 'Account is locked. Try again later.'}, 429
    
    # Verify credentials
    if not user or not verify_password(password, user.password_hash):
        # Log failed attempt
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                AuthLog.create(user.id, 'account_locked', client_ip)
            else:
                AuthLog.create(user.id, 'login_failure', client_ip)
            db.session.commit()
        
        return {'error': 'Invalid credentials'}, 401
    
    # Reset failed attempts on successful login
    user.failed_attempts = 0
    user.locked_until = None
    AuthLog.create(user.id, 'login_success', client_ip)
    db.session.commit()
    
    # Generate session token (simplified; use proper JWT in production)
    session_token = generate_secure_token()
    
    return {
        'status': 'Login successful',
        'token': session_token,
        'user_id': user.id
    }, 200
```

#### Multi-Factor Authentication (MFA)

MFA significantly reduces the risk of account compromise. Implement MFA using:

- **Time-based One-Time Password (TOTP)**: User scans QR code with authenticator app (Google Authenticator, Authy)
- **SMS-based OTP**: Code sent via SMS (less secure than TOTP, but better than nothing)
- **Hardware security keys**: FIDO2/WebAuthn (most secure)

**TOTP implementation example**:

```python
import pyotp
import qrcode
from io import BytesIO
import base64

class User(db.Model):
    # ... existing fields ...
    mfa_secret = db.Column(db.String(32), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)

@app.route('/api/auth/mfa/setup', methods=['POST'])
def setup_mfa():
    """Generate MFA secret and QR code"""
    user = current_user
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    qr = qrcode.QRCode()
    qr.add_data(totp.provisioning_uri(name=user.username, issuer_name='MyApp'))
    qr.make()
    
    img = qr.make_image()
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Store secret temporarily (not yet enabled)
    user.mfa_secret = secret
    db.session.commit()
    
    return {
        'qr_code': qr_code_base64,
        'secret': secret  # For manual entry if QR fails
    },

# Pentest Lens

## Authentication Testing

### Credential Validation Weaknesses

Penetration testers should verify that authentication mechanisms properly validate credentials and resist common attacks.

**Test cases:**

- **Weak password policies**: Attempt to register accounts with passwords like "123456", "password", or single characters. Verify minimum length (12+ characters), complexity requirements, and dictionary checks.
- **Credential stuffing**: Use lists of known compromised credentials (from public breaches) against login endpoints. Check for rate limiting, account lockout, and CAPTCHA challenges.
- **Brute force attacks**: Attempt multiple login failures and verify that rate limiting, account lockout, or progressive delays are enforced. Test whether lockout is temporary or permanent.
- **Default credentials**: Check for hardcoded or default credentials in documentation, configuration files, or common accounts (admin/admin, test/test).
- **Password reset flaws**: Test password reset functionality for:
  - Predictable reset tokens
  - Tokens that don't expire
  - Ability to reset other users' passwords
  - Lack of email verification
  - Tokens sent in URLs (logged in browser history)

### Session Management Testing

**Test cases:**

- **Session fixation**: Obtain a session ID before authentication, authenticate, and verify whether the session ID changes. If it doesn't, the application is vulnerable.
- **Session timeout**: Verify that sessions expire after a reasonable period of inactivity. Test whether the application enforces logout on the server side.
- **Session token predictability**: Analyze session tokens for patterns or low entropy. Use tools like Burp Suite to test randomness.
- **Session cookie security**: Verify that session cookies have:
  - `HttpOnly` flag (prevents JavaScript access)
  - `Secure` flag (HTTPS only)
  - `SameSite` attribute (prevents CSRF)
  - Appropriate domain and path restrictions
- **Concurrent sessions**: Test whether users can have multiple active sessions simultaneously. Verify whether logging in from a new location invalidates previous sessions.

### Multi-Factor Authentication Testing

**Test cases:**

- **MFA bypass**: Attempt to access protected resources without completing MFA. Test whether the application enforces MFA before granting access.
- **OTP reuse**: Verify that one-time passwords cannot be reused. Test whether the same OTP can be used multiple times within its validity window.
- **OTP brute force**: Attempt to brute force OTP codes (typically 6 digits = 1 million combinations). Verify rate limiting and account lockout.
- **MFA recovery codes**: Test whether recovery codes are:
  - Securely generated and stored
  - Single-use
  - Properly validated
  - Not transmitted insecurely
- **MFA bypass via alternative methods**: Test whether users can bypass MFA by using alternative authentication methods (e.g., social login, passwordless authentication).

### Token-Based Authentication Testing

**Test cases:**

- **JWT signature validation**: Modify JWT claims (user ID, role, expiration) and verify whether the application rejects unsigned or incorrectly signed tokens. Test with `alg: none`.
- **Token expiration**: Verify that expired tokens are rejected. Test whether the application checks the `exp` claim.
- **Token revocation**: Revoke a token (logout) and verify that it cannot be used for subsequent requests. Test whether the application maintains a blacklist or checks token status.
- **Token storage**: Verify that tokens are not stored in localStorage (vulnerable to XSS). Check for secure, HttpOnly cookie storage.
- **Token leakage**: Test whether tokens are exposed in:
  - Browser history (avoid URL parameters)
  - Server logs
  - Error messages
  - Referer headers
- **Token refresh**: Verify that refresh tokens are:
  - Stored securely
  - Rotated on use
  - Properly validated
  - Not exposed to the frontend

## Authorization Testing

### Access Control Verification

**Test cases:**

- **Broken object-level authorization (BOLA)**: Authenticate as one user and attempt to access resources belonging to other users by modifying object IDs in requests. Examples:
  - Change `/api/users/123/profile` to `/api/users/124/profile`
  - Modify `/documents/doc-456` to `/documents/doc-789`
  - Test both GET (read) and POST/PUT (modify) operations
- **Horizontal privilege escalation**: Verify that users cannot access resources of other users at the same privilege level.
- **Vertical privilege escalation**: Attempt to access admin functions as a regular user. Test whether authorization checks are enforced on:
  - API endpoints
  - Business logic operations
  - Database queries
  - UI elements (note: UI hiding is not a security control)

### Role and Permission Testing

**Test cases:**

- **Role-based access control (RBAC) bypass**: Test whether users can:
  - Modify their own role in requests
  - Access endpoints restricted to higher roles
  - Perform actions that should require specific permissions
- **Permission inheritance**: Verify that permissions are correctly inherited and not overly permissive. Test whether child resources inherit parent permissions correctly.
- **Permission caching**: If permissions are cached, verify that cache invalidation works correctly. Test whether permission changes take effect immediately.
- **Missing authorization checks**: Identify endpoints that lack authorization checks entirely. Use automated tools to compare endpoints accessible to different user roles.

### Attribute-Based Access Control (ABAC) Testing

**Test cases:**

- **Attribute manipulation**: Attempt to modify user, resource, or environment attributes to gain unauthorized access. Examples:
  - Modify user attributes in JWT claims
  - Change resource ownership in requests
  - Spoof environment attributes (IP address, time, location)
- **Policy logic flaws**: Test edge cases in ABAC policies:
  - Conflicting rules
  - Overly permissive defaults
  - Incorrect boolean logic (AND vs OR)
  - Time-based access (test at boundary times)

### API Authorization Testing

**Test cases:**

- **Unauthenticated API access**: Verify that API endpoints require authentication. Test whether endpoints are accessible without tokens or credentials.
- **Missing authorization headers**: Test whether the application properly validates authorization headers. Attempt requests with:
  - Missing Authorization header
  - Invalid token format
  - Expired tokens
  - Tokens from other users
- **HTTP method override**: Test whether the application is vulnerable to HTTP method override attacks. Some frameworks allow overriding the HTTP method via headers like `X-HTTP-Method-Override` or `X-Method-Override`.
- **API versioning bypass**: If the application supports multiple API versions, test whether authorization is enforced consistently across versions.

### Data-Level Authorization Testing

**Test cases:**

- **Row-level security**: Verify that database queries properly filter results based on user permissions. Test whether users can access rows they shouldn't be able to see.
- **Column-level security**: Test whether sensitive columns are properly restricted. Verify that users cannot access sensitive fields (salary, SSN, etc.) they shouldn't see.
- **Bulk operations**: Test authorization on bulk operations (delete multiple records, export data). Verify that the application checks permissions for each record.

---

# Common Findings

## Authentication Findings

### CWE-256: Plaintext Storage of Password

**Severity**: Critical

**Description**: Passwords stored in plaintext or with weak hashing algorithms allow attackers to compromise accounts if the database is breached.

**Example**:
```python
# VULNERABLE
user.password = request.form['password']  # Stored as plaintext
db.session.commit()
```

**Impact**: Complete account compromise; attacker can log in as any user.

**Remediation**:
- Use bcrypt, scrypt, or Argon2 with appropriate cost factors
- Never store plaintext passwords
- Use unique salts (handled automatically by modern algorithms)
- Implement password hashing at the application layer before storage

### CWE-307: Improper Restriction of Rendered UI Layers or Frames

**Severity**: High

**Description**: Authentication checks are only performed on the frontend, allowing attackers to bypass them by calling APIs directly.

**Example**:
```javascript
// VULNERABLE: Only frontend check
if (user.role === 'admin') {
    showAdminPanel();
}
```

An attacker can call the admin API directly without the frontend check.

**Impact**: Unauthorized access to protected functionality.

**Remediation**:
- Enforce authentication and authorization on the backend for all API endpoints
- Never rely on frontend checks for security
- Implement server-side session validation
- Use middleware to enforce authentication before reaching route handlers

### CWE-384: Session Fixation

**Severity**: High

**Description**: Application reuses session IDs after authentication, allowing attackers to hijack sessions.

**Example**:
```python
# VULNERABLE: Session ID not regenerated after login
@app.route('/login', methods=['POST'])
def login():
    user = authenticate(request.form['username'], request.form['password'])
    session['user_id'] = user.id
    # Session ID remains the same!
    return redirect('/dashboard')
```

**Impact**: Session hijacking; attacker can impersonate authenticated users.

**Remediation**:
- Generate a new session ID after successful authentication
- Invalidate the pre-authentication session
- Use secure, cryptographically random session IDs
- Set secure cookie flags (HttpOnly, Secure, SameSite)

### CWE-521: Weak Password Requirements

**Severity**: Medium

**Description**: Application allows weak passwords that are easily guessed or cracked.

**Example**:
```python
# VULNERABLE: No password strength requirements
if len(password) >= 1:  # Any length is acceptable
    create_user(username, password)
```

**Impact**: Accounts compromised through password guessing or dictionary attacks.

**Remediation**:
- Enforce minimum password length (12+ characters)
- Require character diversity (uppercase, lowercase, numbers, symbols)
- Check against common password lists and user information
- Implement rate limiting on login attempts
- Require MFA for high-value accounts

### CWE-613: Insufficient Session Expiration

**Severity**: Medium

**Description**: Sessions remain valid for too long or don't expire at all, increasing the window for session hijacking.

**Example**:
```python
# VULNERABLE: Session expires after 1 year
SESSION_LIFETIME = 365 * 24 * 60 * 60  # 1 year
```

**Impact**: Extended window for session hijacking and unauthorized access.

**Remediation**:
- Set appropriate session timeout based on risk level (15-30 minutes for sensitive applications)
- Implement idle timeout (logout after inactivity)
- Implement absolute timeout (logout after maximum session duration)
- Provide logout functionality
- Invalidate sessions on the server side

### CWE-640: Weak Password Recovery Mechanism for Forgotten Password

**Severity**: High

**Description**: Password reset mechanism is vulnerable to attacks (predictable tokens, no email verification, tokens don't expire).

**Example**:
```python
# VULNERABLE: Predictable reset token
import time
reset_token = str(int(time.time()))  # Predictable!
```

**Impact**: Attackers can reset other users' passwords and take over accounts.

**Remediation**:
- Generate cryptographically random reset tokens
- Set short expiration times (15-30 minutes)
- Require email verification before allowing password reset
- Send reset links via email, not in responses
- Invalidate tokens after use
- Log password reset events

## Authorization Findings

### CWE-639: Authorization Bypass Through User-Controlled Key

**Severity**: Critical

**Description**: Application uses user-supplied input (user ID, account ID) directly to access resources without verifying ownership.

**Example**:
```python
# VULNERABLE: No authorization check
@app.route('/api/accounts/<account_id>/balance')
def get_balance(account_id):
    account = Account.query.get(account_id)
    return {'balance': account.balance}
```

User can request `/api/accounts/999/balance` and retrieve any account's balance.

**Impact**: Unauthorized access to sensitive data; users can view/modify other users' resources.

**Remediation**:
- Verify that the authenticated user owns or has access to the requested resource
- Use indirect references (UUIDs, opaque identifiers) instead of sequential IDs
- Implement consistent authorization checks on all endpoints
- Use middleware or decorators to enforce authorization

### CWE-276: Incorrect Default Permissions

**Severity**: High

**Description**: Resources are created with overly permissive default permissions, allowing unauthorized access.

**Example**:
```python
# VULNERABLE: New documents are world-readable by default
document = Document(title=title, content=content, is_public=True)
db.session.add(document)
db.session.commit()
```

**Impact**: Sensitive data exposed to unauthorized users.

**Remediation**:
- Default to restrictive permissions (private, owner-only access)
- Require explicit permission grants
- Implement principle of least privilege
- Regularly audit permissions for overly permissive settings

### CWE-269: Improper Access Control (Generic)

**Severity**: High

**Description**: Application lacks proper authorization checks for sensitive operations.

**Example**:
```python
# VULNERABLE: No authorization check on admin operation
@app.route('/api/admin/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return {'status': 'deleted'}
```

Any authenticated user can delete any other user.

**Impact**: Unauthorized modification or deletion of data; privilege escalation.

**Remediation**:
- Implement authorization checks for all sensitive operations
- Verify user role/permissions before allowing actions
- Use role-based or attribute-based access control
- Implement consistent authorization patterns across the application
- Log authorization failures for monitoring

### CWE-434: Unrestricted Upload of File with Dangerous Type

**Severity**: High

**Description**: Application allows users to upload files without proper authorization or validation, potentially leading to code execution.

**Example**:
```python
# VULNERABLE: No file type validation or authorization check
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(f'/uploads/{file.filename}')
    return {'status': 'uploaded'}
```

**Impact**: Arbitrary file upload; potential code execution; malware distribution.

**Remediation**:
- Validate file types (whitelist allowed extensions)
- Check MIME types (verify actual file type, not just extension)
- Store uploads outside web root
- Implement authorization checks (verify user can upload)
- Scan uploads for malware
- Rename files to prevent path traversal

### CWE-862: Missing Authorization

**Severity**: Critical

**Description**: Application performs sensitive operations without checking whether the user has permission.

**Example**:
```python
# VULNERABLE: No authorization check
@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    settings = request.json
    current_user.role = settings['role']  # User can set their own role!
    db.session.commit()
    return {'status': 'updated'}
```

**Impact**: Privilege escalation; unauthorized data modification.

**Remediation**:
- Implement authorization checks for all sensitive operations
- Separate endpoints for different privilege levels
- Use role-based or attribute-based access control
- Implement consistent authorization patterns
- Test authorization on all endpoints

---

# Secure Design Guidance

## Authentication Design Principles

### 1. Defense in Depth for Authentication

Implement multiple layers of authentication controls to reduce the impact of any single failure.

**Design approach**:
- **Layer 1 - Credential strength**: Enforce strong password policies; support passphrases
- **Layer 2 - Credential protection**: Hash passwords with strong algorithms; protect against credential stuffing
- **Layer 3 - Multi-factor authentication**: Require MFA for sensitive accounts or operations
- **Layer 4 - Session security**: Implement secure session management with proper timeout and invalidation
- **Layer 5 - Monitoring**: Log authentication events and alert on suspicious patterns

**Example architecture**:
```
User Input
    ↓
[Password Strength Check]
    ↓
[Rate Limiting & Account Lockout]
    ↓
[Credential Verification]
    ↓
[MFA Challenge]
    ↓
[Session Creation]
    ↓
[Continuous Monitoring]
```

### 2. Secure Password Handling

**Principles**:
- Never store plaintext passwords
- Use strong hashing algorithms with appropriate cost factors
- Implement rate limiting to prevent brute force attacks
- Enforce strong password policies
- Support password managers

**Implementation checklist**:
- [ ] Use bcrypt (cost factor 12+), scrypt, or Argon2
- [ ] Generate unique salts (handled by modern algorithms)
- [ ] Implement account lockout after 5 failed attempts (15-30 minute lockout)
- [ ] Require minimum 12-character passwords
- [ ] Check against common password lists
- [ ] Implement password reset with secure tokens
- [ ] Log authentication events
- [ ] Monitor for credential stuffing attacks

### 3. Multi-Factor Authentication Strategy

**MFA implementation hierarchy** (from most to least secure):
1. **Hardware security keys (FIDO2/WebAuthn)**: Most secure; resistant to phishing
2. **Time-based one-time passwords (TOTP)**: Secure; requires authenticator app
3. **SMS-based OTP**: Less secure; vulnerable to SIM swapping
4. **Email-based OTP**: Convenient; vulnerable to email compromise

**Design guidance**:
- Make MFA mandatory for privileged accounts (admins, service accounts)
- Make MFA optional but encouraged for regular users
- Provide recovery codes for account recovery
- Implement MFA for sensitive operations (password change, permission changes)
- Test MFA bypass vectors (alternative authentication methods, recovery codes)

### 4. Session Management Design

**Secure session design**:
- Generate cryptographically random session IDs (minimum 128 bits of entropy)
- Regenerate session ID after authentication
- Implement idle timeout (15-30 minutes for sensitive applications)
- Implement absolute timeout (maximum session duration)
- Invalidate sessions on logout
- Store sessions securely (server-side, not in cookies)
- Use secure cookie flags (HttpOnly, Secure, SameSite)

**Session storage options**:
- **Server-side sessions**: More secure; requires session storage (Redis, database)
- **Stateless tokens (JWT)**: Scalable; requires careful token validation and revocation

### 5. Token-Based Authentication Design

If using tokens (JWT, OAuth), follow these principles:

**Token design**:
- Use short expiration times for access tokens (15-60 minutes)
- Implement refresh tokens with longer expiration (days/weeks)
- Rotate refresh tokens on use
- Sign tokens with strong algorithms (RS256, not HS256 for multi-service architectures)
- Include minimal claims (user ID, roles, expiration)
- Never include sensitive data in tokens

**Token validation**:
- Validate signature on every request
- Check expiration time
- Verify token hasn't been revoked
- Validate token format and claims
- Implement token blacklist for revocation

**Token storage**:
- Store in secure, HttpOnly cookies (not localStorage)
- Transmit only over HTTPS
- Avoid including tokens in URLs
- Implement CSRF protection for token-based authentication

## Authorization Design Principles

### 1. Principle of Least Privilege

Users should have the minimum permissions necessary to perform their job.

**Design approach**:
- Default to deny (deny all access unless explicitly granted)
- Grant permissions explicitly and specifically
- Regularly audit and remove unnecessary permissions
- Implement role-based access control (RBAC) for simplicity
- Implement attribute-based access control (ABAC) for complex scenarios

**Example**:
```python
# SECURE: Explicit permission grants
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    role = db.Column(db.String(20))  # 'viewer', 'editor', 'admin'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shared_with = db.relationship('User', secondary='document_shares')

def can_view_document(user, document):
    """Check if user can view document"""
    return (user.id == document.owner_id or 
            user in document.shared_with or
            user.role == 'admin')

def can_edit_document(user, document):
    """Check if user can edit document"""
    return (user

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
