# Sketchnote Prompt: Chapter 05 - Common Findings

Create one focused sketchnote-style diagram for this handbook section.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box

## Chapter Context
- Chapter: JSON Web Tokens and Token Management
- Section: Common Findings
- Source stage: final

## Concepts To Visualize
- Splits the token and base64-decodes components without calling a valid
- Uses jwt.decode without the verify parameter set to True
- Catches and ignores signature verification exceptions
- Uses hardcoded or test keys in production
- options={'verify exp': False} or similar disable flags
- Absence of expiration time checks

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: risk_matrix.
- Show relationships between concepts, risks, and controls.
