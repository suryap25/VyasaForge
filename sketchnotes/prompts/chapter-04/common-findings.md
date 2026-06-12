# Sketchnote Prompt: Chapter 04 - Common Findings

Create one focused sketchnote-style diagram for this handbook section.

## Visual Style
- White background
- Hand-drawn black outlines
- Rounded boxes with soft blue, orange, green, and yellow accents
- Clear arrows for normal flow
- Red dashed arrows for risk or attack paths
- Minimal readable text inside each box

## Chapter Context
- Chapter: OpenID Connect and User Information
- Section: Common Findings
- Source stage: final

## Concepts To Visualize
- Token Validation Failures Finding : ID tokens accepted without signatu
- Risk : Attackers forge ID tokens to impersonate any user, bypassing au
- Example : Detection : Review token handling code for jwt.decode withou
- Check for verification options set to false.
- Attempt to modify token payload and observe if application accepts it.
- Remediation : Always use jwt.verify with the IdP's public key.

## Output Requirement
- Produce one landscape diagram suitable for insertion immediately after this section heading.
- Keep labels short enough to read in a DOCX page.
- Use diagram type: risk_matrix.
- Show relationships between concepts, risks, and controls.
