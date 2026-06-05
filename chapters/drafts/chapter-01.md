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