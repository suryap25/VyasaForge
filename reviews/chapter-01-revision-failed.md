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
- Evaluate token-based authentication systems and identify common implementation flaws
- Design authorization systems for multi-tenant and distributed architectures

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
@app.