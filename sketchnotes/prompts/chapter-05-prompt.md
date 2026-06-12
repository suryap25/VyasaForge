# Sketchnote Prompt: Chapter 05 - JSON Web Tokens and Token Management

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
- Title: JSON Web Tokens and Token Management
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
- Understand the structure, composition, and cryptographic properties of JSON Web Tokens (JWTs)
- Identify security risks inherent in JWT implementation and token lifecycle management
- Design and implement secure token generation, validation, and revocation strategies
- Evaluate JWT claims and signature verification mechanisms from an AppSec perspective
- Conduct security assessments of JWT implementations in web and mobile applications

## Common Findings To Visualize
- Splits the token and base64-decodes components without calling a validation function
- Uses `jwt.decode()` without the `verify` parameter set to `True`
- Catches and ignores signature verification exceptions
- Uses hardcoded or test keys in production
- `options={'verify_exp': False}` or similar disable flags

## Secure Guidance To Visualize

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
