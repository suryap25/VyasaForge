Create a compact Visio-style technical architecture diagram plan.

You are not drawing the image. You are creating valid JSON for a deterministic
Graphviz renderer.

STYLE INTENT:
- Clean technical diagram, closer to Visio than sketchnote.
- Light pastel fills with strong readable outlines.
- Short labels only.
- Clear left-to-right flow.
- Use grouped layers for users, security, processing, storage, integrations,
  infrastructure, risk, and outcome.
- Use color-coded arrows:
  - normal = black
  - trust/config = blue
  - control/success = green
  - risk/attack = red dashed
- The renderer numbers arrows and places each flow label in a legend. Keep flow
  labels short and meaningful.

DIAGRAM PRINCIPLES:
- Prioritize architectural clarity over decoration.
- Show trust boundaries and data/control flow where applicable.
- Keep diagrams readable inside a DOCX.
- Avoid noisy implementation details.
- Avoid raw code, citations, long prose, and repeated labels.

INPUTS:
- Chapter title
- Diagram type
- Section name
- Source text

OUTPUT:
Return only valid JSON. No Markdown. No explanation.

JSON schema:
{
  "title": "short diagram title",
  "diagram_type": "architecture_diagram | concept_diagram | attack_flow | control_map | takeaway_map | chapter_map",
  "trust_boundaries": ["short boundary label"],
  "components": [
    {
      "id": "stable_snake_case_id",
      "label": "1 to 4 words",
      "layer": "user | security | processing | storage | integration | infrastructure | risk | outcome",
      "icon": "user | lock | shield | db | key | gear | alert | box"
    }
  ],
  "flows": [
    {
      "from": "component_id",
      "to": "component_id",
      "label": "optional 1 to 3 words",
      "kind": "normal | trust | control | risk"
    }
  ],
  "callouts": ["optional short teaching note"]
}

RULES:
- Use 5 to 9 components.
- Use 4 to 9 flows.
- Flow labels should describe the meaning of the numbered arrow in 1 to 3 words.
- Component labels must fit inside boxes.
- Use only the allowed layer, icon, kind, and diagram_type values.
- For attack_flow, include both a legitimate path and an attack/risk path.
- For control_map, place controls around the protected asset.
- For takeaway_map, create a simple hub-and-spoke summary.
