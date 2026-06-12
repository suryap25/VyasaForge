# Sketchnote Prompt: Chapter 07 - Web Application Authentication Implementation

Create a clean sketchnote-style technical diagram for a handbook chapter.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box
- No dark background and no decorative gradients

## Chapter
- Title: Web Application Authentication Implementation
- Source stage: final

## Required Ideas To Show
- Learning Objectives
- Conceptual Foundation
- Architecture Perspective
- AppSec Lens
- Developer Lens
- Pentest Lens
- Common Findings
- Secure Design Guidance

## Learning Objectives
- Understand the fundamental principles of web application authentication and how they differ from authorization
- Design and implement secure authentication mechanisms for web applications using industry-standard protocols
- Evaluate authentication architecture decisions and their security implications
- Identify common authentication vulnerabilities and implement mitigations
- Conduct security assessments of authentication implementations

## Common Findings To Visualize

## Secure Guidance To Visualize
- **Layer 1: Credential Strength** - Enforce password policies that require sufficient entropy. Minimum 12 characters with mixed character types provides reasonable security for most applications. Consider passphrase requirements (3-4 random words) as an alternative that improves usability while maintaining security.
- **Layer 2: Credential Verification** - Use password hashing functions with appropriate computational cost. Bcrypt with 12+ rounds, scrypt, or Argon2 should require 100-500ms to hash a password on current hardware. This computational cost makes brute-force attacks expensive while remaining acceptable for legitimate login attempts.
- **Layer 3: Session/Token Security** - Generate cryptographically random session identifiers or tokens using secure random number generators. Session identifiers should be at least 128 bits of entropy. Tokens must include expiration claims and be validated on every request.
- **Layer 4: Multi-Factor Authentication** - Require a second verification factor for sensitive operations or high-value accounts. Time-based one-time passwords (TOTP), push notifications, or hardware tokens provide strong second factors. SMS-based OTP is weaker due to SIM swap attacks but better than no MFA.
- **Layer 5: Behavioral Analysis** - Monitor for suspicious authentication patterns such as logins from new geographic locations, unusual times, or multiple failed attempts. Implement step-up authentication (requiring additional verification) when suspicious activity is detected.

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
