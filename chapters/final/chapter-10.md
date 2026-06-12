---
chapter: 10
stage: final
source: drafts
generated_by: appsec-handbook-agent
---

# Chapter 10: Multi-Factor Authentication and Step-Up Authentication

## Learning Objectives

After completing this chapter, you will be able to:

- Explain the fundamental differences between multi-factor authentication (MFA) and step-up authentication
- Design MFA architectures that balance security with user experience
- Implement MFA mechanisms across web and mobile applications
- Identify and remediate common MFA implementation vulnerabilities
- Evaluate MFA solutions from an application security perspective
- Conduct security assessments of authentication flows that incorporate MFA
- Apply step-up authentication patterns to protect sensitive operations
- Understand the security implications of various MFA factor types

## Conceptual Foundation

Multi-factor authentication (MFA) is a security control that requires users to provide two or more independent verification methods before gaining access to a resource. These independent methods—called factors—come from different categories: something you know (knowledge factor), something you have (possession factor), and something you are (inherence factor).

The fundamental principle behind MFA is that compromising a single authentication factor should not grant an attacker access to the system. If an attacker obtains a user's password, they still cannot access the account without the second factor. This significantly raises the cost of account compromise attacks.

Step-up authentication is a related but distinct concept. Rather than requiring MFA for all access, step-up authentication applies additional authentication requirements only when users attempt to perform sensitive operations. A user might authenticate once with a password to access their account, but when attempting to change their password, transfer funds, or modify security settings, the system requires an additional authentication factor. This approach balances security with user experience by reducing friction for routine operations while protecting high-risk actions.

### Factor Categories

**Knowledge Factors** are something the user knows. Passwords and PINs are the most common examples. Security questions also fall into this category, though they are generally considered weaker than passwords due to predictability and social engineering vulnerabilities.

**Possession Factors** are something the user physically possesses. Hardware security keys, mobile devices receiving SMS or push notifications, and authenticator applications all serve as possession factors. The key distinction is that the factor exists outside the user's memory.

**Inherence Factors** are something the user is. Biometric authentication—fingerprints, facial recognition, iris scanning—represents this category. Behavioral biometrics, such as keystroke dynamics or mouse movement patterns, also fall here, though they are generally considered supplementary rather than primary factors.

### Factor Independence

True MFA requires that factors be independent. If an attacker compromises one factor, they should not be able to derive or compromise the other. A password and a security question are not independent factors because an attacker who obtains the password might also be able to answer the security question through social engineering or public information. Similarly, a password and a PIN sent via SMS to the same phone number are not truly independent if the attacker can perform a SIM swap attack to intercept both.

### Enrollment and Recovery

MFA systems must address enrollment and recovery scenarios. Users need a straightforward process to register their second factor. Equally important, systems must provide account recovery mechanisms when users lose access to their second factor. Recovery processes themselves become security-critical because they represent an alternative path to account access. A poorly designed recovery mechanism can undermine the security benefits of MFA.

## Architecture Perspective

### MFA Flow Architecture

A typical MFA architecture consists of several components working in concert:

```
┌─────────────────────────────────────────────────────────────┐
│                    User/Client Application                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication Service                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Validate Primary Credential (Password/Biometric)  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Initiate Secondary Factor Challenge               │   │
│  │    - Generate challenge                              │   │
│  │    - Deliver via appropriate channel                 │   │
│  │    - Store challenge state with TTL                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. Validate Secondary Factor Response                │   │
│  │    - Verify code/response                            │   │
│  │    - Check expiration                                │   │
│  │    - Prevent replay attacks                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Issue Session Token                               │   │
│  │    - Mark session as MFA-verified                    │   │
│  │    - Set appropriate session properties              │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Protected Resources                         │
│              (Accessible only with MFA token)                │
└─────────────────────────────────────────────────────────────┘
```

The authentication service must maintain state throughout the MFA process. After validating the primary credential, the system enters a "partially authenticated" state where the user has proven one factor but not yet the second. This state must be tracked securely and must expire after a reasonable time period (typically 5-15 minutes).

### Stateless vs. Stateful MFA

Stateful MFA systems maintain server-side session state throughout the authentication process. The server tracks which factors have been satisfied, when they were satisfied, and what challenges are pending. This approach provides strong security guarantees but requires session management infrastructure.

Stateless MFA systems encode authentication state into cryptographically signed tokens that the client returns with each request. The server validates the token signature and extracts the authentication state without maintaining server-side records. This approach scales more easily but requires careful token design to prevent tampering.

Most production systems use a hybrid approach: stateless tokens for the final authenticated session, but stateful tracking during the MFA challenge process itself.

### Step-Up Authentication Architecture

Step-up authentication requires the application to identify sensitive operations and enforce additional authentication at the point of execution:

```
User Request
    │
    ▼
Check Session MFA Status
    │
    ├─ MFA verified within acceptable time window?
    │  ├─ YES → Proceed to operation
    │  └─ NO → Initiate step-up challenge
    │
    ▼
Step-Up Challenge
    │
    ├─ Validate secondary factor
    │
    ▼
Update Session MFA Timestamp
    │
    ▼
Execute Sensitive Operation
```

The key architectural decision is determining which operations require step-up authentication and how long an MFA verification remains valid. A user who authenticated with MFA 30 minutes ago might not need to re-authenticate for viewing account details, but should re-authenticate before changing their password or initiating a fund transfer.

### Delivery Channels for MFA Factors

Different delivery channels present different security and usability tradeoffs:

**SMS/Text Message**: Widely supported but vulnerable to SIM swap attacks and interception. SMS should not be considered a secure possession factor in high-security contexts.

**Email**: Requires the user to access their email account, which may itself be compromised. Email delivery is slower than SMS but less vulnerable to SIM swap attacks.

**Push Notifications**: Delivered to a registered mobile device. Requires the user to actively approve the authentication attempt, which provides some protection against unauthorized access. Vulnerable to push notification fatigue attacks where users approve requests without careful review.

**Authenticator Applications**: Time-based one-time passwords (TOTP) or event-based one-time passwords (HOTP) generated by applications like Google Authenticator or Authy. These are not transmitted over any channel, reducing interception risk. However, if the device is compromised, the authenticator application can be accessed.

**Hardware Security Keys**: Physical devices that generate or store cryptographic credentials. These provide strong security guarantees but require users to carry and manage physical hardware.

**Biometric Authentication**: Fingerprint or facial recognition on mobile devices. Provides good usability but requires compatible hardware and careful implementation to prevent spoofing.

## AppSec Lens

### MFA Bypass Vulnerabilities

MFA systems are frequently bypassed through implementation flaws rather than cryptographic weaknesses. Common bypass techniques include:

**Null Factor Bypass**: The application accepts an empty or null value for the second factor. A developer might implement conditional logic that skips MFA validation if the factor is not provided, creating a bypass path.

**Timing Window Exploitation**: MFA codes are typically valid for 30-60 seconds. If the application doesn't properly enforce expiration, attackers can brute-force valid codes within the window.

**Replay Attacks**: If the application doesn't track which MFA codes have been used, an attacker can replay a previously valid code to gain access.

**Session Fixation**: An attacker tricks a user into authenticating with the attacker's session ID. When the user completes MFA, the attacker's session becomes authenticated.

**Backup Code Mishandling**: Many MFA systems provide backup codes for account recovery. If these codes are not properly protected, stored, or rate-limited, they become an alternative authentication path.

**Factor Downgrade**: The application allows users to disable MFA or switch to a weaker factor type without proper verification.

### MFA Enrollment Vulnerabilities

The enrollment process itself presents security risks:

**Insufficient Verification During Enrollment**: An attacker might enroll their own MFA device on a compromised account without the legitimate user's knowledge. The application should require the user to verify their identity before allowing MFA enrollment changes.

**Shared Possession Factors**: If multiple users share a single phone number or email address for MFA delivery, an attacker who compromises one account gains access to MFA codes for multiple accounts.

**Lack of Audit Logging**: Changes to MFA settings should be logged and, ideally, should trigger notifications to the user so they can detect unauthorized modifications.

### Step-Up Authentication Weaknesses

Step-up authentication introduces its own vulnerabilities:

**Insufficient Sensitivity Classification**: Applications that don't properly identify which operations require step-up authentication leave sensitive operations unprotected.

**Excessive Step-Up Frequency**: Requiring step-up authentication too frequently causes user frustration and encourages users to disable the feature or use weaker factors.

**Inadequate Session Binding**: If step-up authentication doesn't properly bind the re-authentication to the current session, an attacker might be able to use a step-up token from one session in another session.

**Missing Step-Up for API Operations**: Web applications often implement step-up authentication for browser-based operations but forget to enforce it for API calls, allowing attackers to bypass the protection by using direct API access.

### Biometric Authentication Risks

Biometric factors introduce unique security considerations:

**Spoofing Attacks**: Fingerprint sensors can be spoofed with high-quality prints; facial recognition systems can be fooled with photographs or masks. The security of biometric authentication depends heavily on the quality of the sensor and the liveness detection mechanisms.

**Irreversibility**: Unlike passwords, biometric data cannot be changed if compromised. A compromised fingerprint is compromised forever.

**Privacy Implications**: Biometric data is highly sensitive personal information. Its collection, storage, and use must comply with privacy regulations and should be minimized.

**Fallback Mechanisms**: Systems that allow users to fall back to password-only authentication when biometric authentication fails undermine the security benefits of biometric MFA.

## Developer Lens

### Implementing MFA: Practical Example

Consider a web application that needs to implement MFA for user login. The following example demonstrates a secure implementation pattern:

```python
### Authentication service pseudocode
class AuthenticationService:
    def initiate_login(self, username, password):
        """Validate primary credential and initiate MFA challenge"""
        user = self.validate_credentials(username, password)
        if not user:
            return {"status": "failed", "message": "Invalid credentials"}
        
        # Check if user has MFA enabled
        if not user.mfa_enabled:
            return self.create_session(user)
        
        # Generate MFA challenge
        challenge_id = self.generate_secure_random_id()
        mfa_code = self.generate_totp_code(user.mfa_secret)
        
        # Store challenge with expiration
        self.cache.set(
            f"mfa_challenge:{challenge_id}",
            {
                "user_id": user.id,
                "code": mfa_code,
                "attempts": 0,
                "created_at": time.time()
            },
            ttl=300  # 5 minutes
        )
        
        # Deliver MFA code via configured channel
        self.deliver_mfa_code(user, mfa_code)
        
        return {
            "status": "mfa_required",
            "challenge_id": challenge_id,
            "message": "MFA code sent to registered device"
        }
    
    def verify_mfa(self, challenge_id, user_provided_code):
        """Verify MFA code and complete authentication"""
        # Retrieve challenge from cache
        challenge = self.cache.get(f"mfa_challenge:{challenge_id}")
        
        if not challenge:
            return {"status": "failed", "message": "Challenge expired"}
        
        # Check expiration
        if time.time() - challenge["created_at"] > 300:
            self.cache.delete(f"mfa_challenge:{challenge_id}")
            return {"status": "failed", "message": "Challenge expired"}
        
        # Rate limit attempts
        if challenge["attempts"] >= 5:
            self.cache.delete(f"mfa_challenge:{challenge_id}")
            return {"status": "failed", "message": "Too many attempts"}
        
        # Verify code (use constant-time comparison)
        if not self.constant_time_compare(
            user_provided_code,
            challenge["code"]
        ):
            challenge["attempts"] += 1
            self.cache.set(
                f"mfa_challenge:{challenge_id}",
                challenge,
                ttl=300
            )
            return {"status": "failed", "message": "Invalid code"}
        
        # Code is valid - mark challenge as used and create session
        self.cache.delete(f"mfa_challenge:{challenge_id}")
        user = self.get_user(challenge["user_id"])
        
        return self.create_session(user, mfa_verified=True)
    
    def create_session(self, user, mfa_verified=False):
        """Create authenticated session"""
        session_token = self.generate_secure_session_token()
        
        session_data = {
            "user_id": user.id,
            "mfa_verified": mfa_verified,
            "mfa_verified_at": time.time() if mfa_verified else None,
            "created_at": time.time(),
            "ip_address": self.get_client_ip()
        }
        
        self.cache.set(
            f"session:{session_token}",
            session_data,
            ttl=3600  # 1 hour
        )
        
        return {
            "status": "success",
            "session_token": session_token,
            "mfa_verified": mfa_verified
        }
```

This implementation demonstrates several security principles:

- **Challenge Expiration**: MFA challenges expire after 5 minutes, preventing indefinite brute-force attempts
- **Rate Limiting**: After 5 failed attempts, the challenge is invalidated
- **Constant-Time Comparison**: Uses constant-time string comparison to prevent timing attacks
- **State Tracking**: Maintains server-side state for the MFA challenge
- **Audit Trail**: Records IP address and timestamps for security monitoring

### Step-Up Authentication Implementation

```python
class StepUpAuthenticationMiddleware:
    SENSITIVE_OPERATIONS = {
        "change_password": {"requires_mfa": True, "max_age": 0},
        "update_email": {"requires_mfa": True, "max_age": 0},
        "disable_mfa": {"requires_mfa": True, "max_age": 0},
        "transfer_funds": {"requires_mfa": True, "max_age": 300},
        "view_account": {"requires_mfa": False, "max_age": None}
    }
    
    def check_step_up_requirement(self, operation, session):
        """Determine if step-up authentication is required"""
        if operation not in self.SENSITIVE_OPERATIONS:
            return False
        
        requirements = self.SENSITIVE_OPERATIONS[operation]
        
        if not requirements["requires_mfa"]:
            return False
        
        # Check if MFA has been verified
        if not session.get("mfa_verified"):
            return True
        
        # Check if MFA verification is still fresh
        max_age = requirements["max_age"]
        if max_age == 0:
            # Require fresh MFA verification
            return True
        
        mfa_verified_at = session.get("mfa_verified_at")
        if time.time() - mfa_verified_at > max_age:
            return True
        
        return False
    
    def handle_request(self, request, operation):
        """Middleware handler for step-up authentication"""
        session = self.get_session(request)
        
        if not session:
            return self.redirect_to_login()
        
        if self.check_step_up_requirement(operation, session):
            # Initiate step-up challenge
            challenge = self.initiate_mfa_challenge(session["user_id"])
            return self.render_step_up_form(challenge)
        
        # Operation allowed
        return None
```

### Mobile MFA Considerations

Mobile applications have unique MFA requirements:

```swift
// iOS example using biometric authentication
import LocalAuthentication

class BiometricAuthenticationManager {
    func authenticateWithBiometric(
        reason: String,
        completion: @escaping (Bool, Error?) -> Void
    ) {
        let context = LAContext()
        var error: NSError?
        
        // Check if biometric authentication is available
        guard context.canEvaluatePolicy(
            .deviceOwnerAuthenticationWithBiometrics,
            error: &error
        ) else {
            completion(false, error)
            return
        }
        
        // Perform biometric authentication
        context.evaluatePolicy(
            .deviceOwnerAuthenticationWithBiometrics,
            localizedReason: reason
        ) { success, error in
            DispatchQueue.main.async {
                if success {
                    // Biometric authentication successful
                    // Proceed with sensitive operation
                    completion(true, nil)
                } else {
                    // Authentication failed
                    completion(false, error)
                }
            }
        }
    }
    
    func performSensitiveOperation(
        operation: String,
        completion: @escaping (Bool) -> Void
    ) {
        // Always require fresh biometric authentication
        // for sensitive operations
        self.authenticateWithBiometric(
            reason: "Authenticate to \(operation)"
        ) { success, error in
            if success {
                // Execute sensitive operation
                completion(true)
            } else {
                // Show error to user
                completion(false)
            }
        }
    }
}
```

## Pentest Lens

### MFA Testing Methodology

Security assessments of MFA implementations should follow a systematic approach:

**1. Identify MFA Requirements**
- Which operations require MFA?
- Which factor types are supported?
- What is the MFA enrollment process?
- Are there bypass mechanisms or recovery paths?

**2. Test Factor Validation**
- Can you submit an empty MFA code?
- Can you submit invalid codes repeatedly without rate limiting?
- Can you reuse previously valid codes?
- Can you brute-force codes within the validity window?
- Are codes properly expired?

**3. Test Session Management**
- Can you use a session token from before MFA completion?

## Common Findings

### MFA Bypass Through Null/Empty Factor

**Description**: Applications accept empty, null, or missing values for the secondary authentication factor, allowing attackers to skip MFA entirely.

**Example Finding**:
```
POST /api/verify-mfa HTTP/1.1
Content-Type: application/json

{
  "challenge_id": "abc123",
  "mfa_code": ""
}

Response: 200 OK
{"status": "success", "session_token": "xyz789"}
```

The application should reject empty codes with a 400 Bad Request and not proceed to session creation.

**Root Cause**: Insufficient input validation or conditional logic that treats missing factors as optional rather than required.

**Remediation**:
- Implement explicit validation that rejects empty, null, or whitespace-only factor values
- Use allowlist validation for expected code formats (e.g., 6-digit numeric codes)
- Never use conditional logic that skips MFA validation based on factor presence
- Return consistent error messages for all validation failures to avoid information disclosure

---

### MFA Code Reuse and Replay

**Description**: Previously used MFA codes are accepted multiple times, or codes are not invalidated after first use.

**Example Finding**:
```
Attacker intercepts valid MFA code: 123456
First attempt: POST /verify-mfa with code 123456 → Success
Second attempt: POST /verify-mfa with code 123456 → Success (should fail)
```

**Root Cause**: Application fails to track which codes have been consumed or doesn't invalidate codes after successful verification.

**Remediation**:
- Maintain a server-side record of consumed codes with timestamps
- Invalidate codes immediately after successful verification
- For TOTP-based systems, track the time window of the last accepted code and reject codes from the same window
- Implement this check before any session creation or privilege escalation

---

### Insufficient MFA Challenge Expiration

**Description**: MFA codes remain valid for extended periods, allowing brute-force attacks.

**Example Finding**:
```
MFA code generated at 14:00:00
Code still valid at 14:45:00 (45 minutes later)
Attacker has 45 minutes to brute-force a 6-digit code (1 million possibilities)
```

**Root Cause**: Overly generous expiration windows or missing expiration checks entirely.

**Remediation**:
- Set MFA code expiration to 5-10 minutes maximum
- Implement server-side timestamp validation on every verification attempt
- Delete expired challenges from storage immediately
- Log and alert on repeated verification attempts against expired challenges

---

### Lack of Rate Limiting on MFA Verification

**Description**: Attackers can attempt unlimited MFA code guesses without throttling.

**Example Finding**:
```
for i in range(1000000):
    POST /verify-mfa with code i
    # No delays, no blocking, no rate limiting
```

**Root Cause**: Missing or ineffective rate limiting on the MFA verification endpoint.

**Remediation**:
- Implement per-challenge attempt limits (e.g., 5 attempts maximum)
- Invalidate the challenge after exceeding attempt limits
- Implement per-user rate limiting (e.g., 10 failed attempts across all challenges in 15 minutes)
- Implement per-IP rate limiting to catch distributed attacks
- Use exponential backoff for repeated failures
- Log all rate limit violations for security monitoring

---

### MFA Enrollment Without Verification

**Description**: Attackers can enroll their own MFA device on a compromised account without the legitimate user's knowledge or consent.

**Example Finding**:
```
Attacker gains access to user account (via password compromise)
POST /api/enroll-mfa
{
  "phone_number": "+1-555-0100",
  "method": "sms"
}
Response: 200 OK - MFA enrolled
User never receives notification of this change
```

**Root Cause**: MFA enrollment doesn't require verification of the user's identity or existing credentials.

**Remediation**:
- Require users to verify their current password or biometric before enrolling new MFA factors
- Send verification codes to the user's existing contact information before activating new factors
- Require explicit confirmation from the user before MFA enrollment takes effect
- Log all MFA enrollment attempts and notify users of successful enrollments
- Implement a grace period where newly enrolled factors require additional verification

---

### Backup Code Mishandling

**Description**: Backup codes for MFA recovery are not properly protected, allowing account takeover.

**Example Finding**:
```
Backup codes stored in plaintext in database
Backup codes not rate-limited during verification
Backup codes displayed in browser history
Backup codes sent via unencrypted email
```

**Root Cause**: Insufficient protection of backup codes as an alternative authentication mechanism.

**Remediation**:
- Hash backup codes using the same algorithm as passwords (bcrypt, Argon2)
- Implement rate limiting on backup code verification (e.g., 3 attempts per code)
- Invalidate backup codes after use
- Display backup codes only once during generation, never in recovery flows
- Require users to store backup codes securely (encourage password managers)
- Log all backup code usage and notify users
- Limit the number of backup codes generated (e.g., 10 maximum)

---

### Session Fixation with MFA

**Description**: Attackers trick users into authenticating with the attacker's session ID, gaining access when the user completes MFA.

**Example Finding**:
```
Attacker generates session ID: attacker_session_123
Attacker tricks user into visiting: /login?session=attacker_session_123
User enters credentials and completes MFA
Session attacker_session_123 becomes authenticated
Attacker uses attacker_session_123 to access the account
```

**Root Cause**: Application reuses the same session ID throughout the authentication process instead of regenerating it after MFA completion.

**Remediation**:
- Generate a new session ID after successful MFA verification
- Invalidate the pre-authentication session ID
- Never accept session IDs from URL parameters; use secure cookies only
- Implement session binding to IP address and User-Agent
- Validate that the session ID was generated by the server, not provided by the client

---

### Step-Up Authentication Bypass via API

**Description**: Web applications enforce step-up authentication for browser-based operations but fail to enforce it for direct API calls.

**Example Finding**:
```
Browser: POST /change-password → Requires step-up MFA ✓
API: POST /api/v1/user/password → No step-up required ✗
Attacker uses API to bypass step-up authentication
```

**Root Cause**: Step-up authentication logic implemented only in web controllers, not in API endpoints.

**Remediation**:
- Implement step-up authentication checks in a centralized middleware or service
- Apply the same step-up requirements to all endpoints (web, API, mobile)
- Use consistent session attributes to track MFA verification across all interfaces
- Test all API endpoints for step-up authentication enforcement
- Document which operations require step-up authentication

---

### Biometric Spoofing and Liveness Detection Bypass

**Description**: Biometric authentication systems accept spoofed biometric data (photographs, masks, replayed recordings).

**Example Finding**:
```
Facial recognition system accepts high-quality photograph of user
Fingerprint sensor accepts lifted fingerprint on tape
Voice recognition accepts recorded audio of user
```

**Root Cause**: Insufficient liveness detection or weak spoofing resistance in biometric implementation.

**Remediation**:
- Implement liveness detection that requires active user participation (e.g., blink detection for facial recognition)
- Use anti-spoofing techniques appropriate to the biometric type
- Require multiple biometric samples and verify consistency
- Implement fallback authentication when biometric authentication fails
- Never allow biometric authentication as the sole factor for sensitive operations
- Regularly test biometric systems against known spoofing techniques
- Consider the security level of the biometric sensor (hardware quality matters significantly)

---

### Push Notification Fatigue and Approval Without Review

**Description**: Users approve push notification MFA requests without carefully reviewing them, allowing attackers to gain access through social engineering or timing attacks.

**Example Finding**:
```
Attacker initiates login attempt
Push notification sent to user's phone
User receives multiple notifications in quick succession
User approves without reading details
Attacker gains access
```

**Root Cause**: Insufficient user education, unclear notification content, or lack of context in push notifications.

**Remediation**:
- Include detailed context in push notifications (location, device, timestamp, operation type)
- Require explicit user action (not just swipe) to approve
- Implement a delay before allowing approval (e.g., 3-5 seconds minimum)
- Show the user's current location and compare to login location
- Limit the number of pending push notifications (reject new attempts if one is pending)
- Log all push notification approvals and denials
- Educate users about reviewing notification details before approving
- Implement anomaly detection to flag unusual login patterns

---

### Insufficient Sensitivity Classification for Step-Up

**Description**: Applications don't properly identify which operations require step-up authentication, leaving sensitive operations unprotected.

**Example Finding**:
```
Step-up required for: Viewing account balance
Step-up NOT required for: Changing email address, initiating fund transfer
```

**Root Cause**: Incomplete threat modeling or inconsistent implementation of step-up requirements.

**Remediation**:
- Conduct threat modeling to identify all sensitive operations
- Classify operations by risk level (high-risk operations require fresh MFA)
- Document step-up requirements for each operation
- Implement step-up for: password changes, email changes, MFA modifications, fund transfers, permission changes, data exports
- Regularly audit operations to ensure step-up is enforced
- Test both positive cases (step-up required) and negative cases (step-up not required)

---

### Excessive Step-Up Authentication Frequency

**Description**: Applications require step-up authentication too frequently, causing user frustration and encouraging users to disable MFA.

**Example Finding**:
```
User must re-authenticate with MFA every 5 minutes
User must re-authenticate for every operation
User disables MFA due to friction
```

**Root Cause**: Overly conservative security settings without consideration for user experience.

**Remediation**:
- Set appropriate MFA freshness windows based on operation sensitivity
- Allow 15-30 minutes for routine operations (viewing data)
- Require fresh MFA (0 minutes) only for high-risk operations (password changes, security settings)
- Allow users to configure their own step-up preferences within security guidelines
- Provide clear feedback about why step-up is required
- Implement smooth step-up flows that don't disrupt user workflows
- Monitor user behavior to detect when step-up frequency is causing abandonment

---

### Missing MFA Audit Logging

**Description**: MFA events are not logged, preventing detection of unauthorized access attempts or account compromise.

**Example Finding**:
```
No logs of MFA enrollment changes
No logs of MFA verification attempts
No logs of backup code usage
No alerts when MFA is disabled
```

**Root Cause**: Incomplete security logging implementation.

**Remediation**:
- Log all MFA-related events: enrollment, verification, backup code usage, disablement
- Include context in logs: user ID, timestamp, IP address, user agent, success/failure
- Alert users when MFA settings are changed
- Alert administrators on suspicious patterns: multiple failed attempts, unusual locations, rapid changes
- Retain MFA logs for at least 90 days
- Implement real-time alerting for high-risk events
- Make logs available to users for review in their security settings

---

### Weak MFA Factor Types

**Description**: Applications support weak MFA factors that don't provide meaningful security improvements.

**Example Finding**:
```
Supported MFA methods:
- Security questions (weak)
- Email verification (moderate)
- SMS (moderate, vulnerable to SIM swap)
- TOTP (strong)
- Hardware keys (very strong)

User selects security questions as MFA
```

**Root Cause**: Offering weak factor types without guidance or enforcement of stronger alternatives.

**Remediation**:
- Prioritize strong factor types: TOTP, hardware security keys, biometric authentication
- Deprecate weak factor types: security questions, email-only verification
- Provide clear guidance on factor strength
- For high-security accounts, require strong factors
- Offer incentives for using stronger factors
- Regularly audit which factors users are actually using
- Plan migration paths away from weak factors

---

## Secure Design Guidance

### MFA Architecture Design Principles

**1. Factor Independence**

Ensure that compromise of one factor does not compromise the other. When designing MFA systems:

- Never use related factors (password + security question, password + PIN sent to same phone)
- Verify that factors come from different categories (knowledge, possession, inherence)
- Evaluate the practical independence of factors in your threat model
- Consider attack chains: if an attacker compromises one factor, can they derive the other?

**Example**: A system using password + SMS code is not truly independent if the attacker can perform a SIM swap attack. Consider requiring a hardware security key as the second factor instead.

**2. Secure State Management During MFA**

The partially-authenticated state between primary and secondary factor verification is a critical security boundary:

- Store MFA challenge state server-side, not in client-side tokens
- Use cryptographically secure random IDs for challenge identifiers
- Set appropriate TTLs (5-10 minutes for most scenarios)
- Never include sensitive information in challenge tokens
- Implement atomic transitions between authentication states
- Ensure that completing MFA invalidates the challenge immediately

**Example Implementation Pattern**:
```
Challenge State: {
  challenge_id: <secure_random>,
  user_id: <verified_user>,
  factor_type: <totp|sms|push>,
  created_at: <timestamp>,
  expires_at: <timestamp + 5min>,
  attempts: 0,
  max_attempts: 5,
  verified: false
}
```

**3. Enrollment Security**

MFA enrollment is a critical security operation that must be protected:

- Require users to verify their identity before enrolling new factors
- Send verification codes to existing verified contact information
- Implement a grace period where newly enrolled factors require additional verification
- Notify users of all MFA enrollment changes
- Provide a way for users to review and revoke enrolled factors
- Log all enrollment attempts and changes

**4. Recovery Mechanism Design**

Account recovery without MFA access must be carefully designed:

- Provide backup codes as a recovery mechanism, not as a primary factor
- Generate backup codes only during initial MFA setup
- Hash and rate-limit backup codes like passwords
- Invalidate backup codes after use
- Limit the number of backup codes (e.g., 10)
- Require additional verification when using backup codes
- Consider alternative recovery paths: security questions verified by support, identity verification, account recovery links

**5. Session Binding and Freshness**

MFA verification must be properly bound to sessions:

- Regenerate session IDs after successful MFA verification
- Track MFA verification status and timestamp in session
- Implement MFA freshness windows based on operation sensitivity
- Bind sessions to IP address and User-Agent for additional security
- Invalidate sessions when MFA settings change
- Require re-authentication when switching networks or devices

### Step-Up Authentication Design

**1. Sensitivity Classification**

Classify operations by risk level and define step-up requirements:

```
HIGH RISK (Require fresh MFA, 0 minute window):
- Change password
- Change email address
- Disable MFA
- Modify security settings
- Add new payment method
- Initiate large transfers

MEDIUM RISK (Require MFA within 15 minutes):
- Change account settings
- Modify notification preferences
- Update profile information
- Initiate moderate transfers

LOW RISK (No step-up required):
- View account information
- View transaction history
- Download statements
- Update display preferences
```

**2. Consistent Enforcement Across Interfaces**

Implement step-up authentication consistently:

- Apply the same requirements to web, API, and mobile interfaces
- Use centralized middleware or service for step-up checks
- Test all interfaces for step-up enforcement
- Document step-up requirements in API documentation
- Provide clear error messages when step-up is required

**3. User Experience Optimization**

Balance security with usability:

- Provide clear explanations for why step-up is required
- Implement smooth step-up flows that don't disrupt workflows
- Allow users to complete step-up without leaving the current page (modal dialogs)
- Remember step-up verification for reasonable periods (15-30 minutes for routine operations)
- Provide progress indicators during step-up challenges
- Offer multiple factor types for step-up (not just the primary MFA method)

### Factor Type Selection and Implementation

**1. Time-Based One-Time Passwords (TOTP)**

TOTP is a strong, widely-supported factor type:

**Advantages**:
- No transmission required (codes generated locally)
- Works offline
- Resistant to interception
- Widely supported by authenticator apps

**Implementation Considerations**:
- Use 6-digit codes with 30-second time windows
- Allow for time skew (±1 time window) to account for clock drift
- Implement rate limiting on verification attempts
- Provide backup codes for recovery
- Educate users about backing up their authenticator app

**2. Push Notifications**

Push notifications provide good usability with reasonable security:

**Advantages**:
- User actively approves authentication
- Provides context about the login attempt
- Works on mobile devices
- Can include location and device information

**Implementation Considerations**:
- Include detailed context in notifications (location, device, timestamp)
- Require explicit user action to approve (not just swipe)
- Implement a delay before allowing approval (3-5 seconds)
- Limit pending notifications (reject new attempts if one is pending)
- Log all approvals and denials
- Implement anomaly detection for unusual patterns

**3. Hardware Security Keys**

Hardware keys provide the strongest security:

**Advantages**:
- Resistant to phishing
- Resistant to malware
- Resistant to SIM swap and interception attacks
- Cryptographically strong

**Implementation Considerations**:
- Support standard protocols (FIDO2/WebAuthn)
- Provide backup keys or recovery mechanisms
- Educate users about physical security of keys
- Test with multiple key types and manufacturers
- Provide clear error messages if key is not detected

**4. Biometric Authentication**

Biometric factors provide good usability but require careful implementation:

**Advantages**:
- Convenient for users
- Difficult to share or forget
- Works on modern mobile devices

**Implementation Considerations**:
- Implement liveness detection to prevent spoofing
- Never use biometric as sole factor for sensitive operations
- Provide fallback authentication methods
- Understand the security level of the biometric sensor
- Consider privacy implications of biometric data collection
- Test against known spoofing techniques
- Implement rate limiting on failed biometric attempts

### MFA for Different User Populations

**1. High-Security Users (Administrators, Finance, Legal)**

- Require strong factors: hardware keys or biometric + TOTP
- Implement step-up authentication for all sensitive operations
- Require fresh MFA verification (0-minute window) for critical operations
- Implement additional controls: IP whitelisting, device registration
- Provide detailed audit logs and real-time alerts
- Require regular MFA factor rotation

**2. Standard Users**

- Offer multiple factor types: TOTP, push notifications, SMS
- Require MFA for account access
- Implement step-up authentication for sensitive operations
- Allow reasonable MFA freshness windows (15-30 minutes)
- Provide clear guidance on factor selection
- Implement user-friendly recovery mechanisms

**3. Legacy or Constrained Users**

- Support SMS as a fallback option (not ideal but better than no MFA)
- Provide email-based verification as alternative
- Implement additional compensating controls
- Plan migration to stronger factors
- Provide extra support and education

### MFA Deployment Patterns

**1. Phased Rollout**

Deploy MFA gradually to minimize disruption:

- Phase 1: Make MFA optional, educate users
- Phase 2: Require MFA for high-risk user groups (administrators)
- Phase 3: Require MFA for all users
- Phase 4: Enforce strong factor types, deprecate weak factors

**2. Graceful Degradation**

Handle MFA failures gracefully:

- If primary MFA method fails, offer alternative factors
- If all MFA methods fail, provide account recovery process
- Don't lock users out permanently
- Implement support workflows for MFA issues
- Log all MFA failures for analysis

**3. Monitoring and Alerting**

Implement comprehensive monitoring:

- Alert on unusual MFA patterns: multiple failed attempts, rapid changes, unusual locations
- Monitor MFA adoption rates and factor type distribution
- Track MFA-related support tickets
-

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
