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

The secure approach uses bcrypt, which is specifically designed for password hashing. The `rounds` parameter controls the computational cost—higher values make brute-force attacks more expensive but also increase legitimate authentication latency. The insecure approach uses SHA-256, which is fast (making brute-force attacks feasible) and lacks salt (enabling rainbow table attacks).

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
        # Session identifier is