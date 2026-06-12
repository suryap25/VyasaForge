# Sketchnote Prompt: Chapter 07 - Developer Lens

Create one focused sketchnote-style diagram for this handbook section.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box

## Chapter Context
- Chapter: Web Application Authentication Implementation
- Section: Developer Lens
- Source stage: final

## Concepts To Visualize
- Always verify the token signature using the correct secret key
- Check token expiration before accepting the token
- Use appropriate algorithms HS256 for symmetric keys, RS256 for asymmet
- Never trust the token payload without verification
- Store the secret key securely in environment variables, not in code
- Use short expiration times 15 minutes to 1 hour for access tokens

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: implementation_flow.
- Show relationships between concepts, risks, and controls.
