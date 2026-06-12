# Sketchnote Prompt: Chapter 03 - AppSec Lens

Create one focused sketchnote-style diagram for this handbook section.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box

## Chapter Context
- Chapter: OAuth 2.0 Protocol and Flows
- Section: AppSec Lens
- Source stage: final

## Concepts To Visualize
- Use PKCE for all public clients
- Validate redirect URIs strictly exact match, not substring matching
- Use short-lived authorization codes 60 seconds or less
- Implement state parameter validation discussed below
- Generate a cryptographically random state parameter for each authoriza
- Store the state parameter in a session or secure cookie

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: attack_path.
- Show relationships between concepts, risks, and controls.
