# Chapter 01: Fundamentals of Authentication and Authorization

## Learning Objectives

After completing this chapter, you will be able to:

- Distinguish between authentication and authorization and explain why both are essential to application security
- Identify the three primary authentication factors and recognize how they combine in multi-factor authentication schemes
- Design authentication flows that resist common attacks including credential stuffing, brute force, and replay attacks
- Implement authorization controls that enforce principle of least privilege and separation of duties
- Evaluate authentication and authorization mechanisms in existing applications using security assessment techniques
- Recognize common misconfigurations and design flaws that lead to authentication and authorization bypasses
- Apply secure design patterns for session management, token validation, and access control decisions
- Conduct security interviews and code reviews focused on authentication and authorization vulnerabilities

## Conceptual Foundation

Authentication and authorization are foundational security controls that protect applications from unauthorized access. Despite their related names and frequent confusion, they serve distinct purposes in the security architecture of any system.

**Authentication** is the process of verifying that a user or system is who they claim to be. It answers the question: "Are you really who you say you are?" Authentication establishes identity through evidence—something the user knows, something they have, or something they are. When a user logs into a web application with a username and password, they are authenticating. When a mobile application validates a certificate presented by an API server, that is also authentication.

**Authorization** is the process of determining what an authenticated user or system is allowed to do. It answers the question: "What are you permitted to access or modify?" Authorization operates on the established identity and applies rules, policies, and permissions to control access to resources. After a user successfully authenticates, authorization determines whether they can view a customer record, modify a configuration setting, or delete a file.

The relationship between these concepts is sequential and complementary. Authentication must occur first—you cannot authorize an unknown entity. However, successful authentication does not automatically grant access to all resources. A user might be successfully authenticated but lack authorization to perform a specific action.

### The Three Factors of Authentication

Authentication mechanisms rely on three fundamental factors:

**Something You Know** represents information only the legitimate user should possess. Passwords, PINs, security questions, and passphrases fall into this category. This factor is vulnerable to guessing, dictionary attacks, phishing, and social engineering. Passwords remain the most common authentication factor in web applications despite their inherent weaknesses.

**Something You Have** represents a physical or digital object that only the legitimate user should possess. Hardware security keys, smart cards, mobile devices receiving SMS codes, and authenticator applications generate time-based one-time passwords (TOTP). This factor is more resistant to remote attacks but introduces complexity and potential loss or theft scenarios.

**Something You Are** represents biometric characteristics unique to the individual. Fingerprints, facial recognition, iris scans, and voice recognition fall into this category. Biometric factors are difficult to forge or steal, but they raise privacy concerns and may have accessibility implications.

**Multi-factor authentication (MFA)** combines two or more of these factors. A user entering a password (something they know) and then providing a code from an authenticator app (something they have) is using two factors. MFA significantly increases the difficulty for attackers to compromise accounts, even when one factor is compromised.

### Authorization Models

Authorization decisions in applications typically follow one of several models:

**Role-Based Access Control (RBAC)** assigns users to roles, and roles have associated permissions. A user with the "Administrator" role can perform administrative actions. This model is simple to understand and implement but can become inflexible as permission requirements grow more granular.

**Attribute-Based Access Control (ABAC)** makes authorization decisions based on attributes of the user, resource, action, and environment. A policy might state: "Allow access to medical records if the user's department is 'Healthcare' AND the resource's classification is 'Internal' AND the current time is during business hours." ABAC is more flexible but requires careful policy design to avoid unintended access.

**Access Control Lists (ACLs)** explicitly define which users or groups can perform which actions on specific resources. A file might have an ACL stating that user "alice" can read and write, while user "bob" can only read. ACLs are granular but do not scale well to large numbers of users and resources.

**Capability-Based Security** grants users unforgeable tokens (capabilities) that represent permission to perform specific actions. The token itself proves authorization. This model is less common in traditional web applications but appears in some API designs and microservices architectures.

## Architecture Perspective

Authentication and authorization must be considered at multiple architectural levels: the application layer, the infrastructure layer, and the organizational layer.

### Application-Level Architecture

Most web and mobile applications implement authentication through a login endpoint that accepts credentials and returns a session token or JWT (JSON Web Token). The application then validates this token on subsequent requests to verify the user's identity and determine their authorization level.

```
User Request Flow:
1. User submits credentials to /login endpoint
2. Application validates credentials against user database
3. Application creates session token or JWT
4. Token is returned to client (in response body, cookie, or header)
5. Client includes token in subsequent requests
6. Application validates token and checks authorization
7. Application processes request or denies access
```

The token serves as proof of authentication. The application must validate the token's integrity, expiration, and association with the correct user on every request that requires authentication. Failure to validate tokens on every request is a common vulnerability.

For web applications, tokens are typically stored in HTTP cookies or the Authorization header. Cookies are automatically sent by browsers with each request but are vulnerable to cross-site request forgery (CSRF) attacks if not properly protected. Authorization headers require explicit client-side code to include but are not automatically sent, providing some protection against CSRF.

Mobile applications typically store tokens in secure local storage (Keychain on iOS, Keystore on Android) and include them in request headers. Mobile applications do not have the same CSRF vulnerability as web browsers, but they must protect tokens from being extracted by malware or through insecure storage.

### Session Management Architecture

Sessions represent the authenticated state of a user. A session has a lifetime—it begins when the user authenticates and ends when the user logs out or the session expires.

**Server-side sessions** store session state on the server. The client receives a session ID (typically in a cookie), and the server maintains a data structure mapping session IDs to user information. When the client makes a request, the server looks up the session ID and retrieves the associated user data. This approach is straightforward but requires server-side storage and does not scale well across multiple servers without a shared session store (like Redis or Memcached).

**Stateless sessions** (typically implemented with JWTs) encode all necessary information in the token itself. The server does not maintain session state; instead, it validates the token's signature and reads the user information directly from the token. This approach scales better across multiple servers but makes it difficult to revoke sessions before expiration and requires careful handling of token contents.

### Cross-System Authentication

In modern architectures, applications often need to authenticate users across multiple systems. A user might authenticate to a central identity provider (IdP) and then access multiple applications without re-authenticating.

**OAuth 2.0** is a delegation protocol that allows users to grant applications access to their resources without sharing passwords. A user can authorize a third-party application to access their Google account data without giving the application their Google password. OAuth 2.0 is widely used for social login and API access delegation.

**OpenID Connect (OIDC)** builds on OAuth 2.0 to add authentication. It provides a standardized way for applications to verify user identity through a central provider. OIDC is commonly used in enterprise environments with centralized identity management.

**SAML 2.0** is an XML-based standard for exchanging authentication and authorization information. It is commonly used in enterprise single sign-on (SSO) scenarios where users authenticate once and access multiple applications.

## AppSec Lens

From an application security perspective, authentication and authorization are critical attack surfaces. Compromising these controls allows attackers to impersonate legitimate users, access unauthorized data, and perform unauthorized actions.

### Authentication Attack Vectors

**Credential-Based Attacks** target the "something you know" factor. Attackers use dictionaries, brute force, and rainbow tables to guess passwords. Phishing attacks trick users into revealing credentials. Credential stuffing uses credentials leaked from one service to attempt access to other services, exploiting password reuse.

**Session Hijacking** involves stealing or predicting session tokens. If tokens are predictable, attackers can forge valid tokens. If tokens are transmitted insecurely (over HTTP instead of HTTPS), attackers can intercept them. If tokens are stored insecurely on the client (in local storage without encryption), malware can steal them.

**Man-in-the-Middle (MITM) Attacks** intercept communication between client and server. Without HTTPS, attackers can capture credentials and session tokens. Even with HTTPS, attackers can perform MITLS attacks if certificate validation is not properly implemented.

**Replay Attacks** capture valid authentication messages and replay them later. A captured login request might be replayed to create a new session. Nonces (numbers used once) and timestamps help prevent replay attacks.

**Factor-Specific Attacks** target individual authentication factors. SMS-based codes can be intercepted through SIM swapping or compromised carrier accounts. Biometric systems can be spoofed with high-quality images or 3D models. Hardware keys can be lost or stolen.

### Authorization Attack Vectors

**Privilege Escalation** occurs when a user gains access to resources or actions beyond their authorized level. Vertical privilege escalation involves gaining higher-level privileges (a regular user becoming an administrator). Horizontal privilege escalation involves accessing resources belonging to other users at the same privilege level.

**Insecure Direct Object References (IDOR)** occur when authorization checks are missing or bypassable. An application might check that a user is authenticated but fail to verify that the user is authorized to access the specific resource. For example, an API endpoint `/api/invoices/123` might return the invoice for any authenticated user, regardless of whether they own that invoice.

**Broken Access Control** encompasses various authorization failures: missing authorization checks, authorization checks that can be bypassed, authorization logic that is incorrect, and authorization policies that are too permissive.

**Attribute Manipulation** occurs when users can modify attributes that affect authorization decisions. If an application stores the user's role in a client-side cookie or JWT without proper validation, an attacker might modify the cookie to grant themselves higher privileges.

**Path Traversal and Resource Enumeration** allow attackers to discover and access resources they should not be able to access. An attacker might enumerate user IDs to discover all users in the system or use path traversal to access files outside their authorized directory.

### Common Vulnerability Patterns

**Missing Authentication** occurs when endpoints that should require authentication do not check for authentication. An API endpoint might process requests without verifying that the user is authenticated.

**Weak Authentication** uses authentication mechanisms that are easily bypassed. Hardcoded credentials, default credentials, or authentication logic that can be circumvented through simple manipulation.

**Improper Session Management** includes session tokens that are predictable, session tokens that are not validated on every request, sessions that do not expire, and sessions that are not properly invalidated on logout.

**Insufficient Authorization Checks** fail to verify that the authenticated user is authorized to perform the requested action. The application might check that a user is authenticated but not verify that they own the resource they are trying to access.

**Hardcoded Credentials** embedded in source code, configuration files, or compiled binaries. These credentials are often discovered through code review, decompilation, or source code leaks.

## Developer Lens

Developers implementing authentication and authorization must balance security with usability and performance. Secure implementation requires understanding common pitfalls and applying proven patterns.

### Password Handling

Passwords must never be stored in plaintext. Instead, passwords should be hashed using a strong, slow hashing algorithm designed for password storage.

**Argon2**, **bcrypt**, **scrypt**, and **PBKDF2** are acceptable password hashing algorithms. These algorithms are intentionally slow, making brute force attacks computationally expensive. Argon2 is recommended for new implementations due to its resistance to GPU and ASIC attacks. Bcrypt is widely supported and remains a solid choice.

```python
# Example: Secure password hashing with bcrypt
import bcrypt

# During registration
password = request.form['password']
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
user.password_hash = hashed

# During login
provided_password = request.form['password']
if bcrypt.checkpw(provided_password.encode('utf-8'), user.password_hash):
    # Password is correct, authenticate user
    create_session(user)
else:
    # Password is incorrect
    return "Invalid credentials"
```

Developers should never implement custom password hashing. Standard library functions or well-tested third-party libraries should be used. Passwords should be hashed with a salt (a random value mixed with the password before hashing) to prevent rainbow table attacks. Modern algorithms like Argon2 and bcrypt handle salting automatically.

### Session Token Generation and Validation

Session tokens must be cryptographically random and sufficiently long to prevent guessing attacks. A token should be at least 128 bits of entropy.

```python
# Example: Secure session token generation
import secrets
import hashlib

# Generate token
token = secrets.token_urlsafe(32)  # 256 bits of entropy

# Store token hash (not the token itself) in database
token_hash = hashlib.sha256(token.encode()).hexdigest()
session = Session(user_id=user.id, token_hash=token_hash, expires_at=datetime.utcnow() + timedelta(hours=1))
db.session.add(session)
db.session.commit()

# Return token to client (only time the plaintext token is transmitted)
return {"token": token}
```

When validating a token, the application should:
1. Verify the token's format and length
2. Hash the token and look up the hash in the session store
3. Verify that the session has not expired
4. Verify that the session is associated with the correct user
5. Verify that the session has not been invalidated

Tokens should have a reasonable expiration time. Short-lived tokens (15 minutes to 1 hour) reduce the window of opportunity if a token is compromised. Refresh tokens can be used to obtain new access tokens without requiring the user to re-authenticate.

### JWT Implementation

JWTs are self-contained tokens that encode user information and are signed by the server. The server can validate a JWT without looking up session state in a database.

```python
# Example: JWT creation and validation
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-keep-this-safe"

# Create JWT
payload = {
    'user_id': user.id,
    'username': user.username,
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Validate JWT
try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = decoded['user_id']
    # Token is valid
except jwt.ExpiredSignatureError:
    # Token has expired
except jwt.InvalidSignatureError:
    # Token signature is invalid (tampered with)
except jwt.DecodeError:
    # Token format is invalid
```

Important considerations for JWT implementation:

- Use a strong, random secret key for signing. The key should be at least 256 bits.
- Always validate the signature. Never trust a JWT without verifying the signature.
- Always check the expiration time. Do not accept expired tokens.
- Use HTTPS to transmit JWTs. JWTs are not encrypted; they are only signed. An attacker who intercepts a JWT can read its contents.
- Do not store sensitive information in JWTs. The payload is base64-encoded, not encrypted.
- Include an expiration time (exp claim) in every JWT.
- Consider including a "not before" time (nbf claim) to prevent tokens from being used before they should be.
- Implement token revocation for logout and password changes. Use a blacklist## Pentest Lens

Security testers and penetration testers assess authentication and authorization controls to identify weaknesses that could be exploited by attackers.

### Authentication Testing

**Credential Testing** involves attempting to log in with common credentials, default credentials, and credentials obtained from breach databases. Testers use tools to automate credential stuffing attacks and measure how quickly accounts are compromised. Testing should verify that rate limiting, account lockouts, and CAPTCHA challenges are properly implemented. Testers should also check whether the application reveals whether a username exists (user enumeration) through different error messages for invalid usernames versus invalid passwords.

**Token Validation Testing** verifies that session tokens and JWTs are properly validated. Testers attempt to:
- Use expired tokens to verify expiration is enforced
- Modify token contents (user ID, role, permissions) to detect signature validation failures
- Use tokens with `alg: none` to detect algorithm validation bypasses
- Predict or brute force tokens to detect weak randomness
- Replay captured tokens to verify they are invalidated after logout
- Use tokens from one user to access another user's resources

**Session Management Testing** examines how sessions are created, stored, and validated. Testers verify that:
- Session IDs are cryptographically random and sufficiently long
- Sessions expire after appropriate timeouts
- Sessions are invalidated on logout
- Session IDs are regenerated after authentication (preventing session fixation)
- Concurrent sessions are limited or properly managed
- Session cookies have Secure, HttpOnly, and SameSite flags
- Sessions cannot be hijacked through MITM attacks (HTTPS enforcement)

**Token Storage Testing** checks where and how tokens are stored on clients. Testers verify that:
- Tokens are not stored in local storage (vulnerable to XSS)
- Tokens are not passed in URLs (exposed in logs and referrer headers)
- Mobile applications use secure storage (Keychain on iOS, Keystore on Android)
- Tokens are transmitted only over HTTPS

### Authorization Testing

**Parameter Manipulation Testing** attempts to bypass authorization by modifying request parameters. Testers change:
- User IDs in URLs or request bodies to access other users' resources
- Role or permission parameters to escalate privileges
- Resource IDs to access unauthorized resources
- Hidden form fields that affect authorization decisions

**Resource Enumeration Testing** discovers resources by systematically testing resource identifiers. Testers attempt to:
- Access sequential resource IDs (`/api/invoices/1`, `/api/invoices/2`, etc.)
- Discover hidden endpoints through directory brute forcing
- Access resources with different user accounts to identify IDOR vulnerabilities
- Use path traversal sequences to access unauthorized resources

**Privilege Escalation Testing** attempts to gain higher-level privileges. Testers verify that:
- Regular users cannot access administrative endpoints
- Users cannot modify their role or permission attributes
- Authorization checks are performed on the server, not the client
- Sensitive operations require appropriate authorization

**Horizontal Access Testing** attempts to access resources belonging to other users at the same privilege level. Testers with one user account attempt to:
- View other users' profiles or data
- Modify other users' resources
- Delete other users' data
- Access other users' files or documents

**Missing Authorization Testing** identifies endpoints that should require authorization but do not. Testers attempt to:
- Access protected endpoints without authentication
- Access protected endpoints with expired or invalid tokens
- Access administrative functions with regular user accounts
- Perform state-changing operations (POST, PUT, DELETE) without authorization

**Attribute-Based Authorization Testing** attempts to bypass authorization by manipulating attributes. Testers verify that:
- Authorization decisions are based on server-side attributes, not client-provided attributes
- Users cannot modify attributes that affect authorization (department, role, clearance level)
- Authorization policies are correctly enforced based on all required attributes

**Session Hijacking Testing** attempts to steal or predict session tokens. Testers verify that:
- Session tokens are not predictable
- Session tokens are not exposed in logs, URLs, or referrer headers
- Session tokens are transmitted only over HTTPS
- Session tokens cannot be intercepted through MITM attacks
- Session tokens are properly validated on every request"
    },
    {## Authentication Vulnerabilities

**Weak Password Requirements**
Applications that do not enforce minimum password length, complexity, or character diversity allow users to set easily guessable passwords. Testing reveals accounts created with passwords like "123456", "password", or "admin". Attackers use dictionary attacks and brute force against these weak passwords. Remediation requires enforcing minimum 12-character passwords with mixed character types and rejecting passwords found in breach databases.

**Credential Stuffing Without Rate Limiting**
Login endpoints that accept unlimited authentication attempts allow attackers to test credentials leaked from other services. An attacker obtains a list of 10 million username/password pairs from a breach and systematically tests them against the application. Without rate limiting, thousands of accounts are compromised in hours. Implement progressive delays after failed attempts, account lockouts after 5-10 failed attempts, and CAPTCHA challenges to slow attackers.

**Session Tokens in URLs**
Applications that pass session tokens as URL parameters (e.g., `https://app.com/dashboard?sessionid=abc123`) expose tokens in browser history, server logs, and referrer headers. Any system that logs URLs captures the session token. Tokens should be transmitted in HTTP-only cookies or Authorization headers, never in URLs.

**Missing Token Expiration**
Sessions that never expire allow attackers who steal a token to maintain access indefinitely. Testing reveals tokens that remain valid months or years after creation. Implement short expiration times (15 minutes to 1 hour for access tokens) and require re-authentication or refresh token validation to obtain new tokens.

**Predictable Session Tokens**
Applications that generate session tokens using weak randomness (sequential numbers, timestamps, or insufficient entropy) allow attackers to predict valid tokens. Testing with multiple login attempts reveals patterns in token generation. Use cryptographically secure random number generators with at least 128 bits of entropy.

**JWT Signature Validation Bypass**
Applications that accept JWTs with `"alg": "none"` or fail to validate signatures allow attackers to forge tokens. An attacker modifies the JWT payload to change their user ID or role and the application accepts it. Always validate JWT signatures and reject tokens with `alg: none`.

**Hardcoded Credentials in Code**
Source code review reveals API keys, database passwords, and service account credentials embedded in application code. These credentials are often discovered through GitHub searches, decompiled mobile apps, or source code leaks. Implement credential management systems and scan code repositories for secrets.

**SMS-Based MFA Bypass**
Applications using SMS for MFA are vulnerable to SIM swapping, where attackers convince mobile carriers to transfer the victim's phone number to a device they control. Testing reveals that SMS codes are also vulnerable to interception on unencrypted networks. Recommend authenticator apps (TOTP) or hardware keys instead of SMS.

**Missing MFA for Privileged Accounts**
Administrative accounts and accounts with elevated privileges are not protected by MFA, allowing attackers who compromise a single password to gain full system access. Mandate MFA for all administrative accounts and accounts with access to sensitive data.

**Concurrent Session Abuse**
Applications allow unlimited concurrent sessions from the same account, enabling attackers to maintain access even after the legitimate user logs out. A user logs in from their office, and an attacker simultaneously logs in from another location. Both sessions remain active. Implement concurrent session limits or invalidate previous sessions when a new login occurs.

## Authorization Vulnerabilities

**Insecure Direct Object References (IDOR)**
API endpoints fail to verify that the authenticated user is authorized to access the requested resource. Testing reveals that changing a resource ID in the URL or API request returns data belonging to other users. For example, `/api/invoices/123` returns the invoice regardless of who owns it. Implement authorization checks that verify the user owns or has permission to access each resource.

**Missing Authorization Checks**
Endpoints that should require authorization do not check permissions. An authenticated user can access administrative functions, modify other users' data, or view sensitive reports. Testing with a low-privilege account reveals that authorization checks are missing. Add authorization checks to every endpoint that accesses protected resources.

**Broken Role-Based Access Control**
RBAC implementation fails to properly enforce role boundaries. Users can modify their role in client-side cookies or JWTs, or the application fails to check roles on the server. Testing reveals that changing a role claim in a JWT grants access to restricted functions. Always validate roles on the server and never trust client-provided role information.

**Privilege Escalation Through Parameter Manipulation**
Applications allow users to modify parameters that affect authorization decisions. A user modifies a hidden form field from `role=user` to `role=admin`, or changes a user ID parameter to access another user's data. Testing reveals that authorization decisions are based on user-controlled parameters. Use server-side authorization checks based on the authenticated user's identity, not user-provided parameters.

**Horizontal Privilege Escalation**
Users can access resources belonging to other users at the same privilege level. A user views their own profile at `/api/users/123` and discovers they can access `/api/users/124`, `/api/users/125`, etc., viewing other users' profiles. Testing with multiple user accounts reveals that authorization checks are missing or insufficient. Implement proper authorization checks for each resource.

**Vertical Privilege Escalation**
Users can perform actions reserved for higher-privilege roles. A regular user accesses administrative endpoints, modifies system settings, or creates new administrator accounts. Testing reveals that authorization checks are missing or can be bypassed. Implement strict authorization checks that verify the user has the required role or permission.

**Path Traversal in Authorization**
Applications use file paths or resource names in authorization decisions without proper validation. A user accesses `/api/files/../../admin/config.txt` to bypass authorization checks. Testing reveals that path traversal sequences are not filtered. Validate and normalize all resource identifiers before using them in authorization decisions.

**Attribute-Based Authorization Bypass**
Applications make authorization decisions based on attributes that users can modify. A user modifies their department attribute in a client-side cookie to access department-specific data they should not see. Testing reveals that authorization decisions are based on user-controlled attributes. Always validate authorization attributes on the server.

**Missing Authorization on State-Changing Operations**
Applications check authorization for read operations but not for write operations. A user cannot view a resource but can modify or delete it. Testing reveals that POST, PUT, and DELETE endpoints lack authorization checks. Implement authorization checks on all operations, not just read operations.

**Overly Permissive Default Permissions**
New resources are created with permissions that allow all users to access them. A user creates a document that is automatically shared with all users in the organization. Testing reveals that default permissions are too permissive. Implement secure defaults where new resources are private by default and permissions must be explicitly granted.

---

# Secure Design Guidance

## Authentication Design Principles

**Implement Multi-Factor Authentication for High-Value Accounts**
Require MFA for administrative accounts, accounts with access to sensitive data, and accounts that can modify security settings. Offer MFA options to all users. Prioritize authenticator apps (TOTP) and hardware keys over SMS, which is vulnerable to SIM swapping. For applications handling financial data or personal information, mandate MFA for all users.

**Use Strong, Slow Password Hashing**
Hash passwords with Argon2, bcrypt, or scrypt using appropriate cost factors. Argon2 is recommended for new implementations. Use a cost factor that requires 100-500ms to hash a password on current hardware. This makes brute force attacks computationally expensive. Never use fast hashing algorithms like MD5 or SHA-1 for passwords.

**Implement Rate Limiting on Authentication Endpoints**
Limit login attempts to prevent brute force attacks. After 5 failed attempts, require a CAPTCHA or delay subsequent attempts exponentially. After 10-15 failed attempts, lock the account temporarily. Implement rate limiting per username and per IP address. Monitor for distributed brute force attacks from multiple IP addresses.

**Transmit Credentials Only Over HTTPS**
Never transmit credentials over unencrypted HTTP. Use HTTPS for all authentication endpoints. Implement HSTS (HTTP Strict-Transport-Security) headers to force browsers to use HTTPS. Validate SSL/TLS certificates properly in mobile applications and API clients.

**Use Secure Session Management**
For server-side sessions, store session state in a secure, centralized store (database, Redis, Memcached). Generate session IDs with cryptographic randomness (at least 128 bits of entropy). Set session cookies with Secure and HttpOnly flags to prevent JavaScript access and transmission over HTTP. Implement session expiration (15 minutes to 1 hour for web applications).

**Implement Proper JWT Handling**
If using JWTs, always validate signatures using the correct algorithm. Reject tokens with `alg: none`. Include expiration times (exp claim) and issue times (iat claim). Use HTTPS to transmit JWTs. Do not store sensitive information in JWT payloads. Consider using short-lived access tokens (15 minutes) with refresh tokens for longer-lived sessions.

**Secure Password Reset Flows**
Use unique, random tokens that expire quickly (1 hour or less). Send reset links via email rather than SMS. Do not include tokens in URLs if possible; instead, use POST requests with tokens in request bodies. Invalidate tokens after use. Invalidate all existing sessions after a password reset. Do not reveal whether an email address is registered (prevent user enumeration).

**Implement Account Lockout Protections**
Lock accounts after multiple failed authentication attempts. Implement progressive delays (exponential backoff) rather than immediate lockouts to reduce user frustration. Provide a mechanism for users to unlock their accounts (email verification or support contact). Monitor for account lockout attacks used to deny service.

**Validate Authentication on Every Request**
Do not assume a user is authenticated based on a previous request. Validate authentication tokens, session IDs, or credentials on every request that requires authentication. Implement centralized authentication middleware that checks authentication before processing requests.

## Authorization Design Principles

**Implement Principle of Least Privilege**
Grant users only the minimum permissions required to perform their job functions. A customer service representative should not have access to financial data or system administration functions. Regularly review and revoke unnecessary permissions. Implement role-based access control with well-defined roles that reflect job functions.

**Enforce Separation of Duties**
Require multiple people to approve sensitive actions. A single person should not be able to create a user account, approve access, and audit the access. Implement approval workflows for sensitive operations. Require different people to request, approve, and perform sensitive actions.

**Implement Server-Side Authorization Checks**
Never rely on client-side authorization checks. Always verify authorization on the server before processing requests. Client-side checks improve user experience but do not provide security. An attacker can bypass client-side checks by modifying requests.

**Use Centralized Authorization Logic**
Implement authorization checks in a centralized location (middleware, decorators, or a dedicated authorization service) rather than scattered throughout the codebase. This ensures consistent authorization decisions and makes it easier to audit and modify authorization policies.

**Verify Resource Ownership**
Before allowing a user to access a resource, verify that the user owns the resource or has explicit permission to access it. Do not assume that because a user is authenticated, they can access any resource. Check that the resource belongs to the user or that the user has been granted permission.

**Implement Attribute-Based Access Control for Complex Scenarios**
For applications with complex authorization requirements, use ABAC instead of simple RBAC. Define policies that consider user attributes, resource attributes, action types, and environmental factors. For example: "Allow access to medical records if the user's role is 'Doctor' AND the user's department matches the record's department AND the current time is during business hours."

**Use Explicit Deny Over Implicit Allow**
Design authorization policies to explicitly deny access by default. Only grant access when a specific permission exists. Do not assume that missing a deny rule means access is allowed. This fail-secure approach prevents accidental over-permissioning.

**Implement Resource-Level Authorization**
Check authorization at the resource level, not just the endpoint level. An endpoint might be accessible to authenticated users, but authorization checks should verify that each user can access each specific resource. For example, a user can access `/api/invoices` but only invoices they own.

**Audit Authorization Decisions**
Log authorization decisions, especially denials. Track who attempted to access what resources and whether access was granted or denied. Use audit logs to detect unauthorized access attempts and identify potential security issues.

**Implement Time-Based Access Control**
For sensitive operations, restrict access to specific times or time windows. Administrative functions might only be accessible during business hours. Sensitive data access might be restricted to specific time periods. Implement time-based authorization checks.

**Use Immutable Audit Trails**
Maintain immutable records of who accessed what resources and when. Audit trails should not be modifiable by users or even administrators. Use append-only logs or write-once storage. Regularly export and archive audit logs to prevent tampering.

## Session Management Design

**Implement Session Timeout**
Set appropriate session timeouts based on the application's security requirements and user experience needs. Web applications typically use 15-minute to 1-hour timeouts. Sensitive applications might use shorter timeouts. Implement both absolute timeout (maximum session duration) and idle timeout (inactivity duration).

**Invalidate Sessions on Logout**
When a user logs out, immediately invalidate their session. Remove the session from the server-side session store or mark it as invalid. Do not rely on client-side token deletion; the server must invalidate the session.

**Regenerate Session IDs After Authentication**
After successful authentication, generate a new session ID. This prevents session fixation attacks where an attacker tricks a user into using a known session ID. The attacker cannot use the pre-authentication session ID after the user logs in.

**Implement Concurrent Session Limits**
Limit the number of concurrent sessions per user. When a user logs in from a new location, either reject the new login or invalidate the previous session. This prevents attackers from maintaining access after the legitimate user logs out.

**Protect Session Cookies**
Set the Secure flag on session cookies to transmit them only over HTTPS. Set the HttpOnly flag to prevent JavaScript access. Set the SameSite attribute to prevent CSRF attacks. For sensitive applications, consider setting the Domain attribute to restrict cookies to specific subdomains.

**Implement Session Binding**
Bind sessions to specific client characteristics (IP address, user agent, device fingerprint) to detect session hijacking. If a session is used from a different IP address or user agent, require re-authentication. Be careful not to bind too tightly, as legitimate users might change networks or devices.

---

# Interview Questions

## Authentication Questions

**1. Explain the difference between authentication and authorization. Why are both necessary?**
*Expected Answer:* Authentication verifies identity (who you are), while authorization determines what you're allowed to do. Both are necessary because authentication alone doesn't prevent unauthorized access—you need to verify both that someone is who they claim to be AND that they have permission to access specific resources.

**2. What are the three factors of authentication, and what are the strengths and weaknesses of each?**
*Expected Answer:* Something you know (passwords—weak to phishing and guessing), something you have (tokens/keys—resistant to remote attacks but can be lost), something you are (biometrics—hard to forge but raises privacy concerns). Multi-factor authentication combines factors to increase security.

**3. Describe a secure password hashing implementation. Why shouldn't developers implement their own hashing?**
*Expected Answer:* Use Argon2, bcrypt, or scrypt with appropriate cost factors (100-500ms per hash). Never use MD5, SHA-1, or unsalted hashing. Custom implementations often have subtle flaws (insufficient entropy, timing attacks, weak salting). Standard libraries have been reviewed by security experts.

**4. What is the difference between server-side sessions and stateless sessions (JWTs)? What are the tradeoffs?**
*Expected Answer:* Server-side sessions store state on the server; JWTs encode state in the token. Server-side sessions are easier to revoke but require shared storage across servers. JWTs scale better but make revocation difficult and require careful handling of token contents. Both require HTTPS and proper validation.

**5. How would you prevent credential stuffing attacks?**
*Expected Answer:* Implement rate limiting on login endpoints, require CAPTCHA after failed attempts, lock accounts after multiple failures, monitor for distributed attacks, encourage users to use unique passwords, and check passwords against breach databases.

**6. What is session fixation, and how do you prevent it?**
*Expected Answer:* Session fixation occurs when an attacker tricks a user into using a known session ID. Prevent it by regenerating the session ID after successful authentication. The attacker's pre-authentication session ID becomes invalid.

**7. Explain the security implications of storing session tokens in URLs versus cookies versus headers.**
*Expected Answer:* URLs expose tokens in browser history, server logs, and referrer headers. Cookies can be protected with Secure and HttpOnly flags but are vulnerable to CSRF. Headers require explicit client-side code but are not automatically sent. Best practice: use HTTP-only cookies for web apps or Authorization headers for APIs.

**8. What vulnerabilities exist in JWT implementations, and how do you prevent them?**
*Expected Answer:* Accepting `alg: none`, not validating signatures, not checking expiration, storing sensitive data in payloads, using weak secrets. Prevent by always validating signatures, checking expiration, using strong secrets (256+ bits), and never storing sensitive data in JWTs.

**9. How would you implement secure password reset?**
*Expected Answer:* Use unique, random tokens that expire quickly (1 hour). Send via email, not SMS. Invalidate tokens after use. Invalidate all sessions after reset. Don't reveal if email exists (prevent enumeration). Require setting a new password, not sending temporary password.

**10. What is multi-factor authentication, and why is it important?**
*Expected Answer:* MFA requires two or more authentication factors. It significantly increases security because compromising one factor doesn't grant access. Recommend authenticator apps or hardware keys over SMS. Mandate MFA for administrative accounts and sensitive data access.

## Authorization Questions

**11. Explain the principle of least privilege and how you would implement it.**
*Expected Answer:* Grant users only minimum permissions needed for their role. Implement role-based access control with well-defined roles. Regularly audit and revoke unnecessary permissions. Default to deny access; only grant when necessary.

**12. What is an Insecure Direct Object Reference (IDOR), and how do you prevent it?**
*Expected Answer:* IDOR occurs when authorization checks are missing or bypassable, allowing users to access resources they shouldn't. Prevent by implementing authorization checks that verify the user owns or has permission to access each resource. Check authorization on the server, not the client.

**13. Describe the difference between vertical and horizontal privilege escalation.**
*Expected Answer:* Vertical escalation: gaining higher-level privileges (user becoming admin). Horizontal escalation: accessing resources of other users at the same level. Prevent both by implementing proper authorization checks that verify the user has required permissions for each action.

**14. How would you implement role-based access control (RBAC)?**
*Expected Answer:* Define roles that reflect job functions. Assign permissions to roles, not individual users. Assign users to roles. Check user's role on the server before allowing actions. Store roles in server-side session or database, not client-side. Validate roles on every request.

**15. What is attribute-based access control (ABAC), and when would you use it instead of RBAC?**
*Expected Answer:* ABAC makes decisions based on user attributes, resource attributes, actions, and environment. Use ABAC when authorization requirements are complex and role-based rules are insufficient. Example: "Allow access if user.department == resource.department AND time is business hours."

**16. How do you prevent privilege escalation through parameter manipulation?**
*Expected Answer:* Never trust user-provided parameters for authorization decisions. Always validate authorization on the server based on the authenticated user's identity. Don't allow users to modify role, permission, or user ID parameters. Use server-side session data for authorization decisions.

**17. Explain the concept of separation of duties and how you would implement it.**
*Expected Answer:* Require multiple people to approve sensitive actions. One person shouldn't create users, approve access, and audit access. Implement approval workflows. Require different people to request, approve, and perform sensitive actions. Log all actions for audit.

**18. How would you implement authorization checks in a microservices architecture?**
*Expected Answer:* Implement centralized authorization service or use API gateway for authorization checks. Pass user identity (JWT or token) between services. Each service validates the token and checks authorization. Avoid duplicating authorization logic across services. Use consistent authorization policies.

**19. What is the difference between authentication and authorization in API design?**
*Expected Answer:* Authentication verifies the API client's identity (API key, OAuth token, certificate). Authorization determines what the authenticated client can do (which endpoints, which resources). Both are necessary. Implement authentication on all API endpoints and authorization checks for protected resources.

**20. How would you audit authorization decisions?**
*Expected Answer:* Log all authorization decisions, especially denials. Record who attempted to access what resources and whether access was granted. Use audit logs to detect unauthorized access attempts. Maintain immutable audit trails. Regularly review logs for suspicious patterns.

---

# Key Takeaways

## Core Concepts

**Authentication and authorization are distinct but complementary security controls.** Authentication establishes identity; authorization determines what an authenticated user can do. Both are essential. Compromising either allows attackers to gain unauthorized access or perform unauthorized actions.

**The three authentication factors—something you know, something you have, something you are—

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]

## Key Takeaways

**Authentication and authorization are distinct but complementary security controls.** Authentication establishes identity (who you are); authorization determines what an authenticated user can do (what you're allowed to access). Both are essential. Compromising either allows attackers to gain unauthorized access or perform unauthorized actions.

**The three authentication factors—something you know, something you have, something you are—each have distinct strengths and weaknesses.** Passwords are convenient but vulnerable to guessing and phishing. Hardware tokens are resistant to remote attacks but can be lost or stolen. Biometrics are difficult to forge but raise privacy concerns. Multi-factor authentication combines factors to increase security significantly.

**Implement multi-factor authentication for high-value accounts.** Require MFA for administrative accounts, accounts with access to sensitive data, and accounts that can modify security settings. Recommend authenticator apps (TOTP) or hardware keys over SMS, which is vulnerable to SIM swapping. For applications handling financial data or personal information, mandate MFA for all users.

**Use strong, slow password hashing algorithms designed for password storage.** Argon2, bcrypt, and scrypt are acceptable; MD5 and SHA-1 are not. Use cost factors that require 100-500ms to hash a password on current hardware. Never implement custom password hashing; use standard library functions or well-tested third-party libraries. Always validate passwords on the server, never on the client.

**Session management must balance security with usability.** Implement appropriate session timeouts (15 minutes to 1 hour for web applications). Regenerate session IDs after authentication to prevent session fixation. Invalidate sessions on logout. Protect session cookies with Secure, HttpOnly, and SameSite flags. For JWTs, always validate signatures, check expiration, and use HTTPS for transmission.

**Authorization checks must be implemented on the server and applied to every request.** Never rely on client-side authorization checks. Verify that the authenticated user is authorized to perform the requested action on the requested resource. Implement authorization checks centrally (middleware, decorators, or a dedicated service) to ensure consistency. Default to deny access; only grant when a specific permission exists.

**Implement the principle of least privilege and separation of duties.** Grant users only the minimum permissions required for their job functions. Require multiple people to approve sensitive actions. Regularly audit and revoke unnecessary permissions. Use role-based access control with well-defined roles that reflect job functions, or attribute-based access control for complex scenarios.

**Common authentication and authorization vulnerabilities are preventable with proper design and implementation.** Weak passwords, missing rate limiting, predictable tokens, missing authorization checks, and hardcoded credentials are among the most frequently exploited vulnerabilities. Implement the secure design patterns and testing approaches described in this chapter to prevent these vulnerabilities in your applications."
    },
    {
