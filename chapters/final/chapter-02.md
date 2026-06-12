---
chapter: 2
stage: final
source: drafts
generated_by: appsec-handbook-agent
---

# Chapter 02: Identity and Access Management Concepts

## Learning Objectives

After completing this chapter, you will be able to:

- Define and distinguish between authentication, authorization, and identity management in web and mobile applications
- Explain the architectural components of an Identity and Access Management (IAM) system and their security implications
- Identify common IAM vulnerabilities and their exploitation vectors in modern application architectures
- Implement secure authentication and authorization mechanisms using industry-standard patterns
- Design and review IAM systems from both developer and security perspectives
- Conduct effective security assessments of IAM implementations
- Apply secure design principles to prevent identity-related attacks

## Conceptual Foundation

Identity and Access Management (IAM) forms the foundational security layer for virtually every application. Before we can discuss authorization, we must first establish what we mean by the core concepts that comprise IAM.

**Identity** is the unique representation of a user, service, or system within an application context. An identity answers the question "Who are you?" Identity can be represented by usernames, email addresses, user IDs, service principals, or device identifiers. In distributed systems, identity becomes more complex—a user might have multiple identities across different systems, and applications must establish trust relationships to recognize identities from other domains.

**Authentication** is the process of verifying that an identity is genuine. It answers "Prove that you are who you claim to be." Authentication mechanisms range from simple password verification to multi-factor approaches combining something you know (password), something you have (hardware token, phone), and something you are (biometric). The strength of authentication directly impacts the security of everything downstream—a compromised authentication mechanism undermines all subsequent authorization decisions.

**Authorization** is the process of determining what an authenticated identity is permitted to do. It answers "What are you allowed to access?" Authorization operates on the principle of least privilege: users should have access only to resources and operations necessary for their role or function. Authorization decisions are made based on policies that consider the identity, the requested resource, the requested action, and contextual factors like time, location, or device posture.

**Access Control** is the enforcement mechanism that implements authorization decisions. Access control systems evaluate requests against policies and either permit or deny access. Access control models vary significantly—from simple role-based access control (RBAC) to attribute-based access control (ABAC) to policy-based systems.

**Session Management** bridges authentication and authorization. After successful authentication, applications must maintain state about the authenticated user across multiple requests. Sessions represent this authenticated state and are typically managed through tokens, cookies, or server-side session stores. Session management is critical because weak session handling can allow attackers to hijack authenticated sessions without compromising the original authentication credentials.

**Credentials** are the secrets or artifacts used to prove identity during authentication. Passwords are the most common credential type, but credentials also include API keys, certificates, tokens, and biometric data. Credential management—how credentials are stored, transmitted, rotated, and revoked—is a critical security concern.

These concepts form an integrated system. A user authenticates using credentials, establishing their identity. The system then authorizes specific actions based on that identity. Access control mechanisms enforce those authorization decisions. Sessions maintain the authenticated state across interactions. Each component must be secure; weakness in any component compromises the entire system.

## Architecture Perspective

IAM systems operate across multiple architectural layers, and understanding these layers is essential for designing secure applications.

### The Authentication Layer

The authentication layer is where identity verification occurs. In traditional monolithic applications, authentication might be handled entirely within the application. In modern distributed architectures, authentication is often delegated to specialized services.

**Direct Authentication** occurs when the application directly verifies credentials. The user submits credentials (typically username and password), the application validates them against a credential store, and if valid, the application establishes an authenticated session. This approach is straightforward but places significant responsibility on the application to securely handle credentials.

**Federated Authentication** delegates authentication to an external identity provider. The application redirects the user to the identity provider, which handles credential verification. Upon successful authentication, the identity provider returns an assertion (typically a token or SAML response) that the application trusts. This approach reduces the application's responsibility for credential handling but introduces dependency on the identity provider's security.

**Multi-Factor Authentication (MFA)** requires multiple independent verification methods. Common factors include:
- Knowledge factors (passwords, security questions)
- Possession factors (hardware tokens, mobile devices)
- Inherence factors (biometrics)
- Location factors (geographic verification)

MFA significantly increases authentication security by requiring attackers to compromise multiple independent systems. However, MFA implementation introduces complexity and potential usability challenges.

### The Authorization Layer

Authorization decisions must be made consistently across the application. Centralized authorization policies ensure consistency and simplify policy management.

**Role-Based Access Control (RBAC)** assigns users to roles, and roles have associated permissions. For example, a "Manager" role might have permissions to "approve_expenses" and "view_team_reports." RBAC is intuitive and scales reasonably well for many applications. However, RBAC can become unwieldy when fine-grained permissions are needed or when authorization depends on resource attributes rather than just user roles.

**Attribute-Based Access Control (ABAC)** makes authorization decisions based on attributes of the user, resource, action, and environment. For example: "Allow access to medical_records if (user.department == 'healthcare' AND resource.classification == 'internal' AND current_time between 09:00 and 17:00)." ABAC is more flexible than RBAC but requires more sophisticated policy engines and can be more difficult to audit.

**Access Control Lists (ACLs)** specify which principals have access to specific resources. ACLs are often used for fine-grained resource-level access control. For example, a document might have an ACL specifying that user_alice has "read" access and user_bob has "read_write" access.

### The Session Management Layer

Sessions maintain authenticated state across multiple requests. Session management architecture varies significantly:

**Server-Side Sessions** store session state on the server. The client receives a session identifier (typically in a cookie), and each request includes this identifier. The server looks up the session state and retrieves the associated user identity. This approach gives the server complete control over session state and enables easy session revocation.

**Token-Based Sessions** encode session information in a cryptographically signed token. The client stores the token and includes it with each request. The server validates the token signature and extracts session information without needing to look up state. This approach is stateless from the server perspective and scales well in distributed systems, but token revocation is more complex.

**Hybrid Approaches** combine server-side and token-based mechanisms. For example, a short-lived access token might be paired with a longer-lived refresh token stored server-side, enabling both scalability and revocation capabilities.

### The Credential Storage Layer

How credentials are stored is critical to IAM security. Credentials should never be stored in plaintext.

**Password Hashing** uses cryptographic hash functions to store passwords irreversibly. When a user authenticates, the submitted password is hashed and compared to the stored hash. Modern password hashing should use algorithms specifically designed for password storage, such as bcrypt, scrypt, or Argon2, which are intentionally slow to resist brute-force attacks.

**Salting** adds random data to passwords before hashing, ensuring that identical passwords produce different hashes. This prevents rainbow table attacks where attackers precompute hashes for common passwords.

**Key Derivation Functions (KDFs)** derive cryptographic keys from passwords. KDFs like PBKDF2 apply the hash function many times (thousands or millions), making brute-force attacks computationally expensive.

## AppSec Lens

From an application security perspective, IAM systems present numerous attack vectors and require careful threat modeling.

### Authentication Attacks

**Credential Compromise** occurs when attackers obtain valid credentials through phishing, malware, data breaches, or social engineering. Once credentials are compromised, attackers can authenticate as legitimate users. Mitigation strategies include MFA, credential monitoring, and user education.

**Brute Force Attacks** attempt to guess credentials by trying many password combinations. Attackers might target a known username with many passwords or try common username/password combinations. Mitigations include rate limiting, account lockout policies, and strong password requirements. However, account lockout can enable denial-of-service attacks, so rate limiting is often preferred.

**Credential Stuffing** uses credentials compromised from one service to attack other services, exploiting password reuse. Mitigations include detecting unusual login patterns, requiring MFA, and monitoring for compromised credentials.

**Session Fixation** tricks a user into using a session identifier controlled by the attacker. The attacker creates a session, tricks the user into authenticating with that session identifier, and then uses the same identifier to access the user's account. Mitigation requires regenerating session identifiers after successful authentication.

**Session Hijacking** involves stealing a valid session identifier and using it to impersonate the authenticated user. Session identifiers might be stolen through network sniffing (if transmitted over unencrypted connections), cross-site scripting (XSS) attacks, or malware. Mitigations include using HTTPS, secure cookie flags, short session timeouts, and detecting anomalous session usage.

### Authorization Attacks

**Privilege Escalation** occurs when users gain access to resources or operations beyond their authorized permissions. Vertical privilege escalation involves gaining higher-level permissions (e.g., a regular user becoming an administrator). Horizontal privilege escalation involves accessing resources belonging to other users at the same privilege level.

**Insecure Direct Object References (IDOR)** occur when authorization checks are insufficient for resource access. For example, an API endpoint `/api/users/123/profile` might return the profile for user 123 without verifying that the requesting user has permission to view that profile. An attacker could simply change the user ID to access other users' profiles.

**Broken Access Control** encompasses various authorization failures where access control mechanisms are improperly implemented. This might include missing authorization checks, inconsistent authorization logic, or authorization bypasses through parameter manipulation.

**Attribute Injection** involves manipulating user attributes to bypass authorization. For example, if an application stores user roles in a client-side cookie without integrity protection, an attacker could modify the cookie to grant themselves additional roles.

### Identity Spoofing

**Identity Spoofing** occurs when attackers impersonate legitimate users or services. In federated authentication scenarios, attackers might forge identity assertions or exploit trust relationships between identity providers and service providers.

**Token Forgery** involves creating fraudulent authentication tokens. If tokens are not properly signed or if signing keys are compromised, attackers can create valid-appearing tokens that the application will accept.

## Developer Lens

Developers implementing IAM systems must balance security with usability and performance. This section provides practical guidance for secure implementation.

### Authentication Implementation

**Password Storage Best Practices:**

```python
### SECURE: Using bcrypt for password hashing
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with automatic salt generation."""
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds provides good security/performance balance
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

### INSECURE: Using simple SHA-256 without salt
import hashlib

def insecure_hash_password(password: str) -> str:
    """DO NOT USE: Simple SHA-256 without salt."""
    return hashlib.sha256(password.encode()).hexdigest()
```

The secure approach uses bcrypt, which is specifically designed for password hashing. The `rounds` parameter controls the computational cost—higher values make brute-force attacks more expensive but also increase legitimate authentication latency. The insecure approach uses SHA-256, which is fast (making brute-force attacks feasible) and lacks salt (enabling rainbow table attacks).

**Session Management Best Practices:**

```python
### SECURE: Server-side session with secure cookie
from flask import Flask, session, request
from datetime import timedelta
import secrets

app = Flask(__name__)
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True    # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = authenticate_user(username, password)
    if user:
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        # Session identifier is automatically generated and secure
        return redirect('/dashboard')
    return render_template('login.html', error='Invalid credentials')

### INSECURE: Client-side session without integrity protection
@app.route('/login_insecure', methods=['POST'])
def login_insecure():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = authenticate_user(username, password)
    if user:
        # Storing user data in cookie without signing
        response = make_response(redirect('/dashboard'))
        response.set_cookie('user_id', str(user.id))
        response.set_cookie('username', user.username)
        response.set_cookie('role', user.role)  # Attacker can modify this!
        return response
```

The secure approach uses server-side sessions with secure cookie flags. The `SECURE` flag ensures cookies are only transmitted over HTTPS. The `HTTPONLY` flag prevents JavaScript from accessing the cookie, mitigating XSS-based session theft. The `SAMESITE` flag provides CSRF protection. The insecure approach stores user data in cookies without integrity protection, allowing attackers to modify their own role or user ID.

**Authorization Implementation:**

```python
### SECURE: Centralized authorization with decorator
from functools import wraps
from flask import abort

def require_permission(permission: str):
    """Decorator to enforce permission requirements."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                abort(401)  # Unauthorized
            
            # Check permission from server-side store
            user = get_user(user_id)
            if not user.has_permission(permission):
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/expenses/<int:expense_id>/approve', methods=['POST'])
@require_permission('approve_expenses')
def approve_expense(expense_id):
    expense = get_expense(expense_id)
    if not expense:
        abort(404)
    
    # Verify user can approve this specific expense
    if not can_approve_expense(session['user_id'], expense):
        abort(403)
    
    expense.approve()
    return {'status': 'approved'}

### INSECURE: Client-side authorization
@app.route('/api/expenses/<int:expense_id>/approve_insecure', methods=['POST'])
def approve_expense_insecure(expense_id):
    # Checking role from client-provided data
    if request.headers.get('X-User-Role') != 'manager':
        abort(403)
    
    expense = get_expense(expense_id)
    expense.approve()
    return {'status': 'approved'}
```

The secure approach uses server-side authorization checks. The decorator verifies that the user has the required permission before allowing the operation. Additionally, resource-level authorization checks verify that the user can perform the action on the specific resource. The insecure approach trusts client-provided role information, which attackers can easily modify.

### Token-Based Authentication

For APIs and distributed systems, token-based authentication is common. JSON Web Tokens (JWTs) are widely used but require careful implementation:

```python
### SECURE: JWT with proper validation
import jwt
from datetime import datetime, timedelta
from functools import wraps

SECRET_KEY = 'your-secret-key-stored-securely'  # Should be in environment variable
ALGORITHM = 'HS256'

def create_access_token(user_id: str, expires_in_hours: int = 1) -> str:
    """Create a signed JWT token."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')

def require_auth(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            abort(401)
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        try:
            payload = verify_token(token)
            request.user_id = payload['user_id']
        except ValueError:
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    user = get_user(request.user_id)
    return {'id': user.id, 'name': user.name, 'email': user.email}

### INSECURE: JWT without signature verification
def verify_token_insecure(token: str) -> dict:
    """DO NOT USE: Decodes JWT without verifying signature."""
    import base64
    import json
    
    # Simply decode without verification
    parts = token.split('.')
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
    return payload
```

The secure approach creates tokens with expiration times, includes a token type to prevent token confusion attacks, and verifies the signature before trusting the token contents. The insecure approach decodes tokens without verifying the signature, allowing attackers to forge tokens.

## Pentest Lens

Security testers and penetration testers should systematically assess IAM implementations using structured approaches.

### Authentication Testing Checklist

- **Credential Handling**: Verify that credentials are transmitted over HTTPS. Check for credentials in logs, error messages, or client-side code.
- **Password Policy**: Test password requirements. Weak policies (short minimum length, no complexity requirements) enable brute-force attacks.
- **Brute Force Protection**: Attempt multiple failed logins. Verify that rate limiting or account lockout is implemented. Test for lockout bypass techniques.
- **Session Fixation**: Obtain a session identifier before authenticating. Attempt to use this identifier after authenticating as a different user. Verify that the session identifier changes after authentication.
- **Session Timeout**: Authenticate and then wait for the session timeout period. Verify that the session is invalidated.
- **Concurrent Sessions**: Authenticate from multiple locations simultaneously. Verify that the application handles concurrent sessions appropriately (some applications allow unlimited concurrent sessions, others limit to one).
- **Logout Functionality**: Verify that logout invalidates the session. Attempt to use the session identifier after logout.

### Authorization Testing Checklist

- **Horizontal Privilege Escalation**: Attempt to access resources belonging to other users at the same privilege level. For example, if viewing your own profile at `/api/users/123/profile`, try accessing `/api/users/124/profile`.
- **Vertical Privilege Escalation**: Attempt to perform actions requiring higher privileges. For example, try accessing administrative functions or modifying other users' data.
- **Parameter Manipulation**: Modify request parameters to attempt authorization bypass. For example, change user IDs, role parameters, or resource identifiers.
- **Attribute Injection**: Attempt to inject or modify user attributes. For example, modify cookies or headers that contain role information.
- **Inconsistent Authorization**: Test authorization across different endpoints and methods. Some applications implement authorization for GET requests but not POST requests, or vice versa.
- **Resource-Level Authorization**: Verify that authorization is enforced at the resource level, not just the endpoint level. For example, an endpoint might require authentication, but not verify that the user has permission to access the specific resource.

### Session Testing Checklist

- **Session Identifier Randomness**: Collect multiple session identifiers and analyze for patterns. Session identifiers should be cryptographically random.

## Common Findings

### Authentication-Related Findings

### Weak Password Hashing Algorithms

**Description**: Applications using fast hashing algorithms (MD5, SHA-1, SHA-256) or unsalted hashes for password storage enable efficient brute-force attacks.

**Example Finding**:
```python
### VULNERABLE CODE
import hashlib

def store_password(password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    db.save_user_password(hashed)
```

An attacker with access to the password database can compute hashes for millions of common passwords per second, compromising all user accounts.

**Impact**: High. Credential compromise affects all users whose passwords are in the database.

**Remediation**: Use password-specific hashing algorithms (bcrypt, scrypt, Argon2) with appropriate cost factors. Implement salting automatically within the algorithm.

---

### Credentials Stored in Code or Configuration

**Description**: API keys, database passwords, or authentication tokens hardcoded in source code, configuration files, or environment files.

**Example Finding**:
```python
### VULNERABLE: Credentials in code
API_KEY = "sk_live_51234567890abcdef"
DB_PASSWORD = "admin123"
JWT_SECRET = "super-secret-key-12345"
```

Credentials in version control are permanently exposed, even if later removed. Credentials in configuration files are exposed if the server is compromised or files are accidentally exposed.

**Impact**: Critical. Attackers gain direct access to backend systems and services.

**Remediation**: Use environment variables, secrets management systems (HashiCorp Vault, AWS Secrets Manager), or key management services. Never commit credentials to version control. Implement pre-commit hooks to detect credential patterns.

---

### Missing or Weak Multi-Factor Authentication

**Description**: Applications lacking MFA or implementing weak MFA (SMS-based without backup methods, easily bypassable MFA).

**Example Finding**:
- No MFA option available for user accounts
- MFA only via SMS (vulnerable to SIM swapping)
- MFA bypass through predictable recovery codes
- MFA not enforced for privileged accounts

**Impact**: High. Compromised passwords alone enable account takeover.

**Remediation**: Implement MFA using TOTP (Time-based One-Time Password) or hardware keys. Provide backup authentication methods. Enforce MFA for administrative accounts. Implement rate limiting on MFA attempts.

---

### Session Fixation Vulnerabilities

**Description**: Session identifiers not regenerated after successful authentication, allowing attackers to pre-set session IDs.

**Example Finding**:
```python
### VULNERABLE: Session ID not regenerated
@app.route('/login', methods=['POST'])
def login():
    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user.id  # Same session ID used before and after login
        return redirect('/dashboard')
```

An attacker can trick a user into clicking a link containing a known session ID, then use that same ID after the user authenticates.

**Impact**: High. Attackers can hijack authenticated sessions without compromising credentials.

**Remediation**: Regenerate session identifiers immediately after successful authentication. Use framework features that handle this automatically (e.g., `session.regenerate()` in most frameworks).

---

### Insecure Session Storage

**Description**: Session data stored in client-side cookies without integrity protection or encryption.

**Example Finding**:
```python
### VULNERABLE: Unprotected session data in cookie
response.set_cookie('user_id', user.id)
response.set_cookie('role', user.role)
response.set_cookie('is_admin', 'true' if user.is_admin else 'false')
```

Attackers can modify cookies to change their user ID, role, or admin status.

**Impact**: Critical. Attackers can escalate privileges or impersonate other users.

**Remediation**: Store session data server-side. If client-side storage is necessary, sign and encrypt the data. Use secure cookie flags (Secure, HttpOnly, SameSite).

---

### Credential Stuffing Vulnerability

**Description**: No detection or prevention of credential stuffing attacks where attackers use compromised credentials from other services.

**Example Finding**:
- No rate limiting on login attempts
- No detection of multiple failed logins from different IPs
- No monitoring for known compromised credentials
- No requirement for MFA after suspicious login patterns

**Impact**: High. Attackers can compromise accounts using credentials from other breaches.

**Remediation**: Implement rate limiting per username and IP. Monitor for multiple failed login attempts. Integrate with breach databases (HaveIBeenPwned API). Require MFA after suspicious login patterns. Implement CAPTCHA after failed attempts.

---

### Authorization-Related Findings

### Insecure Direct Object References (IDOR)

**Description**: Missing authorization checks when accessing resources by ID, allowing users to access resources belonging to other users.

**Example Finding**:
```python
### VULNERABLE: No authorization check
@app.route('/api/invoices/<int:invoice_id>')
def get_invoice(invoice_id):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return invoice.to_json()  # Returns any invoice without checking ownership
```

A user can access any invoice by changing the invoice ID in the URL.

**Impact**: High. Users can access sensitive data belonging to other users.

**Remediation**: Verify that the requesting user has permission to access the resource:
```python
@app.route('/api/invoices/<int:invoice_id>')
def get_invoice(invoice_id):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice or invoice.user_id != session['user_id']:
        abort(403)
    return invoice.to_json()
```

---

### Broken Access Control at Endpoint Level

**Description**: Authorization checks missing or inconsistent across different HTTP methods or endpoints.

**Example Finding**:
- Authorization enforced on GET requests but not POST requests
- Authorization enforced on one endpoint but not another similar endpoint
- Authorization checks in middleware that can be bypassed
- Different authorization logic for different API versions

**Impact**: High. Attackers can bypass authorization through alternative request methods or endpoints.

**Remediation**: Implement centralized authorization logic. Use decorators or middleware consistently across all endpoints. Test all HTTP methods (GET, POST, PUT, DELETE, PATCH). Maintain authorization consistency across API versions.

---

### Privilege Escalation Through Parameter Manipulation

**Description**: User roles or permissions stored in client-controllable locations (cookies, headers, request parameters) without server-side verification.

**Example Finding**:
```python
### VULNERABLE: Role from client-provided header
@app.route('/api/admin/users')
def list_users():
    if request.headers.get('X-User-Role') == 'admin':
        return db.query(User).all()
    abort(403)
```

Attackers can add or modify the `X-User-Role` header to grant themselves admin privileges.

**Impact**: Critical. Attackers can escalate to administrative privileges.

**Remediation**: Store authorization data server-side. Retrieve user permissions from the session or database, never from client-provided data:
```python
@app.route('/api/admin/users')
def list_users():
    user = get_user(session['user_id'])
    if not user.has_role('admin'):
        abort(403)
    return db.query(User).all()
```

---

### Attribute-Based Authorization Bypass

**Description**: Authorization logic that can be bypassed by manipulating request attributes or exploiting logic flaws.

**Example Finding**:
```python
### VULNERABLE: Authorization based on manipulable attributes
@app.route('/api/documents/<int:doc_id>')
def get_document(doc_id):
    doc = db.query(Document).get(doc_id)
    # Authorization based on request parameter
    if request.args.get('department') == doc.department:
        return doc.to_json()
    abort(403)
```

Attackers can change the `department` parameter to match the document's department.

**Impact**: High. Attackers can access resources by manipulating request attributes.

**Remediation**: Base authorization on server-side user attributes, not request parameters:
```python
@app.route('/api/documents/<int:doc_id>')
def get_document(doc_id):
    doc = db.query(Document).get(doc_id)
    user = get_user(session['user_id'])
    if user.department != doc.department:
        abort(403)
    return doc.to_json()
```

---

### Missing Resource-Level Authorization

**Description**: Authorization checks at the endpoint level but not at the resource level, allowing users to perform actions on resources they don't own.

**Example Finding**:
```python
### VULNERABLE: Authorization check on endpoint, not resource
@app.route('/api/expenses/<int:expense_id>/approve', methods=['POST'])
@require_role('manager')  # Only checks if user is a manager
def approve_expense(expense_id):
    expense = db.query(Expense).get(expense_id)
    expense.status = 'approved'
    db.commit()
    return {'status': 'approved'}
```

A manager can approve any expense, even those from other departments or teams.

**Impact**: Medium to High. Users can perform actions on resources outside their scope.

**Remediation**: Implement resource-level authorization checks:
```python
@app.route('/api/expenses/<int:expense_id>/approve', methods=['POST'])
@require_role('manager')
def approve_expense(expense_id):
    expense = db.query(Expense).get(expense_id)
    user = get_user(session['user_id'])
    
    # Verify user can approve this specific expense
    if not user.can_approve_expense(expense):
        abort(403)
    
    expense.status = 'approved'
    db.commit()
    return {'status': 'approved'}
```

---

### Inconsistent Authorization Across API Versions

**Description**: Different authorization logic or enforcement between API versions, allowing attackers to bypass controls using older API versions.

**Example Finding**:
- `/api/v1/users/123` requires authentication
- `/api/v2/users/123` requires authentication and authorization
- Older API versions lack authorization checks present in newer versions

**Impact**: High. Attackers can use older API versions to bypass authorization.

**Remediation**: Maintain consistent authorization across all API versions. Deprecate and remove old API versions. Test authorization across all supported versions.

---

### Session Management Findings

### Weak Session Identifiers

**Description**: Session identifiers that are predictable, short, or not cryptographically random.

**Example Finding**:
```python
### VULNERABLE: Sequential session IDs
import time
session_id = str(int(time.time()))  # Predictable based on timestamp
```

Attackers can predict valid session identifiers and hijack sessions.

**Impact**: Critical. Attackers can hijack any session without stealing the identifier.

**Remediation**: Use cryptographically secure random number generators:
```python
import secrets
session_id = secrets.token_urlsafe(32)  # 256 bits of entropy
```

---

### Missing Secure Cookie Flags

**Description**: Session cookies lacking Secure, HttpOnly, or SameSite flags.

**Example Finding**:
```python
### VULNERABLE: Missing security flags
response.set_cookie('session_id', session_id)
```

- Without `Secure`: Cookie transmitted over HTTP, vulnerable to network sniffing
- Without `HttpOnly`: Cookie accessible to JavaScript, vulnerable to XSS
- Without `SameSite`: Cookie sent in cross-site requests, vulnerable to CSRF

**Impact**: High. Attackers can steal sessions through XSS or CSRF attacks.

**Remediation**:
```python
response.set_cookie(
    'session_id',
    session_id,
    secure=True,        # HTTPS only
    httponly=True,      # No JavaScript access
    samesite='Lax'      # CSRF protection
)
```

---

### Excessive Session Timeout

**Description**: Sessions that remain valid for extended periods without activity.

**Example Finding**:
- Session timeout of 30 days or more
- No idle timeout (session valid as long as user doesn't explicitly logout)
- No re-authentication for sensitive operations

**Impact**: Medium to High. Stolen sessions remain valid for extended periods.

**Remediation**: Implement both absolute and idle timeouts:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # Absolute timeout
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Reset idle timer on each request
```

---

### Session Hijacking Through XSS

**Description**: Session cookies accessible to JavaScript, allowing XSS attacks to steal sessions.

**Example Finding**:
```python
### VULNERABLE: HttpOnly flag missing
response.set_cookie('session_id', session_id, httponly=False)
```

An XSS vulnerability allows attackers to execute JavaScript that steals the session cookie.

**Impact**: Critical. XSS vulnerabilities can lead to session hijacking.

**Remediation**: Always use the `HttpOnly` flag on session cookies. Additionally, implement Content Security Policy (CSP) to prevent XSS attacks.

---

### Concurrent Session Vulnerabilities

**Description**: Improper handling of concurrent sessions allowing session fixation or hijacking.

**Example Finding**:
- Multiple concurrent sessions allowed without notification
- No detection of unusual concurrent session patterns
- Session from one device doesn't invalidate sessions on other devices

**Impact**: Medium. Attackers can maintain persistent access even if the user changes their password.

**Remediation**: Implement concurrent session limits or detection:
```python
def login(username, password):
    user = authenticate_user(username, password)
    if user:
        # Invalidate previous sessions
        invalidate_user_sessions(user.id)
        
        # Create new session
        session['user_id'] = user.id
        return redirect('/dashboard')
```

---

### Token-Based Authentication Findings

### JWT Signature Verification Bypass

**Description**: JWT tokens accepted without verifying the signature or with signature verification disabled.

**Example Finding**:
```python
### VULNERABLE: Signature verification disabled
payload = jwt.decode(token, options={"verify_signature": False})
```

Attackers can forge JWT tokens that the application will accept.

**Impact**: Critical. Attackers can create valid-appearing tokens for any user.

**Remediation**: Always verify JWT signatures:
```python
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
```

---

### JWT Algorithm Confusion

**Description**: JWT libraries accepting tokens signed with unexpected algorithms, particularly accepting unsigned tokens or tokens signed with the wrong algorithm.

**Example Finding**:
```python
### VULNERABLE: Accepting any algorithm
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256', 'RS256', 'none'])
```

An attacker can create a token signed with the `none` algorithm (no signature) that the application will accept.

**Impact**: Critical. Attackers can forge tokens without knowing the signing key.

**Remediation**: Explicitly specify the expected algorithm:
```python
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
```

---

### Missing JWT Expiration Validation

**Description**: JWT tokens lacking expiration claims or expiration not validated.

**Example Finding**:
```python
### VULNERABLE: No expiration in token
payload = {
    'user_id': user.id,
    'username': user.username
    # Missing 'exp' claim
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

Tokens remain valid indefinitely, allowing attackers to use stolen tokens permanently.

**Impact**: High. Stolen tokens provide permanent access.

**Remediation**: Include expiration claims and validate them:
```python
payload = {
    'user_id': user.id,
    'exp': datetime.utcnow() + timedelta(hours=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

### Validation automatically checks expiration
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
```

---

### Sensitive Data in JWT Payload

**Description**: Sensitive information stored in JWT payload, which is base64-encoded but not encrypted.

**Example Finding**:
```python
### VULNERABLE: Sensitive data in JWT
payload = {
    'user_id': user.id,
    'email': user.email,
    'ssn': user.ssn,  # Sensitive!
    'credit_card': user.credit_card,  # Sensitive!
    'is_admin': user.is_admin
}
```

Anyone with the token can decode it and view sensitive information.

**Impact**: Medium to High. Sensitive data exposure.

**Remediation**: Store only necessary claims in JWT. Retrieve sensitive data from the server:
```python
payload = {
    'user_id': user.id,
    'exp': datetime.utcnow() + timedelta(hours=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

### Retrieve user details from server when needed
user = get_user(payload['user_id'])
```

---

### Token Reuse and Replay Attacks

**Description**: Tokens lacking mechanisms to prevent reuse or replay attacks.

**Example Finding**:
- No token versioning or revocation mechanism
- Tokens valid across different services or contexts
- No binding of tokens to specific clients or sessions

**Impact**: Medium. Stolen tokens can be reused indefinitely.

**Remediation**: Implement token revocation and binding:
```python
### Include token version/jti (JWT ID)
payload = {
    'user_id': user.id,
    'jti': secrets.token_urlsafe(16),  # Unique token ID
    'exp': datetime.utcnow() + timedelta(hours=1)
}

### Maintain revocation list
revoked_tokens = set()

def revoke_token(jti):
    revoked_tokens.add(jti)

def verify_token(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    if payload['jti'] in revoked_tokens:
        raise ValueError('Token has been revoked')
    return payload
```

---

### Identity Provider and Federation Findings

### Insecure Redirect in OAuth/OIDC

**Description**: Open redirect vulnerabilities in OAuth/OIDC redirect_uri parameter.

**Example Finding**:
```python
### VULNERABLE: No validation of redirect_uri
@app.route('/oauth/callback')
def oauth_callback():
    redirect_uri = request.args.get('redirect_uri')
    # No validation - attacker can redirect to malicious site
    return redirect(redirect_uri)
```

Attackers can redirect users to malicious sites after authentication.

**Impact**: Medium. Phishing attacks, credential theft.

**Remediation**: Validate redirect URIs against a whitelist:
```python
ALLOWED_REDIRECT_URIS = [
    'https://app.example.com/callback',
    'https://app.example.com/oauth/callback'
]

@app.route('/oauth/callback')
def oauth_callback():
    redirect_uri = request.args.get('redirect_uri')
    if redirect_uri not in ALLOWED_REDIRECT_URIS:
        abort(400)
    return redirect(redirect_uri)
```

---

### Missing CSRF Protection in OAuth Flow

**Description**: OAuth/OIDC flows lacking state parameter validation for CSRF protection.

**Example Finding**:
```python
### VULNERABLE: No state parameter
@app.route('/oauth/authorize')
def oauth_authorize():
    # No state parameter generated
    auth_url = f"{OAUTH_PROVIDER}/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return redirect(auth_url)

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    # No state validation
    token = exchange_code_for_token(code)
    return token
```

Attackers can perform CSRF attacks to link the victim's account with the attacker's account.

**Impact**: Medium. Account linking attacks.

**Remediation**: Implement state parameter validation:
```python
@app.route('/oauth/authorize')
def oauth_authorize():
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    auth_url = f"{OAUTH_PROVIDER}/authorize?client_
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
