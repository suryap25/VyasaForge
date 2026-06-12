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

**Identity** is the unique representation of a user, service, or system within an application context. An identity answers the question "Who are you?" Identity can be represented by usernames, email addresses, user IDs, service principals, or device identifiers. In distributed systems, identity becomes more complex—a user might have multiple identities across different systems, and applications must establish trust relationships to recognize identities from other domains. Identity is not inherently trustworthy; it is merely a claim that must be verified through authentication.

**Authentication** is the process of verifying that an identity is genuine. It answers "Prove that you are who you claim to be." Authentication mechanisms range from simple password verification to multi-factor approaches combining something you know (password), something you have (hardware token, phone), and something you are (biometric). The strength of authentication directly impacts the security of everything downstream—a compromised authentication mechanism undermines all subsequent authorization decisions. Authentication is a point of high leverage in security: a single strong authentication mechanism can protect many downstream systems, while a weak authentication mechanism exposes all of them.

**Authorization** is the process of determining what an authenticated identity is permitted to do. It answers "What are you allowed to access?" Authorization operates on the principle of least privilege: users should have access only to resources and operations necessary for their role or function. Authorization decisions are made based on policies that consider the identity, the requested resource, the requested action, and contextual factors like time, location, or device posture. Critically, authorization must be enforced server-side; client-side authorization checks are security theater and provide no actual protection.

**Access Control** is the enforcement mechanism that implements authorization decisions. Access control systems evaluate requests against policies and either permit or deny access. Access control models vary significantly—from simple role-based access control (RBAC) to attribute-based access control (ABAC) to policy-based systems. The choice of access control model affects both security and operational complexity. RBAC is simpler but less flexible; ABAC is more flexible but requires more sophisticated policy engines and careful policy design to avoid unintended access grants.

**Session Management** bridges authentication and authorization. After successful authentication, applications must maintain state about the authenticated user across multiple requests. Sessions represent this authenticated state and are typically managed through tokens, cookies, or server-side session stores. Session management is critical because weak session handling can allow attackers to hijack authenticated sessions without compromising the original authentication credentials. Session security depends on three factors: secure session identifier generation, secure session storage, and secure session transmission.

**Credentials** are the secrets or artifacts used to prove identity during authentication. Passwords are the most common credential type, but credentials also include API keys, certificates, tokens, and biometric data. Credential management—how credentials are stored, transmitted, rotated, and revoked—is a critical security concern. Credentials should be treated as high-value secrets; any system handling credentials requires careful threat modeling and implementation review.

These concepts form an integrated system. A user authenticates using credentials, establishing their identity. The system then authorizes specific actions based on that identity. Access control mechanisms enforce those authorization decisions. Sessions maintain the authenticated state across interactions. Each component must be secure; weakness in any component compromises the entire system. A common failure mode is over-investing in authentication security while neglecting authorization—strong authentication is worthless if authorization checks are missing or bypassable.

## Architecture Perspective

IAM systems operate across multiple architectural layers, and understanding these layers is essential for designing secure applications.

### The Authentication Layer

The authentication layer is where identity verification occurs. In traditional monolithic applications, authentication might be handled entirely within the application. In modern distributed architectures, authentication is often delegated to specialized services.

**Direct Authentication** occurs when the application directly verifies credentials. The user submits credentials (typically username and password), the application validates them against a credential store, and if valid, the application establishes an authenticated session. This approach is straightforward but places significant responsibility on the application to securely handle credentials. The application must implement secure password hashing, protect the credential store from unauthorized access, and prevent credential leakage through logs or error messages. Direct authentication is appropriate for applications with simple authentication requirements and strong internal security practices.

**Federated Authentication** delegates authentication to an external identity provider. The application redirects the user to the identity provider, which handles credential verification. Upon successful authentication, the identity provider returns an assertion (typically a token or SAML response) that the application trusts. This approach reduces the application's responsibility for credential handling but introduces dependency on the identity provider's security and requires careful validation of identity assertions. Federated authentication is appropriate for applications that need to support multiple identity providers or that want to reduce credential handling responsibility. However, federated authentication introduces new attack vectors: identity assertion forgery, insecure redirect URIs, and trust relationship exploitation.

**Multi-Factor Authentication (MFA)** requires multiple independent verification methods. Common factors include:
- Knowledge factors (passwords, security questions)
- Possession factors (hardware tokens, mobile devices, authenticator apps)
- Inherence factors (biometrics: fingerprint, facial recognition)
- Location factors (geographic verification, IP-based checks)

MFA significantly increases authentication security by requiring attackers to compromise multiple independent systems. However, MFA implementation introduces complexity and potential usability challenges. SMS-based MFA is vulnerable to SIM swapping attacks; email-based MFA is vulnerable if email accounts are compromised; authenticator apps are more secure but require device possession. Hardware keys (FIDO2/WebAuthn) provide the strongest MFA but have higher user friction. The choice of MFA method involves tradeoffs between security and usability.

### The Authorization Layer

Authorization decisions must be made consistently across the application. Centralized authorization policies ensure consistency and simplify policy management.

**Role-Based Access Control (RBAC)** assigns users to roles, and roles have associated permissions. For example, a "Manager" role might have permissions to "approve_expenses" and "view_team_reports." RBAC is intuitive and scales reasonably well for many applications. However, RBAC can become unwieldy when fine-grained permissions are needed or when authorization depends on resource attributes rather than just user roles. A common RBAC failure mode is role explosion: as applications grow, the number of roles multiplies, making policy management difficult and increasing the likelihood of misconfiguration.

**Attribute-Based Access Control (ABAC)** makes authorization decisions based on attributes of the user, resource, action, and environment. For example: "Allow access to medical_records if (user.department == 'healthcare' AND resource.classification == 'internal' AND current_time between 09:00 and 17:00)." ABAC is more flexible than RBAC but requires more sophisticated policy engines and can be more difficult to audit. ABAC policies can become complex and difficult to reason about; a common failure mode is overly permissive policies that grant unintended access due to logical errors.

**Access Control Lists (ACLs)** specify which principals have access to specific resources. ACLs are often used for fine-grained resource-level access control. For example, a document might have an ACL specifying that user_alice has "read" access and user_bob has "read_write" access. ACLs are effective for resource-level access control but scale poorly when managing access across many resources. ACLs also require careful handling of default permissions; a common failure mode is overly permissive default ACLs that grant unintended access.

### The Session Management Layer

Sessions maintain authenticated state across multiple requests. Session management architecture varies significantly:

**Server-Side Sessions** store session state on the server. The client receives a session identifier (typically in a cookie), and each request includes this identifier. The server looks up the session state and retrieves the associated user identity. This approach gives the server complete control over session state and enables easy session revocation. Server-side sessions are more secure than token-based sessions because the server can immediately invalidate sessions. However, server-side sessions require server-side state storage, which can be a scalability challenge in distributed systems. Server-side sessions also require careful handling of session storage: if the session store is compromised, all active sessions are compromised.

**Token-Based Sessions** encode session information in a cryptographically signed token. The client stores the token and includes it with each request. The server validates the token signature and extracts session information without needing to look up state. This approach is stateless from the server perspective and scales well in distributed systems, but token revocation is more complex. If a token is compromised, the attacker can use it until the token expires; there is no way to immediately revoke a compromised token without maintaining a revocation list (which reintroduces server-side state). Token-based sessions are appropriate for distributed systems and APIs but require careful token expiration policies and revocation mechanisms.

**Hybrid Approaches** combine server-side and token-based mechanisms. For example, a short-lived access token might be paired with a longer-lived refresh token stored server-side, enabling both scalability and revocation capabilities. The access token is used for authorization decisions (avoiding server-side lookups), while the refresh token is used to issue new access tokens and can be revoked server-side. This approach provides a good balance between scalability and security.

### The Credential Storage Layer

How credentials are stored is critical to IAM security. Credentials should never be stored in plaintext.

**Password Hashing** uses cryptographic hash functions to store passwords irreversibly. When a user authenticates, the submitted password is hashed and compared to the stored hash. Modern password hashing should use algorithms specifically designed for password storage, such as bcrypt, scrypt, or Argon2, which are intentionally slow to resist brute-force attacks. The computational cost of these algorithms should be calibrated to take approximately 100-500 milliseconds per authentication attempt; this is slow enough to make brute-force attacks infeasible but fast enough for legitimate users to authenticate in reasonable time.

**Salting** adds random data to passwords before hashing, ensuring that identical passwords produce different hashes. This prevents rainbow table attacks where attackers precompute hashes for common passwords. Modern password hashing algorithms (bcrypt, scrypt, Argon2) include salting automatically; explicit salting is not necessary when using these algorithms.

**Key Derivation Functions (KDFs)** derive cryptographic keys from passwords. KDFs like PBKDF2 apply the hash function many times (thousands or millions), making brute-force attacks computationally expensive. KDFs are appropriate for deriving encryption keys from passwords but should not be used for password storage; password-specific hashing algorithms are more appropriate for password storage.

## AppSec Lens

From an application security perspective, IAM systems present numerous attack vectors and require careful threat modeling.

### Authentication Attacks

**Credential Compromise** occurs when attackers obtain valid credentials through phishing, malware, data breaches, or social engineering. Once credentials are compromised, attackers can authenticate as legitimate users. Mitigation strategies include MFA (which prevents authentication even with compromised passwords), credential monitoring (detecting when credentials appear in breach databases), and user education. Credential compromise is particularly dangerous because it is difficult to detect; the attacker authenticates with valid credentials and appears as a legitimate user.

**Brute Force Attacks** attempt to guess credentials by trying many password combinations. Attackers might target a known username with many passwords or try common username/password combinations. Mitigations include rate limiting (limiting the number of login attempts per username or IP address), account lockout policies (temporarily disabling accounts after failed attempts), and strong password requirements. However, account lockout can enable denial-of-service attacks where attackers lock out legitimate users, so rate limiting is often preferred. Rate limiting should be implemented at multiple levels: per username, per IP address, and globally.

**Credential Stuffing** uses credentials compromised from one service to attack other services, exploiting password reuse. Mitigations include detecting unusual login patterns (logins from new locations or devices), requiring MFA, and monitoring for compromised credentials. Services like HaveIBeenPwned provide APIs to check if credentials have appeared in known breaches.

**Session Fixation** tricks a user into using a session identifier controlled by the attacker. The attacker creates a session, tricks the user into authenticating with that session identifier (typically through a crafted link), and then uses the same identifier to access the user's account. Mitigation requires regenerating session identifiers after successful authentication. Most modern frameworks handle this automatically, but custom session implementations must explicitly regenerate session identifiers.

**Session Hijacking** involves stealing a valid session identifier and using it to impersonate the authenticated user. Session identifiers might be stolen through network sniffing (if transmitted over unencrypted connections), cross-site scripting (XSS) attacks, or malware. Mitigations include using HTTPS (preventing network sniffing), secure cookie flags (preventing XSS-based theft), short session timeouts (limiting the window of opportunity), and detecting anomalous session usage (logins from unusual locations or devices).

### Authorization Attacks

**Privilege Escalation** occurs when users gain access to resources or operations beyond their authorized permissions. Vertical privilege escalation involves gaining higher-level permissions (e.g., a regular user becoming an administrator). Horizontal privilege escalation involves accessing resources belonging to other users at the same privilege level. Privilege escalation is often the result of missing or inconsistent authorization checks.

**Insecure Direct Object References (IDOR)** occur when authorization checks are insufficient for resource access. For example, an API endpoint `/api/users/123/profile` might return the profile for user 123 without verifying that the requesting user has permission to view that profile. An attacker could simply change the user ID to access other users' profiles. IDOR is one of the most common authorization vulnerabilities because it is easy to overlook: developers often implement authentication checks but forget to implement authorization checks at the resource level.

**Broken Access Control** encompasses various authorization failures where access control mechanisms are improperly implemented. This might include missing authorization checks, inconsistent authorization logic across different endpoints, or authorization bypasses through parameter manipulation. Broken access control is the most common vulnerability category in modern applications.

**Attribute Injection** involves manipulating user attributes to bypass authorization. For example, if an application stores user roles in a client-side cookie without integrity protection, an attacker could modify the cookie to grant themselves additional roles. Attribute injection is a consequence of trusting client-provided data for authorization decisions.

### Identity Spoofing

**Identity Spoofing** occurs when attackers impersonate legitimate users or services. In federated authentication scenarios, attackers might forge identity assertions or exploit trust relationships between identity providers and service providers. Identity spoofing is particularly dangerous in federated scenarios because the application trusts the identity provider; if the identity provider is compromised or if the application incorrectly validates identity assertions, attackers can impersonate any user.

**Token Forgery** involves creating fraudulent authentication tokens. If tokens are not properly signed or if signing keys are compromised, attackers can create valid-appearing tokens that the application will accept. Token forgery is a critical vulnerability in token-based authentication systems.

## Developer Lens

Developers implementing IAM systems must balance security with usability and performance. This section provides practical guidance for secure implementation.

### Authentication Implementation

**Password Storage Best Practices:**

```python
# SECURE: Using bcrypt for password hashing
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with automatic salt generation."""
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds provides good security/performance balance
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# INSECURE: Using simple SHA-256 without salt
import hashlib

def insecure_hash_password(password: str) -> str:
    """DO NOT USE: Simple SHA-256 without salt."""
    return hashlib.sha256(password.encode()).hexdigest()
```

The secure approach uses bcrypt, which is specifically designed for password hashing. The `rounds` parameter controls the computational cost—higher values make brute-force attacks more expensive but also increase legitimate authentication latency. A value of 12 rounds typically takes 100-300 milliseconds on modern hardware, which is acceptable for most applications. The insecure approach uses SHA-256, which is fast (making brute-force attacks feasible) and lacks salt (enabling rainbow table attacks). Additionally, SHA-256 is a general-purpose cryptographic hash, not designed for password storage; it does not include mechanisms to slow down hash computation.

**Operational Consideration**: When migrating from weak password hashing to strong password hashing, consider a gradual migration approach: hash new passwords with the strong algorithm, and upgrade existing password hashes when users next authenticate. This avoids the need to force all users to reset passwords immediately.

**Session Management Best Practices:**

```python
# SECURE: Server-side session with secure cookie
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

# INSECURE: Client-side session without integrity protection
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

The secure approach uses server-side sessions with secure cookie flags. The `SECURE` flag ensures cookies are only transmitted over HTTPS, preventing network sniffing attacks. The `HTTPONLY` flag prevents JavaScript from accessing the cookie, mitigating XSS-based session theft. The `SAMESITE` flag provides CSRF protection by preventing the browser from sending the cookie in cross-site requests. The `PERMANENT_SESSION_LIFETIME` sets an absolute timeout; sessions expire after this duration regardless of activity. The insecure approach stores user data in cookies without integrity protection, allowing attackers to modify their own role or user ID.

**Operational Consideration**: The `SAMESITE` attribute has three values: `Strict` (never send in cross-site requests), `Lax` (send in top-level navigations but not in subresource requests), and `None` (always send, requires `Secure`). `Lax` is a good default that provides CSRF protection while maintaining reasonable usability.

**Authorization Implementation:**

```python
# SECURE: Centralized authorization with decorator
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

# INSECURE: Client-side authorization
@app