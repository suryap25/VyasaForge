# Authentication vs Authorization

## Learning Objectives

After completing this chapter, you will be able to:

- Define authentication and authorization and explain their distinct roles in application security
- Identify why authentication and authorization failures occur in real applications
- Recognize common architectural patterns that conflate these concerns
- Design authentication and authorization systems that maintain clear separation of concerns
- Review application code and configurations to detect authentication and authorization weaknesses
- Implement practical controls that enforce both identity verification and permission checking
- Conduct security assessments that properly evaluate both mechanisms independently

## Conceptual Foundation

Authentication and authorization are foundational security concepts that are frequently confused, conflated, or implemented as a single monolithic system. This confusion creates security gaps that attackers exploit routinely. Understanding the distinction between these two mechanisms is essential for anyone designing, building, or reviewing application security controls.

**Authentication** answers the question: "Who are you?" It is the process of verifying that a user is who they claim to be. Authentication establishes identity through evidence—something you know (a password), something you have (a hardware token or phone), something you are (biometric data), or some combination of these factors. Once authentication succeeds, the application knows the user's identity with reasonable confidence.

**Authorization** answers the question: "What are you allowed to do?" It is the process of determining whether an authenticated user has permission to perform a specific action or access a specific resource. Authorization is the enforcement of access control policies based on the user's identity, role, attributes, or other contextual information.

The critical distinction is this: authentication is about identity verification, while authorization is about permission enforcement. A user can be successfully authenticated but still lack authorization to perform a requested action. Conversely, a system that fails to properly authenticate a user cannot reliably authorize anything, because it does not know who is making the request.

### Why Confusion Occurs

Teams often conflate these concepts because:

1. **Historical coupling**: Many legacy authentication systems bundled identity verification with basic access control. A user logged in, and the system granted them access to everything associated with their account type.

2. **Terminology overlap**: Both involve checking credentials or permissions, and both use similar technical mechanisms (tokens, sessions, claims). The vocabulary can blur the distinction.

3. **Single-sign-on systems**: SSO platforms handle authentication centrally, and developers sometimes assume that successful SSO login automatically grants authorization to all downstream services.

4. **Role-based access control (RBAC) simplicity**: Simple RBAC systems assign users to roles, and developers may treat role assignment as both authentication and authorization, when role assignment is actually an authorization mechanism that depends on prior authentication.

5. **API token design**: API tokens often serve dual purposes—proving identity and carrying permission information—which can obscure the logical separation between the two concerns.

The consequences of this confusion are severe. A developer might implement strong authentication (multi-factor authentication, secure password hashing) but then fail to check permissions on sensitive operations. Or a system might verify a user's identity but grant authorization based on user-supplied data rather than server-side policy.

## Architecture Perspective

From an architectural standpoint, authentication and authorization should be treated as distinct layers, even though they interact closely.

### Authentication Layer

The authentication layer is responsible for:

- Accepting credentials from a user or system
- Verifying those credentials against a trusted store (password database, certificate authority, identity provider)
- Creating a session or token that represents the authenticated identity
- Maintaining the session or token for the duration of the user's interaction with the system

In a typical web application, the authentication layer might be implemented as:

- A login endpoint that accepts username and password
- A password verification function that compares the submitted password against a securely hashed stored password
- A session management system that creates and validates session cookies
- An optional multi-factor authentication (MFA) mechanism that requires additional proof of identity

In an API context, the authentication layer might be:

- An OAuth 2.0 authorization server that issues access tokens
- A JWT (JSON Web Token) validation mechanism that verifies token signatures
- A mutual TLS (mTLS) system that verifies client certificates
- An API key validation system that checks whether a submitted key is valid and active

### Authorization Layer

The authorization layer is responsible for:

- Receiving a request from an authenticated user
- Determining what resources or actions the user is attempting to access
- Checking the user's permissions against the requested resource or action
- Allowing or denying the request based on policy

In a typical web application, the authorization layer might be:

- A middleware component that checks user roles before allowing access to certain pages
- A service method that verifies the user owns the resource before allowing modification
- A database query filter that restricts results to resources the user has permission to see
- An attribute-based access control (ABAC) engine that evaluates complex policies

In an API context, the authorization layer might be:

- A scope validation mechanism that checks whether the token's scopes include the requested operation
- A resource ownership check that verifies the user owns the resource they are trying to access
- A permission matrix that maps user roles to allowed operations
- A fine-grained access control system that evaluates policies based on user attributes, resource attributes, and context

### Architectural Separation

The key architectural principle is that these layers should be logically separate, even if they are physically close in the codebase. A request should flow through authentication first, establishing identity. Only after authentication succeeds should the request proceed to authorization, where permissions are checked.

```
Request → Authentication Layer → Authorization Layer → Business Logic
                ↓                        ↓
           Is this user?          Can this user do this?
           (Identity)             (Permissions)
```

This separation allows:

- **Independent testing**: You can test authentication without worrying about authorization logic, and vice versa.
- **Clear responsibility**: Authentication code is responsible only for identity verification; authorization code is responsible only for permission checking.
- **Easier auditing**: When a security incident occurs, you can trace whether the problem was in identity verification or permission enforcement.
- **Flexibility**: You can change authentication mechanisms (e.g., from passwords to SAML) without rewriting authorization logic.

## AppSec Lens

From an application security perspective, authentication and authorization failures are among the most commonly exploited vulnerabilities. The OWASP Top 10 consistently includes broken authentication and broken access control as critical risks.

### Authentication Failures

Authentication failures occur when:

- **Weak credential storage**: Passwords are stored in plaintext or with weak hashing algorithms (MD5, SHA1 without salt).
- **Credential transmission vulnerabilities**: Credentials are transmitted over unencrypted channels (HTTP instead of HTTPS).
- **Brute force attacks**: The system allows unlimited login attempts without rate limiting or account lockout.
- **Session fixation**: An attacker can force a user to use a known session ID.
- **Credential stuffing**: Attackers use credentials leaked from other services to gain access.
- **Weak MFA implementation**: MFA is implemented but can be bypassed (e.g., SMS-based MFA intercepted via SIM swapping).
- **Default credentials**: Applications ship with default usernames and passwords that are not changed.
- **Insecure password recovery**: Password reset mechanisms allow attackers to reset other users' passwords.

### Authorization Failures

Authorization failures occur when:

- **Missing authorization checks**: The application performs an action without verifying the user has permission.
- **Broken object-level access control**: A user can access or modify objects belonging to other users by changing an ID in the request.
- **Broken function-level access control**: A user can access administrative functions by directly requesting them.
- **Insecure direct object references (IDOR)**: The application uses user-supplied IDs to fetch objects without checking ownership.
- **Privilege escalation**: A user can perform actions reserved for higher-privilege users.
- **Horizontal privilege escalation**: A user can access resources belonging to other users at the same privilege level.
- **Vertical privilege escalation**: A user can access resources or functions reserved for higher-privilege users.
- **Authorization based on user input**: The application trusts user-supplied data (e.g., a hidden form field) to determine permissions.

### The Critical Distinction in Security Terms

From a security perspective, the distinction matters because:

1. **Authentication is necessary but not sufficient**: A strong authentication system does not prevent authorization failures. You can have perfect authentication and still suffer from broken access control.

2. **Authorization depends on authentication**: If authentication is broken, authorization is meaningless. You cannot reliably enforce permissions if you do not know who the user is.

3. **Different threat models**: Authentication failures are typically exploited through credential compromise, brute force, or session hijacking. Authorization failures are typically exploited through direct object reference manipulation, privilege escalation, or function-level access control bypass.

4. **Different remediation strategies**: Fixing authentication requires stronger credential management, secure transmission, and session handling. Fixing authorization requires explicit permission checks, proper access control models, and secure object reference handling.

## Developer Lens

Developers are responsible for implementing both authentication and authorization correctly. From a developer's perspective, the distinction has practical implications for code design and testing.

### Authentication Implementation

When implementing authentication, developers should:

- **Use established libraries**: Do not implement authentication from scratch. Use well-tested libraries like bcrypt for password hashing, established OAuth 2.0 libraries, or SAML libraries.
- **Hash passwords with strong algorithms**: Use bcrypt, scrypt, Argon2, or PBKDF2 with appropriate work factors. Never use MD5, SHA1, or unsalted hashing.
- **Implement secure session management**: Use secure, HttpOnly, SameSite cookies for session tokens. Regenerate session IDs after successful authentication.
- **Enforce HTTPS**: Transmit credentials only over encrypted channels.
- **Implement rate limiting**: Limit login attempts to prevent brute force attacks.
- **Implement account lockout**: Lock accounts after multiple failed login attempts.
- **Implement MFA**: Require a second factor (TOTP, hardware token, push notification) for sensitive operations or high-value accounts.
- **Implement secure password recovery**: Use time-limited tokens sent to verified email addresses; do not ask security questions.
- **Log authentication events**: Log successful and failed authentication attempts for audit and incident response.

### Authorization Implementation

When implementing authorization, developers should:

- **Check permissions on every operation**: Do not assume that because a user is authenticated, they are authorized. Check permissions explicitly.
- **Check permissions server-side**: Never rely on client-side authorization checks (hidden form fields, client-side role checks). Always verify permissions on the server.
- **Use explicit permission checks**: Rather than checking if a user has a certain role, check if the user has permission for the specific action.
- **Implement object-level access control**: When a user requests a resource by ID, verify they own or have permission to access that resource.
- **Use a consistent authorization model**: Choose an authorization model (RBAC, ABAC, ACL) and apply it consistently across the application.
- **Fail securely**: When authorization fails, deny access by default. Do not grant access if the authorization check is unclear.
- **Log authorization decisions**: Log both successful and failed authorization attempts, especially for sensitive operations.
- **Separate authorization logic from business logic**: Implement authorization checks in a dedicated layer or middleware, not scattered throughout business logic.

### Practical Code Example: Web Application

Consider a web application where users can view and edit their own documents:

```python
# WEAK: Authentication only, no authorization check
@app.route('/documents/<doc_id>', methods=['GET'])
def view_document(doc_id):
    if not is_authenticated():  # Authentication check
        return redirect('/login')
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    return render_template('document.html', document=document)

# STRONG: Authentication and authorization check
@app.route('/documents/<doc_id>', methods=['GET'])
def view_document(doc_id):
    if not is_authenticated():  # Authentication check
        return redirect('/login')
    
    current_user = get_current_user()  # Get authenticated user
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        return abort(404)
    
    # Authorization check: verify user owns the document
    if document.owner_id != current_user.id:
        return abort(403)  # Forbidden
    
    return render_template('document.html', document=document)
```

The weak version checks authentication but not authorization. An attacker could change the `doc_id` parameter to access other users' documents. The strong version adds an explicit authorization check that verifies the current user owns the document.

### Practical Code Example: API

Consider an API endpoint where users can update their profile:

```python
# WEAK: Trusts user-supplied user_id
@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    if not is_authenticated():  # Authentication check
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return jsonify({'error': 'Not found'}), 404
    
    user.email = data.get('email')
    user.name = data.get('name')
    db.commit()
    
    return jsonify({'status': 'updated'})

# STRONG: Verifies user can only update their own profile
@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    if not is_authenticated():  # Authentication check
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user = get_current_user()  # Get authenticated user
    
    # Authorization check: verify user is updating their own profile
    if int(user_id) != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return jsonify({'error': 'Not found'}), 404
    
    user.email = data.get('email')
    user.name = data.get('name')
    db.commit()
    
    return jsonify({'status': 'updated'})
```

The weak version allows any authenticated user to update any user's profile by changing the `user_id` parameter. The strong version adds an authorization check that verifies the authenticated user is updating their own profile.

## Pentest Lens

Penetration testers and security researchers approach authentication and authorization testing systematically, looking for both logical flaws and implementation weaknesses.

### Authentication Testing

Pentesters test authentication by:

- **Attempting default credentials**: Testing common default usernames and passwords (admin/admin, admin/password).
- **Brute forcing credentials**: Attempting to guess passwords through automated login attempts.
- **Testing password policies**: Checking if weak passwords are accepted.
- **Testing session management**: Attempting to reuse, fixate, or hijack session tokens.
- **Testing credential transmission**: Checking if credentials are transmitted over HTTPS and if sensitive data is logged.
- **Testing password recovery**: Attempting to reset other users' passwords through predictable tokens or security questions.
- **Testing MFA bypass**: Attempting to bypass MFA through token reuse, timing attacks, or alternative authentication paths.
- **Testing account enumeration**: Determining if the application reveals whether an account exists.
- **Testing credential stuffing**: Using credentials from known breaches to gain access.

### Authorization Testing

Pentesters test authorization by:

- **Testing object-level access control**: Attempting to access or modify objects belonging to other users by changing IDs.
- **Testing function-level access control**: Attempting to access administrative functions without proper privileges.
- **Testing horizontal privilege escalation**: Attempting to access resources belonging to other users at the same privilege level.
- **Testing vertical privilege escalation**: Attempting to access resources or functions reserved for higher-privilege users.
- **Testing authorization bypass**: Attempting to bypass authorization checks through parameter manipulation, HTTP method changes, or request modification.
- **Testing role-based access control**: Attempting to assume higher-privilege roles or modify role assignments.
- **Testing attribute-based access control**: Attempting to manipulate attributes to gain unauthorized access.
- **Testing authorization in APIs**: Attempting to access API endpoints without proper scopes or permissions.

### Testing Methodology

A systematic approach to testing authentication and authorization:

1. **Map the application**: Identify all authentication mechanisms, authorization models, and protected resources.
2. **Test authentication independently**: Verify that authentication is strong and cannot be bypassed.
3. **Test authorization independently**: Verify that authorization checks are present and cannot be bypassed.
4. **Test the interaction**: Verify that authentication and authorization work together correctly.
5. **Test edge cases**: Test what happens when authentication fails, authorization fails, or both fail.
6. **Test with different user roles**: Test authorization with different privilege levels.
7. **Test with different resources**: Test authorization with different types of resources.
8. **Document findings**: Clearly document whether findings are authentication failures, authorization failures, or both.

## Common Findings

In real-world security assessments, certain authentication and authorization failures appear repeatedly.

### Authentication Findings

**Weak password hashing**: Applications using MD5, SHA1, or unsalted hashing for passwords. Passwords can be cracked quickly with modern hardware.

**No rate limiting on login**: Applications allowing unlimited login attempts without delays or account lockout. Attackers can brute force credentials.

**Credentials in logs**: Applications logging passwords or tokens in application logs, system logs, or error messages. Credentials can be recovered from log files.

**Session fixation**: Applications allowing attackers to set session IDs for other users. Attackers can hijack sessions.

**Insecure password recovery**: Password reset mechanisms using predictable tokens, security questions, or email-only verification. Attackers can reset other users' passwords.

**MFA bypass**: MFA implementations that can be bypassed through alternative authentication paths, token reuse, or timing attacks.

**Default credentials**: Applications shipping with default usernames and passwords that are not changed in production.

**Credentials in URLs**: Applications passing credentials in URL parameters or query strings. Credentials can be captured in logs or browser history.

### Authorization Findings

**Missing authorization checks**: Operations that modify data without verifying the user has permission. Any authenticated user can perform any action.

**Insecure direct object references (IDOR)**: Applications using user-supplied IDs to fetch objects without checking ownership. Users can access other users' data by changing IDs.

**Broken function-level access control**: Administrative functions accessible to non-administrative users. Users can perform administrative actions.

**Horizontal privilege escalation**: Users accessing resources belonging to other users at the same privilege level. Users can view or modify other users' data.

**Vertical privilege escalation**: Users accessing resources or functions reserved for higher-privilege users. Users can perform actions above their privilege level.

**Authorization based on user input**: Applications trusting user-supplied data (hidden form fields, client-side role checks) to determine permissions. Users can modify permissions by changing request data.

**Inconsistent authorization**: Authorization checks present in some places but not others. Some operations are protected while others are not.

**Authorization in APIs**: API endpoints lacking proper scope or permission checks. Users can access API endpoints without proper authorization.

**Role-based access control without object-level checks**: Applications checking user roles but not verifying users own the objects they are accessing. Users can access other users' objects if they have the right role.

## Secure Design Guidance

When designing authentication and authorization systems, follow these principles:

### Authentication Design Principles

**1. Use established standards and libraries**: Do not implement authentication from scratch. Use OAuth 2.0, SAML, OpenID Connect, or established authentication libraries. These have been reviewed by security experts and are less likely to contain vulnerabilities.

**2. Separate authentication from authorization**: Design systems where authentication and authorization are logically separate. Authentication establishes identity; authorization checks permissions.

**3. Implement defense in depth**: Use multiple authentication factors (passwords, MFA, certificates). Do not rely on a single factor.

**4. Secure credential storage**: Hash passwords with strong algorithms (bcrypt, Argon2). Use salts and appropriate work factors.

**5. Secure credential transmission**: Transmit credentials only over HTTPS. Use secure cookies with HttpOnly and SameSite flags.

**6. Implement session management**: Create secure sessions after authentication. Regenerate session IDs after login. Implement session timeouts.

**7. Implement rate limiting**: Limit login attempts to prevent brute force attacks. Implement account lockout after multiple failed attempts.

**8. Implement secure password recovery**: Use time-limited tokens sent to verified email addresses. Do not use security questions.

**9. Log authentication events**: Log successful and failed authentication attempts. Include timestamp, username, IP address, and outcome.

**10. Monitor for suspicious activity**: Detect and alert on suspicious authentication patterns (multiple failed attempts, logins from unusual locations).

### Authorization Design Principles

**1. Implement explicit permission checks**: Check permissions explicitly for every operation. Do not assume authenticated users are authorized.

**2. Check permissions server-side**: Never rely on client-side authorization checks. Always verify permissions on the server.

**3. Use a consistent authorization model**: Choose an authorization model (RBAC, ABAC, ACL) and apply it consistently.

**4. Implement object-level access control**: Verify users own or have permission to access objects

## Interview Questions

### Authentication-Focused Questions

1. **Describe a situation where you discovered an authentication vulnerability in an application you were reviewing. What was the vulnerability, and how did you remediate it?**
   - *Evaluates*: Practical experience identifying authentication flaws, understanding of secure implementation patterns, ability to communicate technical findings.
   - *Look for*: Specific examples (weak hashing, missing rate limiting, session fixation), understanding of why the vulnerability existed, concrete remediation steps.

2. **Walk me through how you would implement password hashing in a new application. What algorithm would you choose, and why? What parameters would you configure?**
   - *Evaluates*: Knowledge of modern password hashing algorithms, understanding of work factors and salt, ability to make secure design decisions.
   - *Look for*: Mention of bcrypt, Argon2, or scrypt; discussion of work factors; understanding that MD5/SHA1 are unacceptable; awareness of timing attacks.

3. **An application you're reviewing uses JWT tokens for API authentication. What security properties would you verify in the token implementation?**
   - *Evaluates*: Understanding of JWT security considerations, ability to identify common JWT vulnerabilities, knowledge of token lifecycle.
   - *Look for*: Signature verification, algorithm validation (not "none"), expiration checking, secure key storage, understanding of token refresh mechanisms.

4. **How would you design a secure password recovery mechanism? What are the common pitfalls?**
   - *Evaluates*: Understanding of secure design principles, awareness of common vulnerabilities, ability to balance security with usability.
   - *Look for*: Time-limited tokens, email verification, no security questions, protection against account enumeration, logging of recovery attempts.

5. **Describe your approach to implementing multi-factor authentication. What factors would you support, and how would you handle MFA bypass scenarios?**
   - *Evaluates*: Knowledge of MFA types, understanding of MFA security considerations, awareness of bypass techniques.
   - *Look for*: Discussion of TOTP, hardware tokens, push notifications; understanding of backup codes; awareness of SMS vulnerabilities; mention of rate limiting on MFA attempts.

### Authorization-Focused Questions

6. **You find an IDOR vulnerability where users can access other users' documents by changing a document ID in the URL. How would you fix this, and how would you prevent similar issues in the future?**
   - *Evaluates*: Understanding of object-level access control, ability to implement fixes, knowledge of prevention strategies.
   - *Look for*: Server-side ownership verification, consistent authorization checks, use of indirect references, automated testing for IDOR.

7. **Explain the difference between role-based access control (RBAC) and attribute-based access control (ABAC). When would you use each?**
   - *Evaluates*: Understanding of authorization models, ability to choose appropriate models for different scenarios.
   - *Look for*: Clear explanation of RBAC simplicity vs. ABAC flexibility; understanding of use cases (RBAC for simple hierarchies, ABAC for complex policies); awareness of implementation complexity.

8. **An application checks user roles on the client side (JavaScript) to hide administrative functions. Is this secure? How would you improve it?**
   - *Evaluates*: Understanding that client-side checks are not security controls, knowledge of proper authorization implementation.
   - *Look for*: Clear statement that client-side checks are not secure; explanation of why (client can be manipulated); description of server-side authorization checks; understanding of defense in depth.

9. **How would you implement authorization for a multi-tenant SaaS application where users belong to organizations and have different roles within each organization?**
   - *Evaluates*: Ability to design authorization for complex scenarios, understanding of tenant isolation, knowledge of practical authorization patterns.
   - *Look for*: Tenant context in authorization checks, role-based permissions within tenant context, prevention of cross-tenant access, consistent enforcement across APIs and UI.

10. **Describe a privilege escalation vulnerability you've encountered or studied. How could it have been prevented?**
    - *Evaluates*: Understanding of privilege escalation techniques, awareness of prevention strategies, ability to think about authorization comprehensively.
    - *Look for*: Specific example (horizontal or vertical escalation); understanding of root cause; discussion of prevention (explicit checks, consistent models, testing).

### Combined Authentication and Authorization Questions

11. **Walk me through how you would test both authentication and authorization in a REST API. What would you test for each, and how would you verify they work together correctly?**
    - *Evaluates*: Systematic testing approach, understanding of distinct concerns, ability to test interactions.
    - *Look for*: Separate test plans for authentication and authorization; testing of edge cases (failed auth, failed authz, both); testing with different user roles; API-specific concerns (scopes, tokens).

12. **An application uses OAuth 2.0 for authentication. Does this mean authorization is handled correctly? Explain your reasoning.**
    - *Evaluates*: Understanding that authentication and authorization are separate, awareness of OAuth limitations, knowledge of what OAuth does and does not provide.
    - *Look for*: Clear statement that OAuth handles authentication but not authorization; understanding that authorization must be implemented separately; awareness of scope limitations; knowledge that OAuth does not enforce object-level access control.

13. **How would you design a security review checklist for authentication and authorization? What would you include?**
    - *Evaluates*: Systematic thinking about security, ability to prioritize concerns, knowledge of common vulnerabilities.
    - *Look for*: Separate sections for authentication and authorization; coverage of common vulnerabilities (OWASP Top 10); testing methodology; code review points; configuration review points.

14. **Describe a situation where authentication was strong but authorization was weak, or vice versa. What was the impact, and how would you prevent it?**
    - *Evaluates*: Understanding that authentication and authorization are independent, awareness of real-world scenarios, ability to think about security holistically.
    - *Look for*: Specific example; clear explanation of the mismatch; understanding of impact; discussion of prevention (separate testing, clear responsibility, consistent review).

15. **How do you explain the difference between authentication and authorization to non-technical stakeholders? Why does this distinction matter for security?**
    - *Evaluates*: Communication skills, ability to simplify complex concepts, understanding of business impact.
    - *Look for*: Clear, non-technical explanation; use of analogies (e.g., ID check vs. permission to enter); explanation of why both matter; discussion of business impact (data breaches, compliance).

### Scenario-Based Questions

16. **You're reviewing code for a banking application. You find that the application checks if a user is authenticated before allowing fund transfers, but does not verify the user owns the account being transferred from. What is this vulnerability called, and how would you fix it?**
    - *Evaluates*: Ability to identify authorization failures, understanding of severity in financial context, knowledge of remediation.
    - *Look for*: Identification as authorization failure or IDOR; understanding of severity; clear remediation (verify account ownership); discussion of testing.

17. **An application implements session-based authentication with cookies. What security properties would you verify to ensure sessions are handled securely?**
    - *Evaluates*: Knowledge of session security, understanding of cookie security flags, awareness of session-specific vulnerabilities.
    - *Look for*: HttpOnly flag (prevents JavaScript access); Secure flag (HTTPS only); SameSite flag (CSRF protection); session timeout; session regeneration after login; secure session ID generation.

18. **You discover that an API endpoint accepts an `admin=true` parameter in the request body to grant administrative access. What is wrong with this, and how would you fix it?**
    - *Evaluates*: Understanding that authorization cannot be based on user input, knowledge of proper authorization implementation.
    - *Look for*: Clear statement that user input cannot determine permissions; explanation of why (user can manipulate); description of proper approach (server-side role/permission checks); understanding of severity.

19. **How would you implement authorization for a file-sharing application where users can share files with other users and set different permission levels (view, edit, delete)?**
    - *Evaluates*: Ability to design authorization for complex scenarios, understanding of access control lists, knowledge of practical implementation.
    - *Look for*: ACL-based approach; server-side permission checks; handling of shared vs. owned files; consistent enforcement across operations; consideration of inheritance and defaults.

20. **An application uses API keys for authentication. What are the security considerations for API key management, and how would you implement secure key rotation?**
    - *Evaluates*: Understanding of API key security, knowledge of key lifecycle management, awareness of practical security concerns.
    - *Look for*: Secure key generation and storage; transmission over HTTPS; rate limiting; key expiration; rotation strategy; revocation mechanism; audit logging.

---

## Key Takeaways

### Core Concepts

**Authentication and authorization are distinct security mechanisms that must be implemented separately.** Authentication verifies identity ("Who are you?"), while authorization enforces permissions ("What are you allowed to do?"). Confusing these concepts is a common source of security vulnerabilities. A system can have strong authentication but weak authorization, or vice versa. Both are necessary for a secure application.

**Authentication is a prerequisite for reliable authorization.** You cannot enforce permissions if you do not know who the user is. However, successful authentication does not automatically grant authorization. Every operation that accesses or modifies sensitive data must include an explicit authorization check, regardless of whether the user is authenticated.

**Authorization checks must be performed server-side, not client-side.** Client-side authorization checks (hidden form fields, JavaScript role checks, client-side permission logic) are not security controls. They can be bypassed by manipulating requests. All authorization decisions must be made on the server, based on server-side policy and the authenticated user's identity.

### Implementation Principles

**Use established libraries and standards for authentication.** Do not implement authentication from scratch. Use well-tested libraries (bcrypt for password hashing, OAuth 2.0 libraries, SAML libraries) and standards (OAuth 2.0, OpenID Connect, SAML). These have been reviewed by security experts and are less likely to contain vulnerabilities.

**Hash passwords with strong algorithms and appropriate parameters.** Use bcrypt, Argon2, or scrypt with appropriate work factors. Never use MD5, SHA1, or unsalted hashing. Ensure passwords are salted and that work factors are configured to make brute force attacks infeasible.

**Implement explicit permission checks for every sensitive operation.** Do not assume that because a user is authenticated, they are authorized. Check permissions explicitly before allowing access to resources or performing actions. Fail securely by denying access by default.

**Verify object ownership or permissions before allowing access.** When a user requests a resource by ID, verify they own or have permission to access that resource. This prevents insecure direct object references (IDOR) and horizontal privilege escalation.

**Use a consistent authorization model across the application.** Choose an authorization model (RBAC, ABAC, ACL) and apply it consistently. Inconsistent authorization is a common source of vulnerabilities where some operations are protected while others are not.

### Security Testing

**Test authentication and authorization independently, then test their interaction.** Verify that authentication is strong and cannot be bypassed. Verify that authorization checks are present and cannot be bypassed. Then verify that they work together correctly.

**Test authorization with different user roles and privilege levels.** Attempt to access resources and perform operations with different user roles. Test both horizontal privilege escalation (accessing other users' resources) and vertical privilege escalation (accessing higher-privilege functions).

**Test authorization in APIs by attempting to access endpoints without proper scopes or permissions.** Verify that API endpoints check scopes, permissions, or other authorization controls. Attempt to access endpoints with tokens that lack required scopes.

**Automate testing for common authorization vulnerabilities.** Implement automated tests that verify authorization checks are present and working correctly. Test for IDOR by attempting to access resources with different IDs. Test for privilege escalation by attempting to access higher-privilege functions.

### Common Vulnerabilities to Prevent

**Weak password hashing**: Use strong algorithms (bcrypt, Argon2) with appropriate work factors. Never use MD5, SHA1, or unsalted hashing.

**Missing rate limiting on authentication**: Implement rate limiting on login attempts to prevent brute force attacks. Implement account lockout after multiple failed attempts.

**Credentials in logs**: Do not log passwords, tokens, or other sensitive credentials. Implement log filtering to prevent accidental credential exposure.

**Missing authorization checks**: Verify that every operation that accesses or modifies sensitive data includes an authorization check. Do not assume authenticated users are authorized.

**Insecure direct object references (IDOR)**: Verify object ownership or permissions before allowing access. Do not trust user-supplied IDs without verification.

**Authorization based on user input**: Do not trust user-supplied data (hidden form fields, request parameters) to determine permissions. Always verify permissions server-side.

**Inconsistent authorization**: Apply authorization checks consistently across the application. Do not protect some operations while leaving others unprotected.

**Privilege escalation**: Implement authorization checks that prevent users from accessing resources or functions above their privilege level. Test for both horizontal and vertical privilege escalation.

### Design and Architecture

**Separate authentication and authorization into distinct layers.** Even if they are physically close in the codebase, they should be logically separate. Authentication establishes identity; authorization checks permissions.

**Implement defense in depth for authentication.** Use multiple authentication factors (passwords, MFA, certificates). Do not rely on a single factor. Implement rate limiting, account lockout, and secure session management.

**Implement a clear authorization architecture.** Choose an authorization model and apply it consistently. Implement authorization checks in a dedicated layer or middleware, not scattered throughout business logic.

**Log authentication and authorization events.** Log successful and failed authentication attempts, including timestamp, username, IP address, and outcome. Log authorization decisions, especially for sensitive operations.

**Monitor for suspicious activity.** Detect and alert on suspicious authentication patterns (multiple failed attempts, logins from unusual locations) and authorization patterns (unusual access patterns, privilege escalation attempts).

### Business and Compliance Perspective

**Authentication and authorization failures have significant business impact.** Weak authentication can lead to account takeover and unauthorized access. Weak authorization can lead to data breaches and unauthorized modifications. Both can result in regulatory fines, reputational damage, and loss of customer trust.

**Regulatory frameworks require strong authentication and authorization.** GDPR, HIPAA, PCI-DSS, and other frameworks require strong access controls. Compliance audits will specifically examine authentication and authorization implementations.

**Clear separation of concerns simplifies compliance and auditing.** When authentication and authorization are logically separate, it is easier to audit and demonstrate compliance. You can trace whether a security incident was due to authentication failure or authorization failure.

**Documentation and testing are essential for compliance.** Document your authentication and authorization architecture. Implement automated tests that verify controls are working correctly. Maintain audit logs that demonstrate compliance.

### Practical Takeaways for Different Roles

**For Developers**: Implement authentication using established libraries and standards. Implement explicit authorization checks for every sensitive operation. Test authorization thoroughly. Never trust client-side authorization checks. Use server-side policy to make authorization decisions.

**For Security Architects**: Design authentication and authorization as separate layers. Choose authorization models that fit your application's complexity. Implement consistent authorization across the application. Plan for scalability and flexibility as authorization requirements evolve.

**For Security Reviewers**: Test authentication and authorization independently. Look for missing authorization checks, IDOR vulnerabilities, and privilege escalation. Verify that authorization is enforced server-side. Check for inconsistent authorization across the application.

**For Penetration Testers**: Systematically test authentication and authorization. Document whether findings are authentication failures, authorization failures, or both. Test with different user roles and privilege levels. Test edge cases where authentication or authorization might fail.

**For Security Leaders**: Ensure authentication and authorization are treated as distinct concerns in your organization. Implement secure development practices that include testing for both. Allocate resources for security reviews and penetration testing. Monitor for authentication and authorization incidents.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]

## Revision Additions

# Additive Revisions for Authentication vs Authorization Chapter

## Addition: Modern Authentication Methods (Insert after "Authentication Layer" subsection in Architecture Perspective)

### Emerging Authentication Methods

Beyond passwords and traditional MFA, modern applications increasingly adopt passwordless and risk-based authentication approaches:

**WebAuthn/FIDO2 and Passkeys**

WebAuthn (Web Authentication) is a W3C standard that enables passwordless authentication using cryptographic keys stored on user devices (phones, security keys, laptops). Passkeys are a user-friendly implementation of WebAuthn that sync across devices.

- **How it works**: User registers a public key with the application; authentication requires the user to prove possession of the corresponding private key through a biometric or PIN.
- **Security properties**: Resistant to phishing (keys are origin-bound), credential stuffing (no password to compromise), and man-in-the-middle attacks.
- **When to use**: High-security applications, financial services, applications with high-value accounts. Increasingly recommended as primary authentication method.
- **Implementation**: Use established libraries (e.g., webauthn.io, Duo Security, Okta) rather than implementing from scratch.

**Certificate-Based Authentication (mTLS)**

Mutual TLS (mTLS) uses X.509 certificates for both client and server authentication. The client presents a certificate to prove identity; the server verifies the certificate chain.

- **How it works**: Client certificate is validated against a trusted certificate authority; the certificate contains identity information (CN, SAN, or custom attributes).
- **Security properties**: Strong cryptographic authentication, resistant to credential compromise (private key is not transmitted), suitable for machine-to-machine authentication.
- **When to use**: API authentication between services, high-security environments, regulatory requirements (e.g., government systems).
- **Implementation considerations**: Certificate lifecycle management (issuance, renewal, revocation), certificate storage and protection, CRL/OCSP checking for revocation.

**Biometric Authentication**

Biometric authentication uses biological characteristics (fingerprint, face, iris) to verify identity. Typically implemented as a second factor or in combination with other methods.

- **Security properties**: Difficult to forge or steal (though not impossible), user-friendly (no passwords to remember).
- **Limitations**: Cannot be changed if compromised (unlike passwords), privacy concerns, accuracy varies by implementation.
- **When to use**: Mobile applications, high-security environments, accessibility improvements.
- **Implementation**: Use platform-provided biometric APIs (iOS Face ID/Touch ID, Android BiometricPrompt) rather than implementing custom biometric processing.

**Risk-Based and Adaptive Authentication**

Risk-based authentication adjusts authentication requirements based on contextual factors (login location, device, time, user behavior). If risk is low, authentication may be streamlined; if risk is high, additional factors are required.

- **Factors considered**: Geographic location, device fingerprint, login time, user behavior patterns, network characteristics.
- **When to use**: Applications with large user bases, fraud-sensitive operations (banking, e-commerce), balancing security with user experience.
- **Implementation**: Requires behavioral analytics and risk scoring engines; often implemented through identity platforms (Okta, Auth0, Azure AD) rather than custom code.

---

## Addition: Authorization Patterns and Models (Insert after "Authorization Layer" subsection in Architecture Perspective)

### Authorization Models in Depth

Different authorization models suit different application architectures and complexity levels. Understanding the tradeoffs helps in selecting the right model.

**Role-Based Access Control (RBAC)**

RBAC assigns users to roles, and roles have permissions. Authorization checks verify whether the user's role has permission for the requested action.

```
User → Role → Permissions → Action
```

- **Advantages**: Simple to understand and implement, scales well for hierarchical organizations, easy to audit.
- **Disadvantages**: Coarse-grained (all users with a role get the same permissions), difficult to express complex policies, requires role explosion for fine-grained control.
- **Example**: Admin role has permission to "delete user"; Editor role has permission to "edit document"; Viewer role has permission to "view document".
- **When to use**: Applications with clear role hierarchies, simple permission structures, small to medium permission matrices.

**Attribute-Based Access Control (ABAC)**

ABAC makes authorization decisions based on attributes of the user, resource, action, and environment. Policies are expressed as rules that evaluate these attributes.

```
Policy: IF (user.department == "Finance" AND resource.classification == "Financial" AND action == "view") THEN allow
```

- **Advantages**: Highly flexible, can express complex policies, scales to large permission matrices, supports dynamic attributes.
- **Disadvantages**: Complex to implement and understand, harder to audit, requires careful policy design to avoid unintended access.
- **Example**: Allow access to financial reports if user is in Finance department, report is marked Financial, and user has completed compliance training.
- **When to use**: Complex authorization requirements, multi-tenant systems, applications with dynamic attributes, regulatory compliance requirements.

**Access Control Lists (ACLs)**

ACLs define which users or groups have access to specific resources. Each resource maintains a list of principals (users, groups) and their permissions.

```
Resource: /documents/report.pdf
ACL:
  - user:alice → read, write
  - user:bob → read
  - group:finance → read, write
```

- **Advantages**: Fine-grained control per resource, intuitive for file-system-like access, easy to understand who has access to what.
- **Disadvantages**: Does not scale well to large numbers of resources, difficult to express policies that apply across many resources, can lead to inconsistent permissions.
- **When to use**: File sharing systems, document management, resource-specific access control, small to medium numbers of resources.

**Policy-as-Code**

Policy-as-Code treats authorization policies as code that can be versioned, tested, and deployed. Policies are written in domain-specific languages (DSLs) or general-purpose languages.

- **Examples**: Open Policy Agent (OPA) with Rego language, AWS IAM policies, Kubernetes RBAC policies.
- **Advantages**: Policies are version-controlled, testable, auditable, can be deployed through CI/CD pipelines.
- **Disadvantages**: Requires expertise in policy language, can be complex for non-technical stakeholders, testing policies is non-trivial.
- **When to use**: Large organizations with complex policies, infrastructure-as-code environments, applications requiring policy auditability.

**Zanzibar-Inspired Fine-Grained Authorization**

Google's Zanzibar model (used internally for authorization) provides a scalable approach to fine-grained authorization. It uses a tuple-based model: (user, relation, resource).

```
Tuples:
  (alice, owner, document:123)
  (bob, editor, document:123)
  (group:finance, viewer, document:123)

Query: Does alice have "edit" permission on document:123?
Answer: Check if alice has "owner" or "editor" relation; if so, allow.
```

- **Advantages**: Highly scalable, supports complex relationships, efficient querying, supports delegation and inheritance.
- **Disadvantages**: Requires careful schema design, not suitable for simple applications, requires specialized systems (e.g., Authzed, Ory Keto).
- **When to use**: Large-scale systems with complex permission hierarchies, multi-tenant platforms, applications requiring delegation.

### Choosing an Authorization Model

| Model | Complexity | Scalability | Use Case |
|-------|-----------|-------------|----------|
| RBAC | Low | Medium | Simple hierarchies, clear roles |
| ABAC | High | High | Complex policies, dynamic attributes |
| ACL | Medium | Low | Resource-specific access, file sharing |
| Policy-as-Code | High | High | Large organizations, infrastructure |
| Zanzibar | High | Very High | Large-scale platforms, complex relationships |

**Decision Framework**:
1. Start with RBAC if your permission structure is simple and hierarchical.
2. Move to ABAC if you need to express policies based on user, resource, or environmental attributes.
3. Use ACLs for resource-specific access control (file sharing, document management).
4. Adopt Policy-as-Code if you need version control, testing, and auditability of policies.
5. Consider Zanzibar-inspired models for large-scale systems with complex permission relationships.

---

## Addition: Session Management Architecture (Insert after "Authorization Layer" subsection in Architecture Perspective)

### Session Management Security

Session management is a critical component of authentication that deserves dedicated attention. Sessions bridge the gap between initial authentication and subsequent requests.

**Session Storage Strategies**

Different storage mechanisms have different security and scalability tradeoffs:

- **In-Memory Storage**: Sessions stored in application memory. Fast, simple, but not suitable for distributed systems (sessions lost on restart, not shared across instances).
- **Server-Side Database**: Sessions stored in a database (SQL or NoSQL). Scalable, persistent, but slower than in-memory. Suitable for distributed systems.
- **Distributed Cache (Redis, Memcached)**: Sessions stored in a fast, distributed cache. Good balance of performance and scalability. Requires cache security (authentication, encryption).
- **Stateless Sessions (JWT)**: No server-side storage; session data is encoded in a signed token. Highly scalable, but token cannot be revoked immediately (revocation requires a blacklist).

**Session Security Properties**

Regardless of storage mechanism, sessions must have these security properties:

- **Secure Generation**: Session IDs must be cryptographically random, not predictable. Use `os.urandom()` or equivalent, not sequential or time-based IDs.
- **HttpOnly Flag**: Session cookies must have the HttpOnly flag to prevent JavaScript access. This prevents XSS attacks from stealing session cookies.
- **Secure Flag**: Session cookies must have the Secure flag to ensure transmission only over HTTPS.
- **SameSite Flag**: Session cookies must have the SameSite flag (Strict or Lax) to prevent CSRF attacks.
- **Session Timeout**: Sessions must expire after a period of inactivity. Implement both absolute timeout (maximum session duration) and idle timeout (inactivity duration).
- **Session Regeneration**: Session IDs must be regenerated after successful authentication to prevent session fixation attacks.
- **Secure Transmission**: Sessions must be transmitted only over HTTPS. Never transmit session IDs over HTTP.

**Session Fixation Prevention**

Session fixation attacks occur when an attacker forces a user to use a known session ID. Prevention strategies:

- **Regenerate Session ID After Login**: Create a new session ID after successful authentication. Invalidate the old session ID.
- **Validate Session ID Format**: Reject session IDs that do not match the expected format (length, character set).
- **Bind Session to IP Address or User-Agent**: Optionally bind sessions to the client's IP address or User-Agent header. This adds friction for attackers but can cause issues for legitimate users with dynamic IPs.

**Distributed Session Management**

In distributed systems with multiple application instances, sessions must be shared across instances:

- **Sticky Sessions**: Route requests from the same user to the same application instance. Simple but reduces load balancing flexibility.
- **Shared Session Store**: Store sessions in a centralized store (Redis, database) accessible to all instances. Requires session store security and availability.
- **Stateless Sessions (JWT)**: Encode session data in a signed token. No server-side storage needed, but token cannot be revoked immediately.

**Session Revocation and Logout**

Logout must invalidate the session:

- **Server-Side Logout**: Delete the session from the session store. Immediate revocation.
- **Token Blacklist**: For JWT tokens, maintain a blacklist of revoked tokens. Requires checking the blacklist on every request.
- **Token Expiration**: Rely on token expiration. Tokens are valid until expiration; revocation is delayed until expiration.

---

## Addition: API Authentication Lifecycle (Insert after "Authentication Layer" subsection in Architecture Perspective)

### API Authentication Patterns and Token Lifecycle

API authentication differs from web application authentication in important ways. APIs typically use tokens (OAuth 2.0 access tokens, JWT, API keys) rather than session cookies.

**OAuth 2.0 Token Lifecycle**

OAuth 2.0 is the industry standard for API authentication. Understanding the token lifecycle is essential for secure implementation.

```
1. Client requests access token (with credentials or refresh token)
2. Authorization server validates credentials and issues access token
3. Client includes access token in API requests (Authorization: Bearer <token>)
4. API server validates token signature and expiration
5. If token expires, client uses refresh token to obtain new access token
6. Refresh token is long-lived; access token is short-lived
```

**Access Token Design**:
- **Short Lifetime**: Access tokens should expire quickly (minutes to
