# Sketchnote Prompt: Chapter 06 - Session Management and State

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
- Title: Session Management and State
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
- Understand the fundamental concepts of session management and stateful authentication in web and mobile applications
- Identify architectural patterns for session storage, validation, and lifecycle management
- Recognize common session-related vulnerabilities including fixation, hijacking, and replay attacks
- Implement secure session management controls aligned with industry standards
- Design and evaluate session management mechanisms from both developer and security perspectives

## Common Findings To Visualize

## Secure Guidance To Visualize
- Use connection pooling to distributed store
- Implement circuit breaker for store unavailability
- Set appropriate TTL on cache entries
- Monitor store latency and capacity
- Pros: Automatic inclusion in requests, browser-native support, can be HttpOnly

## Output Requirement
- Produce one landscape diagram suitable for insertion into a DOCX chapter.
- Keep labels short enough to read when printed.
- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.
