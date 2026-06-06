# Authentication vs Authorization

## Learning Objectives

After reading this chapter, you will be able to:

- Define authentication and authorization and explain their distinct roles in application security
- Identify why authentication and authorization failures occur in real applications
- Recognize common architectural patterns that conflate these concerns
- Design authentication and authorization systems that maintain clear separation of concerns
- Review code and architecture for authentication and authorization vulnerabilities
- Implement practical controls that verify identity and enforce permissions correctly
- Conduct security assessments that test both authentication strength and authorization logic

## Conceptual Foundation

Authentication and authorization are foundational security controls that are frequently confused, conflated, or implemented incorrectly. Understanding the precise difference between them is essential for building secure applications.

**Authentication** answers the question: *Who are you?* It is the process of verifying that a user is who they claim to be. Authentication establishes identity through credentials—passwords, certificates, tokens, biometric data, or other proof of identity. Once authentication succeeds, the system knows the identity of the user making the request.

**Authorization** answers the question: *What are you allowed to do?* It is the process of determining whether an authenticated user has permission to perform a specific action or access a specific resource. Authorization is the enforcement of access control policies based on the authenticated identity and the context of the request.

The critical distinction is this: authentication is about *identity*, while authorization is about *permissions*. A user can be successfully authenticated but still lack authorization to perform a requested action. Conversely, a system that grants authorization without proper authentication has no assurance of who is actually performing the action.

### Why Teams Confuse These Concepts

The confusion between authentication and authorization arises for several reasons:

1. **Sequential dependency**: Authentication typically precedes authorization in the request flow. A user must be authenticated before authorization checks occur. This temporal relationship can blur the conceptual boundary.

2. **Shared infrastructure**: Many frameworks and libraries bundle authentication and authorization together, making it easy to treat them as a single concern rather than two distinct controls.

3. **Terminology overlap**: Terms like "login," "credentials," and "access control" are sometimes used imprecisely, conflating identity verification with permission enforcement.

4. **Legacy systems**: Older applications often implement authentication and authorization as monolithic blocks, making it difficult to reason about them separately.

5. **Incomplete threat modeling**: Teams that do not explicitly model threats related to identity spoofing versus privilege escalation may not recognize the need for distinct controls.

The consequences of this confusion are significant. A system that authenticates users but fails to authorize their actions correctly can leak sensitive data or allow unauthorized modifications. A system that authorizes without authenticating can be manipulated by attackers who forge or steal identities.

## Architecture Perspective

From an architectural standpoint, authentication and authorization should be treated as separate, composable concerns. This separation enables clearer design, easier testing, and more robust security.

### Authentication Architecture

A typical authentication architecture consists of:

1. **Credential collection**: The mechanism by which users provide proof of identity (login form, API key submission, certificate presentation).

2. **Credential verification**: The process of validating that the provided credentials match stored or trusted credentials. This may involve password hashing, cryptographic verification, or delegation to an external identity provider.

3. **Session or token issuance**: Upon successful verification, the system issues a session identifier, JWT, OAuth token, or similar artifact that represents the authenticated identity.

4. **Identity propagation**: The authenticated identity is carried through subsequent requests via cookies, headers, or other mechanisms.

### Authorization Architecture

A typical authorization architecture consists of:

1. **Policy definition**: The specification of who can do what. This may be expressed as role-based access control (RBAC), attribute-based access control (ABAC), access control lists (ACLs), or other models.

2. **Policy storage**: The persistence of authorization policies in a database, configuration file, or policy engine.

3. **Policy evaluation**: The logic that determines whether a specific authenticated user can perform a specific action on a specific resource.

4. **Policy enforcement**: The mechanism that blocks or allows the action based on the evaluation result.

### Separation of Concerns in Practice

A well-architected system maintains clear boundaries between these layers:

```
Request → Authentication Layer → Identity Established
                                        ↓
                            Authorization Layer
                                        ↓
                            Policy Evaluation
                                        ↓
                            Action Allowed/Denied
```

In this flow, the authentication layer is responsible only for verifying identity. It does not make decisions about what the user is allowed to do. The authorization layer receives the authenticated identity and makes permission decisions based on policy.

This separation allows:

- **Independent testing**: Authentication logic can be tested without authorization logic and vice versa.
- **Policy changes**: Authorization policies can be updated without modifying authentication code.
- **Delegation**: Authentication can be delegated to an external provider (LDAP, OAuth, SAML) while authorization remains internal.
- **Auditability**: Each layer can be audited independently.

## AppSec Lens

From an application security perspective, authentication and authorization failures are among the most commonly exploited vulnerabilities. The OWASP Top 10 consistently ranks broken authentication and broken access control as critical risks.

### Authentication Failures

Authentication failures occur when:

- **Weak credential validation**: Passwords are not properly hashed, salted, or validated. For example, a system that stores passwords in plaintext or uses a weak hashing algorithm like MD5.

- **Credential exposure**: Credentials are transmitted over unencrypted channels, logged in plaintext, or stored insecurely. An example is an API that accepts credentials in query parameters, which are logged in server access logs.

- **Session fixation**: An attacker can force a user to use a known session identifier, allowing the attacker to hijack the session. This occurs when session identifiers are not regenerated after authentication.

- **Insufficient session management**: Sessions lack proper expiration, secure flags, or domain restrictions. For example, a session cookie without the `HttpOnly` flag can be stolen via JavaScript.

- **Credential stuffing and brute force**: Systems lack rate limiting or account lockout mechanisms, allowing attackers to guess credentials through automated attacks.

- **Insecure password recovery**: Password reset mechanisms that do not properly verify identity or that send reset tokens via insecure channels.

### Authorization Failures

Authorization failures occur when:

- **Missing authorization checks**: Code that performs an action without verifying that the user has permission. For example, an endpoint that deletes a user account without checking if the requester is an administrator.

- **Inconsistent authorization logic**: Authorization checks that are implemented in some places but not others. For example, authorization checks on the web interface but not on the API.

- **Privilege escalation**: A user with limited permissions can escalate to higher privileges. This may occur through parameter tampering (changing a user ID in a request), insecure direct object references (accessing resources by guessing identifiers), or exploiting authorization logic flaws.

- **Horizontal privilege escalation**: A user can access resources belonging to other users at the same privilege level. For example, a user can view another user's profile by changing the user ID in the URL.

- **Vertical privilege escalation**: A user can escalate to a higher privilege level. For example, a regular user can perform administrative actions.

- **Authorization bypass**: Authorization logic can be circumvented through URL manipulation, HTTP method changes, or other techniques. For example, an endpoint protected by authorization checks on GET requests but not on POST requests.

### The Trust Boundary Problem

A critical AppSec principle is understanding trust boundaries. A common failure is trusting identity without verifying authorization, or trusting client-side authorization decisions.

**Example 1: Trusting Client-Side Authorization**

```javascript
// Client-side code
if (user.role === 'admin') {
  showDeleteButton();
}
```

This code assumes that if the client displays a delete button, the user is authorized to delete. However, an attacker can modify the client-side code or directly call the API endpoint, bypassing the client-side check entirely. The server must independently verify authorization.

**Example 2: Trusting Identity Without Authorization**

```python
# Server-side code
@app.route('/api/users/<user_id>/profile')
def get_user_profile(user_id):
    if request.user:  # Authenticated
        return get_profile_from_db(user_id)
    else:
        return 401_unauthorized()
```

This code checks that the user is authenticated but does not check whether the user is authorized to view the specific profile. An authenticated user can view any profile by changing the `user_id` parameter.

The correct implementation would be:

```python
@app.route('/api/users/<user_id>/profile')
def get_user_profile(user_id):
    if not request.user:
        return 401_unauthorized()
    
    if not is_authorized_to_view_profile(request.user, user_id):
        return 403_forbidden()
    
    return get_profile_from_db(user_id)
```

## Developer Lens

From a developer's perspective, implementing authentication and authorization correctly requires understanding both the mechanics of these controls and the common pitfalls.

### Authentication Implementation

**Password-Based Authentication**

When implementing password-based authentication:

1. **Hash passwords with a strong algorithm**: Use bcrypt, scrypt, Argon2, or PBKDF2. Never use MD5, SHA1, or unsalted hashing.

```python
import bcrypt

# Hashing a password during registration
password = request.form['password']
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
store_in_database(user_id, hashed)

# Verifying a password during login
provided_password = request.form['password']
stored_hash = retrieve_from_database(user_id)
if bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash):
    # Password is correct
    create_session(user_id)
else:
    # Password is incorrect
    return 401_unauthorized()
```

2. **Use HTTPS for all authentication traffic**: Credentials must be transmitted over encrypted channels.

3. **Implement rate limiting and account lockout**: Prevent brute force attacks by limiting login attempts.

```python
def login(username, password):
    failed_attempts = get_failed_attempts(username)
    
    if failed_attempts >= 5:
        return 429_too_many_requests()
    
    user = find_user(username)
    if not user or not verify_password(password, user.password_hash):
        increment_failed_attempts(username)
        return 401_unauthorized()
    
    reset_failed_attempts(username)
    create_session(user.id)
    return 200_ok()
```

4. **Regenerate session identifiers after authentication**: Prevent session fixation attacks.

```python
def login(username, password):
    # ... verify credentials ...
    
    # Invalidate any existing session
    invalidate_session(request.cookies.get('session_id'))
    
    # Create a new session
    new_session_id = generate_secure_random_token()
    store_session(new_session_id, user_id)
    
    response = make_response(redirect('/dashboard'))
    response.set_cookie('session_id', new_session_id, 
                       httponly=True, secure=True, samesite='Strict')
    return response
```

**Token-Based Authentication (OAuth 2.0, JWT)**

When implementing token-based authentication:

1. **Use short-lived access tokens**: Access tokens should expire within minutes to hours.

2. **Use refresh tokens for long-lived sessions**: Refresh tokens can be used to obtain new access tokens without re-entering credentials.

3. **Validate token signatures**: Verify that tokens have not been tampered with.

```python
import jwt

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.InvalidSignatureError:
        return None  # Token has been tampered with
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
```

4. **Store tokens securely**: In web applications, store tokens in secure, HttpOnly cookies. In mobile applications, use secure storage mechanisms.

### Authorization Implementation

**Role-Based Access Control (RBAC)**

RBAC is a common authorization model where users are assigned roles, and roles have permissions.

```python
def is_authorized(user_id, action, resource):
    user = get_user(user_id)
    user_roles = get_user_roles(user_id)
    
    for role in user_roles:
        role_permissions = get_role_permissions(role)
        if (action, resource) in role_permissions:
            return True
    
    return False

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not request.user:
        return 401_unauthorized()
    
    if not is_authorized(request.user.id, 'delete', 'user'):
        return 403_forbidden()
    
    delete_user_from_db(user_id)
    return 204_no_content()
```

**Attribute-Based Access Control (ABAC)**

ABAC is more flexible, allowing authorization decisions based on attributes of the user, resource, and environment.

```python
def is_authorized(user_id, action, resource_id):
    user = get_user(user_id)
    resource = get_resource(resource_id)
    
    # Check if user owns the resource
    if resource.owner_id == user_id:
        return True
    
    # Check if user is an admin
    if 'admin' in user.roles:
        return True
    
    # Check if user is in the same department as the resource
    if user.department == resource.department and action == 'read':
        return True
    
    return False
```

**Centralized Authorization**

For complex applications, implement authorization as a centralized service or middleware:

```python
class AuthorizationMiddleware:
    def __call__(self, request):
        if not request.user:
            return 401_unauthorized()
        
        required_permission = get_required_permission(request.path, request.method)
        
        if required_permission and not self.check_permission(request.user, required_permission):
            return 403_forbidden()
        
        return request
    
    def check_permission(self, user, permission):
        user_permissions = get_user_permissions(user.id)
        return permission in user_permissions
```

## Pentest Lens

From a penetration testing perspective, authentication and authorization are primary targets for exploitation. Testers should systematically evaluate both controls.

### Authentication Testing

**Test credential validation**:
- Attempt to register with weak passwords (single character, common passwords).
- Attempt to register with duplicate usernames.
- Attempt to bypass email verification.
- Test password reset functionality for security flaws.

**Test session management**:
- Capture session identifiers and attempt to reuse them.
- Check if session identifiers are predictable.
- Attempt to fixate sessions by forcing a known session ID.
- Check if sessions expire properly.
- Verify that session cookies have secure flags (HttpOnly, Secure, SameSite).

**Test credential transmission**:
- Verify that login requests use HTTPS.
- Check if credentials are logged in access logs or error messages.
- Attempt to capture credentials through network sniffing.

**Test brute force resistance**:
- Attempt multiple failed login attempts and observe rate limiting.
- Check if account lockout is implemented.
- Verify that lockout messages do not leak information about valid usernames.

### Authorization Testing

**Test access control on resources**:
- Authenticate as a low-privilege user.
- Attempt to access resources belonging to other users (horizontal privilege escalation).
- Attempt to access administrative resources (vertical privilege escalation).
- Change user IDs, resource IDs, or other parameters in requests to access unauthorized resources.

**Test authorization consistency**:
- Test authorization on all HTTP methods (GET, POST, PUT, DELETE, PATCH).
- Test authorization on all API endpoints.
- Test authorization on both web and API interfaces.

**Test authorization logic**:
- Attempt to bypass authorization checks by manipulating parameters.
- Attempt to exploit race conditions in authorization logic.
- Attempt to escalate privileges through role manipulation.

**Test authorization on sensitive operations**:
- Attempt to delete accounts without proper authorization.
- Attempt to modify user roles or permissions.
- Attempt to access sensitive data (PII, financial information).

### Common Testing Scenarios

**Scenario 1: Horizontal Privilege Escalation**

```
1. Authenticate as User A
2. Request: GET /api/users/B/profile
3. Expected: 403 Forbidden
4. Actual: 200 OK with User B's profile
```

This indicates missing authorization checks.

**Scenario 2: Vertical Privilege Escalation**

```
1. Authenticate as a regular user
2. Request: POST /api/admin/users with admin=true in request body
3. Expected: 403 Forbidden
4. Actual: 200 OK, user is now an admin
```

This indicates that authorization is not enforced on sensitive operations.

**Scenario 3: Session Fixation**

```
1. Obtain a session ID without authenticating
2. Force a user to use this session ID
3. User authenticates with the forced session ID
4. Attacker uses the same session ID to access the user's account
```

This indicates that session IDs are not regenerated after authentication.

## Common Findings

Based on thousands of security assessments, the following authentication and authorization findings are consistently discovered:

### Authentication Findings

1. **Weak password hashing**: Applications using MD5, SHA1, or unsalted hashing. Severity: Critical.

2. **Credentials in logs**: Passwords or API keys logged in application logs or error messages. Severity: Critical.

3. **Missing rate limiting**: No protection against brute force attacks. Severity: High.

4. **Session fixation**: Session IDs not regenerated after authentication. Severity: High.

5. **Insecure session storage**: Session cookies without HttpOnly or Secure flags. Severity: High.

6. **Weak password requirements**: No minimum length, complexity, or history requirements. Severity: Medium.

7. **Insecure password recovery**: Password reset tokens sent via email without expiration or verification. Severity: High.

8. **Credentials in URLs**: Passwords or tokens in query parameters. Severity: Critical.

9. **Missing HTTPS**: Authentication traffic over unencrypted HTTP. Severity: Critical.

10. **Hardcoded credentials**: API keys or passwords in source code. Severity: Critical.

### Authorization Findings

1. **Missing authorization checks**: Endpoints that perform sensitive actions without verifying permissions. Severity: Critical.

2. **Inconsistent authorization**: Authorization checks on some endpoints but not others. Severity: High.

3. **Insecure direct object references (IDOR)**: Users can access resources by guessing or manipulating identifiers. Severity: High.

4. **Client-side authorization**: Authorization decisions made in client-side code without server-side verification. Severity: High.

5. **Privilege escalation**: Users can escalate to higher privilege levels through parameter manipulation. Severity: Critical.

6. **Authorization bypass**: Authorization logic can be circumvented through URL manipulation or HTTP method changes. Severity: High.

7. **Role-based authorization flaws**: Incorrect role assignments or role hierarchy issues. Severity: Medium to High.

8. **Missing authorization on APIs**: API endpoints lack authorization checks present on web interfaces. Severity: High.

9. **Authorization based on user input**: Authorization decisions based on user-supplied data without validation. Severity: High.

10. **Stale authorization data**: Authorization decisions based on cached or outdated permission data. Severity: Medium.

## Secure Design Guidance

### Authentication Design Principles

1. **Use established standards**: Implement OAuth 2.0, OpenID Connect, or SAML rather than custom authentication. These standards have been vetted by security experts.

2. **Separate authentication from authorization**: Do not conflate identity verification with permission checking.

3. **Use strong credential storage**: Hash passwords with bcrypt, scrypt, or Argon2. Use salting and key derivation.

4. **Implement multi-factor authentication (MFA)**: Require a second factor (TOTP, SMS, hardware key) for sensitive accounts.

5. **Protect credentials in transit**: Use HTTPS for all authentication traffic. Use secure, HttpOnly cookies for session storage.

6. **Implement session management**: Generate cryptographically secure session identifiers. Regenerate identifiers after authentication. Implement proper expiration.

7. **Implement rate limiting**: Limit login attempts to prevent brute force attacks. Implement account lockout after repeated failures.

8. **Secure password recovery**: Use time-limited tokens. Verify user identity before allowing password reset. Send reset links via secure channels.

9. **Log authentication events**: Log successful and failed authentication attempts for audit trails. Do not log credentials.

10. **Monitor for suspicious activity**: Detect and alert on

## Interview Questions

### For Developers

1. **Explain the difference between authentication and authorization. Can you describe a scenario where a system authenticates users correctly but fails to authorize them properly?**
   - Expected answer: Authentication verifies identity (who you are), authorization verifies permissions (what you can do). Example: A user logs in successfully (authenticated) but can view another user's private data (authorization failure).

2. **Walk me through how you would implement password-based authentication securely. What hashing algorithm would you use and why?**
   - Expected answer: Use bcrypt, scrypt, or Argon2 with salt. Never use MD5 or SHA1. Demonstrate knowledge of password hashing best practices and why weak algorithms are vulnerable.

3. **Describe a time you discovered an authorization vulnerability in code. How did you identify it and what was the fix?**
   - Expected answer: Look for specific examples like IDOR, missing authorization checks, or privilege escalation. Candidate should explain the vulnerability, its impact, and the remediation.

4. **How would you design authorization for an application where users have different roles and permissions? What approach would you take?**
   - Expected answer: Discuss RBAC or ABAC. Explain how to centralize authorization logic, avoid duplication, and ensure consistency across all endpoints.

5. **What are the security risks of storing session identifiers in localStorage versus secure cookies?**
   - Expected answer: localStorage is vulnerable to XSS attacks. Secure cookies with HttpOnly and Secure flags are more resistant to client-side attacks. Demonstrate understanding of attack vectors.

6. **How do you prevent session fixation attacks?**
   - Expected answer: Regenerate session identifiers after successful authentication. Invalidate old sessions. Explain why this is important and how attackers exploit session fixation.

7. **Describe how you would implement rate limiting for login attempts. What metrics would you track?**
   - Expected answer: Track failed attempts per username and IP address. Implement exponential backoff or account lockout. Discuss balancing security with user experience.

8. **What is the difference between horizontal and vertical privilege escalation? Can you provide examples?**
   - Expected answer: Horizontal = accessing resources of other users at same level. Vertical = escalating to higher privilege level. Provide concrete examples and explain how to prevent each.

9. **How would you handle authorization for a multi-tenant application where users should only access their own data?**
   - Expected answer: Implement tenant isolation at the authorization layer. Verify that the authenticated user belongs to the requested tenant before allowing access. Discuss data isolation strategies.

10. **What would you do if you discovered that authorization checks were missing from an API endpoint that was already in production?**
    - Expected answer: Assess impact, implement authorization checks, deploy with proper testing, monitor for exploitation attempts, notify affected users if necessary.

### For Security Engineers / Architects

1. **How would you design an authentication and authorization system that maintains clear separation of concerns? What are the benefits of this separation?**
   - Expected answer: Separate authentication layer (identity verification) from authorization layer (permission checking). Benefits include independent testing, policy changes without code changes, delegation to external providers, and auditability.

2. **Describe the trust boundary between client and server in authentication and authorization. What assumptions should we make about client-side controls?**
   - Expected answer: Never trust client-side authorization decisions. Always verify authorization on the server. Client-side controls are for UX, not security. Explain why attackers can bypass client-side checks.

3. **What are the security implications of using JWT tokens for authentication? How would you mitigate the risks?**
   - Expected answer: JWTs are stateless but can be stolen or forged. Mitigations: use short expiration, validate signatures, use HTTPS, store securely, implement token revocation, use refresh tokens.

4. **How would you implement authorization in a microservices architecture where different services need to enforce different permissions?**
   - Expected answer: Discuss centralized authorization service, distributed authorization with local caches, token-based authorization, and consistency challenges. Explain trade-offs.

5. **What authentication and authorization controls would you implement for an API that serves both web and mobile clients?**
   - Expected answer: Use OAuth 2.0 or similar standard. Implement token-based authentication. Secure token storage differently for web (HttpOnly cookies) and mobile (secure storage). Enforce authorization on all endpoints.

6. **Describe how you would audit and monitor authentication and authorization in a production system. What events should you log?**
   - Expected answer: Log successful and failed authentication attempts, authorization failures, privilege escalation attempts, sensitive operations. Implement alerting for suspicious patterns. Do not log credentials.

7. **How would you approach a security assessment of authentication and authorization in a legacy application?**
   - Expected answer: Map authentication and authorization flows, identify trust boundaries, test for common vulnerabilities, review code for hardcoded credentials and weak hashing, assess session management, test access controls.

8. **What is the difference between authentication and authorization in the context of API security? How do you enforce both?**
   - Expected answer: Authentication verifies the API client's identity (API key, OAuth token, certificate). Authorization verifies the client's permissions for the requested resource. Both must be enforced on every API request.

9. **How would you implement passwordless authentication? What are the security trade-offs?**
   - Expected answer: Discuss options like FIDO2, magic links, biometrics. Explain benefits (phishing resistance, better UX) and challenges (device dependency, recovery mechanisms).

10. **Describe a scenario where authorization logic is complex and difficult to reason about. How would you simplify and secure it?**
    - Expected answer: Discuss centralization, policy-as-code, attribute-based access control, and testing strategies. Explain how to make authorization logic auditable and maintainable.

### For Security Testers / Pentesters

1. **Walk me through your methodology for testing authentication in a web application. What are the first things you check?**
   - Expected answer: Verify HTTPS usage, test password requirements, check session management, test for brute force protection, verify secure cookie flags, test password reset functionality.

2. **How would you test for insecure direct object references (IDOR)? Describe your approach and tools.**
   - Expected answer: Authenticate as one user, capture requests with resource identifiers, modify identifiers to access other users' resources, test across all endpoints, document findings with proof of concept.

3. **Describe how you would identify and exploit a privilege escalation vulnerability. What would you look for?**
   - Expected answer: Test parameter manipulation, role-based authorization flaws, API endpoint authorization gaps, function-level access control issues. Provide specific examples and exploitation techniques.

4. **How do you test for session fixation vulnerabilities? What is your testing process?**
   - Expected answer: Obtain session ID before authentication, force user to use this ID, authenticate, verify if attacker can use the same ID. Explain why this is a vulnerability and its impact.

5. **What techniques would you use to test authorization consistency across an application?**
   - Expected answer: Test all HTTP methods (GET, POST, PUT, DELETE), test all endpoints, test both web and API interfaces, test with different user roles, document inconsistencies.

6. **How would you test for authorization bypass in a REST API?**
   - Expected answer: Test parameter tampering, HTTP method changes, URL manipulation, header manipulation, test with different authentication methods, test with missing or invalid tokens.

7. **Describe how you would test multi-factor authentication (MFA) for security flaws.**
   - Expected answer: Test MFA bypass, test MFA recovery mechanisms, test for race conditions, test for brute force on MFA codes, verify MFA is enforced on sensitive operations.

8. **How would you identify if credentials are being logged or exposed in error messages?**
   - Expected answer: Monitor network traffic, check application logs, trigger errors and observe output, search for credentials in responses, test with known credentials and search for them in logs.

9. **What would you do if you discovered that an application stores passwords in plaintext or with weak hashing?**
   - Expected answer: Document the vulnerability with severity assessment, provide proof of concept, recommend remediation (bcrypt, scrypt, Argon2), explain the impact and risk.

10. **How would you test authorization in a multi-tenant application to ensure data isolation?**
    - Expected answer: Authenticate as user in Tenant A, attempt to access Tenant B's data, test across all endpoints, verify tenant isolation at database level, test for tenant ID manipulation.

---

## Key Takeaways

### Core Concepts

1. **Authentication and authorization are distinct controls**: Authentication verifies identity (who you are), while authorization verifies permissions (what you can do). Conflating these controls leads to security vulnerabilities.

2. **Authentication is a prerequisite for authorization**: A user must be authenticated before authorization checks can be meaningful. However, successful authentication does not imply authorization.

3. **Never trust client-side authorization**: Authorization decisions must always be verified on the server. Client-side controls are for user experience, not security.

4. **Maintain clear separation of concerns**: Design systems where authentication and authorization are separate layers. This enables independent testing, policy changes, and delegation to external providers.

5. **Authorization must be consistent**: Authorization checks must be enforced on all endpoints, all HTTP methods, and all interfaces (web, API, mobile). Inconsistent authorization is a common vulnerability.

### Authentication Best Practices

6. **Use strong password hashing**: Hash passwords with bcrypt, scrypt, or Argon2. Never use MD5, SHA1, or unsalted hashing. Use unique salts for each password.

7. **Protect credentials in transit**: Use HTTPS for all authentication traffic. Never transmit credentials in URLs, query parameters, or unencrypted channels.

8. **Implement secure session management**: Generate cryptographically secure session identifiers. Regenerate identifiers after authentication. Implement proper expiration and secure cookie flags (HttpOnly, Secure, SameSite).

9. **Implement rate limiting and account lockout**: Protect against brute force attacks by limiting login attempts. Implement exponential backoff or temporary account lockout.

10. **Use established standards**: Implement OAuth 2.0, OpenID Connect, or SAML rather than custom authentication. These standards have been vetted by security experts and are more resistant to vulnerabilities.

11. **Implement multi-factor authentication (MFA)**: Require a second factor for sensitive accounts. MFA significantly reduces the risk of account compromise.

12. **Secure password recovery**: Use time-limited tokens for password reset. Verify user identity before allowing password reset. Send reset links via secure channels.

### Authorization Best Practices

13. **Implement centralized authorization**: Centralize authorization logic to ensure consistency and reduce duplication. Use middleware, decorators, or a dedicated authorization service.

14. **Use role-based or attribute-based access control**: Implement RBAC for simple scenarios or ABAC for complex scenarios. Make authorization policies explicit and auditable.

15. **Verify authorization on every request**: Check authorization on all endpoints, all HTTP methods, and all interfaces. Do not assume that authorization checks on one interface apply to others.

16. **Test authorization thoroughly**: Include authorization testing in security assessments. Test for horizontal privilege escalation, vertical privilege escalation, and authorization bypass.

17. **Avoid authorization based on user input**: Do not make authorization decisions based on user-supplied data without validation. Always verify authorization on the server using trusted data.

18. **Implement proper error handling**: Return generic error messages for authorization failures. Do not leak information about valid usernames, resource existence, or authorization policies.

19. **Monitor and audit authorization**: Log authorization failures and sensitive operations. Implement alerting for suspicious patterns like repeated authorization failures or privilege escalation attempts.

### Common Vulnerabilities to Avoid

20. **Insecure direct object references (IDOR)**: Always verify that the authenticated user is authorized to access the requested resource. Do not assume that if a user can guess a resource ID, they should be able to access it.

21. **Missing authorization checks**: Ensure that all endpoints that perform sensitive actions have authorization checks. Regularly audit code for missing checks.

22. **Privilege escalation**: Prevent users from escalating to higher privilege levels through parameter manipulation, role modification, or other techniques.

23. **Session fixation**: Always regenerate session identifiers after authentication. Invalidate old sessions to prevent attackers from hijacking sessions.

24. **Credentials in logs**: Never log passwords, API keys, or other sensitive credentials. Implement log filtering to prevent accidental exposure.

25. **Weak password requirements**: Enforce minimum password length, complexity, and history. Educate users about password security.

### Implementation Guidance

26. **Separate authentication from authorization in code**: Use different functions, classes, or services for authentication and authorization. This makes code easier to understand, test, and maintain.

27. **Use dependency injection for authorization**: Inject authorization logic as a dependency. This makes it easier to test and swap implementations.

28. **Implement authorization as middleware or decorators**: Use framework-provided mechanisms to enforce authorization consistently across all endpoints.

29. **Test authentication and authorization independently**: Write unit tests for authentication logic and authorization logic separately. Write integration tests to verify the interaction between them.

30. **Document authorization policies**: Make authorization policies explicit and documented. Use policy-as-code approaches to make policies auditable and version-controlled.

### Assessment and Monitoring

31. **Include authentication and authorization in threat modeling**: Explicitly model threats related to identity spoofing and privilege escalation. Design controls to mitigate these threats.

32. **Conduct regular security assessments**: Include authentication and authorization testing in security assessments. Test for common vulnerabilities and misconfigurations.

33. **Monitor authentication and authorization events**: Log and monitor authentication attempts, authorization failures, and sensitive operations. Implement alerting for suspicious patterns.

34. **Implement security metrics**: Track metrics like failed login attempts, authorization failures, and privilege escalation attempts. Use these metrics to identify trends and improve security.

35. **Stay informed about emerging threats**: Follow security advisories and research related to authentication and authorization. Update systems and practices as new vulnerabilities are discovered.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]
