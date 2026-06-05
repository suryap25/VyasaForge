---
chapter: 1
stage: final
source: drafts
generated_by: appsec-handbook-agent
---

# Authentication vs Authorization

## Learning Objectives

After reading this chapter, you will be able to:

- Define authentication and authorization and explain their distinct roles in application security
- Identify why authentication and authorization failures occur in real applications
- Recognize common architectural patterns that conflate these concerns
- Design authentication and authorization systems that maintain proper separation of concerns
- Review code and architecture for authentication and authorization vulnerabilities
- Implement practical controls that verify both identity and permissions
- Conduct security interviews using authentication and authorization as a lens

## Conceptual Foundation

Authentication and authorization are foundational security concepts that are frequently confused, conflated, or implemented as a single monolithic system. This confusion creates security gaps that attackers exploit routinely. Understanding the distinction between these two concepts is essential for anyone designing, building, or reviewing application security controls.

**Authentication** answers the question: "Who are you?" It is the process of verifying that a user is who they claim to be. Authentication establishes identity through evidence—something you know (a password), something you have (a hardware token or phone), or something you are (biometric data). Once authentication succeeds, the system has reasonable confidence about the user's identity.

**Authorization** answers the question: "What are you allowed to do?" It is the process of determining whether an authenticated user has permission to perform a specific action or access a specific resource. Authorization is the enforcement of access control policies based on the authenticated identity and the context of the request.

The critical distinction is this: authentication is about identity verification, while authorization is about permission enforcement. A system can authenticate a user perfectly but fail catastrophically at authorization. Conversely, a system might have strong authorization logic but weak authentication, allowing attackers to impersonate legitimate users.

Consider a practical example: A user logs into a banking application with their username and password. The authentication system verifies the credentials against a stored hash and establishes a session. This is authentication—the system now knows who the user is. When that user attempts to view their account balance, the authorization system checks whether the authenticated user has permission to view that specific account. If the user tries to view another customer's account, authorization should deny the request, even though the user is authenticated.

Many security breaches occur not because authentication failed, but because authorization was missing or improperly implemented. A user might be authenticated, but the application fails to verify that they have permission to perform the requested action. This is sometimes called a "broken access control" vulnerability, and it consistently ranks among the most common and impactful application security issues.

## Architecture Perspective

From an architectural standpoint, authentication and authorization should be treated as separate concerns, even though they are often implemented in proximity to each other. This separation of concerns principle is critical for building secure, maintainable systems.

### Authentication Architecture

Authentication systems typically consist of several components:

**Identity Provider (IdP)**: The system responsible for verifying credentials and issuing proof of identity. This might be a local authentication service, an LDAP directory, or a third-party service like Okta or Azure AD.

**Credential Storage**: The secure storage of authentication material. Passwords should be hashed using a strong algorithm (bcrypt, Argon2, or PBKDF2). Multi-factor authentication (MFA) credentials should be stored securely, with backup codes encrypted.

**Session Management**: The mechanism for maintaining authenticated state across multiple requests. This might be session tokens, JWT tokens, or cookies. The session must be cryptographically secure, resistant to tampering, and properly invalidated on logout.

**Authentication Gateway**: The entry point where credentials are exchanged for proof of identity. This is typically an HTTP endpoint that accepts credentials and returns a token or session identifier.

A typical authentication flow looks like this:

1. User submits credentials to the authentication gateway
2. The gateway verifies credentials against stored identity data
3. If credentials are valid, the gateway issues a token or session identifier
4. The client includes this token in subsequent requests
5. The application verifies the token is valid and has not expired

### Authorization Architecture

Authorization systems are typically implemented as a layer that sits between the authenticated request and the business logic. Authorization decisions should be made before sensitive operations execute.

**Access Control Models**: Different authorization models exist, including:

- **Role-Based Access Control (RBAC)**: Users are assigned roles, and roles have permissions. A user with the "admin" role can perform administrative actions.
- **Attribute-Based Access Control (ABAC)**: Permissions are determined by attributes of the user, resource, and environment. A user might be allowed to view a document if they are in the same department as the document owner.
- **Access Control Lists (ACLs)**: Specific permissions are granted to specific users for specific resources.

**Policy Enforcement Point (PEP)**: The component that intercepts requests and enforces authorization policies. This might be middleware in a web framework, a proxy, or code within the application itself.

**Policy Decision Point (PDP)**: The component that evaluates authorization policies and makes decisions. This might be a dedicated service or logic embedded in the application.

A typical authorization flow looks like this:

1. An authenticated request arrives at the application
2. The PEP extracts the user's identity and the requested action
3. The PEP queries the PDP with the user's identity, the action, and the resource
4. The PDP evaluates policies and returns a permit or deny decision
5. If the decision is permit, the business logic executes; if deny, an error is returned

### Architectural Separation

The key architectural principle is that authentication and authorization should not be tightly coupled. A common anti-pattern is to embed authorization logic directly in the authentication system, or to assume that successful authentication implies authorization for all actions.

Consider a microservices architecture: A central authentication service issues tokens to authenticated users. Each microservice receives the token and must independently verify that the user has permission to perform the requested action. The authentication service does not make authorization decisions for individual microservices; it only verifies identity. Each service is responsible for enforcing its own authorization policies.

This separation allows:

- **Independent scaling**: Authentication and authorization can be scaled independently based on demand
- **Flexible policies**: Different services can have different authorization policies without modifying the authentication system
- **Auditability**: Authorization decisions can be logged and audited separately from authentication events
- **Resilience**: If the authorization system is unavailable, authentication can still function (though requests will be denied)

## AppSec Lens

From an application security perspective, authentication and authorization failures are among the most exploited vulnerabilities in production systems. The OWASP Top 10 consistently includes broken authentication and broken access control as critical risks.

### Authentication Failures

Authentication failures occur when:

- **Weak credential validation**: The system accepts weak passwords, allows credential reuse, or fails to enforce password complexity
- **Insecure credential transmission**: Credentials are transmitted over unencrypted channels or logged in plaintext
- **Insecure credential storage**: Passwords are stored in plaintext, hashed with weak algorithms, or stored without salt
- **Session fixation**: An attacker can force a user to use a known session identifier
- **Session hijacking**: An attacker can steal or predict session tokens
- **Lack of MFA**: The system relies solely on passwords, which are vulnerable to phishing and credential stuffing
- **Credential stuffing**: Attackers use leaked credentials from other systems to gain access
- **Brute force attacks**: The system does not rate-limit authentication attempts

### Authorization Failures

Authorization failures occur when:

- **Missing authorization checks**: The application performs an action without verifying the user has permission
- **Insecure direct object references (IDOR)**: A user can access resources belonging to other users by manipulating object identifiers
- **Privilege escalation**: A user can perform actions reserved for higher-privilege users
- **Horizontal access control bypass**: A user can access resources belonging to other users at the same privilege level
- **Vertical access control bypass**: A user can access resources or perform actions reserved for higher-privilege users
- **Function-level access control bypass**: A user can access administrative functions without proper authorization
- **Data-level access control bypass**: A user can access data they should not have permission to view

### Real-World Examples

**Example 1: Authentication Without Authorization**

A SaaS application implements strong authentication: users must provide a username, password, and a code from an authenticator app. However, the authorization system is weak. Once authenticated, a user can view any other user's data by changing a user ID in the URL from `/api/users/123/profile` to `/api/users/124/profile`. The application verifies that the request includes a valid authentication token but does not verify that the authenticated user has permission to access user 124's profile. This is a classic IDOR vulnerability.

**Example 2: Authorization Without Authentication**

An internal API endpoint is protected by authorization checks—it verifies that the user has the "admin" role before allowing access. However, the endpoint does not require authentication. An attacker can call the endpoint without any credentials, and the authorization check fails because there is no authenticated user. The application should have verified authentication before checking authorization.

**Example 3: Conflating Authentication and Authorization**

A legacy application stores user credentials and permissions in a single table:

```
users:
  id: 1
  username: alice
  password_hash: $2b$12$...
  role: admin
  is_authenticated: true
```

The application sets `is_authenticated = true` after verifying the password. Later, when a user requests an action, the application checks `is_authenticated` and `role`. However, the `is_authenticated` flag is never cleared when the user logs out—it remains true indefinitely. An attacker who gains access to the database can set `is_authenticated = true` for any user, effectively authenticating as that user without knowing their password.

**Example 4: Trusting Client-Side Authorization**

A web application implements authorization checks in JavaScript on the client side. The application hides certain UI elements based on the user's role:

```javascript
if (user.role === 'admin') {
  showAdminPanel();
}
```

However, the server does not enforce authorization. An attacker can open the browser console, modify the `user.role` variable to `'admin'`, and call the API endpoints directly. The server accepts the requests because it trusts the client's claim about the user's role.

## Developer Lens

From a developer's perspective, implementing authentication and authorization correctly requires understanding both the technical mechanisms and the common pitfalls.

### Authentication Implementation

When implementing authentication, follow these principles:

**Use Strong Hashing Algorithms**: Never store passwords in plaintext. Use bcrypt, Argon2, or PBKDF2 with a high iteration count. These algorithms are intentionally slow, making brute force attacks computationally expensive.

```python
# Good: Using bcrypt
import bcrypt

password = "user_password"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
# Store hashed in database

# Verify password
if bcrypt.checkpw(password.encode(), hashed):
    # Password is correct
    pass
```

**Implement Rate Limiting**: Limit the number of authentication attempts from a single IP address or user account to prevent brute force attacks.

```python
# Pseudocode: Rate limiting on authentication attempts
def authenticate(username, password):
    attempts = get_recent_attempts(username)
    if attempts > 5:
        raise RateLimitError("Too many attempts")
    
    user = find_user(username)
    if not user or not verify_password(password, user.password_hash):
        log_failed_attempt(username)
        raise AuthenticationError("Invalid credentials")
    
    return create_session(user)
```

**Use Secure Session Management**: Session tokens should be cryptographically random, long enough to resist brute force attacks, and stored securely on the client (in secure, HTTP-only cookies or in memory).

```python
# Good: Generating a secure session token
import secrets

def create_session(user):
    token = secrets.token_urlsafe(32)  # 256 bits of entropy
    session = Session(
        user_id=user.id,
        token=hash_token(token),  # Hash the token before storing
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1)
    )
    db.session.add(session)
    db.session.commit()
    return token
```

**Implement Multi-Factor Authentication**: Require users to provide a second factor of authentication, such as a code from an authenticator app or a hardware token.

```python
# Pseudocode: MFA flow
def authenticate_with_mfa(username, password, mfa_code):
    user = find_user(username)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid credentials")
    
    if not verify_mfa_code(user, mfa_code):
        raise AuthenticationError("Invalid MFA code")
    
    return create_session(user)
```

**Transmit Credentials Over HTTPS**: Always use HTTPS to encrypt credentials in transit. Never transmit credentials over HTTP.

### Authorization Implementation

When implementing authorization, follow these principles:

**Check Authorization Before Executing Business Logic**: Authorization checks should be the first thing that happens when processing a request, before any business logic executes.

```python
# Good: Authorization check before business logic
@app.route('/api/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    # Step 1: Verify authentication
    current_user = get_authenticated_user()
    if not current_user:
        return error("Unauthorized", 401)
    
    # Step 2: Verify authorization
    if not can_view_user_profile(current_user, user_id):
        return error("Forbidden", 403)
    
    # Step 3: Execute business logic
    user = find_user(user_id)
    return user.profile
```

**Use a Consistent Authorization Framework**: Implement authorization checks consistently across the application. Use a framework or library that enforces authorization policies uniformly.

```python
# Good: Using a decorator for authorization
def require_permission(permission):
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = get_authenticated_user()
            if not current_user or not current_user.has_permission(permission):
                return error("Forbidden", 403)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/admin/users', methods=['GET'])
@require_permission('admin.view_users')
def list_all_users():
    return find_all_users()
```

**Avoid Trusting Client-Side Authorization**: Never rely on client-side checks for authorization. Always verify authorization on the server.

```python
# Bad: Trusting client-side role
@app.route('/api/admin/delete-user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # This is bad—the client claims to be an admin, but we don't verify
    if request.json.get('role') == 'admin':
        delete_user_from_db(user_id)
        return success()

# Good: Verifying authorization on the server
@app.route('/api/admin/delete-user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    current_user = get_authenticated_user()
    if not current_user or not current_user.is_admin:
        return error("Forbidden", 403)
    delete_user_from_db(user_id)
    return success()
```

**Implement Attribute-Based Access Control for Complex Scenarios**: When authorization rules are complex, use ABAC to express policies clearly.

```python
# Pseudocode: ABAC for document access
def can_view_document(user, document):
    # User can view if:
    # 1. They are the owner, OR
    # 2. They are in the same department and the document is marked as shared, OR
    # 3. They are an admin
    
    if user.id == document.owner_id:
        return True
    
    if user.department == document.department and document.is_shared:
        return True
    
    if user.is_admin:
        return True
    
    return False
```

**Log Authorization Decisions**: Log both successful and failed authorization checks for audit and forensic purposes.

```python
# Good: Logging authorization decisions
def check_authorization(user, action, resource):
    allowed = evaluate_policy(user, action, resource)
    
    if allowed:
        log_info(f"Authorization granted: user={user.id}, action={action}, resource={resource.id}")
    else:
        log_warning(f"Authorization denied: user={user.id}, action={action}, resource={resource.id}")
    
    return allowed
```

## Pentest Lens

From a penetration testing perspective, authentication and authorization are primary targets for exploitation. Testers look for specific patterns and weaknesses.

### Authentication Testing

Penetration testers test authentication by:

**Testing Credential Validation**:
- Attempting to register with weak passwords
- Attempting to register with duplicate usernames
- Attempting to use common passwords
- Testing password reset mechanisms for weaknesses

**Testing Session Management**:
- Attempting to predict or brute force session tokens
- Testing for session fixation vulnerabilities
- Testing for session timeout enforcement
- Attempting to use expired or invalidated sessions
- Testing for secure cookie flags (HttpOnly, Secure, SameSite)

**Testing MFA**:
- Attempting to bypass MFA
- Testing for MFA bypass through alternative authentication methods
- Testing for MFA code reuse
- Testing for MFA code prediction

**Testing Credential Transmission**:
- Intercepting credentials in transit to verify HTTPS is used
- Testing for credentials in logs or error messages
- Testing for credentials in browser history or cache

### Authorization Testing

Penetration testers test authorization by:

**Testing for Insecure Direct Object References (IDOR)**:
- Modifying object identifiers in requests to access other users' resources
- Testing for sequential or predictable object identifiers
- Testing for authorization checks on all CRUD operations

```
# Tester attempts to access another user's data
GET /api/users/123/profile  # Returns current user's profile
GET /api/users/124/profile  # Should return 403, but returns another user's profile
```

**Testing for Privilege Escalation**:
- Attempting to access administrative functions as a regular user
- Attempting to modify user roles or permissions
- Testing for authorization bypass through parameter manipulation

```
# Tester attempts to escalate privileges
POST /api/users/123/role
{
  "role": "admin"
}
# If the server accepts this without authorization checks, privilege escalation is possible
```

**Testing for Horizontal Access Control Bypass**:
- Attempting to access resources belonging to other users at the same privilege level
- Testing for authorization checks on all endpoints that access user-specific data

**Testing for Function-Level Access Control Bypass**:
- Attempting to call administrative API endpoints directly
- Testing for authorization checks on all endpoints, not just those visible in the UI

**Testing for Data-Level Access Control Bypass**:
- Attempting to access sensitive data through search, filter, or export functions
- Testing for authorization checks on data returned by queries

### Practical Testing Approach

A penetration tester might follow this approach:

1. **Map the application**: Identify all endpoints, parameters, and data flows
2. **Authenticate**: Establish an authenticated session as a regular user
3. **Test authorization on each endpoint**: For each endpoint, attempt to access resources that should be denied
4. **Test privilege escalation**: Attempt to perform actions reserved for higher-privilege users
5. **Test horizontal access control**: Attempt to access resources belonging to other users
6. **Test for IDOR**: Modify object identifiers to access other users' resources
7. **Document findings**: Record all authorization bypasses and privilege escalation vulnerabilities

## Common Findings

Based on thousands of security assessments, certain authentication and authorization vulnerabilities appear consistently:

### Finding 1: Missing Authorization Checks

**Description**: The application performs sensitive operations without verifying that the user has permission.

**Example**: A user can delete any document by calling `DELETE /api/documents/123` without the application checking whether the user owns the document or has permission to delete it.

**Impact**: High. An attacker can perform unauthorized actions, including modifying or deleting data belonging to other users.

**Root Cause**: Developers assume that authentication is sufficient and forget to implement authorization checks.

### Finding 2: Insecure Direct Object References (IDOR)

**Description**: The application uses predictable or sequential object identifiers, allowing attackers to access resources belonging to other users by modifying the identifier.

**Example**: A user can view another user's profile by changing the user ID in the URL from `/api/users/123/profile` to `/api/users/124/profile`.

**Impact**: High. An attacker can access sensitive data belonging to other users.

**Root Cause**: Developers use sequential IDs without implementing authorization checks, or they implement authorization checks that are easily bypassed.

### Finding 3: Privilege Escalation

**Description**: A user can perform actions reserved for higher-privilege users.

**Example**: A regular user can call an administrative API endpoint to delete other users or modify system settings.

**Impact**: Critical. An attacker can gain administrative access

# Secure Design Guidance

## Principle 1: Separate Authentication from Authorization

Design systems where authentication and authorization are distinct, independently testable components. Authentication should establish identity; authorization should enforce permissions. Never assume that successful authentication implies authorization for all actions.

**Implementation Pattern**:
- Create a dedicated authentication service or module responsible only for verifying credentials and issuing tokens
- Implement authorization as a separate layer that intercepts requests after authentication
- Use middleware or aspect-oriented programming to enforce authorization checks consistently
- Ensure each microservice or application component independently verifies authorization, even if they share a central authentication provider

**Example Architecture**:
```
Request → Authentication Middleware → Authorization Middleware → Business Logic
          (Verify token/session)      (Check permissions)        (Execute action)
```

## Principle 2: Implement Defense in Depth for Authentication

Use multiple authentication factors and mechanisms to prevent credential compromise. No single authentication method is foolproof; layering defenses increases the cost and complexity of attacks.

**Implementation Guidance**:
- Require multi-factor authentication (MFA) for all users, especially those with elevated privileges
- Implement rate limiting on authentication endpoints to prevent brute force attacks
- Use strong password hashing algorithms (Argon2, bcrypt with 12+ rounds, or PBKDF2 with 100,000+ iterations)
- Enforce password complexity requirements and prevent password reuse
- Implement account lockout after repeated failed authentication attempts
- Monitor for anomalous authentication patterns (impossible travel, unusual locations, unusual times)
- Use HTTPS exclusively for all authentication-related traffic
- Store authentication credentials and tokens securely, never in logs or error messages

## Principle 3: Default to Deny in Authorization

Implement authorization using a whitelist approach: explicitly grant permissions rather than denying them. Default to denying access unless the user has been explicitly granted permission.

**Implementation Pattern**:
```python
# Good: Whitelist approach (default deny)
def can_access_resource(user, resource):
    # Explicitly check if user has permission
    if user.has_permission(f"view:{resource.type}:{resource.id}"):
        return True
    if user.role == "admin":
        return True
    return False  # Default deny

# Bad: Blacklist approach (default allow)
def can_access_resource(user, resource):
    # Only deny if explicitly forbidden
    if user.is_banned:
        return False
    return True  # Default allow
```

## Principle 4: Enforce Authorization at Multiple Layers

Do not rely on a single authorization check. Implement authorization at the API layer, the business logic layer, and the data access layer. This prevents authorization bypasses through alternative code paths.

**Implementation Pattern**:
- API Layer: Verify authorization before accepting the request
- Business Logic Layer: Verify authorization before executing sensitive operations
- Data Access Layer: Filter query results to include only data the user is authorized to access
- Logging Layer: Log authorization decisions for audit purposes

**Example**:
```python
# API Layer
@app.route('/api/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    user = get_authenticated_user()
    if not user:
        return error("Unauthorized", 401)
    if not user.can_view_document(doc_id):  # Authorization check
        return error("Forbidden", 403)
    return fetch_document_from_service(doc_id)

# Business Logic Layer
def fetch_document_from_service(doc_id):
    user = get_authenticated_user()
    if not user.can_view_document(doc_id):  # Second authorization check
        raise PermissionError("User cannot view this document")
    return db.get_document(doc_id)

# Data Access Layer
def get_document(doc_id):
    user = get_authenticated_user()
    # Query only documents the user is authorized to view
    return db.query(Document).filter(
        Document.id == doc_id,
        Document.owner_id == user.id  # Third authorization check
    ).first()
```

## Principle 5: Use Unique, Non-Sequential Identifiers

Avoid using sequential or predictable identifiers for resources. Use UUIDs or other cryptographically random identifiers to prevent attackers from guessing valid resource identifiers.

**Implementation Guidance**:
- Use UUID v4 or similar cryptographically random identifiers for all resources
- If sequential IDs are necessary for business reasons, implement authorization checks on every access to ensure users can only access resources they own or have permission to access
- Never rely on the difficulty of guessing an identifier as a security control

**Example**:
```python
# Good: Using UUID
from uuid import uuid4

class Document(Base):
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String)

# Bad: Using sequential ID without authorization checks
class Document(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String)
    
    # Attacker can guess IDs: 1, 2, 3, 4, ...
```

## Principle 6: Implement Attribute-Based Access Control for Complex Scenarios

When authorization rules depend on multiple attributes (user attributes, resource attributes, environment attributes), use ABAC to express policies clearly and maintain them consistently.

**Implementation Pattern**:
- Define authorization policies as rules that evaluate user, resource, and environment attributes
- Centralize policy definitions to avoid duplication and inconsistency
- Use a policy language or framework (e.g., XACML, OPA, Casbin) for complex scenarios
- Test policies thoroughly, including edge cases and policy conflicts

**Example**:
```python
# ABAC policy: User can view document if:
# 1. User is the document owner, OR
# 2. User is in the same department and document is marked shared, OR
# 3. User is an admin, OR
# 4. User has explicit "view_document" permission

def can_view_document(user, document):
    # Attribute-based rules
    if user.id == document.owner_id:
        return True
    
    if (user.department == document.department and 
        document.is_shared and 
        user.department is not None):
        return True
    
    if user.role == "admin":
        return True
    
    if user.has_permission("view_document"):
        return True
    
    return False
```

## Principle 7: Validate Authorization on the Server, Never on the Client

Always enforce authorization on the server. Client-side authorization checks are for user experience only; they provide no security. An attacker can bypass client-side checks by modifying the client or calling the API directly.

**Implementation Guidance**:
- Implement all authorization logic on the server
- Use client-side checks only to improve user experience (hiding UI elements the user cannot access)
- Never trust claims about the user's role or permissions from the client
- Verify authorization for every API request, regardless of whether the request came from the official client

**Example**:
```python
# Bad: Trusting client-side role
@app.route('/api/admin/users', methods=['GET'])
def list_users():
    # Client sends role in request—this is not trustworthy
    if request.json.get('role') == 'admin':
        return get_all_users()
    return error("Forbidden", 403)

# Good: Verifying authorization on server
@app.route('/api/admin/users', methods=['GET'])
def list_users():
    user = get_authenticated_user()
    if not user or not user.is_admin:
        return error("Forbidden", 403)
    return get_all_users()
```

## Principle 8: Log and Monitor Authorization Events

Log both successful and failed authorization checks. Monitor for patterns that indicate authorization attacks, such as repeated failed attempts to access resources the user should not have access to.

**Implementation Guidance**:
- Log the user, the action, the resource, and the authorization decision
- Include timestamps and request context (IP address, user agent)
- Monitor for suspicious patterns: rapid authorization failures, attempts to access resources outside the user's normal scope, privilege escalation attempts
- Alert on critical authorization failures (e.g., attempts to access administrative functions)
- Retain logs for audit and forensic purposes

**Example**:
```python
import logging

def check_authorization(user, action, resource):
    allowed = evaluate_policy(user, action, resource)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user.id,
        'action': action,
        'resource_id': resource.id,
        'allowed': allowed,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    }
    
    if allowed:
        logging.info(f"Authorization granted: {log_entry}")
    else:
        logging.warning(f"Authorization denied: {log_entry}")
        # Alert if this is a critical resource
        if resource.is_critical:
            alert_security_team(log_entry)
    
    return allowed
```

## Principle 9: Use Secure Session Management

Implement session management that prevents session hijacking, session fixation, and session prediction attacks.

**Implementation Guidance**:
- Generate session tokens using a cryptographically secure random number generator
- Use tokens with sufficient entropy (at least 128 bits, preferably 256 bits)
- Hash session tokens before storing them in the database
- Set appropriate session timeouts (shorter for sensitive operations, longer for less sensitive operations)
- Implement session invalidation on logout
- Use secure, HTTP-only cookies for session tokens (set HttpOnly, Secure, and SameSite flags)
- Regenerate session tokens after authentication to prevent session fixation
- Implement absolute session timeouts (maximum session duration) and idle timeouts (maximum inactivity duration)

**Example**:
```python
import secrets
from datetime import datetime, timedelta

def create_session(user):
    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)  # 256 bits
    
    # Hash token before storing
    token_hash = hash_token(token)
    
    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        created_at=datetime.now(),
        last_activity=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=8),  # Absolute timeout
        idle_timeout=datetime.now() + timedelta(minutes=30)  # Idle timeout
    )
    db.session.add(session)
    db.session.commit()
    
    # Return token to client (not the hash)
    return token

def verify_session(token):
    token_hash = hash_token(token)
    session = db.query(Session).filter(Session.token_hash == token_hash).first()
    
    if not session:
        return None
    
    # Check absolute timeout
    if datetime.now() > session.expires_at:
        db.session.delete(session)
        db.session.commit()
        return None
    
    # Check idle timeout
    if datetime.now() > session.idle_timeout:
        db.session.delete(session)
        db.session.commit()
        return None
    
    # Update last activity
    session.last_activity = datetime.now()
    session.idle_timeout = datetime.now() + timedelta(minutes=30)
    db.session.commit()
    
    return session.user
```

## Principle 10: Implement Consistent Authorization Across All Interfaces

Ensure that authorization policies are enforced consistently across all interfaces: web UI, REST API, GraphQL API, webhooks, and any other interface that accesses protected resources.

**Implementation Guidance**:
- Centralize authorization logic so it can be reused across interfaces
- Use a framework or library that enforces authorization consistently
- Test authorization for each interface independently
- Document authorization policies clearly so developers can implement them correctly

---

# Interview Questions

## Authentication Questions

1. **Describe the difference between authentication and authorization. Why is this distinction important?**
   - *Expected Answer*: Authentication verifies identity (who you are); authorization determines permissions (what you can do). The distinction is important because a system can authenticate a user perfectly but fail at authorization, or vice versa. Conflating these concerns leads to security vulnerabilities.

2. **What are the risks of storing passwords in plaintext? What hashing algorithm would you recommend?**
   - *Expected Answer*: Plaintext passwords are vulnerable if the database is compromised. Recommended algorithms are Argon2 (most secure), bcrypt (12+ rounds), or PBKDF2 (100,000+ iterations). The candidate should understand that hashing is one-way and that salting prevents rainbow table attacks.

3. **How would you implement multi-factor authentication (MFA) in a web application? What are the trade-offs?**
   - *Expected Answer*: MFA requires a second factor (authenticator app, SMS, hardware token). Implementation involves generating and validating codes, storing MFA secrets securely, and providing backup codes. Trade-offs include increased security but reduced user convenience and increased support burden.

4. **Describe a session management vulnerability and how you would prevent it.**
   - *Expected Answer*: Vulnerabilities include session fixation (attacker forces user to use known session ID), session hijacking (attacker steals session token), and session prediction (attacker guesses session token). Prevention includes using cryptographically random tokens, HTTPS-only transmission, secure cookie flags (HttpOnly, Secure, SameSite), and session timeouts.

5. **What is credential stuffing, and how would you defend against it?**
   - *Expected Answer*: Credential stuffing is using leaked credentials from other systems to gain access. Defenses include rate limiting on authentication endpoints, account lockout after repeated failures, monitoring for anomalous authentication patterns, and requiring MFA.

## Authorization Questions

6. **Explain the difference between RBAC, ABAC, and ACLs. When would you use each?**
   - *Expected Answer*: 
     - RBAC: Users have roles, roles have permissions. Simple, scalable, good for most applications.
     - ABAC: Permissions based on user, resource, and environment attributes. Complex but flexible, good for fine-grained control.
     - ACLs: Specific permissions for specific users on specific resources. Granular but difficult to manage at scale.

7. **What is an Insecure Direct Object Reference (IDOR) vulnerability? How would you test for it?**
   - *Expected Answer*: IDOR occurs when an application uses predictable identifiers and fails to check authorization. Testing involves modifying object identifiers in requests to access resources belonging to other users. Prevention includes using non-sequential identifiers and implementing authorization checks on every access.

8. **Describe a privilege escalation vulnerability. How would you prevent it?**
   - *Expected Answer*: Privilege escalation allows a user to perform actions reserved for higher-privilege users. Prevention includes implementing authorization checks on all sensitive operations, using a whitelist approach (default deny), and testing authorization for each endpoint.

9. **How would you implement authorization in a microservices architecture?**
   - *Expected Answer*: A central authentication service issues tokens. Each microservice independently verifies authorization using the token and its own authorization policies. This allows services to have different policies without modifying the authentication system. Services should not trust claims about the user's role from other services.

10. **What is the principle of least privilege, and how would you implement it?**
    - *Expected Answer*: Users should have the minimum permissions necessary to perform their job. Implementation includes defining granular roles, assigning users to the least-privileged role that allows them to work, regularly auditing permissions, and removing unnecessary permissions.

## Architecture and Design Questions

11. **How would you design an authentication and authorization system for a new application?**
    - *Expected Answer*: The candidate should describe separating authentication from authorization, using a centralized identity provider, implementing authorization as a separate layer, using strong hashing and MFA, implementing rate limiting, logging authorization decisions, and testing thoroughly.

12. **Describe how you would implement authorization for a document management system where users can have different permissions on different documents.**
    - *Expected Answer*: Use ABAC or ACLs. For each document, define who can view, edit, and delete it. Implement authorization checks before returning documents or allowing modifications. Consider using a policy engine for complex rules.

13. **How would you handle authorization in a system with hierarchical roles (e.g., admin > manager > employee)?**
    - *Expected Answer*: Define permissions for each role. Higher-level roles inherit permissions from lower-level roles. Implement authorization checks that verify the user's role is at least the required level. Be careful with role inheritance to avoid unintended permission grants.

14. **What are the security implications of using JWT tokens for authentication? How would you mitigate risks?**
    - *Expected Answer*: JWTs are stateless but cannot be revoked immediately. Risks include token theft, token tampering, and inability to revoke tokens. Mitigations include using short expiration times, implementing token refresh mechanisms, signing tokens with a strong algorithm, and validating token signatures on every request.

15. **How would you implement single sign-on (SSO) securely?**
    - *Expected Answer*: Use an established protocol (SAML, OAuth 2.0, OpenID Connect). Validate tokens from the identity provider, implement proper session management, use HTTPS, and log authentication events. Be careful with token validation to prevent bypass attacks.

## Testing and Review Questions

16. **How would you test authentication in a security code review?**
    - *Expected Answer*: Check password hashing algorithm and iteration count, verify MFA is implemented, test rate limiting on authentication endpoints, verify HTTPS is used, check for credentials in logs, test session management, and verify account lockout after failed attempts.

17. **How would you test authorization in a security code review?**
    - *Expected Answer*: Verify authorization checks exist on all sensitive operations, test for IDOR vulnerabilities, test for privilege escalation, verify authorization is checked on the server (not client), test for horizontal and vertical access control bypass, and verify authorization is logged.

18. **Describe a security test plan for a REST API with authentication and authorization.**
    - *Expected Answer*: Test authentication (valid/invalid credentials, MFA, rate limiting), test authorization (access own resources, attempt to access others' resources, privilege escalation), test for IDOR, test for missing authorization checks, test for authorization bypass through parameter manipulation, and test for authorization bypass through alternative code paths.

19. **How would you identify if a system is conflating authentication and authorization?**
    - *Expected Answer*: Look for authorization checks that depend on authentication state, authorization logic in the authentication system, assumptions that successful authentication implies authorization, and missing authorization checks on sensitive operations.

20. **What would you look for in a security audit of an authentication and authorization system?**
    - *Expected Answer*: Password hashing strength, MFA implementation, rate limiting, session management security, authorization checks on all sensitive operations, authorization logging, HTTPS usage, credential handling, and testing coverage.

---

# Key Takeaways

1. **Authentication and authorization are distinct concerns that must be separated in design and implementation.** Authentication verifies identity; authorization enforces permissions. Conflating these concerns creates security vulnerabilities that attackers exploit routinely.

2. **Successful authentication does not imply authorization for all actions.** A user can be authenticated but lack permission to perform a specific action. Authorization must be checked independently for every sensitive operation.

3. **Authorization failures are among the most common and impactful application security vulnerabilities.** Missing authorization checks, insecure direct object references, and privilege escalation vulnerabilities appear in the majority of security assessments.

4. **Implement authorization using a whitelist approach (default deny).** Explicitly grant permissions rather than denying them. This prevents authorization bypasses through unexpected code paths.

5. **Enforce authorization at multiple layers: API, business logic, and data access.** Do not rely on a single authorization check. Multiple layers prevent authorization bypasses through alternative code paths.

6. **Never trust client-side authorization checks.** Always enforce authorization on the server. Client-side checks are for user experience only; they provide no security.

7. **Use cryptographically random, non-sequential identifiers for resources.** Sequential or predictable identifiers enable IDOR attacks. UUIDs or similar random identifiers prevent attackers from guessing valid identifiers.

8. **Implement strong authentication with multiple factors.** Use MFA, rate limiting, strong password hashing, and account lockout to prevent credential compromise and brute force attacks.

9. **Log and monitor authorization events.** Log both successful and failed authorization checks. Monitor for patterns that indicate authorization attacks, such as repeated failed attempts to access unauthorized resources.

10. **Test authorization thoroughly, including edge cases and alternative code paths.** Authorization vulnerabilities are often subtle and appear only in specific scenarios. Comprehensive testing is essential.

11. **Use established frameworks and libraries for

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]
