# Sketchnote Prompt: Chapter 10 - Common Findings

Create one focused sketchnote-style diagram for this handbook section.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box

## Chapter Context
- Chapter: Multi-Factor Authentication and Step-Up Authentication
- Section: Common Findings
- Source stage: final

## Concepts To Visualize
- Implement explicit validation that rejects empty, null, or whitespace-
- Use allowlist validation for expected code formats e.g., 6-digit numer
- Never use conditional logic that skips MFA validation based on factor 
- Return consistent error messages for all validation failures to avoid 
- Maintain a server-side record of consumed codes with timestamps
- Invalidate codes immediately after successful verification

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: risk_matrix.
- Show relationships between concepts, risks, and controls.
