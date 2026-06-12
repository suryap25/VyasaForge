---
chapter: 8
stage: final
source: drafts
generated_by: appsec-handbook-agent
---

# Chapter 08: Mobile Application Authentication Patterns

## Learning Objectives

After completing this chapter, you will be able to:

- Understand the unique authentication challenges and constraints of mobile applications compared to web applications
- Design and implement secure authentication flows for iOS, Android, and cross-platform mobile applications
- Evaluate token-based authentication mechanisms including OAuth 2.0, OpenID Connect, and JWT in mobile contexts
- Implement secure credential storage and session management on mobile devices
- Assess mobile authentication implementations for common vulnerabilities and misconfigurations
- Apply secure design patterns that account for mobile-specific threats including device compromise, network interception, and app tampering
- Conduct security reviews and penetration testing of mobile authentication systems
- Make informed decisions about certificate pinning, biometric authentication, and multi-factor authentication in mobile applications

## Conceptual Foundation

Mobile application authentication differs fundamentally from web application authentication due to the unique constraints and capabilities of mobile devices. Unlike web browsers, which operate in a relatively controlled environment with built-in security mechanisms, mobile applications run on devices that users control completely, can be rooted or jailbroken, and may connect through untrusted networks.

**Core Authentication Principles for Mobile**

Mobile authentication must balance three competing concerns: security, user experience, and device resource constraints. Users expect seamless authentication experiences without repeated credential entry, yet security requires strong verification mechanisms. Mobile devices have limited processing power, battery life, and network connectivity compared to desktop computers, necessitating efficient authentication protocols.

The fundamental goal of mobile authentication remains unchanged from web authentication: verify that the user claiming to be a particular identity is actually that user, and establish a secure session for subsequent requests. However, the mechanisms and considerations differ substantially.

**Token-Based Authentication**

Mobile applications predominantly use token-based authentication rather than session cookies. When a user authenticates with credentials, the server issues a token—typically a JSON Web Token (JWT) or opaque token—that the client stores and includes with subsequent requests. This approach works better for mobile because:

- Tokens can be stored securely on the device using platform-provided secure storage
- Tokens work across multiple network connections and device sleep cycles
- Tokens enable offline-first architectures where some operations continue without network connectivity
- Tokens reduce server-side session state requirements, supporting scalable backend architectures

**OAuth 2.0 and OpenID Connect**

OAuth 2.0 provides a framework for delegated authorization, allowing users to authenticate through third-party identity providers (Google, Apple, Microsoft, etc.) without sharing passwords with the application. OpenID Connect extends OAuth 2.0 with an identity layer, providing standardized claims about the authenticated user.

For mobile applications, OAuth 2.0 with the Authorization Code flow (using Proof Key for Public Clients, or PKCE) has become the industry standard. This flow prevents authorization code interception attacks specific to mobile platforms where applications cannot securely store client secrets.

**Biometric Authentication**

Modern mobile devices include fingerprint sensors, face recognition, and other biometric capabilities. Biometric authentication provides strong user experience—users authenticate with a single touch or glance—while maintaining security through hardware-backed cryptographic keys. However, biometric authentication typically authenticates the user to the device, not to the application. Applications must still establish authenticated sessions after biometric verification.

## Architecture Perspective

**Mobile Authentication Architecture Layers**

A complete mobile authentication system comprises multiple layers:

1. **Device Layer**: Hardware security modules, secure enclaves, and biometric sensors
2. **OS Layer**: Keychain (iOS), Keystore (Android), and secure storage mechanisms
3. **Application Layer**: Authentication logic, token management, and session handling
4. **Network Layer**: TLS/SSL, certificate pinning, and secure communication
5. **Backend Layer**: Identity provider, token issuance, validation, and revocation

Each layer must be secured independently and in concert with others.

**Token Lifecycle Architecture**

Mobile applications must manage multiple token types with different lifespans:

- **Access Tokens**: Short-lived tokens (minutes to hours) used to authenticate API requests. Short lifespans limit exposure if tokens are compromised.
- **Refresh Tokens**: Long-lived tokens (days to months) used to obtain new access tokens without requiring user re-authentication. Refresh tokens must be stored securely and rotated regularly.
- **ID Tokens**: OpenID Connect tokens containing identity claims about the authenticated user. These should not be used for API authorization.

A typical flow: User authenticates → Server issues access token and refresh token → Application uses access token for API requests → When access token expires, application uses refresh token to obtain a new access token → If refresh token expires, user must re-authenticate.

**Multi-Device Authentication Architecture**

Users often own multiple mobile devices. Authentication architecture must handle:

- **Device Registration**: Tracking which devices are authorized for a user account
- **Device Identification**: Distinguishing between devices to detect unauthorized access
- **Cross-Device Revocation**: Invalidating sessions on compromised devices while maintaining sessions on trusted devices
- **Device-Specific Tokens**: Issuing tokens bound to specific devices to prevent token reuse across devices

**Example Architecture: OAuth 2.0 PKCE Flow for Mobile**

```
Mobile App                          Authorization Server              Resource Server
    |                                      |                                |
    |--1. Initiate Login (PKCE)----------->|                                |
    |   (code_challenge, state)            |                                |
    |                                      |                                |
    |<--2. Redirect to Login UI------------|                                |
    |   (authorization_code, state)        |                                |
    |                                      |                                |
    |--3. Exchange Code for Token--------->|                                |
    |   (code, code_verifier, client_id)   |                                |
    |                                      |                                |
    |<--4. Issue Tokens-------------------|                                |
    |   (access_token, refresh_token)      |                                |
    |                                      |                                |
    |--5. API Request with Access Token----|------------------------------>|
    |                                      |                                |
    |                                      |<--6. Return Protected Resource-|
    |<--7. Return Data to User-------------|                                |
    |                                      |                                |
    |--8. Refresh Token Request----------->|                                |
    |   (refresh_token, client_id)         |                                |
    |                                      |                                |
    |<--9. New Access Token----------------|                                |
```

This architecture provides security through:
- PKCE prevents authorization code interception attacks
- Short-lived access tokens limit exposure window
- Refresh tokens enable seamless user experience without repeated authentication
- Tokens stored in secure device storage

## AppSec Lens

**Mobile-Specific Authentication Threats**

Mobile applications face authentication threats that web applications do not:

**Device Compromise**: If a user's device is rooted (Android) or jailbroken (iOS), attackers can:
- Extract tokens from secure storage
- Intercept application traffic despite TLS
- Modify application behavior at runtime
- Inject malicious code into the application process

**Insecure Network Connections**: Mobile devices frequently connect through untrusted networks (public WiFi, cellular networks with weak encryption). Even with TLS, attackers can:
- Perform man-in-the-middle attacks if certificate validation is weak
- Intercept tokens if certificate pinning is not implemented
- Perform DNS hijacking to redirect authentication requests

**Token Exposure**: Mobile applications store tokens on devices. Attackers can:
- Extract tokens through physical device access
- Obtain tokens through malware or compromised applications
- Intercept tokens during transmission if network security is weak
- Replay tokens if they lack binding to the device or user session

**Reverse Engineering**: Mobile applications can be decompiled and analyzed. Attackers can:
- Extract hardcoded credentials or API keys
- Understand authentication logic and identify bypasses
- Modify application behavior to skip authentication
- Identify backend API endpoints and parameters

**Credential Phishing**: Mobile users are particularly vulnerable to phishing attacks. Attackers can:
- Create fake login screens that capture credentials
- Intercept OAuth flows through malicious applications
- Perform social engineering to trick users into revealing credentials

**AppSec Assessment Focus Areas**

When assessing mobile authentication security:

1. **Token Storage**: Verify tokens are stored in platform-provided secure storage (Keychain on iOS, Keystore on Android), not in SharedPreferences, UserDefaults, or application-accessible files.

2. **Token Transmission**: Confirm all authentication requests use TLS 1.2 or higher with proper certificate validation. Verify certificate pinning is implemented for critical authentication endpoints.

3. **Token Validation**: Ensure tokens are validated on the backend for signature, expiration, and binding to the requesting device or user session.

4. **Credential Handling**: Verify credentials are never stored on the device after authentication. Credentials should be used only during the authentication request and then discarded.

5. **Session Management**: Confirm sessions can be revoked server-side and that revocation is enforced on the client.

6. **Biometric Integration**: If biometric authentication is implemented, verify it authenticates the user to the device, not directly to the application, and that a proper authenticated session is established afterward.

7. **Logout Implementation**: Verify logout properly clears tokens from secure storage and invalidates sessions server-side.

## Developer Lens

**Implementing Secure Mobile Authentication**

**Step 1: Choose an Authentication Pattern**

For most mobile applications, OAuth 2.0 with PKCE is the recommended pattern:

```swift
// iOS Example: OAuth 2.0 PKCE Flow
import AuthenticationServices

class OAuthManager {
    let clientID = "your-client-id"
    let redirectURI = "com.yourapp://oauth-callback"
    let authorizationEndpoint = URL(string: "https://auth.example.com/authorize")!
    let tokenEndpoint = URL(string: "https://auth.example.com/token")!
    
    func initiateLogin() {
        // Generate PKCE parameters
        let codeVerifier = generateCodeVerifier()
        let codeChallenge = generateCodeChallenge(from: codeVerifier)
        let state = generateRandomState()
        
        // Store for later verification
        UserDefaults.standard.set(codeVerifier, forKey: "pkce_verifier")
        UserDefaults.standard.set(state, forKey: "oauth_state")
        
        // Build authorization URL
        var components = URLComponents(url: authorizationEndpoint, resolvingAgainstBaseURL: false)!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: clientID),
            URLQueryItem(name: "redirect_uri", value: redirectURI),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "scope", value: "openid profile email"),
            URLQueryItem(name: "code_challenge", value: codeChallenge),
            URLQueryItem(name: "code_challenge_method", value: "S256"),
            URLQueryItem(name: "state", value: state)
        ]
        
        // Open authorization endpoint
        if let authURL = components.url {
            UIApplication.shared.open(authURL)
        }
    }
    
    func handleCallback(url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
              let returnedState = components.queryItems?.first(where: { $0.name == "state" })?.value else {
            print("Invalid callback URL")
            return
        }
        
        // Verify state parameter
        let storedState = UserDefaults.standard.string(forKey: "oauth_state")
        guard returnedState == storedState else {
            print("State mismatch - possible CSRF attack")
            return
        }
        
        // Exchange code for token
        let codeVerifier = UserDefaults.standard.string(forKey: "pkce_verifier")!
        exchangeCodeForToken(code: code, codeVerifier: codeVerifier)
    }
    
    func exchangeCodeForToken(code: String, codeVerifier: String) {
        var request = URLRequest(url: tokenEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let body = "grant_type=authorization_code&code=\(code)&client_id=\(clientID)&redirect_uri=\(redirectURI)&code_verifier=\(codeVerifier)"
        request.httpBody = body.data(using: .utf8)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data else { return }
            
            do {
                let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
                self.storeTokensSecurely(tokenResponse)
            } catch {
                print("Token exchange failed: \(error)")
            }
        }.resume()
    }
    
    func storeTokensSecurely(_ tokenResponse: TokenResponse) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "access_token",
            kSecValueData as String: tokenResponse.accessToken.data(using: .utf8)!
        ]
        
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
        
        // Store refresh token separately
        let refreshQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "refresh_token",
            kSecValueData as String: tokenResponse.refreshToken.data(using: .utf8)!
        ]
        
        SecItemDelete(refreshQuery as CFDictionary)
        SecItemAdd(refreshQuery as CFDictionary, nil)
    }
    
    func generateCodeVerifier() -> String {
        var buffer = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, buffer.count, &buffer)
        return Data(buffer).base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
    
    func generateCodeChallenge(from verifier: String) -> String {
        let data = verifier.data(using: .utf8)!
        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { buffer in
            _ = CC_SHA256(buffer.baseAddress, CC_LONG(data.count), &digest)
        }
        return Data(digest).base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
    
    func generateRandomState() -> String {
        var buffer = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, buffer.count, &buffer)
        return Data(buffer).base64EncodedString()
    }
}

struct TokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
}
```

**Step 2: Implement Secure Token Storage**

Never store tokens in UserDefaults, SharedPreferences, or application-accessible files. Use platform-provided secure storage:

```swift
// iOS: Keychain Storage
class KeychainManager {
    static func storeToken(_ token: String, forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: token.data(using: .utf8)!,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    static func retrieveToken(forKey key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return token
    }
    
    static func deleteToken(forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}
```

```kotlin
// Android: EncryptedSharedPreferences
class TokenManager(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val encryptedPreferences = EncryptedSharedPreferences.create(
        context,
        "secret_shared_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun storeAccessToken(token: String) {
        encryptedPreferences.edit().putString("access_token", token).apply()
    }
    
    fun retrieveAccessToken(): String? {
        return encryptedPreferences.getString("access_token", null)
    }
    
    fun deleteAccessToken() {
        encryptedPreferences.edit().remove("access_token").apply()
    }
}
```

**Step 3: Implement Certificate Pinning**

Certificate pinning prevents man-in-the-middle attacks by validating that the server's certificate matches an expected certificate or public key:

```swift
// iOS: Certificate Pinning with URLSessionDelegate
class CertificatePinningDelegate: NSObject, URLSessionDelegate {
    let pinnedCertificates: [SecCertificate]
    
    init(certificateNames: [String]) {
        var certificates: [SecCertificate] = []
        
        for name in certificateNames {
            if let path = Bundle.main.path(forResource: name, ofType: "cer"),
               let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
               let certificate = SecCertificateCreateWithData(nil, data as CFData) {
                certificates.append(certificate)
            }
        }
        
        self.pinnedCertificates = certificates
    }
    
    func urlSession(_ session: URLSession,
                    didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        var secResult = SecTrustResultType.invalid
        let status = SecTrustEvaluate(serverTrust, &secResult)
        
        guard status == errSecSuccess else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        let certificateCount
```

## Pentest Lens

### Mobile Authentication Testing Methodology

Mobile authentication penetration testing requires a systematic approach that combines network interception, static analysis, dynamic runtime analysis, and device-level testing. Unlike web application testing where a proxy intercepts all traffic transparently, mobile testing must account for certificate pinning, encrypted local storage, and application-specific authentication mechanisms.

**Network-Level Testing**

Begin by establishing a testing environment where you can intercept mobile application traffic:

1. **Proxy Configuration**: Configure the mobile device to route traffic through a testing proxy (Burp Suite, Fiddler, mitmproxy). For iOS, this typically involves installing a custom CA certificate and configuring WiFi proxy settings. For Android, use system-wide proxy settings or install the proxy's CA certificate in the system certificate store.

2. **Certificate Pinning Bypass**: If the application implements certificate pinning, you must bypass it to intercept traffic:
   - **Frida-based Bypass**: Use Frida to hook certificate validation functions at runtime and force them to return success
   - **Xposed Framework (Android)**: Install modules that disable certificate pinning
   - **Objection**: Use the objection framework to disable pinning on iOS
   - **Repackaging**: Decompile the application, remove pinning code, recompile, and resign

3. **Traffic Analysis**: Once traffic is interceptable, analyze authentication flows:
   - Capture the complete OAuth 2.0 or token-based authentication flow
   - Verify PKCE implementation: confirm code_challenge and code_verifier are present and properly validated
   - Check state parameter validation to detect CSRF vulnerabilities
   - Analyze token structure (if JWT, decode and examine claims)
   - Verify tokens are transmitted only over TLS
   - Check for token leakage in logs, error messages, or referer headers

**Example Frida Script for Certificate Pinning Bypass (iOS)**

```javascript
// Bypass certificate pinning on iOS
if (ObjC.available) {
    var NSURLSessionConfiguration = ObjC.classes.NSURLSessionConfiguration;
    var original = NSURLSessionConfiguration['$waitsForConnectivity'];
    
    Interceptor.attach(original, {
        onEnter: function(args) {
            console.log("[*] Intercepted certificate validation");
        },
        onLeave: function(retval) {
            return retval;
        }
    });
    
    // Hook URLSession delegate methods
    var URLSessionDelegate = ObjC.classes.NSURLSessionDelegate;
    var URLAuthenticationChallenge = ObjC.classes.NSURLAuthenticationChallenge;
    
    Interceptor.attach(ObjC.classes.NSURLSessionDelegate['- URLSession:didReceiveChallenge:completionHandler:'].implementation, {
        onEnter: function(args) {
            console.log("[*] Certificate challenge intercepted - forcing acceptance");
            var challenge = new ObjC.Object(args[2]);
            var credential = ObjC.classes.NSURLCredential['credentialForTrust:'](challenge.$ownMembers().protectionSpace.serverTrust);
            args[4](0, credential); // 0 = NSURLSessionAuthChallengeUseCredential
        }
    });
}
```

**Static Analysis Testing**

Decompile the application and analyze authentication implementation:

1. **Credential Storage Analysis**:
   - Search for hardcoded API keys, client secrets, or credentials in the application binary
   - Check SharedPreferences files (Android) for stored tokens or credentials
   - Examine UserDefaults (iOS) for sensitive data
   - Look for credentials in application logs or debug output

2. **Token Handling Analysis**:
   - Verify tokens are stored in secure storage (Keychain/Keystore), not in accessible files
   - Check token expiration handling and refresh token implementation
   - Analyze token validation logic on the client side
   - Look for token leakage in error messages or logging

3. **OAuth Implementation Analysis**:
   - Verify PKCE is implemented (code_challenge and code_verifier present)
   - Check state parameter generation and validation
   - Analyze redirect URI validation
   - Look for hardcoded client secrets

**Example: Analyzing Android APK for Credential Storage**

```bash
### Decompile APK
apktool d application.apk

### Search for SharedPreferences usage
grep -r "SharedPreferences" application/smali/

### Search for hardcoded credentials
grep -r "password\|api_key\|secret" application/smali/ | head -20

### Check AndroidManifest for exported components
grep -i "exported\|intent-filter" application/AndroidManifest.xml

### Analyze strings for sensitive data
strings application/classes.dex | grep -i "token\|password\|secret"
```

**Dynamic Runtime Testing**

Use dynamic analysis tools to test authentication at runtime:

1. **Frida-based Testing**:
   - Hook authentication functions to observe parameters and return values
   - Intercept token storage operations to verify secure storage is used
   - Monitor network requests to verify TLS and certificate validation
   - Inspect memory for stored credentials or tokens

2. **Debugger-based Testing**:
   - Attach a debugger (lldb for iOS, Android Studio debugger for Android)
   - Set breakpoints in authentication code
   - Inspect variables containing tokens or credentials
   - Modify authentication logic at runtime to test validation

3. **Memory Analysis**:
   - Dump application memory while authenticated
   - Search for tokens, credentials, or sensitive data in memory
   - Verify tokens are cleared from memory after logout

**Example: Using Frida to Monitor Token Storage**

```javascript
// Monitor token storage on Android
Java.perform(function() {
    var SharedPreferences = Java.use("android.content.SharedPreferences");
    var Editor = Java.use("android.content.SharedPreferences$Editor");
    
    Editor.putString.overload('java.lang.String', 'java.lang.String').implementation = function(key, value) {
        if (key.includes("token") || key.includes("password")) {
            console.log("[!] Storing sensitive data in SharedPreferences:");
            console.log("    Key: " + key);
            console.log("    Value: " + value);
            console.log("    Stack trace: " + Java.use("java.lang.Exception").$new().printStackTrace());
        }
        return this.putString(key, value);
    };
});
```

**Device-Level Testing**

Test authentication on actual devices or emulators:

1. **Token Extraction**:
   - On rooted Android devices, access the Keystore database directly
   - On jailbroken iOS devices, access the Keychain database
   - Extract tokens and attempt to use them from other devices or applications

2. **Token Replay**:
   - Capture valid authentication tokens
   - Attempt to use tokens from different devices, networks, or applications
   - Test if tokens are bound to device identifiers or user sessions
   - Verify token expiration is enforced

3. **Session Hijacking**:
   - Intercept refresh token requests
   - Attempt to use captured refresh tokens to obtain new access tokens
   - Test if refresh tokens are rotated after use
   - Verify refresh token revocation is enforced

4. **Biometric Bypass**:
   - If biometric authentication is implemented, test if it can be bypassed
   - Attempt to use the application without biometric verification
   - Test if biometric authentication is properly bound to the user account
   - Verify that biometric authentication doesn't bypass server-side validation

**Testing OAuth 2.0 PKCE Implementation**

```bash
### Capture authorization request
### Look for: code_challenge, code_challenge_method, state

### Test PKCE bypass by:
### 1. Intercepting authorization code
### 2. Attempting to exchange code without code_verifier
### 3. Attempting to exchange code with invalid code_verifier
### 4. Attempting to exchange code with code_verifier from different client

### Example: Attempting code exchange without PKCE
curl -X POST https://auth.example.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=CAPTURED_CODE&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI"

### Should fail if PKCE is properly implemented
```

**Testing Multi-Device Authentication**

1. **Device Registration Testing**:
   - Authenticate on Device A
   - Attempt to use the same token on Device B
   - Verify tokens are bound to specific devices
   - Test device registration and deregistration flows

2. **Cross-Device Revocation Testing**:
   - Authenticate on Device A
   - Revoke the session from Device B
   - Verify the session is invalidated on Device A
   - Test if revocation is immediate or delayed

3. **Device Identification Testing**:
   - Analyze how devices are identified (IMEI, UUID, etc.)
   - Test if device identifiers can be spoofed
   - Verify device identifiers are not leaked in logs or error messages

## Common Findings

**Finding 1: Tokens Stored in Insecure Storage**

**Severity**: Critical

**Description**: Authentication tokens are stored in SharedPreferences (Android) or UserDefaults (iOS) instead of secure storage mechanisms. These storage locations are accessible to other applications on rooted/jailbroken devices and can be extracted through static analysis.

**Example**:
```kotlin
// INSECURE - DO NOT USE
val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
prefs.edit().putString("access_token", token).apply()
```

**Testing Method**: Decompile the application and search for SharedPreferences or UserDefaults usage with token keys. On rooted devices, directly access the SharedPreferences XML files.

**Remediation**:
```kotlin
// SECURE - Use EncryptedSharedPreferences
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val encryptedPrefs = EncryptedSharedPreferences.create(
    context,
    "secret_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

encryptedPrefs.edit().putString("access_token", token).apply()
```

---

**Finding 2: Missing Certificate Pinning**

**Severity**: High

**Description**: The application does not implement certificate pinning, allowing attackers to intercept authentication traffic through man-in-the-middle attacks on untrusted networks. Even with TLS, attackers can use their own certificates if the application trusts the system certificate store without additional validation.

**Example**: Application accepts any valid certificate signed by a trusted CA, including attacker-controlled CAs installed on the device.

**Testing Method**: Configure a testing proxy with a custom CA certificate. If the application accepts the proxy's certificate without additional validation, certificate pinning is not implemented.

**Remediation**:
```swift
// iOS: Implement certificate pinning
class PinningDelegate: NSObject, URLSessionDelegate {
    let pinnedCertificates: [SecCertificate]
    
    func urlSession(_ session: URLSession,
                    didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Validate certificate chain
        var secResult = SecTrustResultType.invalid
        SecTrustEvaluate(serverTrust, &secResult)
        
        // Check if certificate is in pinned list
        let certificateCount = SecTrustGetCertificateCount(serverTrust)
        for i in 0..<certificateCount {
            if let certificate = SecTrustGetCertificateAtIndex(serverTrust, i) {
                if pinnedCertificates.contains(certificate) {
                    completionHandler(.useCredential, URLCredential(trust: serverTrust))
                    return
                }
            }
        }
        
        completionHandler(.cancelAuthenticationChallenge, nil)
    }
}
```

---

**Finding 3: Credentials Stored After Authentication**

**Severity**: Critical

**Description**: User credentials (username and password) are stored on the device after authentication, either in secure storage or accessible files. This violates the principle that credentials should be used only during authentication and then discarded.

**Example**:
```kotlin
// INSECURE - DO NOT STORE CREDENTIALS
val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
prefs.edit()
    .putString("username", username)
    .putString("password", password)
    .apply()
```

**Testing Method**: Decompile the application and search for credential storage. On rooted devices, access the secure storage and verify credentials are not present.

**Remediation**: Never store credentials. Use token-based authentication and discard credentials after obtaining tokens.

```kotlin
// SECURE - Discard credentials after authentication
fun authenticate(username: String, password: String) {
    val credentials = Base64.getEncoder().encodeToString("$username:$password".toByteArray())
    
    val request = Request.Builder()
        .url("https://api.example.com/authenticate")
        .header("Authorization", "Basic $credentials")
        .build()
    
    val response = httpClient.newCall(request).execute()
    val tokenResponse = parseTokenResponse(response.body?.string())
    
    // Store token securely
    storeTokenSecurely(tokenResponse.accessToken)
    
    // Credentials are now out of scope and will be garbage collected
}
```

---

**Finding 4: Weak PKCE Implementation**

**Severity**: High

**Description**: The application implements OAuth 2.0 PKCE but with weak code_challenge generation. The code_verifier may be predictable, reused across requests, or not properly validated by the authorization server.

**Example**:
```swift
// INSECURE - Predictable code_verifier
let codeVerifier = UUID().uuidString
let codeChallenge = codeVerifier // Should be SHA256 hash
```

**Testing Method**: Capture multiple authorization requests and analyze code_challenge values. If they follow a pattern or are not SHA256 hashes of random values, PKCE is weak.

**Remediation**:
```swift
// SECURE - Proper PKCE implementation
func generateCodeVerifier() -> String {
    var buffer = [UInt8](repeating: 0, count: 32)
    _ = SecRandomCopyBytes(kSecRandomDefault, buffer.count, &buffer)
    return Data(buffer).base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
}

func generateCodeChallenge(from verifier: String) -> String {
    let data = verifier.data(using: .utf8)!
    var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
    data.withUnsafeBytes { buffer in
        _ = CC_SHA256(buffer.baseAddress, CC_LONG(data.count), &digest)
    }
    return Data(digest).base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
}
```

---

**Finding 5: Missing State Parameter Validation**

**Severity**: High

**Description**: The OAuth 2.0 flow does not implement or properly validate the state parameter, allowing CSRF attacks where an attacker tricks a user into authorizing access to the attacker's account.

**Example**:
```swift
// INSECURE - No state parameter
var components = URLComponents(url: authorizationEndpoint, resolvingAgainstBaseURL: false)!
components.queryItems = [
    URLQueryItem(name: "client_id", value: clientID),
    URLQueryItem(name: "redirect_uri", value: redirectURI),
    URLQueryItem(name: "response_type", value: "code")
    // Missing state parameter
]
```

**Testing Method**: Initiate an OAuth flow and capture the authorization request. Verify the state parameter is present and unique. Modify the state parameter in the callback and verify the application rejects it.

**Remediation**:
```swift
// SECURE - Implement state parameter
func initiateLogin() {
    let state = generateRandomState()
    UserDefaults.standard.set(state, forKey: "oauth_state")
    
    var components = URLComponents(url: authorizationEndpoint, resolvingAgainstBaseURL: false)!
    components.queryItems = [
        URLQueryItem(name: "client_id", value: clientID),
        URLQueryItem(name: "redirect_uri", value: redirectURI),
        URLQueryItem(name: "response_type", value: "code"),
        URLQueryItem(name: "state", value: state)
    ]
    
    UIApplication.shared.open(components.url!)
}

func handleCallback(url: URL) {
    let returnedState = URLComponents(url: url, resolvingAgainstBaseURL: false)?
        .queryItems?.first(where: { $0.name == "state" })?.value
    
    let storedState = UserDefaults.standard.string(forKey: "oauth_state")
    
    guard returnedState == storedState else {
        print("State mismatch - CSRF attack detected")
        return
    }
}
```

---

**Finding 6: Tokens Not Bound to Device or User Session**

**Severity**: High

**Description**: Authentication tokens are not bound to the device or user session, allowing attackers to use tokens extracted from one device on another device or from a different application.

**Example**: A token extracted from a rooted device can be used from a web browser or different mobile application without additional validation.

**Testing Method**: Extract a token from the application. Attempt to use the token from a different device, network, or application. If the token is accepted, it is not properly bound.

**Remediation**: Implement device binding by including device identifiers in token claims and validating them server-side.

```swift
// iOS: Include device identifier in authentication request
func authenticate(username: String, password: String) {
    let deviceID = UIDevice.current.identifierForVendor?.uuidString ?? ""
    
    var request = URLRequest(url: authenticationEndpoint)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body: [String: Any] = [
        "username": username,
        "password": password,
        "device_id": deviceID
    ]
    
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        guard let data = data else { return }
        let tokenResponse = try? JSONDecoder().decode(TokenResponse.self, from: data)
        self.storeTokenSecurely(tokenResponse?.accessToken ?? "")
    }.resume()
}
```

Server-side validation:

```python
### Backend: Validate device binding
def validate_token(token, device_id):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    if payload.get("device_id") != device_id:
        raise InvalidTokenError("Token not bound to this device")
    
    return payload
```

---

**Finding 7: Insufficient Token Expiration**

**Severity**: Medium

**Description**: Access tokens have excessively long expiration times (days or weeks), increasing the window of exposure if tokens are compromised. Refresh tokens may not be rotated, allowing indefinite access after a single compromise.

**Example**: Access tokens valid for 30 days without refresh token rotation.

**Testing Method**: Capture a token and verify its expiration time (

## Secure Design Guidance

This section requires additional handbook content. Cover the topic with vendor-neutral guidance, practical AppSec examples, implementation considerations, and testing notes.

## Interview Questions

- How do authentication and authorization failures show up differently in application logs?
- What controls would you expect around session creation, token validation, and privilege checks?
- How would you review an API endpoint to confirm that authorization is enforced server-side?
- What is the risk of relying on client-side checks for access control?
- How should teams test for horizontal and vertical privilege escalation?

## Key Takeaways

- Authentication verifies identity; authorization decides what that identity can access.
- Strong authentication does not compensate for missing or inconsistent authorization checks.
- Authorization belongs on the server side and should be enforced close to protected resources.
- AppSec reviews should trace identity, session, role, permission, and object ownership decisions.
- Secure design requires clear access-control models, centralized policy logic, and repeatable tests.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]
