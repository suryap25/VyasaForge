---
chapter: 11
stage: final
source: drafts
generated_by: appsec-handbook-agent
---

# Chapter 11: Security Best Practices and Threat Mitigation

## Learning Objectives

After completing this chapter, you will be able to:

- Understand the foundational principles of security best practices within authentication and authorization systems
- Identify and categorize common threats to authentication and authorization mechanisms
- Apply defense-in-depth strategies to mitigate authentication and authorization risks
- Design and implement secure authentication and authorization architectures
- Conduct threat modeling and risk assessment for identity systems
- Evaluate and test authentication and authorization controls for vulnerabilities
- Recognize common implementation failures and their remediation strategies
- Implement monitoring and incident response procedures for authentication and authorization events
- Make informed decisions about security controls based on risk assessment and threat landscape

## Conceptual Foundation

Security best practices and threat mitigation in the context of authentication and authorization represent a comprehensive approach to protecting identity systems from exploitation, compromise, and misuse. Unlike point solutions that address single vulnerabilities, best practices encompass systematic, layered defenses that reduce risk across the entire identity lifecycle.

**Core Principles**

The foundation of effective security practices rests on several core principles:

**Defense in Depth** means implementing multiple layers of security controls so that if one layer fails, others remain effective. In authentication systems, this translates to combining something you know (password), something you have (hardware token), and something you are (biometric). No single control is trusted completely; each layer validates and reinforces the others.

**Least Privilege** ensures that users, applications, and services receive only the minimum permissions necessary to perform their functions. This principle applies equally to authentication (minimal credential exposure) and authorization (minimal permission grants). When a user account is compromised, the damage is limited to the scope of that account's permissions.

**Fail Secure** dictates that when security controls fail or are bypassed, the system defaults to a secure state rather than an open one. A failed authentication check should deny access, not grant it. A misconfigured authorization policy should restrict access, not permit it.

**Zero Trust** represents a modern evolution of security thinking: never trust, always verify. Every access request—whether from an internal user, external partner, or service-to-service communication—must be authenticated and authorized, regardless of network location or previous trust decisions.

**Threat Categories**

Understanding threat categories helps organize mitigation strategies:

**Credential-Based Threats** involve stealing, guessing, or reusing credentials. Password spraying, credential stuffing, and phishing attacks fall into this category. Mitigation focuses on credential strength, protection, and detection of abnormal usage patterns.

**Session-Based Threats** exploit active sessions after authentication succeeds. Session fixation, session hijacking, and cross-site request forgery (CSRF) attacks target the authenticated state. Mitigation involves secure session management, token binding, and request validation.

**Authorization Bypass Threats** circumvent access controls to access resources without proper permissions. Insecure direct object references (IDOR), privilege escalation, and policy confusion attacks fall here. Mitigation requires consistent authorization checks and proper policy design.

**Infrastructure Threats** target the systems that manage authentication and authorization. Man-in-the-middle (MITM) attacks, DNS spoofing, and compromised identity providers represent infrastructure-level risks. Mitigation involves encryption, certificate validation, and secure communication channels.

**Insider Threats** involve malicious or negligent actions by authorized users. Excessive privilege usage, credential sharing, and policy violations represent insider risks. Mitigation includes monitoring, audit logging, and access reviews.

## Architecture Perspective

Effective security best practices require architectural decisions that embed security into system design rather than bolting it on afterward.

**Centralized Identity Management**

Modern applications benefit from centralized identity management rather than distributed, per-application credential stores. A centralized identity provider (IdP) serves as the single source of truth for user identity and attributes. This architecture provides several advantages:

- **Consistent Policy Enforcement**: Security policies are defined once and applied uniformly across all applications
- **Simplified Credential Management**: Users manage credentials in one place; administrators enforce password policies centrally
- **Audit Trail Consolidation**: All authentication events flow through a single system, enabling comprehensive logging and analysis
- **Rapid Incident Response**: Compromised credentials can be revoked immediately across all dependent applications

However, centralized systems introduce single points of failure. Architectural resilience requires:

- **High Availability**: The IdP must be deployed with redundancy, failover capabilities, and geographic distribution
- **Graceful Degradation**: Applications must handle IdP unavailability without completely denying access to legitimate users
- **Offline Capability**: Critical systems should maintain local credential caches or alternative authentication mechanisms for IdP outages

**Layered Authorization Architecture**

Authorization decisions should be distributed across multiple layers, each with specific responsibilities:

**Network Layer** controls which systems can communicate. Firewalls, network segmentation, and VPNs restrict access at the infrastructure level. This layer cannot authenticate users but can enforce network-level policies.

**Application Layer** enforces business logic authorization. After authentication succeeds, the application verifies that the user has permission to perform the requested action on the requested resource. This is where most authorization logic resides.

**Data Layer** enforces data-level access controls. Database row-level security, encryption, and field-level masking ensure that even if an attacker bypasses application-layer controls, sensitive data remains protected.

**API Layer** enforces authorization for service-to-service communication. API keys, OAuth tokens, and mutual TLS ensure that only authorized services can invoke APIs.

Each layer operates independently; compromise of one layer does not automatically compromise others.

**Token-Based Architecture**

Modern distributed systems increasingly use token-based authentication rather than session-based approaches. Tokens (such as JWTs) contain claims about the user and can be validated without contacting a central authority on every request.

Token-based architecture provides:

- **Scalability**: Stateless validation eliminates the need for session storage and replication
- **Microservices Compatibility**: Tokens can be passed between services without shared session state
- **Mobile Friendliness**: Tokens work naturally with mobile applications and single-page applications (SPAs)

However, tokens introduce new risks:

- **Token Leakage**: Tokens in URLs, logs, or error messages expose credentials
- **Token Expiration**: Long-lived tokens increase the window of vulnerability if compromised
- **Revocation Challenges**: Revoking a token before expiration requires maintaining a revocation list or blacklist
- **Token Binding**: Tokens can be stolen and used by attackers if not bound to the original requester

Secure token architecture requires careful attention to token generation, storage, transmission, validation, and revocation.

## AppSec Lens

From an application security perspective, authentication and authorization failures represent critical vulnerabilities that enable attackers to impersonate legitimate users or access unauthorized resources.

**OWASP Top 10 Alignment**

The OWASP Top 10 identifies broken authentication and broken access control as among the most critical web application security risks. These categories encompass:

- Weak password policies and credential management
- Inadequate session management
- Missing or ineffective authorization checks
- Privilege escalation vulnerabilities
- Insecure direct object references (IDOR)
- Horizontal and vertical privilege escalation

**Risk Assessment Framework**

Effective AppSec programs assess authentication and authorization risks using a structured framework:

**Threat Identification** catalogs potential threats specific to the application. What are the high-value assets? Who are the threat actors? What attack vectors are most likely? For a financial application, credential compromise and unauthorized fund transfers represent high-impact threats. For a healthcare application, unauthorized access to patient records represents a critical threat.

**Vulnerability Assessment** identifies weaknesses in current controls. Penetration testing, code review, and architecture analysis reveal gaps. Common gaps include missing authorization checks, weak password policies, and inadequate session management.

**Impact Analysis** quantifies the business impact of successful attacks. How many users would be affected? What financial loss would result? What regulatory penalties apply? Impact analysis helps prioritize remediation efforts.

**Likelihood Assessment** estimates the probability of successful exploitation. How difficult is the attack? How many attackers have the capability? How easily can the vulnerability be discovered? Likelihood assessment helps distinguish between theoretical risks and practical threats.

**Risk Scoring** combines impact and likelihood to produce risk scores that guide remediation prioritization. High-impact, high-likelihood risks receive immediate attention. Low-impact, low-likelihood risks may be accepted or deferred.

**Secure Code Review Focus Areas**

Code review for authentication and authorization should focus on:

- **Credential Handling**: Are credentials stored securely? Are they transmitted over encrypted channels? Are they logged or exposed in error messages?
- **Authentication Logic**: Is authentication enforced on all protected endpoints? Are there bypass conditions? Is the authentication mechanism cryptographically sound?
- **Authorization Logic**: Is authorization checked before sensitive operations? Are checks consistent across the codebase? Can authorization be bypassed through parameter manipulation?
- **Session Management**: Are sessions created securely? Are session tokens unpredictable? Are sessions invalidated on logout? Are sessions protected from fixation and hijacking?
- **Token Handling**: Are tokens validated on every request? Are token signatures verified? Are token expiration times appropriate? Are revoked tokens rejected?

## Developer Lens

Developers implementing authentication and authorization systems must balance security with usability and performance. This section provides practical guidance for secure implementation.

**Password Management Best Practices**

Passwords remain the most common authentication mechanism despite their limitations. Secure password handling requires:

**Hashing, Not Encryption**: Passwords must be hashed, not encrypted. Hashing is one-way; even if an attacker obtains the hash, they cannot recover the original password. Use modern hashing algorithms like bcrypt, scrypt, or Argon2 with appropriate work factors. Never use MD5, SHA-1, or unsalted hashing.

```python
### Secure password hashing with bcrypt
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with appropriate work factor."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

### Usage
user_password = "SecureP@ssw0rd123"
stored_hash = hash_password(user_password)
is_valid = verify_password(user_password, stored_hash)
```

**Salting**: Each password must be salted with a unique, random value. Salting prevents rainbow table attacks and ensures that identical passwords produce different hashes. Modern hashing libraries like bcrypt handle salting automatically.

**Work Factor**: Hashing algorithms should include a configurable work factor (rounds, cost, or iterations) that makes hashing computationally expensive. This slows down brute-force attacks. As computational power increases, the work factor should be increased. A work factor that takes 100ms to compute is appropriate for interactive authentication.

**Password Policy**: Enforce password policies that balance security and usability:

- Minimum length of 12-16 characters (longer is better than complex)
- No arbitrary complexity requirements (uppercase, numbers, symbols) unless mandated by compliance
- Prohibition of common passwords using a password dictionary
- Prevention of password reuse (last 5-10 passwords)
- Expiration policies only if required by compliance; regular expiration encourages weak passwords

**Secure Session Management**

Sessions represent the authenticated state after successful authentication. Secure session management requires:

**Unpredictable Session Tokens**: Session identifiers must be cryptographically random and unpredictable. Use a cryptographically secure random number generator with sufficient entropy (at least 128 bits). Never use sequential, timestamp-based, or user-derived session identifiers.

```python
### Secure session token generation
import secrets
import hashlib

def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    random_bytes = secrets.token_bytes(32)  # 256 bits of entropy
    token = secrets.token_urlsafe(32)  # URL-safe base64 encoding
    return token

def hash_session_token(token: str) -> str:
    """Hash a session token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()

### Usage
session_token = generate_session_token()
stored_hash = hash_session_token(session_token)
```

**Secure Transmission**: Session tokens must be transmitted over encrypted channels (HTTPS/TLS). Tokens should be stored in HTTP-only, Secure cookies that cannot be accessed by JavaScript and are only transmitted over HTTPS.

```python
### Secure session cookie in Flask
from flask import Flask, session
from datetime import timedelta

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,      # Only transmit over HTTPS
    SESSION_COOKIE_HTTPONLY=True,    # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE='Strict', # Prevent CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)
```

**Appropriate Expiration**: Sessions should expire after a period of inactivity (15-30 minutes for sensitive applications, longer for low-risk applications). Absolute session lifetime (regardless of activity) should be enforced for high-risk operations.

**Logout Implementation**: Logout must invalidate the session on the server side. Simply deleting the client-side cookie is insufficient; an attacker with the session token can still use it. Maintain a session revocation list or use a session store that can be queried to verify session validity.

**CSRF Protection**: Protect against cross-site request forgery by implementing the synchronizer token pattern. Generate a unique, unpredictable token for each form or state-changing request. Verify the token on the server before processing the request.

```python
### CSRF token implementation
import secrets
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/transfer', methods=['GET'])
def transfer_form():
    csrf_token = secrets.token_urlsafe(32)
    # Store token in session for validation
    session['csrf_token'] = csrf_token
    return render_template('transfer.html', csrf_token=csrf_token)

@app.route('/transfer', methods=['POST'])
def process_transfer():
    # Verify CSRF token before processing
    if request.form.get('csrf_token') != session.get('csrf_token'):
        return "CSRF token validation failed", 403
    
    # Process the transfer
    return "Transfer successful"
```

**Authorization Implementation**

Authorization checks must be consistent, comprehensive, and enforced at multiple layers:

**Centralized Authorization Logic**: Implement authorization logic in a centralized location (middleware, decorator, or service) rather than scattered throughout the codebase. This ensures consistency and simplifies auditing.

```python
### Centralized authorization decorator
from functools import wraps
from flask import request, abort

def require_permission(permission: str):
    """Decorator to enforce permission requirements."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or not user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/users', methods=['GET'])
@require_permission('admin.users.read')
def list_users():
    return get_all_users()

@app.route('/admin/users/<user_id>', methods=['DELETE'])
@require_permission('admin.users.delete')
def delete_user(user_id):
    return delete_user_by_id(user_id)
```

**Resource-Level Authorization**: Authorization must be checked for each specific resource, not just endpoints. Verify that the user has permission to access the specific resource being requested, not just the resource type.

```python
### Resource-level authorization
@app.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    user = get_current_user()
    document = Document.query.get(doc_id)
    
    if not document:
        abort(404)
    
    # Check if user has permission to access THIS document
    if not user.can_access(document):
        abort(403)
    
    return document.to_json()
```

**Deny by Default**: Authorization should follow a deny-by-default approach. If a permission is not explicitly granted, it should be denied. Avoid whitelisting approaches that grant permissions by default.

**Regular Authorization Audits**: Periodically review user permissions to ensure they remain appropriate. Users change roles, projects end, and permissions should be revoked accordingly. Implement access reviews where managers confirm that their team members have appropriate permissions.

## Pentest Lens

Penetration testers and security researchers assess authentication and authorization controls through systematic testing and exploitation techniques.

**Authentication Testing Methodology**

**Credential Enumeration**: Determine which usernames or email addresses are valid. Many systems leak this information through error messages ("User not found" vs. "Invalid password"), timing differences, or account recovery mechanisms.

```
Testing approach:
1. Attempt login with known valid username
2. Attempt login with invalid username
3. Compare error messages, response times, and HTTP status codes
4. Attempt password reset with valid and invalid usernames
5. Document any information leakage
```

**Weak Credential Testing**: Test for weak or default credentials:

- Default credentials (admin/admin, admin/password)
- Weak password policies (short passwords, no complexity requirements)
- Common passwords (password, 123456, qwerty)
- Credentials related to the organization (company name, product name)

**Session Management Testing**: Examine session handling for vulnerabilities:

- **Session Fixation**: Determine if an attacker can set a user's session token. Attempt to use a known session token after the user authenticates.
- **Session Prediction**: Analyze session tokens for patterns. Are they sequential? Timestamp-based? Predictable?
- **Session Hijacking**: Attempt to use captured or guessed session tokens. Can an attacker use a valid session token to impersonate a user?
- **Session Timeout**: Verify that sessions expire appropriately. Can an attacker use an old session token?

**Multi-Factor Authentication Testing**: If MFA is implemented, test for bypasses:

- Can MFA be disabled or skipped?
- Can MFA codes be reused?
- Are MFA codes transmitted securely?
- Can MFA be bypassed through alternative authentication methods?
- Are backup codes stored securely?

**Authorization Testing Methodology**

**Horizontal Privilege Escalation**: Attempt to access resources belonging to other users at the same privilege level:

```
Testing approach:
1. Authenticate as User A
2. Identify resource identifiers (user IDs, document IDs, etc.)
3. Attempt to access resources belonging to User B by modifying identifiers
4. Test both direct object references (URLs, API parameters) and indirect references
5. Document any successful unauthorized access
```

**Vertical Privilege Escalation**: Attempt to access resources or functions requiring higher privileges:

```
Testing approach:
1. Authenticate as a low-privilege user
2. Identify high-privilege functions (admin panels, sensitive operations)
3. Attempt to access these functions directly via URL or API
4. Attempt to modify parameters to escalate privileges
5. Test for missing authorization checks on sensitive operations
```

**Insecure Direct Object Reference (IDOR) Testing**: Test for authorization bypass through object reference manipulation:

```
Example vulnerable API:
GET /api/users/123/profile

Testing:
1. Authenticate as User A (ID 123)
2. Modify the ID parameter to access other users: /api/users/124/profile
3. If User A can access User B's profile, IDOR vulnerability exists
4. Test with sequential IDs, UUIDs, and other identifier formats
5. Test across different endpoints and HTTP methods
```

**Authorization Policy Testing**: Examine authorization policies for logical flaws:

- Can permissions be combined to achieve unintended access?
- Are there race conditions in permission checks?
- Can permissions be bypassed through parameter manipulation?
- Are there inconsistencies between different authorization checks?

## Common Findings

**Finding 1: Missing Authorization Checks**

**Description**: Authorization checks are not performed before sensitive operations, allowing users to access resources or perform actions without proper permissions.

**Example**: A banking application allows users to view their account balance through `/api/accounts/123/balance`. The application verifies that the user is authenticated but fails to verify that the user owns account 123. An attacker can access any account balance by modifying the account ID.

**Impact**: Unauthorized access to sensitive data or functionality. In the banking example, an attacker could view all customer account balances.

**Remediation**:

```python
### Vulnerable code
@app.route('/api/accounts/<account_id>/balance', methods=['GET'])
def get_balance(account_id):
    user = get_current_user()
    if not user:
        abort(401)
    # Missing authorization check!
    account = Account.query.get(account_id)
    return {'balance': account.balance}

### Secure code
```

## Secure Design Guidance

### Authentication Architecture Patterns

**Stateless Token-Based Authentication**

Design authentication systems using stateless tokens (JWT, OAuth 2.0) rather than server-side sessions when building distributed or microservices architectures. Stateless tokens eliminate session replication complexity and enable horizontal scaling.

Key design considerations:

- **Token Structure**: Include minimal claims (user ID, roles, expiration). Avoid storing sensitive data in tokens; they can be decoded by anyone.
- **Signature Verification**: Always verify token signatures using the issuer's public key. Never trust unsigned tokens.
- **Expiration Strategy**: Use short-lived access tokens (15-60 minutes) with longer-lived refresh tokens (days/weeks) for token rotation. This limits exposure if an access token is compromised.
- **Token Revocation**: Implement a revocation mechanism for scenarios requiring immediate invalidation (logout, permission changes, security incidents). Use a blacklist for short-lived tokens or a whitelist for long-lived tokens.

```python
### Secure JWT implementation with expiration and refresh tokens
from datetime import datetime, timedelta
import jwt
from functools import wraps
from flask import request, abort, jsonify

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_tokens(user_id: str, roles: list) -> dict:
    """Create access and refresh tokens."""
    now = datetime.utcnow()
    
    access_payload = {
        'user_id': user_id,
        'roles': roles,
        'type': 'access',
        'exp': now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': now
    }
    
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': now
    }
    
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode a token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise jwt.InvalidTokenError("Invalid token type")
        
        # Check revocation list (implement based on your needs)
        if is_token_revoked(token):
            raise jwt.InvalidTokenError("Token has been revoked")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

def require_auth(f):
    """Decorator to require valid authentication token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            abort(401)
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                abort(401)
            
            payload = verify_token(token, token_type='access')
            request.user_id = payload['user_id']
            request.user_roles = payload.get('roles', [])
            
        except (ValueError, jwt.InvalidTokenError):
            abort(401)
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/api/refresh', methods=['POST'])
def refresh_access_token():
    """Endpoint to refresh access token using refresh token."""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({'error': 'Missing refresh token'}), 401
    
    try:
        scheme, token = auth_header.split()
        payload = verify_token(token, token_type='refresh')
        
        new_tokens = create_tokens(payload['user_id'], payload.get('roles', []))
        return jsonify(new_tokens), 200
        
    except (ValueError, jwt.InvalidTokenError) as e:
        return jsonify({'error': 'Invalid refresh token'}), 401
```

**Multi-Factor Authentication Integration**

Design MFA as a mandatory security layer for high-risk operations and privileged accounts. Implement MFA at the authentication layer, not as an afterthought.

Design principles:

- **Multiple Methods**: Support multiple MFA methods (TOTP, SMS, push notifications, hardware keys) to accommodate different user preferences and security requirements.
- **Backup Codes**: Provide backup codes for account recovery when primary MFA methods are unavailable. Store backup codes securely (hashed, rate-limited).
- **Graceful Degradation**: If MFA is temporarily unavailable, implement a secure fallback (security questions, email verification) rather than disabling MFA entirely.
- **MFA Enforcement**: Enforce MFA for all users, not just administrators. Phased rollout can begin with high-risk users.

```python
### MFA implementation with TOTP and backup codes
import pyotp
import secrets
from datetime import datetime, timedelta

class MFAManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def setup_totp(self) -> dict:
        """Generate TOTP secret for user."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        return {
            'secret': secret,
            'provisioning_uri': totp.provisioning_uri(
                name=self.user_id,
                issuer_name='YourApp'
            ),
            'backup_codes': self.generate_backup_codes()
        }
    
    def generate_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes for account recovery."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # 8-character hex code
            # Store hashed version in database
            hashed = hash_backup_code(code)
            codes.append(code)
        
        return codes
    
    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code with time window tolerance."""
        totp = pyotp.TOTP(secret)
        
        # Allow codes from current and previous time windows
        # to account for clock skew
        return totp.verify(code, valid_window=1)
    
    def verify_backup_code(self, code: str) -> bool:
        """Verify and consume a backup code."""
        # Retrieve user's backup codes from database
        user_codes = get_user_backup_codes(self.user_id)
        
        for stored_hash in user_codes:
            if verify_backup_code_hash(code, stored_hash):
                # Remove used backup code
                remove_backup_code(self.user_id, stored_hash)
                return True
        
        return False

@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint with MFA support."""
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Verify credentials
    user = authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if MFA is enabled
    if user.mfa_enabled:
        # Generate temporary session for MFA verification
        temp_session = create_temporary_session(user.id, expires_in=300)
        
        return jsonify({
            'status': 'mfa_required',
            'temp_session': temp_session,
            'mfa_methods': user.get_enabled_mfa_methods()
        }), 202
    
    # MFA not required, issue tokens
    tokens = create_tokens(user.id, user.roles)
    return jsonify(tokens), 200

@app.route('/api/mfa/verify', methods=['POST'])
def verify_mfa():
    """Verify MFA code and complete authentication."""
    temp_session = request.json.get('temp_session')
    mfa_code = request.json.get('code')
    method = request.json.get('method', 'totp')
    
    # Validate temporary session
    session_data = validate_temporary_session(temp_session)
    if not session_data:
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    user_id = session_data['user_id']
    user = User.query.get(user_id)
    
    mfa_manager = MFAManager(user_id)
    
    # Verify MFA code based on method
    if method == 'totp':
        if not mfa_manager.verify_totp(user.totp_secret, mfa_code):
            return jsonify({'error': 'Invalid MFA code'}), 401
    
    elif method == 'backup':
        if not mfa_manager.verify_backup_code(mfa_code):
            return jsonify({'error': 'Invalid backup code'}), 401
    
    else:
        return jsonify({'error': 'Unsupported MFA method'}), 400
    
    # MFA verified, issue tokens
    tokens = create_tokens(user_id, user.roles)
    
    # Invalidate temporary session
    invalidate_temporary_session(temp_session)
    
    return jsonify(tokens), 200
```

**Role-Based Access Control (RBAC) Design**

Design authorization systems using role-based access control with clear role definitions and permission mappings. RBAC simplifies permission management at scale.

Design principles:

- **Role Hierarchy**: Define roles in a hierarchy (Admin > Manager > User) to reduce permission duplication and simplify management.
- **Permission Granularity**: Define permissions at an appropriate granularity level. Too coarse (read/write) loses expressiveness; too fine (read_user_profile_first_name) becomes unmanageable.
- **Separation of Duties**: Design roles to enforce separation of duties. No single role should have all permissions for sensitive operations (e.g., request and approve payments).
- **Dynamic Role Assignment**: Support dynamic role assignment based on context (time-based, location-based, project-based) for fine-grained control.

```python
### RBAC implementation with role hierarchy and permissions
from enum import Enum
from typing import Set

class Permission(Enum):
    """Define all system permissions."""
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    REPORT_APPROVE = "report:approve"
    ADMIN_ACCESS = "admin:access"

class Role:
    """Define roles with associated permissions."""
    def __init__(self, name: str, permissions: Set[Permission], parent_role=None):
        self.name = name
        self.permissions = permissions
        self.parent_role = parent_role
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission (including inherited)."""
        if permission in self.permissions:
            return True
        
        if self.parent_role:
            return self.parent_role.has_permission(permission)
        
        return False
    
    def get_all_permissions(self) -> Set[Permission]:
        """Get all permissions including inherited."""
        all_perms = self.permissions.copy()
        
        if self.parent_role:
            all_perms.update(self.parent_role.get_all_permissions())
        
        return all_perms

### Define role hierarchy
admin_role = Role(
    name="Admin",
    permissions={
        Permission.USER_READ, Permission.USER_CREATE,
        Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.REPORT_READ, Permission.REPORT_CREATE,
        Permission.REPORT_APPROVE, Permission.ADMIN_ACCESS
    }
)

manager_role = Role(
    name="Manager",
    permissions={
        Permission.USER_READ, Permission.REPORT_READ,
        Permission.REPORT_CREATE, Permission.REPORT_APPROVE
    },
    parent_role=admin_role  # Inherits from admin
)

user_role = Role(
    name="User",
    permissions={
        Permission.USER_READ, Permission.REPORT_READ,
        Permission.REPORT_CREATE
    },
    parent_role=manager_role  # Inherits from manager
)

class AuthorizationService:
    """Centralized authorization service."""
    
    def __init__(self):
        self.roles = {
            'admin': admin_role,
            'manager': manager_role,
            'user': user_role
        }
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission."""
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        # Get user's roles
        user_roles = user.get_roles()
        
        # Check if any role has the permission
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and role.has_permission(permission):
                return True
        
        return False
    
    def require_permission(self, permission: Permission):
        """Decorator to enforce permission requirements."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = request.user_id
                
                if not self.check_permission(user_id, permission):
                    abort(403)
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator

### Usage in endpoints
auth_service = AuthorizationService()

@app.route('/api/users', methods=['POST'])
@auth_service.require_permission(Permission.USER_CREATE)
def create_user():
    """Create new user (requires USER_CREATE permission)."""
    return create_new_user(request.json)

@app.route('/api/reports/<report_id>/approve', methods=['POST'])
@auth_service.require_permission(Permission.REPORT_APPROVE)
def approve_report(report_id):
    """Approve report (requires REPORT_APPROVE permission)."""
    return approve_report_by_id(report_id)
```

**Attribute-Based Access Control (ABAC) for Complex Scenarios**

For complex authorization requirements, design using attribute-based access control (ABAC) where access decisions are based on attributes of the user, resource, action, and environment.

Design principles:

- **Attribute Definition**: Define relevant attributes (user department, resource classification, time of access, IP address).
- **Policy Language**: Use a policy language (XACML, Rego, Cedar) to express complex authorization rules.
- **Evaluation Engine**: Implement a policy evaluation engine that makes access decisions based on attributes.
- **Audit Trail**: Log all attribute-based access decisions for compliance and incident investigation.

```python
### ABAC implementation using attribute-based policies
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class AccessContext:
    """Context for access decision."""
    user_id: str
    user_department: str
    user_clearance_level: int
    resource_id: str
    resource_classification: int
    action: str
    request_time: datetime
    request_ip: str
    request_location: str

class ABACPolicyEngine:
    """Evaluate access decisions based on attributes."""
    
    def __init__(self):
        self.policies = []
    
    def add_policy(self, policy_name: str, condition_func, effect: str = 'allow'):
        """Add a policy rule."""
        self.policies.append({
            'name': policy_name,
            'condition': condition_func,
            'effect': effect
        })
    
    def evaluate(self, context: AccessContext) -> bool:
        """Evaluate access decision."""
        for policy in self.policies:
            try:
                if policy['condition'](context):
                    return policy['effect'] == 'allow'
            except Exception as e:
                # Log policy evaluation error
                log_policy_error(policy['name'], str(e))
                continue
        
        # Default deny if no policy matches
        return False

### Initialize policy engine
abac_engine = ABACPolicyEngine()

### Define policies
abac_engine.add_policy(
    'allow_same_department_read',
    lambda ctx: (
        ctx.action == 'read' and
        ctx.user_department == get_resource_department(ctx.resource_id)
    ),
    effect='allow'
)

abac_engine.add_policy(
    'allow_high_clearance_classified',
    lambda ctx: (
        ctx.action == 'read' and
        ctx.user_clearance_level >= get_resource_classification(ctx.resource_id)
    ),
    effect='allow'
)

abac_engine.add_policy(
    'deny_after_hours_sensitive',
    lambda ctx: (
        ctx.action == 'write' and
        get_resource_classification(ctx.resource_id) >= 3 and
        (ctx.request_time.hour < 9 or ctx.request_time.hour > 17)
    ),
    effect='deny'
)

abac_engine.add_policy(
    'deny_external_network_admin',
    lambda ctx: (
        ctx.action == 'admin' and
        not is_internal_ip(ctx.request_ip)
    ),
    effect='deny'
)

@app.route('/api/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Get resource with ABAC authorization."""
    user = get_current_user()
    
    context = AccessContext(
        user_id=user.id,
        user_department=user.department,
        user_clearance_level=user.clearance_level,
        resource_id=resource_id,
        resource_classification=get_resource_classification(resource_id),
        action='read',
        request_time=datetime.utcnow(),
        request_ip=request.remote_addr,
        request_location=get_location_from_ip(request.remote_addr)
    )
    
    if not abac_engine.evaluate(context):
        log_access_denial(user.id, resource_id, 'read')
        abort(403)
    
    return get_resource_data(resource_id)
```

### Authorization Consistency Patterns

**Consistent Authorization Across Layers**

Design systems to enforce authorization consistently across all layers (API, business logic, data access). Authorization decisions should be made once and enforced uniformly.

Implementation pattern:

```python
### Centralized authorization decision point
class AuthorizationDecision:
    """Encapsulate authorization decision."""
    def __init__(self, allowed: bool, reason: str = None):
        self.allowed = allowed
        self.reason = reason

class ResourceAuthorizationService:
    """Centralized service for resource authorization."""
    
    def can_access_resource(self, user_id: str, resource_id: str, 
                           action: str) -> AuthorizationDecision:
        """Make authorization decision for resource access."""
        
        # Get user and resource
        user = User.query.get(user_id)
        resource = Resource.query.get(resource_id)
        
        if not user
```

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
