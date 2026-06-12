# Chapter 3: OAuth 2.0 Protocol and Flows

## Learning Objectives

After completing this chapter, you will be able to:

- Explain the core components and actors in OAuth 2.0 authorization flows
- Distinguish between different OAuth 2.0 grant types and their appropriate use cases
- Identify common security vulnerabilities in OAuth 2.0 implementations
- Design and review OAuth 2.0 implementations from an application security perspective
- Conduct security assessments of OAuth 2.0 integrations and custom implementations
- Implement OAuth 2.0 flows securely in web and mobile applications
- Recognize and mitigate authorization bypass and token theft attacks
- Understand the operational and detection strategies for OAuth 2.0 security incidents

## Conceptual Foundation

OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on an HTTP service without exposing user credentials. It is fundamentally different from authentication—OAuth 2.0 answers the question "What is this application allowed to do?" rather than "Who is this user?"

This distinction is critical from an AppSec perspective. OAuth 2.0 is a *delegation* protocol, not an *authentication* protocol. Many security incidents stem from treating OAuth 2.0 as if it provides authentication guarantees or from conflating token possession with identity verification.

### Core Concepts

**Resource Owner**: The user who owns the data or resources being protected. In a typical scenario, this is the end user granting permission to a third-party application. The resource owner is the party whose trust and consent are essential to the security model.

**Client**: The application requesting access to the user's resources. This could be a web application, mobile app, or backend service. The client is identified by a client ID and authenticated using a client secret (in confidential client scenarios). Clients can be public (unable to securely store secrets, such as SPAs and mobile apps) or confidential (capable of securely storing secrets, such as backend services).

**Authorization Server**: The server that authenticates the resource owner and issues access tokens to the client. This server maintains the user's credentials and determines what permissions the client has requested. The authorization server is a critical trust anchor and must be treated as such in security architecture.

**Resource Server**: The server hosting the protected resources. It validates access tokens and serves the protected data. In many implementations, the authorization server and resource server are the same entity, though they can be separate. The resource server is responsible for enforcing authorization decisions based on token claims and scopes.

**Access Token**: A credential that represents the authorization grant. It contains scope information (what the client can do) and has a limited lifetime. Access tokens are typically opaque to the client but are validated by the resource server. Access tokens may be JWTs (self-contained, verifiable) or opaque references (validated via introspection). The token format has significant security implications for token validation and revocation.

**Refresh Token**: A long-lived credential that allows the client to obtain a new access token without requiring the user to re-authenticate. Refresh tokens are sensitive and must be protected carefully. Refresh token compromise is particularly dangerous because it provides persistent, offline access to user resources.

**Scope**: A mechanism for limiting the access granted to a client. Scopes define what actions the client can perform on behalf of the user (e.g., "read:profile", "write:posts", "delete:account"). Scope design is a critical security control; poorly designed scopes can lead to over-privileged tokens and excessive data exposure.

**Authorization Code**: A short-lived, single-use credential issued by the authorization server to the client after the user grants permission. The client exchanges this code for an access token. The authorization code is the foundation of the Authorization Code flow's security; its single-use nature and short lifetime are essential protections.

### Why OAuth 2.0 Matters

Before OAuth 2.0, applications requesting access to user data typically asked for the user's password directly. This approach created significant security risks: users had to trust third-party applications with their credentials, password changes would break integrations, and there was no way to revoke access without changing the password. Additionally, users had no visibility into what data third-party applications could access, and there was no mechanism to grant limited, scoped access.

OAuth 2.0 solves these problems by introducing a delegation mechanism. Users authenticate directly with the authorization server (the service they trust), and the authorization server issues a token to the client application. The user never shares their password with the client, and access can be revoked independently of password changes. Users can see what permissions they have granted and revoke them at any time.

From an AppSec perspective, OAuth 2.0 also enables better security monitoring and incident response. Authorization servers can log all token issuance and usage, detect anomalous patterns, and revoke tokens in response to security incidents. This centralized visibility is not possible with password-based access.

## Architecture Perspective

### OAuth 2.0 Grant Types and Their Use Cases

OAuth 2.0 defines several grant types, each suited to different application architectures and security contexts. Choosing the correct grant type is fundamental to secure OAuth 2.0 implementation.

#### Authorization Code Flow

The Authorization Code flow is the most common and secure flow for traditional web applications. It involves the following steps:

1. **User Initiates Login**: The user clicks "Login with [Provider]" on the client application.

2. **Redirect to Authorization Server**: The client redirects the user to the authorization server with parameters including the client ID, requested scopes, and a redirect URI.

3. **User Authenticates and Consents**: The user authenticates with the authorization server and grants permission for the requested scopes. The authorization server may display a consent screen showing what data and permissions the client is requesting.

4. **Authorization Code Issued**: The authorization server redirects the user back to the client's redirect URI with an authorization code.

5. **Backend Token Exchange**: The client's backend server exchanges the authorization code for an access token by making a direct request to the authorization server, authenticating with its client secret. This backend-to-backend communication is not visible to the user's browser.

6. **Access Token Issued**: The authorization server validates the authorization code and client secret, then issues an access token (and optionally a refresh token).

7. **Resource Access**: The client uses the access token to request protected resources from the resource server.

**Why this flow is secure**: The authorization code is single-use and short-lived (typically 10 seconds to 10 minutes). The client secret is never exposed to the browser or user agent. The access token is obtained through a backend-to-backend channel, reducing exposure to browser-based attacks. The flow provides clear separation between the user-facing authorization step and the backend token exchange.

**Operational considerations**: The Authorization Code flow requires the client to maintain backend infrastructure capable of securely storing the client secret and making authenticated requests to the authorization server. For simple applications or those without backend infrastructure, this flow may be impractical.

#### Authorization Code Flow with PKCE

PKCE (Proof Key for Code Exchange, pronounced "pixy") is an extension to the Authorization Code flow designed for public clients (applications that cannot securely store a client secret), such as single-page applications (SPAs) and mobile applications.

In PKCE:

1. The client generates a random string called a `code_verifier` (43-128 characters of unreserved characters).
2. The client creates a `code_challenge` by hashing the code verifier using SHA-256 (S256 method) or using the verifier directly (plain method, not recommended).
3. The client sends the code challenge to the authorization server during the initial authorization request.
4. After receiving the authorization code, the client sends the code verifier along with the code when exchanging for an access token.
5. The authorization server verifies that the code verifier matches the code challenge, ensuring the same client that initiated the flow is completing it.

PKCE prevents authorization code interception attacks where an attacker could capture the authorization code and exchange it for a token without the original client's involvement. Even if an attacker intercepts the authorization code, they cannot exchange it without the code verifier, which is never transmitted to the authorization server in the initial request.

**PKCE implementation details**: The S256 method (SHA-256 hash) is strongly recommended over the plain method. The plain method provides no protection if the code verifier is intercepted. The code verifier should be generated using a cryptographically secure random number generator and should be at least 43 characters long.

**Operational considerations**: PKCE adds complexity to the OAuth 2.0 flow but is essential for public clients. Authorization servers should require PKCE for all public clients and should reject authorization requests from public clients that do not include a code challenge.

#### Implicit Flow (Deprecated)

The Implicit flow was historically used for browser-based applications. It skipped the authorization code exchange step and directly issued an access token to the client in the browser. The flow worked as follows:

1. User initiates login on the client application
2. Client redirects to authorization server
3. User authenticates and grants permission
4. Authorization server redirects back to client with access token in URL fragment

This flow is now deprecated because it exposes the access token in the URL and browser history, increasing the risk of token theft. The URL fragment is visible in browser history, referrer headers, and server logs. Additionally, the Implicit flow does not provide a mechanism to refresh tokens, requiring users to re-authenticate frequently.

**Current guidance**: Do not use the Implicit flow for new implementations. Use Authorization Code with PKCE instead. If you encounter the Implicit flow in legacy applications, prioritize migration to Authorization Code with PKCE.

**Why this matters for AppSec**: The Implicit flow represents a fundamental misunderstanding of browser security. Tokens should never be exposed in URLs or visible to JavaScript. The deprecation of the Implicit flow reflects the industry's recognition of these risks.

#### Client Credentials Flow

The Client Credentials flow is used for server-to-server communication where there is no resource owner (user) involved. The client authenticates directly with the authorization server using its credentials and receives an access token.

Example use case: A backend service needs to call another backend service's API.

```
POST /token HTTP/1.1
Host: authorization-server.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=s6BhdRkqt3
&client_secret=gX1fBat3bV
&scope=read:data
```

The authorization server validates the client credentials and issues an access token. The token represents the client's identity and permissions, not a user's identity.

**Security considerations**: The Client Credentials flow is appropriate only when both parties are trusted entities under the same organizational control or have a strong business relationship. The client secret must be protected with the same rigor as a password. If the client secret is compromised, the attacker gains full access to the resources protected by that token.

**Operational concerns**: Client Credentials tokens should have short lifetimes and should be rotated regularly. Monitor for unusual token usage patterns, such as tokens being used from unexpected locations or at unusual times. Implement rate limiting on the token endpoint to detect brute force attacks.

#### Resource Owner Password Credentials Flow (Deprecated)

This flow allows the client to collect the user's username and password directly and exchange them for an access token. It is deprecated because it requires users to share their credentials with the client application, defeating the primary security benefit of OAuth 2.0.

In this flow:

1. User enters username and password into the client application
2. Client sends credentials to authorization server
3. Authorization server validates credentials and issues access token

**Why this is problematic**: Users must trust the client application with their credentials. There is no way to revoke access without changing the password. The client can use the credentials to access resources beyond the scope of the current authorization. Password changes break integrations. There is no user consent mechanism; the user cannot see what permissions the client is requesting.

**Current guidance**: Do not use this flow for new implementations. Use Authorization Code with PKCE instead. If you encounter this flow in legacy applications, prioritize migration to Authorization Code with PKCE.

**Exception**: This flow may be acceptable for first-party applications (applications developed and operated by the same organization that operates the authorization server) in specific scenarios, such as mobile applications where the authorization server is operated by the same organization. Even in these cases, Authorization Code with PKCE is preferred.

### Token Lifecycle and Management

**Access Token Lifetime**: Access tokens should have a short lifetime (typically 15 minutes to 1 hour). Short-lived tokens limit the window of exposure if a token is compromised. However, very short lifetimes (less than 5 minutes) can create performance issues and increase the frequency of token refresh operations.

**Operational guidance**: Choose access token lifetimes based on the sensitivity of the resources being protected and the risk tolerance of the organization. For highly sensitive resources (e.g., financial data, personal health information), use shorter lifetimes (15-30 minutes). For less sensitive resources, longer lifetimes (1 hour) may be acceptable.

**Refresh Token Lifetime**: Refresh tokens can have longer lifetimes (days, weeks, or months) but should be rotated regularly. Some implementations issue new refresh tokens with each refresh operation, invalidating the old one. This approach, called "refresh token rotation," reduces the window of exposure if a refresh token is compromised.

**Operational guidance**: Implement refresh token rotation for high-security applications. For lower-security applications, refresh tokens with fixed lifetimes may be acceptable. Monitor refresh token usage for anomalies, such as tokens being used from unexpected locations or at unusual times.

**Token Revocation**: Authorization servers should support token revocation endpoints that allow clients or users to explicitly invalidate tokens before they expire naturally. This is essential for security incident response and for allowing users to revoke application access.

```
POST /revoke HTTP/1.1
Host: authorization-server.example.com
Content-Type: application/x-www-form-urlencoded

token=access_token_or_refresh_token
&client_id=client_id
&client_secret=client_secret
```

**Operational guidance**: Implement token revocation endpoints and ensure that revoked tokens are immediately invalidated. For opaque tokens, this requires a revocation list or database lookup. For JWT tokens, revocation is more challenging and typically requires a blacklist or token introspection endpoint.

**Token Storage**: Access tokens should be stored securely. In web applications, they should be stored in memory or in secure, HTTP-only cookies. In mobile applications, they should be stored in secure storage mechanisms provided by the operating system.

**Web applications**: Store tokens in HTTP-only, Secure cookies with SameSite attribute set to Strict. This prevents JavaScript from accessing the token (protecting against XSS) and prevents the token from being sent in cross-site requests (protecting against CSRF).

**Mobile applications**: Store tokens in platform-specific secure storage:
- iOS: Keychain
- Android: Keystore or EncryptedSharedPreferences

**Never** store tokens in browser local storage or session storage, as these are accessible to JavaScript and vulnerable to XSS attacks.

**Token Introspection**: For opaque tokens, authorization servers should provide an introspection endpoint that allows resource servers to validate tokens and retrieve token claims.

```
POST /introspect HTTP/1.1
Host: authorization-server.example.com
Content-Type: application/x-www-form-urlencoded

token=access_token
&client_id=resource_server_id
&client_secret=resource_server_secret
```

**Operational guidance**: Implement token introspection endpoints for opaque tokens. Cache introspection results to reduce latency and load on the authorization server. Implement rate limiting on introspection endpoints to prevent abuse.

## AppSec Lens

### Common OAuth 2.0 Vulnerabilities

#### Authorization Code Interception

**Vulnerability**: An attacker intercepts the authorization code returned to the client's redirect URI and uses it to obtain an access token.

**Attack Scenario**: A user clicks a malicious link that initiates an OAuth 2.0 flow with a legitimate authorization server but redirects to an attacker-controlled redirect URI. The attacker captures the authorization code and exchanges it for a token. Alternatively, an attacker performs a man-in-the-middle attack on an unencrypted connection and intercepts the authorization code.

**Root causes**:
- Lack of PKCE implementation for public clients
- Weak redirect URI validation
- Use of HTTP instead of HTTPS
- Authorization codes with long lifetimes or reusable codes

**Mitigation**: 
- Use PKCE for all public clients
- Validate redirect URIs strictly (exact match, not substring matching)
- Use short-lived authorization codes (60 seconds or less)
- Implement state parameter validation (discussed below)
- Require HTTPS for all OAuth 2.0 communications
- Implement single-use enforcement for authorization codes

**Detection**:
- Monitor for multiple token exchanges using the same authorization code
- Monitor for authorization codes being exchanged from unexpected IP addresses or geographic locations
- Monitor for authorization codes being exchanged shortly after issuance (indicating interception)
- Implement logging of all authorization code exchanges with client ID, timestamp, and IP address

#### State Parameter Bypass

**Vulnerability**: The client fails to validate the `state` parameter, allowing Cross-Site Request Forgery (CSRF) attacks.

**Attack Scenario**: An attacker tricks a user into clicking a link that initiates an OAuth 2.0 flow. The authorization server redirects back to the client with an authorization code. The attacker's browser receives the code and can exchange it for a token, potentially gaining access to the user's account. The attacker can also use the authorization code to log in as the user on the client application.

**Root causes**:
- State parameter not generated or validated
- State parameter stored in insecure location (e.g., URL parameter)
- State parameter validation logic flawed or missing
- State parameter reused across multiple flows

**Mitigation**:
- Generate a cryptographically random state parameter for each authorization request
- Store the state parameter in a session or secure cookie
- Validate that the state parameter returned by the authorization server matches the stored value
- Reject requests with missing or invalid state parameters
- Implement SameSite cookie attribute to prevent CSRF

**Detection**:
- Monitor for authorization callbacks with missing or invalid state parameters
- Monitor for state parameter reuse across multiple flows
- Implement logging of all authorization callbacks with state parameter validation results

**Operational concern**: State parameter validation is a simple but critical control. Many implementations fail to implement it correctly, often due to misunderstanding of CSRF risks in OAuth 2.0 flows.

#### Token Theft and Exposure

**Vulnerability**: Access tokens are exposed through insecure storage, logging, or transmission.

**Attack Scenarios**:
- Tokens stored in browser local storage are accessible to JavaScript, including malicious scripts injected through XSS vulnerabilities
- Tokens logged in application logs or error messages are exposed to anyone with log access
- Tokens transmitted over unencrypted HTTP connections are intercepted by network attackers
- Tokens included in URLs are exposed in browser history and server logs
- Tokens exposed in error messages or stack traces
- Tokens exposed in debug output or verbose logging

**Root causes**:
- Tokens stored in insecure locations (localStorage, sessionStorage)
- Tokens logged or included in error messages
- Use of HTTP instead of HTTPS
- Tokens included in URLs or query parameters
- Overly verbose logging or debug output

**Mitigation**:
- Store tokens in memory or secure, HTTP-only cookies
- Never log tokens or include them in error messages
- Always use HTTPS for all OAuth 2.0 communications
- Implement Content Security Policy (CSP) to prevent XSS attacks
- Use short-lived access tokens with refresh token rotation
- Implement token masking in logs (e.g., log only first and last 4 characters)
- Sanitize error messages to avoid exposing tokens

**Detection**:
- Scan logs for token patterns (e.g., "Bearer " followed by base64 or JWT)
- Monitor for tokens being transmitted over HTTP
- Monitor for tokens being included in URLs
- Implement automated scanning of error messages and stack traces for tokens

**Operational concern**: Token exposure is a common finding in security assessments. Developers often underestimate the sensitivity of tokens and fail to implement proper storage and logging controls.

#### Redirect URI Validation Bypass

**Vulnerability**: The authorization server does not properly validate redirect URIs, allowing attackers to redirect users to malicious sites.

**Attack Scenario**: An attacker registers a client application with a redirect URI like `https://attacker.example.com/callback`. When a user initiates login through the attacker's application, the authorization server redirects to the attacker's site with the authorization code. The attacker can then exchange the code for a token or use it to impersonate the user.

Alternatively, an attacker exploits weak redirect URI validation by registering a redirect URI like `https://legitimate.example.com.attacker.example.com` or `https://legitimate.example.com@attacker.example.com`. If the authorization server performs substring matching instead of exact matching, the attacker's redirect URI may be accepted.

**Root causes**:
- Redirect URIs not validated against whitelist
- Substring matching instead of exact matching
- Redirect URIs with user-controlled components
- Redirect URIs accepting HTTP instead of HTTPS
- Redirect URIs accepting wildcard or pattern-based matching

**Mitigation**:
- Maintain a whitelist of allowed redirect URIs for each client
- Perform exact string matching on redirect URIs (not substring or pattern matching)
- Reject redirect URIs with user-controlled components
- Use HTTPS for all redirect URIs