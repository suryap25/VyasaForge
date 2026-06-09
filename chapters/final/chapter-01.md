---
chapter: 1
stage: final
source: reviewed
generated_by: appsec-handbook-agent
---

# Chapter 01: Authentication vs Authorization

## Learning Objectives

After completing this chapter, you will be able to:

- **Distinguish** between authentication and authorization and explain why both are essential to application security
- **Design** authentication mechanisms that verify user identity while maintaining security and usability
- **Implement** authorization controls that enforce principle of least privilege across application resources
- **Identify** common authentication and authorization failures in code review and penetration testing
- **Evaluate** authentication and authorization architectures for security gaps and design flaws
- **Apply** secure design patterns for both authentication and authorization in modern applications
- **Assess** the security posture of authentication and authorization systems using industry-standard testing approaches

---

## Conceptual Foundation

Authentication and authorization are foundational security concepts that are frequently confused, conflated, or implemented incorrectly. Understanding the distinction between them is critical for building secure applications.

### Authentication: Proving Identity

**Authentication** is the process of verifying that a user is who they claim to be. It answers the question: *"Who are you?"*

Authentication establishes identity through one or more factors:

- **Something you know**: A password, PIN, or security question answer
- **Something you have**: A hardware token, mobile device, or cryptographic key
- **Something you are**: Biometric data such as fingerprints, facial recognition, or iris scans
- **Somewhere you are**: Geographic location or network context

When a user provides credentials (username and password), the application verifies those credentials against a stored record. If the credentials match, the user is authenticated. The application now knows (or believes it knows) the identity of the user.

### Authorization: Granting Access

**Authorization** is the process of determining what an authenticated user is allowed to do. It answers the question: *"What are you allowed to access?"*

Authorization is based on:

- **User identity**: Who the user is (established through authentication)
- **User roles**: Assigned roles such as "admin," "editor," or "viewer"
- **User attributes**: Properties like department, location, or clearance level
- **Resource attributes**: Properties of the resource being accessed
- **Context**: Time of day, network location, or device type

After authentication succeeds, the application checks authorization policies to determine whether the authenticated user can perform the requested action on the requested resource.

### The Critical Distinction

Consider a real-world analogy: A passport control officer at an airport performs authentication by checking your passport and verifying your identity. Once your identity is confirmed, a border agent performs authorization by checking whether you are allowed to enter the country (based on visa status, travel restrictions, or other policies).

In application security:

- **Authentication failure** means an attacker can impersonate a legitimate user
- **Authorization failure** means an authenticated user (or attacker who has compromised a user account) can access resources they should not be able to access

Both failures are critical security vulnerabilities, but they require different mitigation strategies.

### Common Misconceptions

**Misconception 1**: "If authentication is strong, authorization doesn't matter."

This is false. A user with a strong password can still be compromised through phishing, malware, or credential stuffing. Even if authentication is perfect, weak authorization allows compromised accounts to cause significant damage.

**Misconception 2**: "Authorization is just role-based access control (RBAC)."

RBAC is one authorization model, but modern applications often require more sophisticated models such as attribute-based access control (ABAC), policy-based access control, or relationship-based access control.

**Misconception 3**: "Authentication and authorization happen once at login."

In modern applications, both authentication and authorization are continuous processes. A user may be authenticated but lose authorization to a resource if their role changes. A session may be revoked. Permissions may be updated in real-time.

---

## Architecture Perspective

### Authentication Architecture Patterns

#### Centralized Authentication

In a centralized authentication architecture, a single authentication service validates credentials and issues tokens or sessions. All applications trust this central service.

**Example**: An organization uses a central identity provider (IdP) such as LDAP, Active Directory, or a custom authentication service. All applications delegate authentication to this service.

**Advantages**:
- Single source of truth for user credentials
- Consistent authentication policy across applications
- Easier to implement multi-factor authentication (MFA) globally
- Simplified credential rotation and revocation

**Disadvantages**:
- Single point of failure
- Requires network connectivity to the central service
- Potential performance bottleneck
- Increased complexity in distributed systems

#### Decentralized Authentication

In a decentralized architecture, each application manages its own authentication. Users may have separate credentials for each application.

**Advantages**:
- No single point of failure
- Applications can implement authentication independently
- Reduced dependency on central infrastructure

**Disadvantages**:
- Credential management burden on users
- Inconsistent authentication policies
- Difficult to enforce MFA globally
- Higher operational overhead

#### Federated Authentication

Federated authentication allows users to authenticate using credentials from an external identity provider. The application trusts the external provider to perform authentication.

**Example**: A web application allows users to "Sign in with Google" or "Sign in with GitHub." The application delegates authentication to Google or GitHub.

**Advantages**:
- Users do not need to create new credentials
- Reduces credential management burden
- Leverages security investments of large identity providers
- Enables single sign-on (SSO) across multiple applications

**Disadvantages**:
- Dependency on external provider availability
- Privacy concerns about sharing user data with external providers
- Limited control over authentication mechanisms
- Potential for account enumeration attacks

### Authorization Architecture Patterns

#### Role-Based Access Control (RBAC)

In RBAC, users are assigned roles, and roles are granted permissions. Authorization decisions are based on role membership.

**Example**:
```
User: alice
Roles: [editor, reviewer]

Role: editor
Permissions: [create_post, edit_own_post, delete_own_post]

Role: reviewer
Permissions: [view_all_posts, approve_posts]

Resource: /posts/123
Required permission: edit_own_post
```

Alice can edit post 123 if she created it (owns it) and has the editor role.

**Advantages**:
- Simple to understand and implement
- Scales well with moderate numbers of users and roles
- Aligns with organizational structure

**Disadvantages**:
- Difficult to express complex policies
- Role explosion as organizations grow
- Cannot easily express attribute-based conditions
- Difficult to implement fine-grained access control

#### Attribute-Based Access Control (ABAC)

In ABAC, authorization decisions are based on attributes of the user, resource, action, and environment.

**Example**:
```
Policy: A user can edit a document if:
  - User.role == "editor" AND
  - Document.owner == User.id AND
  - Document.classification <= User.clearance_level AND
  - CurrentTime.hour >= 9 AND CurrentTime.hour <= 17
```

**Advantages**:
- Expresses complex policies flexibly
- Reduces role explosion
- Supports fine-grained access control
- Adapts to changing organizational needs

**Disadvantages**:
- More complex to implement and maintain
- Performance overhead from policy evaluation
- Requires careful policy design to avoid unintended access
- Difficult to audit and understand policy decisions

#### Relationship-Based Access Control (ReBAC)

In ReBAC, authorization decisions are based on relationships between users and resources.

**Example**:
```
User: alice
Relationships:
  - alice is_owner_of document_123
  - alice is_member_of team_engineering
  - team_engineering has_access_to project_backend

Authorization: alice can view project_backend because:
  alice is_member_of team_engineering AND
  team_engineering has_access_to project_backend
```

**Advantages**:
- Naturally expresses organizational relationships
- Scales to large numbers of users and resources
- Supports dynamic relationship changes
- Enables efficient permission queries

**Disadvantages**:
- Requires careful relationship modeling
- Performance considerations for large relationship graphs
- Complexity in policy evaluation
- Potential for unintended access through relationship chains

### Session and Token Management

After authentication succeeds, the application must maintain the authenticated state. Two primary approaches exist:

**Session-Based Authentication**:
- Server creates a session object and stores it in memory or a session store
- Server sends a session identifier (session ID) to the client, typically in a cookie
- Client includes the session ID in subsequent requests
- Server looks up the session to verify the user is authenticated

**Token-Based Authentication**:
- Server creates a cryptographically signed token containing user information
- Server sends the token to the client
- Client includes the token in subsequent requests (typically in an Authorization header)
- Server verifies the token signature and extracts user information

Token-based authentication is more suitable for distributed systems, APIs, and mobile applications. Session-based authentication is simpler for traditional web applications but requires server-side state.

---

## AppSec Lens

### Authentication Vulnerabilities

#### Weak Credential Storage

**Vulnerability**: Passwords stored in plaintext or with weak hashing algorithms.

**Risk**: If the database is compromised, attackers can immediately use passwords to access user accounts.

**Example of Vulnerable Code**:
```python
# VULNERABLE: Storing plaintext password
def register_user(username, password):
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()

# VULNERABLE: Using weak hash (MD5)
import hashlib
def register_user(username, password):
    hashed = hashlib.md5(password.encode()).hexdigest()
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()
```

**Secure Implementation**:
```python
# SECURE: Using bcrypt with salt
import bcrypt

def register_user(username, password):
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode(), salt)
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()

def verify_password(stored_hash, provided_password):
    return bcrypt.checkpw(provided_password.encode(), stored_hash)
```

#### Broken Authentication Logic

**Vulnerability**: Flaws in the authentication mechanism that allow bypassing authentication.

**Examples**:
- SQL injection in login form: `SELECT * FROM users WHERE username = 'admin' --' AND password = '...'`
- Logic flaws: Checking only username without verifying password
- Session fixation: Reusing session IDs without regeneration after login
- Insufficient session timeout: Sessions remain valid indefinitely

**Example of Vulnerable Code**:
```python
# VULNERABLE: No password verification
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if user:
        session['user_id'] = user.id
        return redirect('/dashboard')
    return 'Login failed'

# VULNERABLE: Session not regenerated after login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and verify_password(user.password_hash, password):
        # Session ID is not regenerated - vulnerable to session fixation
        session['user_id'] = user.id
        return redirect('/dashboard')
    return 'Login failed'
```

**Secure Implementation**:
```python
# SECURE: Proper authentication with session regeneration
from flask import session
from werkzeug.security import check_password_hash

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        # Regenerate session ID to prevent session fixation
        session.clear()
        session['user_id'] = user.id
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=1)
        return redirect('/dashboard')
    
    return 'Login failed', 401
```

#### Credential Stuffing and Brute Force

**Vulnerability**: Applications do not implement rate limiting or account lockout mechanisms.

**Risk**: Attackers can attempt many password combinations or use leaked credentials from other breaches.

**Mitigation**:
- Implement rate limiting on login attempts (e.g., 5 failed attempts per 15 minutes)
- Implement account lockout after multiple failed attempts
- Use CAPTCHA after failed attempts
- Monitor for suspicious login patterns
- Implement multi-factor authentication (MFA)

### Authorization Vulnerabilities

#### Broken Access Control

**Vulnerability**: Users can access resources they should not be able to access.

**Example 1: Direct Object Reference**:
```python
# VULNERABLE: No authorization check
@app.route('/documents/<int:doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    return render_template('document.html', document=document)
```

An attacker can change the `doc_id` parameter to access documents belonging to other users.

**Secure Implementation**:
```python
# SECURE: Authorization check
@app.route('/documents/<int:doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    
    # Verify the current user owns the document
    if document.owner_id != current_user.id:
        abort(403)
    
    return render_template('document.html', document=document)
```

**Example 2: Privilege Escalation**:
```python
# VULNERABLE: No role check
@app.route('/admin/users', methods=['POST'])
def create_user():
    username = request.form.get('username')
    role = request.form.get('role')  # User can set their own role!
    user = User(username=username, role=role)
    db.session.add(user)
    db.session.commit()
    return 'User created'
```

An attacker can create an admin account by setting `role=admin`.

**Secure Implementation**:
```python
# SECURE: Role check and fixed role assignment
@app.route('/admin/users', methods=['POST'])
def create_user():
    # Verify current user is admin
    if current_user.role != 'admin':
        abort(403)
    
    username = request.form.get('username')
    # Role is not user-controlled; always create as 'user'
    user = User(username=username, role='user')
    db.session.add(user)
    db.session.commit()
    return 'User created'
```

#### Insecure Direct Object References (IDOR)

**Vulnerability**: Application uses user-controllable input to directly access objects without authorization checks.

**Example**:
```
GET /api/invoices/42
GET /api/invoices/43
GET /api/invoices/44
```

An attacker can enumerate invoice IDs and access invoices belonging to other users.

**Mitigation**:
- Always verify authorization before returning objects
- Use indirect references (UUIDs, opaque tokens) instead of sequential IDs
- Implement comprehensive access control checks
- Log and monitor access to sensitive resources

#### Horizontal vs Vertical Privilege Escalation

**Horizontal Privilege Escalation**: A user accesses resources belonging to another user at the same privilege level.

**Example**: User A accesses User B's profile or documents.

**Vertical Privilege Escalation**: A user gains higher privileges than they should have.

**Example**: A regular user becomes an admin.

Both types of privilege escalation are critical vulnerabilities.

---

## Developer Lens

### Implementing Authentication

#### Password Hashing Best Practices

Use modern password hashing algorithms designed for this purpose:

- **bcrypt**: Adaptive hashing algorithm with built-in salt and work factor
- **scrypt**: Memory-hard algorithm resistant to GPU attacks
- **Argon2**: Winner of Password Hashing Competition; memory-hard and time-hard

**Never use**:
- MD5, SHA-1, SHA-256 without salt (too fast, vulnerable to rainbow tables)
- Custom hashing algorithms
- Encryption instead of hashing (passwords should not be decryptable)

**Implementation Example** (Node.js):
```javascript
const bcrypt = require('bcrypt');

// Register user
async function registerUser(username, password) {
  const saltRounds = 12;
  const hashedPassword = await bcrypt.hash(password, saltRounds);
  
  const user = {
    username: username,
    passwordHash: hashedPassword
  };
  
  // Store user in database
  await db.users.insert(user);
}

// Verify password during login
async function verifyPassword(username, providedPassword) {
  const user = await db.users.findOne({ username: username });
  
  if (!user) {
    return false;
  }
  
  return await bcrypt.compare(providedPassword, user.passwordHash);
}
```

#### Multi-Factor Authentication (MFA)

Implement MFA to protect against compromised passwords:

**Time-Based One-Time Password (TOTP)**:
- User scans QR code with authenticator app (Google Authenticator, Authy, etc.)
- App generates 6-digit code that changes every 30 seconds
- User enters code during login

**Implementation Example** (Python):
```python
import pyotp
import qrcode

# Generate secret for user
def setup_mfa(user_id):
    secret = pyotp.random_base32()
    user = User.query.get(user_id)
    user.mfa_secret = secret
    db.session.commit()
    
    # Generate QR code for user to scan
    totp = pyotp.TOTP(secret)
    qr = qrcode.QRCode()
    qr.add_data(totp.provisioning_uri(name=user.email, issuer_name='MyApp'))
    qr.make()
    
    return qr

# Verify MFA code during login
def verify_mfa(user_id, code):
    user = User.query.get(user_id)
    totp = pyotp.TOTP(user.mfa_secret)
    
    # Allow for time drift (±1 time window)
    return totp.verify(code, valid_window=1)
```

#### Session Management

**Secure Session Configuration**:

```python
# Flask example
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True    # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Timeout
```

**Session Regeneration**:
```python
@app.route('/login', methods=['POST'])
def login():
    # ... authentication logic ...
    
    # Regenerate session ID after successful authentication
    session.clear()
    session['user_id'] = user.id
    
    return redirect('/dashboard')
```

### Implementing Authorization

#### Decorator-Based Authorization

Use decorators to enforce authorization checks:

```python
from functools import wraps
from flask import abort, session

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                abort(401)  # Not authenticated
            
            user = User.query.get(user_id)
            if user.role != required_role:
                abort(403)  # Not authorized
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/dashboard')
@require_role('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')
```

#### Resource-Level Authorization

Always check authorization at the resource level:

```python
def require_resource_access(resource_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(resource_id, *args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                abort(401)
            
            # Fetch resource
            resource = get_resource(resource_type

# Pentest Lens

## Authentication Testing

### Credential Validation Testing

**Objective**: Verify that the application properly validates credentials and rejects invalid authentication attempts.

**Test Cases**:

1. **Null/Empty Credentials**
   - Submit login with empty username and password
   - Submit login with empty username only
   - Submit login with empty password only
   - Expected: All attempts rejected with appropriate error messages

2. **SQL Injection in Authentication**
   - Username: `admin' --`
   - Username: `' OR '1'='1`
   - Username: `admin' OR 1=1 --`
   - Expected: Injection attempts rejected; no database errors exposed

3. **Authentication Bypass Attempts**
   - Test for logic flaws: Submit valid username with any password
   - Test for case sensitivity: `Admin` vs `admin`
   - Test for whitespace handling: `admin ` vs `admin`
   - Test for default credentials: `admin/admin`, `test/test`

4. **Timing Attacks**
   - Measure response time for valid vs invalid usernames
   - Measure response time for correct vs incorrect passwords
   - Expected: Consistent response times (no information leakage)

### Session Management Testing

**Objective**: Verify that sessions are properly created, maintained, and invalidated.

**Test Cases**:

1. **Session Fixation**
   - Obtain a session ID before authentication
   - Authenticate with that session ID
   - Verify that a new session ID is issued after authentication
   - Expected: Session ID changes after login

2. **Session Timeout**
   - Authenticate and obtain a session
   - Wait for the configured timeout period
   - Attempt to use the expired session
   - Expected: Expired session is rejected; user must re-authenticate

3. **Session Invalidation**
   - Authenticate and obtain a session
   - Logout
   - Attempt to use the invalidated session
   - Expected: Session is rejected; user must re-authenticate

4. **Session Prediction**
   - Collect multiple session IDs
   - Analyze for patterns or predictability
   - Attempt to predict valid session IDs
   - Expected: Session IDs are cryptographically random and unpredictable

5. **Cookie Attributes**
   - Inspect session cookies for security attributes
   - Verify `Secure` flag is set (HTTPS only)
   - Verify `HttpOnly` flag is set (no JavaScript access)
   - Verify `SameSite` attribute is set (CSRF protection)
   - Expected: All security attributes properly configured

### Multi-Factor Authentication Testing

**Objective**: Verify that MFA is properly implemented and cannot be bypassed.

**Test Cases**:

1. **MFA Bypass**
   - Authenticate with valid credentials
   - Attempt to access protected resources without completing MFA
   - Expected: Access denied until MFA is completed

2. **MFA Code Reuse**
   - Complete MFA with a valid code
   - Attempt to use the same code again
   - Expected: Code is rejected on reuse

3. **MFA Code Prediction**
   - Collect multiple MFA codes
   - Analyze for patterns
   - Attempt to predict valid codes
   - Expected: Codes are unpredictable and time-bound

4. **MFA Bypass via Session Manipulation**
   - Authenticate with valid credentials
   - Manipulate session to indicate MFA is complete without actually completing it
   - Expected: Session manipulation is detected and rejected

### Credential Stuffing and Brute Force Testing

**Objective**: Verify that the application implements rate limiting and account lockout.

**Test Cases**:

1. **Brute Force Attack**
   - Attempt multiple login attempts with incorrect passwords
   - Expected: After configured threshold (e.g., 5 attempts), account is locked or rate limiting is applied

2. **Rate Limiting**
   - Attempt rapid login requests
   - Expected: Requests are rate-limited; attacker receives 429 (Too Many Requests) response

3. **Account Lockout Recovery**
   - Trigger account lockout through failed login attempts
   - Verify lockout duration
   - Attempt login after lockout expires
   - Expected: Account is unlocked after configured duration

4. **Credential Stuffing with Valid Credentials**
   - Use credentials from known breaches
   - Expected: Rate limiting prevents rapid testing of multiple credentials

## Authorization Testing

### Access Control Testing

**Objective**: Verify that users can only access resources they are authorized to access.

**Test Cases**:

1. **Horizontal Privilege Escalation (IDOR)**
   - Authenticate as User A
   - Attempt to access resources belonging to User B by modifying resource ID
   - Example: Change `/documents/123` to `/documents/124`
   - Expected: Access denied; error message does not reveal resource existence

2. **Vertical Privilege Escalation**
   - Authenticate as regular user
   - Attempt to access admin-only resources
   - Attempt to modify user role in request parameters
   - Expected: Access denied; role cannot be modified by user

3. **Function-Level Access Control**
   - Authenticate as user without admin privileges
   - Attempt to access admin functions directly via URL or API
   - Example: `/admin/delete-user`, `/api/admin/reports`
   - Expected: Access denied with 403 Forbidden

4. **Data-Level Access Control**
   - Authenticate as User A
   - Query API for data belonging to User B
   - Example: `/api/users/B/profile`, `/api/users/B/orders`
   - Expected: Access denied; data not returned

### Role-Based Access Control Testing

**Objective**: Verify that RBAC is properly enforced.

**Test Cases**:

1. **Role Verification**
   - Authenticate as user with specific role
   - Verify that only resources permitted for that role are accessible
   - Test boundary conditions between roles

2. **Role Modification**
   - Attempt to modify user role in request parameters
   - Attempt to modify role in JWT token (if applicable)
   - Expected: Role modifications are rejected or ignored

3. **Missing Role Checks**
   - Identify all protected resources
   - Verify that each resource has explicit role checks
   - Test resources that may have been missed in implementation

### Attribute-Based Access Control Testing

**Objective**: Verify that ABAC policies are correctly evaluated.

**Test Cases**:

1. **Policy Evaluation**
   - Identify ABAC policies
   - Test boundary conditions of policies
   - Example: If policy is "user can edit document if owner AND time is 9-17", test at 8:59 and 17:01

2. **Attribute Manipulation**
   - Attempt to modify user attributes in request
   - Attempt to modify resource attributes
   - Expected: Attribute modifications are rejected or ignored

3. **Policy Bypass**
   - Identify complex policies
   - Test for logical flaws or unintended combinations
   - Example: Policy with OR conditions may allow unintended access

### API Authorization Testing

**Objective**: Verify that API endpoints properly enforce authorization.

**Test Cases**:

1. **Missing Authorization Checks**
   - Enumerate all API endpoints
   - Test each endpoint without authentication
   - Test each endpoint with insufficient privileges
   - Expected: Endpoints return 401 or 403 as appropriate

2. **Token Manipulation**
   - Modify JWT token claims (if applicable)
   - Modify OAuth token scope
   - Expected: Manipulated tokens are rejected

3. **API Key Testing**
   - Attempt to use API key from one user to access another user's data
   - Attempt to use expired API keys
   - Expected: Invalid keys are rejected

---

# Common Findings

## Authentication Findings

### Finding 1: Weak Password Hashing Algorithm

**Severity**: High

**Description**: The application stores passwords using a weak hashing algorithm (MD5, SHA-1, or SHA-256 without salt) instead of a modern password hashing algorithm.

**Impact**: If the password database is compromised, attackers can quickly crack passwords using rainbow tables or GPU-accelerated attacks.

**Example**:
```python
# VULNERABLE
import hashlib
password_hash = hashlib.sha256(password.encode()).hexdigest()
```

**Remediation**:
```python
# SECURE
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

**Verification**: Verify that passwords are hashed using bcrypt, scrypt, or Argon2 with appropriate work factors.

---

### Finding 2: Missing Multi-Factor Authentication

**Severity**: High

**Description**: The application does not implement multi-factor authentication (MFA) for user accounts, particularly for administrative or sensitive accounts.

**Impact**: Compromised passwords (through phishing, malware, or credential stuffing) allow attackers to access user accounts without additional verification.

**Remediation**:
- Implement TOTP-based MFA using authenticator apps
- Implement SMS-based MFA as fallback
- Enforce MFA for administrative accounts
- Provide backup codes for account recovery

**Verification**: Verify that MFA is required for login and cannot be bypassed.

---

### Finding 3: Session Fixation Vulnerability

**Severity**: High

**Description**: The application does not regenerate the session ID after successful authentication.

**Impact**: An attacker can trick a user into using a known session ID, then hijack the session after the user authenticates.

**Example**:
```
1. Attacker obtains session ID: ABC123
2. Attacker tricks user into visiting: /login?sessionid=ABC123
3. User authenticates with session ID ABC123
4. Attacker uses session ID ABC123 to access user's account
```

**Remediation**:
```python
@app.route('/login', methods=['POST'])
def login():
    # ... authentication logic ...
    session.clear()  # Clear old session
    session['user_id'] = user.id  # Create new session
    return redirect('/dashboard')
```

**Verification**: Verify that session ID changes after authentication.

---

### Finding 4: Insufficient Rate Limiting on Login

**Severity**: High

**Description**: The application does not implement rate limiting on login attempts, allowing brute force and credential stuffing attacks.

**Impact**: Attackers can attempt many password combinations or test leaked credentials without restriction.

**Remediation**:
- Implement rate limiting: 5 failed attempts per 15 minutes per IP
- Implement account lockout: Lock account after 5 failed attempts for 30 minutes
- Implement CAPTCHA after failed attempts
- Monitor for suspicious login patterns

**Verification**: Attempt multiple failed login attempts and verify that rate limiting is applied.

---

### Finding 5: Credentials Exposed in Logs or Error Messages

**Severity**: High

**Description**: Passwords or other sensitive credentials are logged or displayed in error messages.

**Impact**: Credentials may be exposed in log files, error pages, or debugging output.

**Example**:
```python
# VULNERABLE
try:
    authenticate(username, password)
except Exception as e:
    logger.error(f"Authentication failed for {username} with password {password}: {e}")
```

**Remediation**:
```python
# SECURE
try:
    authenticate(username, password)
except Exception as e:
    logger.error(f"Authentication failed for {username}")
    # Never log passwords or sensitive data
```

**Verification**: Review logs and error messages to ensure credentials are not exposed.

---

## Authorization Findings

### Finding 6: Insecure Direct Object Reference (IDOR)

**Severity**: High

**Description**: The application uses user-controllable input to directly access objects without authorization checks.

**Impact**: Users can access resources belonging to other users by modifying object IDs.

**Example**:
```python
# VULNERABLE
@app.route('/documents/<int:doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    return render_template('document.html', document=document)
```

An attacker can access any document by changing the `doc_id` parameter.

**Remediation**:
```python
# SECURE
@app.route('/documents/<int:doc_id>')
def view_document(doc_id):
    document = Document.query.get(doc_id)
    if document.owner_id != current_user.id:
        abort(403)
    return render_template('document.html', document=document)
```

**Verification**: Enumerate object IDs and verify that access is denied for objects not owned by the current user.

---

### Finding 7: Missing Authorization Checks on API Endpoints

**Severity**: High

**Description**: API endpoints do not verify that the authenticated user is authorized to perform the requested action.

**Impact**: Authenticated users can perform actions they should not be able to perform.

**Example**:
```python
# VULNERABLE
@app.route('/api/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return 'User deleted'
```

Any authenticated user can delete any other user.

**Remediation**:
```python
# SECURE
@app.route('/api/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return 'User deleted'
```

**Verification**: Test each API endpoint with different user roles and verify authorization is enforced.

---

### Finding 8: Privilege Escalation via Parameter Manipulation

**Severity**: High

**Description**: Users can escalate their privileges by modifying request parameters.

**Impact**: Regular users can become administrators or gain other elevated privileges.

**Example**:
```python
# VULNERABLE
@app.route('/profile/update', methods=['POST'])
def update_profile():
    user = User.query.get(current_user.id)
    user.role = request.form.get('role')  # User can set their own role!
    db.session.commit()
    return 'Profile updated'
```

An attacker can change their role to 'admin' by submitting `role=admin` in the request.

**Remediation**:
```python
# SECURE
@app.route('/profile/update', methods=['POST'])
def update_profile():
    user = User.query.get(current_user.id)
    # Role is not user-controllable; only allow specific fields
    user.email = request.form.get('email')
    user.phone = request.form.get('phone')
    # Role is never modified by user
    db.session.commit()
    return 'Profile updated'
```

**Verification**: Attempt to modify sensitive parameters (role, permissions, etc.) and verify they cannot be changed by users.

---

### Finding 9: Horizontal Privilege Escalation

**Severity**: High

**Description**: Users can access resources belonging to other users at the same privilege level.

**Impact**: Users can view, modify, or delete data belonging to other users.

**Example**:
```
User A accesses: /api/profile/user/123
User A modifies URL to: /api/profile/user/124
User A can now view User B's profile
```

**Remediation**:
- Always verify that the current user owns or has explicit permission to access the resource
- Use indirect references (UUIDs, opaque tokens) instead of sequential IDs
- Implement comprehensive access control checks at the resource level

**Verification**: Attempt to access resources belonging to other users and verify access is denied.

---

### Finding 10: Broken Function-Level Access Control

**Severity**: High

**Description**: Administrative functions are accessible to non-administrative users.

**Impact**: Regular users can perform administrative actions.

**Example**:
```
Regular user accesses: /admin/users
Regular user accesses: /admin/settings
Regular user accesses: /admin/reports
```

**Remediation**:
```python
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/users')
@require_admin
def admin_users():
    return render_template('admin_users.html')
```

**Verification**: Enumerate all endpoints and verify that administrative endpoints require administrative privileges.

---

# Secure Design Guidance

## Authentication Design Principles

### 1. Use Strong, Modern Password Hashing

**Principle**: Passwords must be hashed using algorithms specifically designed for password storage, not general-purpose cryptographic hash functions.

**Implementation Guidance**:

- **Choose a modern algorithm**: Use bcrypt, scrypt, or Argon2. Do not use MD5, SHA-1, or SHA-256.
- **Use appropriate work factors**: Configure the algorithm to be computationally expensive (e.g., bcrypt with 12+ rounds).
- **Use unique salts**: Each password should have a unique salt (modern algorithms handle this automatically).
- **Never decrypt passwords**: Passwords should be hashed, not encrypted. Comparison is done by hashing the provided password and comparing hashes.

**Example Architecture**:
```
User Registration:
1. User provides password
2. Application generates salt
3. Application hashes password with salt using bcrypt
4. Application stores hash in database
5. Application discards plaintext password

User Login:
1. User provides password
2. Application retrieves stored hash from database
3. Application hashes provided password with stored salt
4. Application compares hashes
5. If hashes match, user is authenticated
```

---

### 2. Implement Multi-Factor Authentication

**Principle**: Require at least two factors of authentication for sensitive accounts and operations.

**Implementation Guidance**:

- **Primary factor**: Username and password (something you know)
- **Secondary factor**: TOTP (something you have) or biometric (something you are)
- **Backup codes**: Provide backup codes for account recovery if MFA device is lost
- **Enforcement**: Require MFA for administrative accounts; make optional for regular users

**Recommended MFA Methods** (in order of preference):
1. TOTP (Time-Based One-Time Password) using authenticator apps
2. Hardware security keys (FIDO2/WebAuthn)
3. SMS-based OTP (less secure but better than nothing)
4. Email-based OTP

**Example Architecture**:
```
MFA Setup:
1. User enables MFA in account settings
2. Application generates secret key
3. Application displays QR code
4. User scans QR code with authenticator app
5. User confirms setup by entering code from app
6. Application stores secret key (encrypted)

MFA Login:
1. User enters username and password
2. Application verifies credentials
3. Application prompts for MFA code
4. User enters code from authenticator app
5. Application verifies code using stored secret
6. If code is valid, user is authenticated
```

---

### 3. Implement Secure Session Management

**Principle**: Sessions must be created, maintained, and invalidated securely.

**Implementation Guidance**:

- **Session ID generation**: Use cryptographically secure random number generator
- **Session ID length**: At least 128 bits of entropy
- **Session storage**: Store sessions server-side (in-memory, database, or cache)
- **Session timeout**: Implement absolute timeout (e.g., 1 hour) and idle timeout (e.g., 15 minutes)
- **Session regeneration**: Regenerate session ID after authentication to prevent session fixation
- **Session invalidation**: Invalidate session on logout and when user role changes
- **Cookie attributes**: Set Secure, HttpOnly, and SameSite attributes

**Example Architecture**:
```
Session Creation:
1. User authenticates
2. Application generates cryptographically random session ID
3. Application creates session object with user ID and timestamp
4. Application stores session in session store
5. Application sends session ID to client in secure cookie

Session Validation:
1. Client sends session ID in cookie
2. Application looks up session in session store
3. Application verifies session has not expired
4. Application verifies user ID in session
5. If valid, request is processed; otherwise, user is redirected to login

Session Invalidation:
1. User logs out
2. Application deletes session from session store
3. Application clears session cookie on client
```

---

### 4. Implement Rate Limiting and Account Lockout

**Principle**: Prevent brute force and credential stuffing attacks by limiting login attempts.

**Implementation Guidance**:

- **Rate limiting**: Limit login attempts per IP address

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

## Revision Additions

# Additive Revisions for Chapter 01: Authentication vs Authorization

## Technical Accuracy Corrections

### Correction 1: TOTP Time Window Clarification

**Location**: Developer Lens > Multi-Factor Authentication (MFA) section, Python code example

**Add after the code block**:

```markdown
**Time Window Explanation**: The `valid_window=1` parameter allows the TOTP verification to accept codes from the previous, current, and next 30-second time window. This accounts for clock skew between the client device and server (typically ±30 seconds). A window of 0 would only accept the current time window; a window of 1 accepts ±1 window (±30 seconds total).

**Security Consideration**: Do not increase the time window beyond 1, as this weakens the security of TOTP by allowing a wider window for code reuse or prediction attacks.
```

---

### Correction 2: Session Timeout Configuration - Idle vs Absolute

**Location**: Developer Lens > Session Management section

**Replace the existing session configuration example with**:

```python
# Flask example - Secure Session Configuration
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True    # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # CSRF protection

# Absolute timeout: Session expires after this duration regardless of activity
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Idle timeout: Session expires after this period of inactivity
# Note: Requires custom middleware to track last activity timestamp
IDLE_TIMEOUT = timedelta(minutes=15)

@app.before_request
def check_session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)
    
    # Check idle timeout
    last_activity = session.get('last_activity')
    if last_activity:
        if datetime.utcnow() - last_activity > IDLE_TIMEOUT:
            session.clear()
            abort(401)
    
    # Update last activity timestamp
    session['last_activity'] = datetime.utcnow()
```

**Add explanatory note**:

```markdown
**Absolute vs Idle Timeout**:
- **Absolute Timeout**: Session expires after a fixed duration (e.g., 1 hour) from creation, regardless of user activity. Protects against long-lived session hijacking.
- **Idle Timeout**: Session expires after a period of inactivity (e.g., 15 minutes). Protects against unattended sessions. Requires tracking last activity timestamp.

Both timeouts should be implemented for defense in depth. Absolute timeout should be longer than idle timeout.
```

---

### Correction 3: Add Argon2 to Password Hashing Best Practices

**Location**: Developer Lens > Implementing Authentication > Password Hashing Best Practices section

**Add after the bcrypt implementation example**:

```markdown
**Argon2 Implementation** (Python):

Argon2 is the winner of the Password Hashing Competition and is recommended for new applications. It is memory-hard and resistant to GPU and ASIC attacks.

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize password hasher
ph = PasswordHasher()

# Register user
def register_user(username, password):
    hashed_password = ph.hash(password)
    user = {
        'username': username,
        'password_hash': hashed_password
    }
    # Store user in database
    db.users.insert(user)

# Verify password during login
def verify_password(username, provided_password):
    user = db.users.find_one({'username': username})
    
    if not user:
        return False
    
    try:
        ph.verify(user['password_hash'], provided_password)
        return True
    except VerifyMismatchError:
        return False
```

**Argon2 Configuration**:
- `time_cost`: Number of iterations (default: 2, recommended: 2-3)
- `memory_cost`: Memory usage in KiB (default: 65536, recommended: 65536-262144)
- `parallelism`: Number of parallel threads (default: 4, recommended: 4-8)

Higher values increase security but also increase computation time. Balance security with acceptable login latency.
```

---

### Correction 4: JWT Token Validation Guidance

**Location**: Architecture Perspective > Session and Token Management section

**Add new subsection after token-based authentication explanation**:

```markdown
#### JWT Token Validation

When using JWT tokens, the server must validate both the signature and claims:

**Signature Verification**:
```python
import jwt
from datetime import datetime

SECRET_KEY = 'your-secret-key'  # Should be stored securely

def verify_jwt_token(token):
    try:
        # Verify signature and decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.InvalidSignatureError:
        # Token signature is invalid
        return None
    except jwt.DecodeError:
        # Token is malformed
        return None

def validate_token_claims(payload):
    # Check expiration claim
    if 'exp' in payload:
        if datetime.utcnow().timestamp() > payload['exp']:
            return False  # Token has expired
    
    # Check issued-at claim
    if 'iat' in payload:
        if datetime.utcnow().timestamp() < payload['iat']:
            return False  # Token not yet valid
    
    # Check other required claims
    if 'user_id' not in payload:
        return False
    
    return True

@app.route('/api/protected')
def protected_resource():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    payload = verify_jwt_token(token)
    if not payload or not validate_token_claims(payload):
        abort(401)
    
    user_id = payload['user_id']
    # Process request with authenticated user
    return {'data': 'sensitive'}
```

**Critical JWT Validation Points**:
- Always verify the signature using the correct algorithm and secret key
- Always check the `exp` (expiration) claim
- Always check the `iat` (issued-at) claim to prevent tokens issued in the future
- Never trust the token payload without signature verification
- Do not use `jwt.decode()` with `verify=False` in production
- Use strong, randomly generated secret keys (at least 256 bits for HS256)
```

---

## Missing Content Additions

### Addition 1: OAuth 2.0 and OpenID Connect

**Location**: Architecture Perspective > Authentication Architecture Patterns section

**Add new subsection after Federated Authentication**:

```markdown
#### OAuth 2.0 and OpenID Connect

**OAuth 2.0** is an authorization framework that allows users to grant applications access to their resources without sharing passwords. **OpenID Connect (OIDC)** extends OAuth 2.0 to provide authentication (identity verification) in addition to authorization.

**OAuth 2.0 Authorization Code Flow** (most common for web applications):

```
1. User clicks "Sign in with Google"
2. Application redirects to Google's authorization endpoint
3. User authenticates with Google and grants permission
4. Google redirects back to application with authorization code
5. Application exchanges code for access token (server-to-server)
6. Application uses access token to fetch user information
7. Application creates session for user
```

**OpenID Connect Flow** (adds authentication layer):

OpenID Connect adds an ID token (JWT) that contains user identity information:

```python
# After exchanging authorization code for tokens
id_token = response['id_token']  # JWT containing user info
access_token = response['access_token']  # For accessing user resources

# Verify ID token signature
payload = jwt.decode(id_token, GOOGLE_PUBLIC_KEY, algorithms=['RS256'])

# Extract user information
user_id = payload['sub']  # Subject (unique user identifier)
email = payload['email']
email_verified = payload['email_verified']
name = payload['name']

# Create application session
session['user_id'] = user_id
session['email'] = email
```

**PKCE (Proof Key for Code Exchange)** for Mobile and SPA Applications:

PKCE adds an additional security layer for applications that cannot securely store a client secret (mobile apps, single-page applications):

```python
import secrets
import hashlib
import base64

# Step 1: Generate code verifier and challenge
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')

# Step 2: Redirect to authorization endpoint with code_challenge
authorization_url = f"{OAUTH_PROVIDER}/authorize?client_id={CLIENT_ID}&code_challenge={code_challenge}&code_challenge_method=S256"

# Step 3: Exchange authorization code for token, including code_verifier
token_response = requests.post(
    f"{OAUTH_PROVIDER}/token",
    data={
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'client_id': CLIENT_ID,
        'code_verifier': code_verifier  # Proves we initiated the request
    }
)
```

**Advantages of OAuth 2.0 / OIDC**:
- Users do not share passwords with applications
- Applications do not store passwords
- Users can revoke access without changing passwords
- Leverages security investments of large identity providers
- Enables single sign-on across multiple applications

**Disadvantages**:
- Dependency on external provider availability
- Privacy concerns about sharing user data
- More complex implementation than basic authentication
- Potential for misconfiguration (e.g., not validating ID token signature)
```

---

### Addition 2: Secure Password Reset and Recovery

**Location**: AppSec Lens section

**Add new subsection after Authorization Vulnerabilities**:

```markdown
#### Insecure Password Reset

**Vulnerability**: Password reset mechanisms that do not properly validate reset tokens or allow unauthorized password changes.

**Common Flaws**:

1. **Predictable Reset Tokens**
```python
# VULNERABLE: Predictable token based on user ID
def generate_reset_token(user_id):
    return str(user_id) + str(int(time.time()))

# VULNERABLE: Token not time-limited
def generate_reset_token(user_id):
    return hashlib.md5(user_email.encode()).hexdigest()
```

2. **No Token Expiration**
```python
# VULNERABLE: Token never expires
reset_token = secrets.token_urlsafe(32)
db.store_reset_token(user_id, reset_token)  # No expiration time stored
```

3. **Token Reuse**
```python
# VULNERABLE: Token can be used multiple times
@app.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    user = db.find_user_by_reset_token(token)
    if user:
        user.password = hash_password(request.form.get('new_password'))
        db.session.commit()
        # Token is never invalidated; can be reused
```

4. **Account Enumeration via Reset**
```python
# VULNERABLE: Different responses reveal whether email exists
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if user:
        send_reset_email(user)
        return 'Reset email sent'  # Reveals email exists
    else:
        return 'Email not found'  # Reveals email does not exist
```

**Secure Password Reset Implementation**:

```python
import secrets
from datetime import datetime, timedelta

# Generate secure reset token
def generate_reset_token(user_id):
    token = secrets.token_urlsafe(32)
    expiration = datetime.utc
