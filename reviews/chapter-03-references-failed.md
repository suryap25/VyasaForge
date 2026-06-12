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

## Conceptual Foundation

OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on an HTTP service without exposing user credentials. It is fundamentally different from authentication—OAuth 2.0 answers the question "What is this application allowed to do?" rather than "Who is this user?"

### Core Concepts

**Resource Owner**: The user who owns the data or resources being protected. In a typical scenario, this is the end user granting permission to a third-party application.

**Client**: The application requesting access to the user's resources. This could be a web application, mobile app, or backend service. The client is identified by a client ID and authenticated using a client secret (in confidential client scenarios).

**Authorization Server**: The server that authenticates the resource owner and issues access tokens to the client. This server maintains the user's credentials and determines what permissions the client has requested.

**Resource Server**: The server hosting the protected resources. It validates access tokens and serves the protected data. In many implementations, the authorization server and resource server are the same entity, though they can be separate.

**Access Token**: A credential that represents the authorization grant. It contains scope information (what the client can do) and has a limited lifetime. Access tokens are typically opaque to the client but are validated by the resource server.

**Refresh Token**: A long-lived credential that allows the client to obtain a new access token without requiring the user to re-authenticate. Refresh tokens are sensitive and must be protected carefully.

**Scope**: A mechanism for limiting the access granted to a client. Scopes define what actions the client can perform on behalf of the user (e.g., "read:profile", "write:posts", "delete:account").

**Authorization Code**: A short-lived, single-use credential issued by the authorization server to the client after the user grants permission. The client exchanges this code for an access token.

### Why OAuth 2.0 Matters

Before OAuth 2.0, applications requesting access to user data typically asked for the user's password directly. This approach created significant security risks: users had to trust third-party applications with their credentials, password changes would break integrations, and there was no way to revoke access without changing the password.

OAuth 2.0 solves these problems by introducing a delegation mechanism. Users authenticate directly with the authorization server (the service they trust), and the authorization server issues a token to the client application. The user never shares their password with the client, and access can be revoked independently of password changes.

## Architecture Perspective

### OAuth 2.0 Grant Types and Their Use Cases

OAuth 2.0 defines several grant types, each suited to different application architectures and security contexts.

#### Authorization Code Flow

The Authorization Code flow is the most common and secure flow for traditional web applications. It involves four main steps:

1. **User Initiates Login**: The user clicks "Login with [Provider]" on the client application.

2. **Redirect to Authorization Server**: The client redirects the user to the authorization server with parameters including the client ID, requested scopes, and a redirect URI.

3. **User Authenticates and Consents**: The user authenticates with the authorization server and grants permission for the requested scopes.

4. **Authorization Code Issued**: The authorization server redirects the user back to the client's redirect URI with an authorization code.

5. **Backend Token Exchange**: The client's backend server exchanges the authorization code for an access token by making a direct request to the authorization server, authenticating with its client secret.

6. **Access Token Issued**: The authorization server validates the authorization code and client secret, then issues an access token (and optionally a refresh token).

7. **Resource Access**: The client uses the access token to request protected resources from the resource server.

**Why this flow is secure**: The authorization code is single-use and short-lived. The client secret is never exposed to the browser or user agent. The access token is obtained through a backend-to-backend channel, reducing exposure.

#### Authorization Code Flow with PKCE

PKCE (Proof Key for Code Exchange) is an extension to the Authorization Code flow designed for public clients (applications that cannot securely store a client secret), such as single-page applications (SPAs) and mobile applications.

In PKCE:

1. The client generates a random string called a `code_verifier`.
2. The client creates a `code_challenge` by hashing the code verifier.
3. The client sends the code challenge to the authorization server during the initial authorization request.
4. After receiving the authorization code, the client sends the code verifier along with the code when exchanging for an access token.
5. The authorization server verifies that the code verifier matches the code challenge, ensuring the same client that initiated the flow is completing it.

PKCE prevents authorization code interception attacks where an attacker could capture the authorization code and exchange it for a token without the original client's involvement.

#### Implicit Flow (Deprecated)

The Implicit flow was historically used for browser-based applications. It skipped the authorization code exchange step and directly issued an access token to the client in the browser. This flow is now deprecated because it exposes the access token in the URL and browser history, increasing the risk of token theft.

**Current guidance**: Do not use the Implicit flow for new implementations. Use Authorization Code with PKCE instead.

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

This flow is appropriate only when both parties are trusted entities under the same organizational control or have a strong business relationship.

#### Resource Owner Password Credentials Flow (Deprecated)

This flow allows the client to collect the user's username and password directly and exchange them for an access token. It is deprecated because it requires users to share their credentials with the client application, defeating the primary security benefit of OAuth 2.0.

**Current guidance**: Do not use this flow for new implementations. Use Authorization Code with PKCE instead.

### Token Lifecycle and Management

**Access Token Lifetime**: Access tokens should have a short lifetime (typically 15 minutes to 1 hour). Short-lived tokens limit the window of exposure if a token is compromised.

**Refresh Token Lifetime**: Refresh tokens can have longer lifetimes (days, weeks, or months) but should be rotated regularly. Some implementations issue new refresh tokens with each refresh operation, invalidating the old one.

**Token Revocation**: Authorization servers should support token revocation endpoints that allow clients or users to explicitly invalidate tokens before they expire naturally.

**Token Storage**: Access tokens should be stored securely. In web applications, they should be stored in memory or in secure, HTTP-only cookies. In mobile applications, they should be stored in secure storage mechanisms provided by the operating system.

## AppSec Lens

### Common OAuth 2.0 Vulnerabilities

#### Authorization Code Interception

**Vulnerability**: An attacker intercepts the authorization code returned to the client's redirect URI and uses it to obtain an access token.

**Attack Scenario**: A user clicks a malicious link that initiates an OAuth 2.0 flow with a legitimate authorization server but redirects to an attacker-controlled redirect URI. The attacker captures the authorization code and exchanges it for a token.

**Mitigation**: 
- Use PKCE for all public clients
- Validate redirect URIs strictly (exact match, not substring matching)
- Use short-lived authorization codes (60 seconds or less)
- Implement state parameter validation (discussed below)

#### State Parameter Bypass

**Vulnerability**: The client fails to validate the `state` parameter, allowing Cross-Site Request Forgery (CSRF) attacks.

**Attack Scenario**: An attacker tricks a user into clicking a link that initiates an OAuth 2.0 flow. The authorization server redirects back to the client with an authorization code. The attacker's browser receives the code and can exchange it for a token, potentially gaining access to the user's account.

**Mitigation**:
- Generate a cryptographically random state parameter for each authorization request
- Store the state parameter in a session or secure cookie
- Validate that the state parameter returned by the authorization server matches the stored value
- Reject requests with missing or invalid state parameters

#### Token Theft and Exposure

**Vulnerability**: Access tokens are exposed through insecure storage, logging, or transmission.

**Attack Scenarios**:
- Tokens stored in browser local storage are accessible to JavaScript, including malicious scripts injected through XSS vulnerabilities
- Tokens logged in application logs or error messages are exposed to anyone with log access
- Tokens transmitted over unencrypted HTTP connections are intercepted by network attackers
- Tokens included in URLs are exposed in browser history and server logs

**Mitigation**:
- Store tokens in memory or secure, HTTP-only cookies
- Never log tokens or include them in error messages
- Always use HTTPS for all OAuth 2.0 communications
- Implement Content Security Policy (CSP) to prevent XSS attacks
- Use short-lived access tokens with refresh token rotation

#### Redirect URI Validation Bypass

**Vulnerability**: The authorization server does not properly validate redirect URIs, allowing attackers to redirect users to malicious sites.

**Attack Scenario**: An attacker registers a client application with a redirect URI like `https://attacker.example.com/callback`. When a user initiates login through the attacker's application, the authorization server redirectes to the attacker's site with the authorization code. The attacker can then exchange the code for a token or use it to impersonate the user.

**Mitigation**:
- Maintain a whitelist of allowed redirect URIs for each client
- Perform exact string matching on redirect URIs (not substring or pattern matching)
- Reject redirect URIs with user-controlled components
- Use HTTPS for all redirect URIs
- Regularly audit registered redirect URIs

#### Scope Creep and Over-Privileged Tokens

**Vulnerability**: Clients request excessive scopes, and users grant permissions without understanding the implications.

**Attack Scenario**: A photo-sharing application requests scopes to read the user's email, contacts, and location data, even though these are not necessary for the application's core functionality. If the application is compromised, the attacker gains access to all these data categories.

**Mitigation**:
- Request only the minimum scopes necessary for functionality
- Clearly communicate to users what data the application will access
- Implement incremental authorization, requesting additional scopes only when needed
- Regularly audit and remove unused scopes
- Implement scope validation on the authorization server to reject requests for excessive scopes

#### Refresh Token Compromise

**Vulnerability**: Refresh tokens are stolen or exposed, allowing attackers to obtain new access tokens indefinitely.

**Attack Scenario**: A mobile application stores a refresh token in insecure storage. An attacker gains access to the device and extracts the refresh token. The attacker can then use the token to obtain new access tokens and impersonate the user.

**Mitigation**:
- Store refresh tokens in secure storage (encrypted, protected by OS-level mechanisms)
- Implement refresh token rotation: issue a new refresh token with each refresh operation and invalidate the old one
- Implement token binding to tie tokens to specific clients or devices
- Monitor for unusual refresh token usage patterns
- Implement short refresh token lifetimes with periodic re-authentication

#### Insecure Client Authentication

**Vulnerability**: Clients are not properly authenticated when exchanging authorization codes or refresh tokens for access tokens.

**Attack Scenario**: A public client (SPA or mobile app) is registered without a client secret. An attacker can exchange a captured authorization code for an access token by simply providing the client ID.

**Mitigation**:
- Use PKCE for all public clients instead of relying on client secrets
- For confidential clients, use strong client authentication (mutual TLS, client assertions)
- Implement rate limiting on token endpoints to detect brute force attacks
- Monitor for unusual token exchange patterns

### OAuth 2.0 and Third-Party Risk

When integrating with third-party OAuth 2.0 providers, consider