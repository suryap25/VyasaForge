# Sketchnote Prompt: Chapter 05 - AppSec Lens

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
- Section: AppSec Lens
- Source stage: final

## Concepts To Visualize
- Short token lifetimes 15-30 minutes
- Token blacklist: Maintain a list of revoked tokens reduces statelessne
- Token versioning: Include a version number in the token; increment on 
- Distributed cache: Store revocation information in Redis or similar fo
- LocalStorage : Vulnerable to XSS attacks; JavaScript can access and ex
- SessionStorage : Similar XSS vulnerability

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: attack_path.
- Show relationships between concepts, risks, and controls.
