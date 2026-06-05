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

1. User submits credentials to the authentication gateway over HTTPS
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

An internal API endpoint is protected by authorization checks—it verifies that the user has the "admin" role before allowing access. However, the endpoint does not require authentication