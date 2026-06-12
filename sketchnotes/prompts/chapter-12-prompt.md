# Sketchnote Prompt: Chapter 12 - Compliance, Auditing, and Operational Considerations

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
- Title: Compliance, Auditing, and Operational Considerations
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
- Understand the relationship between authentication, authorization, compliance frameworks, and operational security
- Design audit logging and monitoring systems that meet regulatory requirements without compromising performance
- Implement retention policies, data protection, and access controls for sensitive authentication and authorization logs
- Conduct compliance assessments for authentication and authorization systems across common frameworks (SOC 2, ISO 27001, HIPAA, PCI-DSS, GDPR)
- Build operational runbooks for incident response, access revocation, and credential lifecycle management

## Common Findings To Visualize
- Log all authentication attempts (successful and failed) with consistent fields: timestamp, username, authentication method, source IP, user agent, MFA status, and result
- Implement centralized logging that captures events from all authentication systems (application, directory service, API gateway, VPN)
- Define minimum logging requirements in code review and architecture standards
- Validate logging completeness through automated tests that perform authentication operations and verify corresponding log entries
- Log authorization decisions with full context: user ID, resource identifier, action requested, permissions required, user's roles and permissions, decision, and decision reason

## Secure Guidance To Visualize
- **Separation of concerns**: Audit logs are security-sensitive and must be protected differently from application logs. Use a dedicated logging service with restricted write and read access.
- **Immutability**: Implement append-only storage where logs can be added but never modified or deleted. Use cryptographic integrity checks (hash chains, digital signatures, or Merkle trees) to detect tampering.
- **Centralization**: Collect authentication and authorization events from all systems (application, API gateway, directory service, VPN, cloud provider) into a single audit log. This enables comprehensive investigation and compliance reporting.
- **Structured format**: Use JSON or another structured format for all log entries. This enables automated parsing, indexing, and analysis.
- **Minimal latency**: Logging should not block authentication or authorization operations. Use asynchronous logging (message queues, background workers) to decouple logging from request processing.

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
