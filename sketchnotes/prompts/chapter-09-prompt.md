# Sketchnote Prompt: Chapter 09 - Authorization Strategies and Access Control

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
- Title: Authorization Strategies and Access Control
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
- Distinguish between authentication and authorization, and explain why both are essential to application security
- Identify and evaluate different authorization models (RBAC, ABAC, PBAC) for your application architecture
- Design and implement role-based and attribute-based access control systems that scale with application complexity
- Recognize common authorization vulnerabilities including broken access control, privilege escalation, and insecure direct object references
- Apply authorization testing techniques to validate access control enforcement across your application

## Common Findings To Visualize

## Secure Guidance To Visualize
- Use **RBAC** for applications with well-defined roles and relatively static permissions. RBAC is simple to implement and understand, making it suitable for traditional applications with clear organizational hierarchies.
- Use **ABAC** for applications requiring fine-grained, context-dependent access control. ABAC is necessary when authorization depends on multiple factors (user attributes, resource attributes, time, location, etc.) that don't fit neatly into roles.
- Use **PBAC** for applications where permissions are highly granular and don't align with roles. PBAC is useful for systems where users need specific, ad-hoc permissions that don't fit into predefined roles.
- Use **hybrid approaches** combining RBAC for coarse-grained access and ABAC for fine-grained decisions. Most production systems benefit from this approach.
- **Centralized authorization** is appropriate for applications where consistent policy enforcement is critical and performance requirements allow for centralized decision-making. Use centralized authorization when policies must be synchronized across multiple services or when audit requirements demand centralized logging.

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
