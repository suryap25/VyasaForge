Create a clean, hand-drawn sketchnote-style architecture diagram plan.

You are not drawing the image. You are creating a compact JSON plan for a deterministic renderer.

STYLE INTENT:
- Soft pastel color palette:
  - orange = core logic / processing
  - blue = integrations / external services / users
  - green = storage / databases / telemetry
  - yellow = security / governance / control plane
  - grey = infrastructure / execution environment
- Rounded rectangles with slightly imperfect sketch-style outlines.
- Minimal black icons.
- Smooth arrows with rounded edges.
- White or very light background.
- Subtle depth, no heavy shadows.
- Presentation-quality aesthetics.

LAYOUT INTENT:
- Primary flow moves left to right.
- Top layer is security / governance / control plane.
- Middle layer is application / processing / AI or agentic systems.
- Bottom layer is storage / persistence / telemetry.
- Right side is execution systems / external integrations.
- Keep spacing balanced and uncluttered.
- Avoid excessive text inside boxes.

DIAGRAM PRINCIPLES:
- Prioritize architectural clarity over implementation detail.
- Emphasize trust boundaries and data flow.
- Group components by responsibility.
- Highlight control plane vs data plane where relevant.
- Minimize arrow crossing.
- Use spacing and hierarchy to communicate importance.
- Keep the diagram understandable at a glance.
- Simplify noisy implementation details.

INPUTS:
- Chapter title
- Diagram type
- Section name
- Source text

TASK:
Analyze the inputs and identify:
- Core concepts/services
- Workflows or orchestration loops
- APIs and integrations
- Security layers and gateways
- Storage/databases/logs
- Users and external systems
- Infrastructure/runtime environments
- Request, data, authentication, authorization, risk, and telemetry flows

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
- Use 6 to 10 components.
- Use 5 to 10 flows.
- Component labels must be short enough to fit inside boxes.
- Use only the allowed layer, icon, kind, and diagram_type values.
- For attack_flow, include both a legitimate path and an attack/risk path.
- Do not include raw paragraphs, code, config, citations, or long explanations.
