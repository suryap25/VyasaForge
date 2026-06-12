# Sketchnote Prompt: Chapter 11 - Security Best Practices and Threat Mitigation

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
- Title: Security Best Practices and Threat Mitigation
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
- Understand the foundational principles of security best practices within authentication and authorization systems
- Identify and categorize common threats to authentication and authorization mechanisms
- Apply defense-in-depth strategies to mitigate authentication and authorization risks
- Design and implement secure authentication and authorization architectures
- Conduct threat modeling and risk assessment for identity systems

## Common Findings To Visualize

## Secure Guidance To Visualize
- **Token Structure**: Include minimal claims (user ID, roles, expiration). Avoid storing sensitive data in tokens; they can be decoded by anyone.
- **Signature Verification**: Always verify token signatures using the issuer's public key. Never trust unsigned tokens.
- **Expiration Strategy**: Use short-lived access tokens (15-60 minutes) with longer-lived refresh tokens (days/weeks) for token rotation. This limits exposure if an access token is compromised.
- **Token Revocation**: Implement a revocation mechanism for scenarios requiring immediate invalidation (logout, permission changes, security incidents). Use a blacklist for short-lived tokens or a whitelist for long-lived tokens.
- **Multiple Methods**: Support multiple MFA methods (TOTP, SMS, push notifications, hardware keys) to accommodate different user preferences and security requirements.

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
