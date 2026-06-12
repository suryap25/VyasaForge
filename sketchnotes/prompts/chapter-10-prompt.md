# Sketchnote Prompt: Chapter 10 - Multi-Factor Authentication and Step-Up Authentication

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
- Title: Multi-Factor Authentication and Step-Up Authentication
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
- Explain the fundamental differences between multi-factor authentication (MFA) and step-up authentication
- Design MFA architectures that balance security with user experience
- Implement MFA mechanisms across web and mobile applications
- Identify and remediate common MFA implementation vulnerabilities
- Evaluate MFA solutions from an application security perspective

## Common Findings To Visualize
- Implement explicit validation that rejects empty, null, or whitespace-only factor values
- Use allowlist validation for expected code formats (e.g., 6-digit numeric codes)
- Never use conditional logic that skips MFA validation based on factor presence
- Return consistent error messages for all validation failures to avoid information disclosure
- Maintain a server-side record of consumed codes with timestamps

## Secure Guidance To Visualize
- Never use related factors (password + security question, password + PIN sent to same phone)
- Verify that factors come from different categories (knowledge, possession, inherence)
- Evaluate the practical independence of factors in your threat model
- Consider attack chains: if an attacker compromises one factor, can they derive the other?
- Store MFA challenge state server-side, not in client-side tokens

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
