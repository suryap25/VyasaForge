"""Sketchnote prompt and local SVG generation."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

from src.diagrams import DiagramArtifact, write_diagram_registry
from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS

PROMPT_DIR = Path("sketchnotes/prompts")
IMAGE_DIR = Path("sketchnotes/images")
SPEC_DIR = Path("sketchnotes/specs")
SKETCHNOTE_PLAN_PROMPT = Path("prompts/sketchnote_plan.md")
SUPPORTED_STAGES = {"drafts", "reviewed", "final"}
SECTION_SKETCHNOTE_SECTIONS = [
    "Conceptual Foundation",
    "Architecture Perspective",
    "AppSec Lens",
    "Secure Design Guidance",
    "Key Takeaways",
]
SECTION_DIAGRAM_TYPES = {
    "Conceptual Foundation": "concept_diagram",
    "Architecture Perspective": "architecture_diagram",
    "AppSec Lens": "attack_flow",
    "Secure Design Guidance": "control_map",
    "Key Takeaways": "takeaway_map",
    "Sketchnote Placeholder": "chapter_map",
}

PALETTE = {
    "blue": ("#eef6ff", "#1e66b1"),
    "orange": ("#fff4df", "#df7c18"),
    "green": ("#eef9ea", "#2e7d32"),
    "yellow": ("#fef8df", "#d9a300"),
    "purple": ("#f5f0ff", "#5e3c99"),
    "red": ("#fff0ef", "#d71920"),
}


@dataclass(frozen=True)
class DiagramNode:
    """One semantic visual node."""

    node_id: str
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str
    icon: str = "box"


@dataclass(frozen=True)
class DiagramFlow:
    """One semantic arrow between nodes."""

    source: str
    target: str
    kind: str = "normal"
    label: str | None = None


@dataclass(frozen=True)
class DiagramGroup:
    """One grouped visual container."""

    label: str
    x: int
    y: int
    w: int
    h: int
    kind: str = "container"


@dataclass(frozen=True)
class DiagramSpec:
    """Semantic diagram contract consumed by renderers."""

    title: str
    diagram_type: str
    nodes: list[DiagramNode]
    flows: list[DiagramFlow]
    groups: list[DiagramGroup]
    legend: list[tuple[str, str]]
    callouts: list[str] | None = None


ALLOWED_LAYERS = {"user", "security", "processing", "storage", "integration", "infrastructure", "risk", "outcome"}
ALLOWED_ICONS = {"user", "lock", "shield", "db", "key", "gear", "alert", "box"}
ALLOWED_FLOW_KINDS = {"normal", "trust", "control", "risk"}
ALLOWED_DIAGRAM_TYPES = {"architecture_diagram", "concept_diagram", "attack_flow", "control_map", "takeaway_map", "chapter_map"}
LAYER_COLORS = {
    "user": "blue",
    "security": "yellow",
    "processing": "orange",
    "storage": "green",
    "integration": "blue",
    "infrastructure": "purple",
    "risk": "red",
    "outcome": "green",
}


def prompt_path_for(chapter: int) -> Path:
    """Return the sketchnote prompt path for a chapter."""
    return PROMPT_DIR / f"chapter-{chapter:02d}-prompt.md"


def image_path_for(chapter: int) -> Path:
    """Return the sketchnote image path for a chapter."""
    return IMAGE_DIR / f"chapter-{chapter:02d}.svg"


def png_path_for(chapter: int) -> Path:
    """Return the DOCX-compatible PNG path for a chapter sketchnote."""
    return IMAGE_DIR / f"chapter-{chapter:02d}.png"


def slugify(value: str) -> str:
    """Return a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def section_prompt_path_for(chapter: int, section: str) -> Path:
    """Return the sketchnote prompt path for one chapter section."""
    return PROMPT_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.md"


def section_image_path_for(chapter: int, section: str) -> Path:
    """Return the sketchnote SVG path for one chapter section."""
    return IMAGE_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.svg"


def section_png_path_for(chapter: int, section: str) -> Path:
    """Return the DOCX-compatible PNG path for one chapter section."""
    return IMAGE_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.png"


def spec_path_for(chapter: int) -> Path:
    """Return the planned sketchnote spec path for a chapter."""
    return SPEC_DIR / f"chapter-{chapter:02d}.json"


def section_spec_path_for(chapter: int, section: str) -> Path:
    """Return the planned sketchnote spec path for one section."""
    return SPEC_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.json"


def preferred_image_path_for(chapter: int) -> Path:
    """Return the preferred image path for DOCX compilation."""
    png_path = png_path_for(chapter)
    return png_path if png_path.exists() else image_path_for(chapter)


def preferred_section_image_path_for(chapter: int, section: str) -> Path:
    """Return the preferred section image path for DOCX compilation."""
    png_path = section_png_path_for(chapter, section)
    return png_path if png_path.exists() else section_image_path_for(chapter, section)


def section_sketchnote_sections() -> list[str]:
    """Return the chapter sections that get dedicated sketchnotes."""
    return list(SECTION_SKETCHNOTE_SECTIONS)


def diagram_type_for_section(section: str) -> str:
    """Return the preferred visual diagram type for a chapter section."""
    return SECTION_DIAGRAM_TYPES.get(section, "concept_map")


def chapter_path_for(chapter: int, stage: str) -> Path:
    """Return the chapter path for a supported stage."""
    if stage not in SUPPORTED_STAGES:
        available = ", ".join(sorted(SUPPORTED_STAGES))
        raise ValueError(f"Unknown sketchnote stage '{stage}'. Available stages: {available}")
    metadata = resolve_chapter(chapter)
    if stage == "drafts":
        return metadata.draft_path
    if stage == "reviewed":
        return metadata.reviewed_path
    return metadata.final_path


def _chapter_text(chapter: int, stage: str) -> str:
    path = chapter_path_for(chapter, stage)
    if not path.exists():
        raise FileNotFoundError(f"Missing {stage} chapter file: {path}")
    return path.read_text(encoding="utf-8")


def _section_text(markdown: str, section: str) -> str:
    pattern = rf"(?ims)^##\s+{re.escape(section)}\s*$(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, markdown)
    return match.group(1).strip() if match else ""


def _headings(markdown: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", markdown)]


def _short_bullets(text: str, limit: int = 5) -> list[str]:
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        if len(bullets) >= limit:
            break
    return bullets


def _plain_text(markdown: str) -> str:
    text = re.sub(r"(?ms)^```.*?^```", " ", markdown)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>\[\]()]|https?://\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_label(label: str) -> str:
    """Remove Markdown punctuation from a short SVG label."""
    cleaned = re.sub(r"`([^`]+)`", r"\1", label)
    cleaned = re.sub(r"[*_#>\[\]()]|https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "concept"


def _concept_labels(text: str, fallback: list[str], limit: int = 5) -> list[str]:
    bullets = _short_bullets(text, limit=limit)
    if bullets:
        labels = [_clean_label(label)[:70] for label in bullets[:limit]]
        while len(labels) < limit:
            labels.append(fallback[len(labels) % len(fallback)])
        return labels[:limit]

    plain = _plain_text(text)
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", plain) if sentence.strip()]
    labels = [_clean_label(sentence)[:70] for sentence in sentences[:limit]]
    while len(labels) < limit:
        labels.append(fallback[len(labels) % len(fallback)])
    return labels[:limit]


def _domain_fallbacks(title: str, diagram_type: str) -> list[str]:
    """Return concise visual labels for common AppSec handbook topics."""
    topic = title.casefold()
    if "oauth" in topic:
        base = ["User", "Client App", "Authorization Server", "Token", "Resource API", "Scope Check", "Protected Data"]
    elif "openid" in topic or "oidc" in topic:
        base = ["User", "Client App", "Identity Provider", "ID Token", "UserInfo", "Session", "Claims"]
    elif "jwt" in topic or "token" in topic:
        base = ["Issuer", "JWT Claims", "Signature", "JWKS", "API", "Validation", "Revocation Risk"]
    elif "session" in topic:
        base = ["Browser", "Session Cookie", "App", "Session Store", "Logout", "Fixation Risk", "Secure Flags"]
    elif "multi-factor" in topic or "mfa" in topic:
        base = ["User", "Password", "Second Factor", "Risk Signal", "Step-Up", "Recovery", "Bypass Risk"]
    elif "authorization" in topic or "authentication" in topic or "identity" in topic:
        base = ["User", "Authentication", "Identity", "Authorization", "Policy Check", "Protected Resource", "Access Decision"]
    else:
        base = ["User", "Request", "Trust Check", "Policy", "Application", "Control", "Outcome"]

    if diagram_type == "attack_flow":
        return ["Normal Request", "Policy Check", "Resource Access", "Tampered ID", "Missing AuthZ", "Data Exposure", "Detect"]
    if diagram_type == "control_map":
        return ["Secure Design", "Least Privilege", "Strong Identity", "Session Safety", "Audit Logs", "Monitoring", "Review"]
    if diagram_type == "takeaway_map":
        return ["What Matters", "Trust Boundary", "Common Failure", "Secure Default", "Test Strategy", "Operational Signal", "Key Takeaway"]
    return base


def _semantic_labels(title: str, body: str, diagram_type: str, limit: int = 7) -> list[str]:
    """Return visual labels that describe the topic rather than the chapter structure."""
    fallback = _domain_fallbacks(title, diagram_type)
    labels = _concept_labels(body, fallback=fallback, limit=limit)
    generic_terms = {section.casefold() for section in REQUIRED_SECTIONS}
    cleaned = [
        label
        for label in labels
        if label.casefold() not in generic_terms and len(label.split()) <= 5 and len(label) <= 36
    ]
    if len(cleaned) < max(3, limit // 2):
        cleaned = []
    while len(cleaned) < limit:
        cleaned.append(fallback[len(cleaned) % len(fallback)])
    return cleaned[:limit]


def _short_label(value: str, fallback: str = "Concept") -> str:
    """Return a compact label suitable for a diagram card."""
    cleaned = _clean_label(value)
    words = cleaned.split()
    if not words:
        return fallback
    return " ".join(words[:4])[:34]


def _stable_id(value: str, fallback: str) -> str:
    """Return a renderer-safe component id."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or fallback


def _extract_json_object(text: str) -> dict:
    """Extract the first JSON object from an LLM response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Sketchnote plan must be a JSON object.")
    return parsed


def _sanitize_plan(raw_plan: dict, title: str, diagram_type: str) -> dict:
    """Validate and normalize a sketchnote plan from the LLM."""
    plan_type = raw_plan.get("diagram_type") if raw_plan.get("diagram_type") in ALLOWED_DIAGRAM_TYPES else diagram_type
    components = raw_plan.get("components", [])
    if not isinstance(components, list):
        components = []

    sanitized_components = []
    seen_ids: set[str] = set()
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            continue
        label = _short_label(str(component.get("label", "")), fallback=f"Concept {index + 1}")
        component_id = _stable_id(str(component.get("id") or label), f"node_{index + 1}")
        while component_id in seen_ids:
            component_id = f"{component_id}_{index + 1}"
        seen_ids.add(component_id)
        layer = str(component.get("layer", "processing")).lower()
        if layer not in ALLOWED_LAYERS:
            layer = "processing"
        icon = str(component.get("icon", "box")).lower()
        if icon not in ALLOWED_ICONS:
            icon = "box"
        sanitized_components.append(
            {
                "id": component_id,
                "label": label,
                "layer": layer,
                "icon": icon,
            }
        )
        if len(sanitized_components) >= 10:
            break

    if len(sanitized_components) < 6:
        return {}

    ids = {component["id"] for component in sanitized_components}
    flows = raw_plan.get("flows", [])
    if not isinstance(flows, list):
        flows = []
    sanitized_flows = []
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        source = _stable_id(str(flow.get("from", "")), "")
        target = _stable_id(str(flow.get("to", "")), "")
        if source not in ids or target not in ids or source == target:
            continue
        kind = str(flow.get("kind", "normal")).lower()
        if kind not in ALLOWED_FLOW_KINDS:
            kind = "normal"
        sanitized_flows.append(
            {
                "from": source,
                "to": target,
                "label": _short_label(str(flow.get("label", "")), fallback="") if flow.get("label") else None,
                "kind": kind,
            }
        )
        if len(sanitized_flows) >= 10:
            break

    if len(sanitized_flows) < 4:
        for left, right in zip(sanitized_components, sanitized_components[1:]):
            sanitized_flows.append({"from": left["id"], "to": right["id"], "label": None, "kind": "normal"})
            if len(sanitized_flows) >= 6:
                break

    trust_boundaries = raw_plan.get("trust_boundaries", [])
    if not isinstance(trust_boundaries, list):
        trust_boundaries = []

    callouts = raw_plan.get("callouts", [])
    if not isinstance(callouts, list):
        callouts = []

    return {
        "title": _short_label(title, fallback=title)[:60],
        "diagram_type": plan_type,
        "trust_boundaries": [_short_label(str(item), fallback="Trust Boundary") for item in trust_boundaries[:2]],
        "components": sanitized_components,
        "flows": sanitized_flows,
        "callouts": [_short_label(str(item), fallback="Key Idea") for item in callouts[:2]],
    }


def _plan_prompt() -> str:
    if not SKETCHNOTE_PLAN_PROMPT.exists():
        raise FileNotFoundError(f"Missing sketchnote planning prompt: {SKETCHNOTE_PLAN_PROMPT}")
    return SKETCHNOTE_PLAN_PROMPT.read_text(encoding="utf-8")


def _planned_sketchnote(
    chapter: int,
    title: str,
    diagram_type: str,
    section: str,
    body: str,
    output_path: Path,
) -> dict:
    """Ask the planner model for a sketchnote diagram plan and save it."""
    from src import llm_gateway

    content = body[:9000]
    messages = [
        {"role": "system", "content": _plan_prompt()},
        {
            "role": "user",
            "content": "\n".join(
                [
                    f"Chapter title: {title}",
                    f"Diagram type: {diagram_type}",
                    f"Section: {section}",
                    "",
                    "Source text:",
                    content,
                ]
            ),
        },
    ]
    response = llm_gateway.call_llm(role="planner", messages=messages, chapter=chapter)
    plan = _sanitize_plan(_extract_json_object(response), title=title, diagram_type=diagram_type)
    if not plan:
        raise ValueError("Sketchnote planner returned too few usable components.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    output_path.with_suffix(".failed.txt").unlink(missing_ok=True)
    return plan


def _layer_positions(plan: dict) -> dict[str, tuple[int, int, int, int]]:
    """Return node positions for a layered sketchnote plan."""
    components = plan["components"]
    by_layer: dict[str, list[dict]] = {layer: [] for layer in ALLOWED_LAYERS}
    for component in components:
        by_layer.setdefault(component["layer"], []).append(component)

    positions: dict[str, tuple[int, int, int, int]] = {}
    component_by_id = {component["id"]: component for component in components}
    order_scores: dict[str, int] = {}
    queue = [component["id"] for component in components if component["layer"] == "user"]
    if not queue and components:
        queue = [components[0]["id"]]
    for item in queue:
        order_scores[item] = 0
    while queue:
        current = queue.pop(0)
        current_score = order_scores[current]
        for flow in plan.get("flows", []):
            if flow["from"] == current and flow["to"] not in order_scores:
                order_scores[flow["to"]] = current_score + 1
                queue.append(flow["to"])
    for index, component in enumerate(components):
        order_scores.setdefault(component["id"], index + 10)

    def ordered(layer: str) -> list[dict]:
        return sorted(by_layer.get(layer, []), key=lambda item: (order_scores.get(item["id"], 999), item["label"]))

    def place_row(layer: str, y: int, x_start: int, x_end: int, w: int, h: int) -> None:
        items = ordered(layer)
        if not items:
            return
        if len(items) == 1:
            xs = [(x_start + x_end - w) // 2]
        else:
            gap = (x_end - x_start - w) / max(1, len(items) - 1)
            xs = [int(x_start + gap * index) for index in range(len(items))]
        for item, x in zip(items, xs):
            positions[item["id"]] = (x, y, w, h)

    def related_x(component_id: str, w: int, default_x: int) -> int:
        component = component_by_id.get(component_id, {})
        label = str(component.get("label", "")).casefold()
        positioned_processing = [
            (item_id, rect)
            for item_id, rect in positions.items()
            if component_by_id.get(item_id, {}).get("layer") == "processing"
        ]
        if positioned_processing and ("author" in label or "policy" in label):
            x, _y, ow, _h = max(positioned_processing, key=lambda item: item[1][0])[1]
            return max(280, min(1220 - w, x + ow // 2 - w // 2))
        if positioned_processing and ("auth" in label or "identity" in label):
            x, _y, ow, _h = min(positioned_processing, key=lambda item: item[1][0])[1]
            return max(280, min(1220 - w, x + ow // 2 - w // 2))
        centers = []
        for flow in plan.get("flows", []):
            other_id = None
            if flow["from"] == component_id:
                other_id = flow["to"]
            elif flow["to"] == component_id:
                other_id = flow["from"]
            if other_id and other_id in positions:
                x, _y, ow, _h = positions[other_id]
                centers.append(x + ow // 2)
        if not centers:
            return default_x
        center = sum(centers) // len(centers)
        return max(280, min(1220 - w, center - w // 2))

    def place_support_layer(layer: str, y: int, w: int, h: int) -> None:
        items = ordered(layer)
        if not items:
            return
        count = len(items)
        defaults = [int(300 + index * ((920 - w) / max(1, count - 1))) for index in range(count)]
        candidate_positions = [
            (related_x(item["id"], w, defaults[index]), item)
            for index, item in enumerate(items)
        ]
        last_x = 260
        for x, item in sorted(candidate_positions, key=lambda pair: pair[0]):
            x = max(last_x + 28, x)
            x = min(x, 1280 - w)
            positions[item["id"]] = (x, y, w, h)
            last_x = x + w

    place_row("processing", 350, 330, 1220, 220, 145)
    place_row("user", 375, 70, 240, 190, 130)
    place_row("integration", 375, 1340, 1530, 190, 130)
    place_row("outcome", 375, 1340, 1530, 190, 130)
    place_support_layer("security", 115, 190, 120)
    place_support_layer("storage", 655, 230, 120)
    place_support_layer("infrastructure", 655, 230, 120)

    for layer, x in (("risk", 70),):
        items = ordered(layer)
        for index, item in enumerate(items):
            y = 570 + (index * 130)
            positions[item["id"]] = (x, y, 190, 130)

    missing = [component for component in components if component["id"] not in positions]
    for index, component in enumerate(missing):
        positions[component["id"]] = (390 + (index % 3) * 300, 335 + (index // 3) * 185, 220, 135)

    return positions


def spec_from_plan(plan: dict, fallback_type: str) -> DiagramSpec:
    """Convert a planned sketchnote JSON object into a renderable diagram spec."""
    positions = _layer_positions(plan)
    component_by_id = {component["id"]: component for component in plan["components"]}
    nodes = [
        DiagramNode(
            node_id=component["id"],
            label=component["label"],
            x=positions[component["id"]][0],
            y=positions[component["id"]][1],
            w=positions[component["id"]][2],
            h=positions[component["id"]][3],
            color=LAYER_COLORS.get(component["layer"], "orange"),
            icon=component["icon"],
        )
        for component in plan["components"]
    ]
    node_ids = {node.node_id for node in nodes}
    if plan.get("diagram_type") in {"chapter_map", "architecture_diagram"}:
        flows = _normalized_architecture_flows(plan, nodes, component_by_id)
    else:
        flows = [
            DiagramFlow(
                source=flow["from"],
                target=flow["to"],
                kind=flow["kind"],
                label=flow.get("label"),
            )
            for flow in plan["flows"]
            if flow["from"] in node_ids and flow["to"] in node_ids
        ]
    groups = []
    processing_nodes = [node for node in nodes if 285 <= node.x <= 1220 and 250 <= node.y <= 520]
    if processing_nodes:
        label = (plan.get("trust_boundaries") or ["Application Trust Boundary"])[0]
        groups.append(DiagramGroup(label, 300, 260, 960, 360, "trust"))
    if plan.get("diagram_type") == "attack_flow":
        groups = [
            DiagramGroup("legitimate path", 320, 165, 960, 260, "container"),
            DiagramGroup("attack/risk path", 320, 520, 960, 255, "risk"),
        ]
    spec_title = str(plan.get("title") or "Sketchnote").replace("_", " ")
    if spec_title.casefold().endswith(" fun"):
        spec_title = spec_title[:-4]

    return DiagramSpec(
        title=spec_title,
        diagram_type=plan.get("diagram_type") or fallback_type,
        nodes=nodes,
        flows=flows,
        groups=groups,
        legend=_legend(),
        callouts=[_polish_callout(str(callout)) for callout in (plan.get("callouts") or [])] or None,
    )


def _nearest_node(source: DiagramNode, candidates: list[DiagramNode]) -> DiagramNode | None:
    """Return the candidate whose center is closest to source horizontally."""
    if not candidates:
        return None
    source_cx = source.x + source.w // 2
    return min(candidates, key=lambda node: abs((node.x + node.w // 2) - source_cx))


def _polish_callout(value: str) -> str:
    """Return a concise teaching callout."""
    lowered = value.casefold()
    if "authentication" in lowered:
        return "Authentication: who are you?"
    if "authorization" in lowered:
        return "Authorization: what can you do?"
    return value


def _normalized_architecture_flows(
    plan: dict,
    nodes: list[DiagramNode],
    component_by_id: dict[str, dict],
) -> list[DiagramFlow]:
    """Simplify planned architecture flows into an ordered teaching diagram."""
    nodes_by_layer: dict[str, list[DiagramNode]] = {}
    for node in nodes:
        layer = component_by_id.get(node.node_id, {}).get("layer", "processing")
        nodes_by_layer.setdefault(layer, []).append(node)
    for layer_nodes in nodes_by_layer.values():
        layer_nodes.sort(key=lambda node: node.x)

    flows: list[DiagramFlow] = []
    users = nodes_by_layer.get("user", [])
    processing = nodes_by_layer.get("processing", [])
    security = nodes_by_layer.get("security", [])
    storage = nodes_by_layer.get("storage", []) + nodes_by_layer.get("infrastructure", [])
    outcomes = nodes_by_layer.get("outcome", []) + nodes_by_layer.get("integration", [])
    risks = nodes_by_layer.get("risk", [])

    if users and processing:
        flows.append(DiagramFlow(users[0].node_id, processing[0].node_id, "normal", "request"))

    for index, (left, right) in enumerate(zip(processing, processing[1:])):
        label = "decision" if index == len(processing) - 2 else "claims"
        flows.append(DiagramFlow(left.node_id, right.node_id, "normal", label))

    if processing and outcomes:
        flows.append(DiagramFlow(processing[-1].node_id, outcomes[0].node_id, "control", "access"))

    for control in security:
        target = _nearest_node(control, processing)
        if target is not None:
            label = "policy" if "author" in control.label.casefold() or "policy" in control.label.casefold() else "identity"
            flows.append(DiagramFlow(control.node_id, target.node_id, "trust", label))

    for data_node in storage:
        target = _nearest_node(data_node, processing)
        if target is not None:
            label = "logs" if "audit" in data_node.label.casefold() or "log" in data_node.label.casefold() else "lookup"
            flows.append(DiagramFlow(target.node_id, data_node.node_id, "control", label))

    if risks:
        target = storage[-1] if storage else (processing[-1] if processing else None)
        if target is not None:
            flows.append(DiagramFlow(risks[0].node_id, target.node_id, "risk", None))

    return flows


def _legend() -> list[tuple[str, str]]:
    return [
        ("normal", "normal flow"),
        ("trust", "trust/config"),
        ("control", "control/success"),
        ("risk", "attack/risk"),
    ]


def _flow_color(kind: str) -> tuple[str, bool]:
    if kind == "trust":
        return ("#1e66b1", False)
    if kind == "control":
        return ("#2e7d32", False)
    if kind == "risk":
        return ("#d71920", True)
    return ("#111111", False)


def _node_lookup(spec: DiagramSpec) -> dict[str, DiagramNode]:
    return {node.node_id: node for node in spec.nodes}


def _flow_points(source: DiagramNode, target: DiagramNode) -> tuple[int, int, int, int]:
    sx = source.x + source.w
    sy = source.y + source.h // 2
    tx = target.x
    ty = target.y + target.h // 2
    if abs((source.y + source.h // 2) - (target.y + target.h // 2)) > abs(source.x - target.x):
        sx = source.x + source.w // 2
        tx = target.x + target.w // 2
        if source.y < target.y:
            sy = source.y + source.h
            ty = target.y
        else:
            sy = source.y
            ty = target.y + target.h
    return sx, sy, tx, ty


def _flow_route_points(source: DiagramNode, target: DiagramNode) -> list[tuple[int, int]]:
    """Return ordered elbow-route points for a clean sketchnote connector."""
    source_cx = source.x + source.w // 2
    source_cy = source.y + source.h // 2
    target_cx = target.x + target.w // 2
    target_cy = target.y + target.h // 2

    if source.y + source.h < target.y:
        start = (source_cx, source.y + source.h)
        end = (target_cx, target.y)
        mid_y = (start[1] + end[1]) // 2
        return [start, (start[0], mid_y), (end[0], mid_y), end]
    if target.y + target.h < source.y:
        start = (source_cx, source.y)
        end = (target_cx, target.y + target.h)
        mid_y = (start[1] + end[1]) // 2
        return [start, (start[0], mid_y), (end[0], mid_y), end]
    if source.x < target.x:
        start = (source.x + source.w, source_cy)
        end = (target.x, target_cy)
    else:
        start = (source.x, source_cy)
        end = (target.x + target.w, target_cy)
    mid_x = (start[0] + end[0]) // 2
    return [start, (mid_x, start[1]), (mid_x, end[1]), end]


def _svg_path_from_route(points: list[tuple[int, int]]) -> str:
    """Return a rounded-looking SVG path for route points."""
    if len(points) < 2:
        return ""
    commands = [f"M{points[0][0]},{points[0][1]}"]
    for point in points[1:]:
        commands.append(f"L{point[0]},{point[1]}")
    return " ".join(commands)


def _route_label_point(points: list[tuple[int, int]]) -> tuple[int, int]:
    """Return a readable label position along a routed connector."""
    if len(points) < 2:
        return points[0] if points else (0, 0)
    segment_lengths = []
    total = 0
    for left, right in zip(points, points[1:]):
        length = abs(right[0] - left[0]) + abs(right[1] - left[1])
        segment_lengths.append(length)
        total += length
    halfway = total / 2
    walked = 0
    for (left, right), length in zip(zip(points, points[1:]), segment_lengths):
        if walked + length >= halfway:
            if length == 0:
                return left
            ratio = (halfway - walked) / length
            return (
                int(left[0] + (right[0] - left[0]) * ratio),
                int(left[1] + (right[1] - left[1]) * ratio),
            )
        walked += length
    return points[-1]


def _rough_rect_path(x: int, y: int, w: int, h: int, r: int = 20) -> str:
    """Return a slightly irregular rounded rectangle path."""
    return (
        f"M{x+r},{y+2} C{x+5},{y-1} {x},{y+7} {x+2},{y+r} "
        f"L{x+1},{y+h-r} C{x+2},{y+h-5} {x+8},{y+h+1} {x+r},{y+h-1} "
        f"L{x+w-r},{y+h+2} C{x+w-7},{y+h+1} {x+w+1},{y+h-8} {x+w-2},{y+h-r} "
        f"L{x+w+1},{y+r} C{x+w},{y+7} {x+w-8},{y} {x+w-r},{y+1} Z"
    )


def _icon_svg(icon: str, x: int, y: int, color: str = "#111111") -> str:
    """Return a small primitive icon."""
    if icon == "user":
        return f'<circle cx="{x+18}" cy="{y+14}" r="10" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+2},{y+42} C{x+8},{y+24} {x+28},{y+24} {x+34},{y+42}" fill="none" stroke="{color}" stroke-width="3"/>'
    if icon == "lock":
        return f'<rect x="{x+5}" y="{y+20}" width="34" height="28" rx="4" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+12},{y+20} v-8 C{x+12},{y} {x+32},{y} {x+32},{y+12} v8" fill="none" stroke="{color}" stroke-width="3"/>'
    if icon == "shield":
        return f'<path d="M{x+22},{y+2} L{x+42},{y+10} C{x+39},{y+34} {x+31},{y+45} {x+22},{y+50} C{x+13},{y+45} {x+5},{y+34} {x+2},{y+10} Z" fill="none" stroke="{color}" stroke-width="3"/>'
    if icon == "db":
        return f'<ellipse cx="{x+24}" cy="{y+10}" rx="20" ry="8" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+4},{y+10} v30 C{x+4},{y+50} {x+44},{y+50} {x+44},{y+40} v-30" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+4},{y+25} C{x+4},{y+35} {x+44},{y+35} {x+44},{y+25}" fill="none" stroke="{color}" stroke-width="3"/>'
    if icon == "key":
        return f'<circle cx="{x+15}" cy="{y+22}" r="10" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+25},{y+22} H{x+48} M{x+38},{y+22} v9 M{x+45},{y+22} v7" stroke="{color}" stroke-width="3"/>'
    if icon == "gear":
        return f'<circle cx="{x+24}" cy="{y+24}" r="13" fill="none" stroke="{color}" stroke-width="3"/><circle cx="{x+24}" cy="{y+24}" r="4" fill="{color}"/><path d="M{x+24},{y+2}v9 M{x+24},{y+37}v9 M{x+2},{y+24}h9 M{x+37},{y+24}h9" stroke="{color}" stroke-width="3"/>'
    if icon == "alert":
        return f'<path d="M{x+24},{y+4} L{x+46},{y+44} H{x+2} Z" fill="none" stroke="{color}" stroke-width="3"/><path d="M{x+24},{y+17} v13 M{x+24},{y+36} v3" stroke="{color}" stroke-width="4"/>'
    return f'<rect x="{x+7}" y="{y+8}" width="34" height="34" rx="6" fill="none" stroke="{color}" stroke-width="3"/>'


def _svg_node(node: DiagramNode) -> str:
    fill, stroke = PALETTE.get(node.color, PALETTE["orange"])
    icon = _icon_svg(node.icon, node.x + node.w // 2 - 24, node.y + 22, "#111111")
    label_y = node.y + node.h - 34
    return "\n".join(
        [
            f'<path d="{_rough_rect_path(node.x + 6, node.y + 8, node.w, node.h)}" fill="#000000" opacity="0.08"/>',
            f'<path d="{_rough_rect_path(node.x, node.y, node.w, node.h)}" fill="{fill}" stroke="{stroke}" stroke-width="4" filter="url(#roughen)"/>',
            icon,
            _svg_text(node.label, node.x + node.w // 2, label_y, width=max(10, node.w // 12), size=24),
        ]
    )


def _svg_flow(flow: DiagramFlow, nodes: dict[str, DiagramNode]) -> str:
    source = nodes[flow.source]
    target = nodes[flow.target]
    route = _flow_route_points(source, target)
    color, dashed = _flow_color(flow.kind)
    dash = ' stroke-dasharray="12 10"' if dashed else ""
    marker = f"arrow-{flow.kind if flow.kind in {'trust', 'control', 'risk'} else 'normal'}"
    line = f'<path d="{_svg_path_from_route(route)}" fill="none" stroke="{color}" stroke-width="4"{dash} marker-end="url(#{marker})" stroke-linecap="round" stroke-linejoin="round"/>'
    if not flow.label:
        return line
    lx, ly = _route_label_point(route)
    label_bg = f'<rect x="{lx - 80}" y="{ly - 28}" width="160" height="30" rx="10" fill="#fffdf7" opacity="0.94"/>'
    return line + "\n" + label_bg + "\n" + _svg_text(flow.label, lx, ly - 8, width=16, size=17)


def _svg_lanes(spec: DiagramSpec) -> str:
    """Draw subtle teaching lanes behind richer architecture diagrams."""
    if spec.diagram_type not in {"chapter_map", "architecture_diagram"}:
        return ""
    lanes = [
        ("Security / Governance", 105, "#fef8df", "#d9a300"),
        ("Application / Processing", 305, "#fff4df", "#df7c18"),
        ("Data / Telemetry", 625, "#eef9ea", "#2e7d32"),
    ]
    rows = []
    for label, y, fill, stroke in lanes:
        rows.append(f'<rect x="48" y="{y}" width="1504" height="150" rx="26" fill="{fill}" opacity="0.28" stroke="{stroke}" stroke-width="2" stroke-dasharray="8 12"/>')
        rows.append(f'<text x="92" y="{y + 34}" font-size="22" fill="{stroke}" font-family="Comic Sans MS, Segoe Print, Arial" font-weight="700">{html.escape(label)}</text>')
    return "\n".join(rows)


def _svg_callouts(spec: DiagramSpec) -> str:
    """Render small sticky-note teaching callouts."""
    if not spec.callouts:
        return ""
    rows = []
    x = 1250
    y = 610
    for index, callout in enumerate(spec.callouts[:2]):
        yy = y + index * 82
        rows.append(f'<path d="{_rough_rect_path(x, yy, 280, 62, 14)}" fill="#fef8df" stroke="#d9a300" stroke-width="3" filter="url(#roughen)"/>')
        rows.append(_svg_text(callout, x + 140, yy + 39, width=20, size=18))
    return "\n".join(rows)


def _svg_group(group: DiagramGroup) -> str:
    if group.kind == "risk":
        stroke = "#d71920"
    elif group.kind == "trust":
        stroke = "#777777"
    else:
        stroke = "#2e7d32"
    dash = ' stroke-dasharray="14 12"' if group.kind in {"risk", "trust"} else ""
    return "\n".join(
        [
            f'<path d="{_rough_rect_path(group.x, group.y, group.w, group.h, 26)}" fill="none" stroke="{stroke}" stroke-width="4"{dash}/>',
            f'<text x="{group.x + group.w // 2}" y="{group.y + 42}" text-anchor="middle" font-size="24" fill="#555555" font-family="Comic Sans MS, Segoe Print, Arial">{html.escape(group.label)}</text>',
        ]
    )


def _svg_legend(spec: DiagramSpec) -> str:
    x = 45
    y = 790
    rows = [f'<path d="{_rough_rect_path(x, y, 380, 105, 16)}" fill="#ffffff" stroke="#777777" stroke-width="3"/>']
    for index, (kind, label) in enumerate(spec.legend):
        color, dashed = _flow_color(kind)
        yy = y + 26 + index * 20
        dash = ' stroke-dasharray="10 8"' if dashed else ""
        rows.append(f'<line x1="{x+25}" y1="{yy}" x2="{x+85}" y2="{yy}" stroke="{color}" stroke-width="4"{dash} marker-end="url(#arrow-{kind if kind in {"trust", "control", "risk"} else "normal"})"/>')
        rows.append(f'<text x="{x+105}" y="{yy+6}" font-size="17" font-family="Comic Sans MS, Segoe Print, Arial">{html.escape(label)}</text>')
    return "\n".join(rows)


def render_svg_spec(spec: DiagramSpec) -> str:
    """Render a semantic diagram spec to SVG."""
    nodes = _node_lookup(spec)
    lanes = _svg_lanes(spec)
    groups = "\n".join(_svg_group(group) for group in spec.groups)
    flows = "\n".join(_svg_flow(flow, nodes) for flow in spec.flows)
    rendered_nodes = "\n".join(_svg_node(node) for node in spec.nodes)
    callouts = _svg_callouts(spec)
    legend = _svg_legend(spec)
    title = html.escape(spec.title)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <defs>
    <pattern id="paper" width="18" height="18" patternUnits="userSpaceOnUse">
      <path d="M 18 0 L 0 0 0 18" fill="none" stroke="#f2ead8" stroke-width="0.8" opacity="0.25"/>
    </pattern>
    <filter id="roughen">
      <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="1" result="noise"/>
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="0.85"/>
    </filter>
    <marker id="arrow-normal" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M2,2 L10,6 L2,10 z" fill="#111111"/></marker>
    <marker id="arrow-trust" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M2,2 L10,6 L2,10 z" fill="#1e66b1"/></marker>
    <marker id="arrow-control" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M2,2 L10,6 L2,10 z" fill="#2e7d32"/></marker>
    <marker id="arrow-risk" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M2,2 L10,6 L2,10 z" fill="#d71920"/></marker>
  </defs>
  <rect width="1600" height="900" fill="#fffdf7"/>
  <rect width="1600" height="900" fill="url(#paper)"/>
  <text x="800" y="58" text-anchor="middle" font-size="40" font-family="Comic Sans MS, Segoe Print, Arial" font-weight="700">{title}</text>
  <path d="M540 78 C650 92, 940 90, 1060 78" fill="none" stroke="#d9a300" stroke-width="5" stroke-linecap="round"/>
  {lanes}
  {groups}
  {flows}
  {rendered_nodes}
  {callouts}
  {legend}
</svg>
'''


def diagram_spec(title: str, diagram_type: str, labels: list[str]) -> DiagramSpec:
    """Build a semantic diagram spec for a supported diagram type."""
    while len(labels) < 8:
        labels.append(_domain_fallbacks(title, diagram_type)[len(labels) % 7])

    if diagram_type == "concept_diagram":
        nodes = [
            DiagramNode("user", labels[0], 80, 360, 210, 140, "blue", "user"),
            DiagramNode("authn", labels[1], 390, 250, 245, 140, "orange", "key"),
            DiagramNode("identity", labels[2], 390, 540, 245, 140, "orange", "user"),
            DiagramNode("decision", labels[3], 720, 365, 260, 140, "green", "shield"),
            DiagramNode("authz", labels[4], 1080, 250, 245, 140, "orange", "lock"),
            DiagramNode("resource", labels[5], 1080, 540, 245, 140, "green", "db"),
        ]
        flows = [
            DiagramFlow("user", "authn", "trust", "who?"),
            DiagramFlow("user", "identity", "trust"),
            DiagramFlow("authn", "decision", "normal"),
            DiagramFlow("identity", "decision", "normal"),
            DiagramFlow("decision", "authz", "control", "can do?"),
            DiagramFlow("decision", "resource", "control"),
        ]
        return DiagramSpec(title, diagram_type, nodes, flows, [], _legend())

    if diagram_type == "chapter_map":
        nodes = [
            DiagramNode("passwords", "Credentials", 335, 115, 150, 118, "yellow", "key"),
            DiagramNode("sessions", "Sessions", 725, 115, 150, 118, "yellow", "lock"),
            DiagramNode("policies", "Policies", 1115, 115, 150, 118, "yellow", "shield"),
            DiagramNode("user", "User", 70, 375, 190, 135, "blue", "user"),
            DiagramNode("authn", "Authenticate", 360, 335, 205, 150, "orange", "key"),
            DiagramNode("identity", "Identity", 640, 335, 205, 150, "orange", "user"),
            DiagramNode("authz", "Authorize", 920, 335, 205, 150, "orange", "shield"),
            DiagramNode("resource", "Protected Resource", 1340, 375, 190, 135, "green", "db"),
            DiagramNode("mfa", "MFA / Step-Up", 390, 650, 220, 125, "green", "lock"),
            DiagramNode("store", "Session Store", 690, 650, 220, 125, "green", "db"),
            DiagramNode("audit", "Audit Logs", 990, 650, 220, 125, "green", "gear"),
        ]
        flows = [
            DiagramFlow("user", "authn", "normal"),
            DiagramFlow("authn", "identity", "trust"),
            DiagramFlow("identity", "authz", "normal"),
            DiagramFlow("authz", "resource", "control"),
            DiagramFlow("passwords", "authn", "trust"),
            DiagramFlow("sessions", "identity", "trust"),
            DiagramFlow("policies", "authz", "trust"),
            DiagramFlow("mfa", "authn", "control"),
            DiagramFlow("store", "identity", "control"),
            DiagramFlow("audit", "authz", "control"),
        ]
        groups = [DiagramGroup("application trust boundary", 300, 255, 955, 355, "trust")]
        return DiagramSpec(title, diagram_type, nodes, flows, groups, _legend())

    if diagram_type == "architecture_diagram":
        nodes = [
            DiagramNode("user", labels[0], 70, 360, 190, 130, "blue", "user"),
            DiagramNode("client", labels[1], 390, 315, 220, 130, "orange", "box"),
            DiagramNode("idp", labels[2], 690, 315, 220, 130, "orange", "shield"),
            DiagramNode("api", labels[3], 990, 315, 220, 130, "orange", "gear"),
            DiagramNode("resource", labels[4], 1340, 360, 190, 130, "green", "db"),
            DiagramNode("logs", labels[5], 410, 680, 220, 110, "green", "box"),
            DiagramNode("monitor", labels[6], 720, 680, 220, 110, "green", "shield"),
            DiagramNode("review", labels[7], 1030, 680, 220, 110, "green", "key"),
        ]
        flows = [
            DiagramFlow("user", "client", "normal"),
            DiagramFlow("client", "idp", "trust"),
            DiagramFlow("idp", "api", "normal"),
            DiagramFlow("api", "resource", "control"),
            DiagramFlow("logs", "client", "control"),
            DiagramFlow("monitor", "idp", "control"),
            DiagramFlow("review", "api", "control"),
        ]
        groups = [DiagramGroup("trust boundary", 305, 190, 990, 430, "trust")]
        return DiagramSpec(title, diagram_type, nodes, flows, groups, _legend())

    if diagram_type == "attack_flow":
        nodes = [
            DiagramNode("valid", "Valid User", 85, 245, 185, 125, "blue", "user"),
            DiagramNode("normal", "Normal Request", 390, 210, 220, 130, "green", "box"),
            DiagramNode("policy", "Policy Check", 695, 210, 220, 130, "green", "shield"),
            DiagramNode("allowed", "Allowed Action", 1000, 210, 220, 130, "green", "db"),
            DiagramNode("attacker", "Attacker", 85, 610, 185, 125, "red", "alert"),
            DiagramNode("tamper", "Tampered ID", 390, 570, 220, 130, "orange", "key"),
            DiagramNode("missing", "Missing AuthZ", 695, 570, 220, 130, "orange", "alert"),
            DiagramNode("exposure", "Data Exposure", 1000, 570, 220, 130, "red", "db"),
        ]
        flows = [
            DiagramFlow("valid", "normal", "control"),
            DiagramFlow("normal", "policy", "control"),
            DiagramFlow("policy", "allowed", "control"),
            DiagramFlow("attacker", "tamper", "risk"),
            DiagramFlow("tamper", "missing", "risk"),
            DiagramFlow("missing", "exposure", "risk"),
        ]
        groups = [
            DiagramGroup("legitimate path", 345, 150, 920, 245, "container"),
            DiagramGroup("attack/risk path", 345, 510, 920, 245, "risk"),
        ]
        return DiagramSpec(title, diagram_type, nodes, flows, groups, _legend())

    if diagram_type == "control_map":
        nodes = [
            DiagramNode("asset", labels[0], 650, 360, 300, 145, "orange", "lock"),
            DiagramNode("least", labels[1], 130, 235, 260, 120, "green", "shield"),
            DiagramNode("identity", labels[2], 1210, 235, 260, 120, "green", "user"),
            DiagramNode("session", labels[3], 130, 590, 260, 120, "green", "key"),
            DiagramNode("audit", labels[4], 1210, 590, 260, 120, "green", "db"),
            DiagramNode("monitor", labels[5], 650, 690, 300, 110, "blue", "gear"),
        ]
        flows = [
            DiagramFlow("least", "asset", "control"),
            DiagramFlow("identity", "asset", "control"),
            DiagramFlow("session", "asset", "control"),
            DiagramFlow("audit", "asset", "control"),
            DiagramFlow("monitor", "asset", "trust"),
        ]
        groups = [DiagramGroup("controls around protected asset", 470, 235, 660, 385, "container")]
        return DiagramSpec(title, diagram_type, nodes, flows, groups, _legend())

    nodes = [
        DiagramNode("hub", labels[0], 635, 335, 330, 150, "orange", "shield"),
        DiagramNode("a", labels[1], 135, 210, 260, 120, "blue", "box"),
        DiagramNode("b", labels[2], 665, 150, 270, 115, "green", "key"),
        DiagramNode("c", labels[3], 1200, 210, 260, 120, "blue", "lock"),
        DiagramNode("d", labels[4], 135, 610, 260, 120, "green", "gear"),
        DiagramNode("e", labels[5], 665, 650, 270, 115, "blue", "db"),
        DiagramNode("f", labels[6], 1200, 610, 260, 120, "green", "shield"),
    ]
    flows = [
        DiagramFlow("a", "hub", "normal"),
        DiagramFlow("b", "hub", "control"),
        DiagramFlow("c", "hub", "trust"),
        DiagramFlow("d", "hub", "control"),
        DiagramFlow("e", "hub", "trust"),
        DiagramFlow("f", "hub", "control"),
    ]
    return DiagramSpec(title, diagram_type, nodes, flows, [], _legend())


def sketchnote_prompt(chapter: int, stage: str = "final") -> str:
    """Build a reusable sketchnote image prompt from a chapter."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    concepts = _semantic_labels(metadata.title, markdown, "chapter_map", limit=7)

    lines = [
        f"# Sketchnote Prompt: Chapter {metadata.number:02d} - {metadata.title}",
        "",
        "Create a clean sketchnote-style teaching diagram for a handbook chapter.",
        "",
        "## Visual Style",
        "- White background",
        "- Hand-drawn black outlines",
        "- Rounded boxes with soft blue, orange, green, and yellow accents",
        "- Clear arrows for normal flow",
        "- Red dashed arrows for risk or attack paths",
        "- Minimal readable text inside each box",
        "- No dark background and no decorative gradients",
        "",
        "## Chapter",
        f"- Title: {metadata.title}",
        f"- Source stage: {stage}",
        "",
        "## Concepts To Show",
        *[f"- {concept}" for concept in concepts],
        "",
        "## Output Requirement",
        "- Produce one landscape diagram suitable for insertion into a DOCX chapter.",
        "- Keep labels short enough to read when printed.",
        "- Avoid visualizing chapter section headings.",
        "- Show a beginning state, process flow, risk path, and secure outcome.",
        "- Use visual hierarchy: user/context on the left, core concept in the center, outcome/guidance on the right.",
        "",
    ]
    return "\n".join(lines)


def generate_sketchnote_prompt(chapter: int, stage: str = "final") -> Path:
    """Generate and save a chapter sketchnote prompt."""
    path = prompt_path_for(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sketchnote_prompt(chapter, stage=stage), encoding="utf-8")
    return path


def section_sketchnote_prompt(chapter: int, section: str, stage: str = "final") -> str:
    """Build a reusable sketchnote prompt for one chapter section."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    section_body = _section_text(markdown, section)
    if not section_body:
        raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")

    concepts = _concept_labels(
        section_body,
        fallback=["core idea", "risk", "control", "implementation", "verification"],
        limit=6,
    )
    lines = [
        f"# Sketchnote Prompt: Chapter {metadata.number:02d} - {section}",
        "",
        "Create one focused sketchnote-style teaching diagram for this handbook section.",
        "",
        "## Visual Style",
        "- White background",
        "- Hand-drawn black outlines",
        "- Rounded boxes with soft blue, orange, green, and yellow accents",
        "- Clear arrows for normal flow",
        "- Red dashed arrows for risk or attack paths",
        "- Minimal readable text inside each box",
        "",
        "## Chapter Context",
        f"- Chapter: {metadata.title}",
        f"- Section: {section}",
        f"- Source stage: {stage}",
        "",
        "## Concepts To Visualize",
        *[f"- {concept}" for concept in concepts],
        "",
        "## Output Requirement",
        "- Produce one landscape diagram suitable for insertion immediately after this section heading.",
        "- Keep labels short enough to read in a DOCX page.",
        f"- Use diagram type: {diagram_type_for_section(section)}.",
        "- Avoid chapter section names as diagram nodes.",
        "- Use icons, grouping, whitespace, and color-coded arrows.",
        "- Show relationships between concepts, risks, and controls.",
        "",
    ]
    return "\n".join(lines)


def generate_section_sketchnote_prompt(chapter: int, section: str, stage: str = "final") -> Path:
    """Generate and save a section sketchnote prompt."""
    path = section_prompt_path_for(chapter, section)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(section_sketchnote_prompt(chapter, section, stage=stage), encoding="utf-8")
    return path


def _wrap_label(label: str, width: int = 16) -> list[str]:
    return textwrap.wrap(label, width=width, max_lines=3, placeholder="...")


def _svg_text(label: str, x: int, y: int, width: int = 16, size: int = 22) -> str:
    lines = _wrap_label(label, width=width)
    tspans = []
    for index, line in enumerate(lines):
        escaped = html.escape(line)
        dy = 0 if index == 0 else size + 4
        tspans.append(f'<tspan x="{x}" dy="{dy}">{escaped}</tspan>')
    return f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-family="Comic Sans MS, Segoe Print, Arial">{"".join(tspans)}</text>'


def _box(x: int, y: int, w: int, h: int, fill: str, stroke: str, label: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="4"/>',
            _svg_text(label, x + w // 2, y + 58),
        ]
    )


def _arrow(x1: int, y1: int, x2: int, y2: int, color: str = "#111111", dashed: bool = False) -> str:
    dash = ' stroke-dasharray="12 10"' if dashed else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4"{dash} marker-end="url(#arrow)"/>'
    )


def sketchnote_svg(chapter: int, stage: str = "final") -> str:
    """Create an SVG-first semantic sketchnote for a chapter."""
    return render_svg_spec(_chapter_diagram_spec(chapter, stage))


def _summary_labels(chapter: int, stage: str) -> tuple[str, list[str]]:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    return metadata.title, _semantic_labels(metadata.title, markdown, "chapter_map", limit=8)


def _section_labels(chapter: int, section: str, stage: str) -> tuple[str, list[str]]:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    section_body = _section_text(markdown, section)
    if not section_body:
        raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")
    diagram_type = diagram_type_for_section(section)
    labels = _semantic_labels(metadata.title, section_body, diagram_type, limit=8)
    return f"{metadata.title}: {section}", labels


def _chapter_diagram_spec(chapter: int, stage: str) -> DiagramSpec:
    """Return the best available diagram spec for a chapter summary."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    diagram_type = diagram_type_for_section("Sketchnote Placeholder")
    try:
        plan = _planned_sketchnote(
            chapter=chapter,
            title=metadata.title,
            diagram_type=diagram_type,
            section="Sketchnote Placeholder",
            body=markdown,
            output_path=spec_path_for(chapter),
        )
        return spec_from_plan(plan, fallback_type=diagram_type)
    except Exception as exc:
        cached_path = spec_path_for(chapter)
        if cached_path.exists():
            print(f"Sketchnote planner unavailable for chapter {chapter}; using cached plan. Reason: {exc}")
            cached_plan = json.loads(cached_path.read_text(encoding="utf-8"))
            return spec_from_plan(cached_plan, fallback_type=diagram_type)
        failure_path = cached_path.with_suffix(".failed.txt")
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(str(exc), encoding="utf-8")
        print(f"Sketchnote planner unavailable for chapter {chapter}; using deterministic fallback. Reason: {exc}")
        title, labels = _summary_labels(chapter, stage)
        return diagram_spec(title, diagram_type, labels)


def _section_diagram_spec(chapter: int, section: str, stage: str) -> DiagramSpec:
    """Return the best available diagram spec for one section."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    section_body = _section_text(markdown, section)
    if not section_body:
        raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")
    diagram_type = diagram_type_for_section(section)
    try:
        plan = _planned_sketchnote(
            chapter=chapter,
            title=metadata.title,
            diagram_type=diagram_type,
            section=section,
            body=section_body,
            output_path=section_spec_path_for(chapter, section),
        )
        return spec_from_plan(plan, fallback_type=diagram_type)
    except Exception as exc:
        cached_path = section_spec_path_for(chapter, section)
        if cached_path.exists():
            print(
                f"Sketchnote planner unavailable for chapter {chapter} section '{section}'; "
                f"using cached plan. Reason: {exc}"
            )
            cached_plan = json.loads(cached_path.read_text(encoding="utf-8"))
            return spec_from_plan(cached_plan, fallback_type=diagram_type)
        failure_path = cached_path.with_suffix(".failed.txt")
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(str(exc), encoding="utf-8")
        print(
            f"Sketchnote planner unavailable for chapter {chapter} section '{section}'; "
            f"using deterministic fallback. Reason: {exc}"
        )
        title, labels = _section_labels(chapter, section, stage)
        return diagram_spec(title, diagram_type, labels)


def _render_png(output_path: Path, title: str, labels: list[str], diagram_type: str = "concept_map") -> None:
    """Render a simple sketchnote-style PNG using Windows System.Drawing."""
    powershell = shutil.which("powershell")
    if powershell is None:
        raise RuntimeError("PowerShell is required to render PNG sketchnotes on this platform.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = IMAGE_DIR / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    spec_path = tmp_dir / f"{output_path.stem}.json"
    script_path = tmp_dir / f"{output_path.stem}.ps1"
    spec_path.write_text(
        json.dumps(
            {
                "title": title,
                "labels": labels,
                "diagram_type": diagram_type,
                "output": str(output_path.resolve()),
            }
        ),
        encoding="utf-8",
    )
    script_path.write_text(
        r'''
param([string]$SpecPath)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$spec = Get-Content -Raw -Path $SpecPath | ConvertFrom-Json
$bmp = New-Object System.Drawing.Bitmap 1600,900
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::FromArgb(255,253,247))
$fontTitle = New-Object System.Drawing.Font 'Arial',32,[System.Drawing.FontStyle]::Bold
$font = New-Object System.Drawing.Font 'Arial',20,[System.Drawing.FontStyle]::Regular
$penBlack = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(30,30,30)),4
$penBlue = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(30,102,177)),4
$penOrange = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(223,124,24)),4
$penGreen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(46,125,50)),4
$penRed = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(215,25,32)),4
$penRed.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
$brushText = [System.Drawing.Brushes]::Black
$brushBlue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(238,246,255))
$brushOrange = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255,244,223))
$brushGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(238,249,234))
$format = New-Object System.Drawing.StringFormat
$format.Alignment = [System.Drawing.StringAlignment]::Center
$format.LineAlignment = [System.Drawing.StringAlignment]::Center
$textFlags = [System.Windows.Forms.TextFormatFlags]::HorizontalCenter -bor [System.Windows.Forms.TextFormatFlags]::VerticalCenter -bor [System.Windows.Forms.TextFormatFlags]::WordBreak -bor [System.Windows.Forms.TextFormatFlags]::NoPrefix
function Box($x,$y,$w,$h,$fill,$pen,$text) {
  $rect = New-Object System.Drawing.Rectangle $x,$y,$w,$h
  $g.FillRectangle($fill,$rect)
  $g.DrawRectangle($pen,$rect)
  [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$text,$font,$rect,[System.Drawing.Color]::Black,$textFlags)
}
function Arrow($x1,$y1,$x2,$y2,$pen) {
  $g.DrawLine($pen,$x1,$y1,$x2,$y2)
  $g.DrawLine($pen,$x2,$y2,$x2-16,$y2-8)
  $g.DrawLine($pen,$x2,$y2,$x2-16,$y2+8)
}
$titleRect = New-Object System.Drawing.Rectangle 90,25,1420,80
[System.Windows.Forms.TextRenderer]::DrawText($g,[string]$spec.title,$fontTitle,$titleRect,[System.Drawing.Color]::Black,$textFlags)
$labels = @($spec.labels)
while ($labels.Count -lt 8) { $labels += 'concept' }
$diagramType = [string]$spec.diagram_type
if ($diagramType -eq 'concept_diagram') {
  Box 80 345 210 145 $brushBlue $penBlue $labels[0]
  Box 415 220 250 145 $brushOrange $penOrange $labels[1]
  Box 415 515 250 145 $brushOrange $penOrange $labels[2]
  Box 755 345 250 145 $brushGreen $penGreen $labels[3]
  Box 1110 220 250 145 $brushOrange $penOrange $labels[4]
  Box 1110 515 250 145 $brushGreen $penGreen $labels[5]
  Arrow 290 418 415 292 $penBlue
  Arrow 290 418 415 588 $penBlue
  Arrow 665 292 755 418 $penBlack
  Arrow 665 588 755 418 $penBlack
  Arrow 1005 418 1110 292 $penGreen
  Arrow 1005 418 1110 588 $penGreen
  $q1 = New-Object System.Drawing.Rectangle 420,375,245,60
  [System.Windows.Forms.TextRenderer]::DrawText($g,'Who are you?',$font,$q1,[System.Drawing.Color]::FromArgb(30,102,177),$textFlags)
  $q2 = New-Object System.Drawing.Rectangle 1095,375,290,60
  [System.Windows.Forms.TextRenderer]::DrawText($g,'What can you do?',$font,$q2,[System.Drawing.Color]::FromArgb(46,125,50),$textFlags)
} elseif ($diagramType -eq 'architecture_diagram' -or $diagramType -eq 'chapter_map') {
  $boundaryPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(120,120,120)),4
  $boundaryPen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
  $boundaryRect = New-Object System.Drawing.Rectangle 300,190,990,430
  $g.DrawRectangle($boundaryPen,$boundaryRect)
  Box 70 350 190 130 $brushBlue $penBlue $labels[0]
  Box 390 305 210 130 $brushOrange $penOrange $labels[1]
  Box 690 305 210 130 $brushOrange $penOrange $labels[2]
  Box 990 305 210 130 $brushOrange $penOrange $labels[3]
  Box 1340 350 190 130 $brushGreen $penGreen $labels[4]
  Arrow 260 415 390 370 $penBlack
  Arrow 600 370 690 370 $penBlack
  Arrow 900 370 990 370 $penBlack
  Arrow 1200 370 1340 415 $penBlack
  Box 410 670 220 110 $brushGreen $penGreen $labels[5]
  Box 720 670 220 110 $brushGreen $penGreen $labels[6]
  Box 1030 670 220 110 $brushGreen $penGreen $labels[7]
  Arrow 520 670 500 435 $penGreen
  Arrow 830 670 795 435 $penGreen
  Arrow 1140 670 1095 435 $penGreen
  $bt = New-Object System.Drawing.Rectangle 610,210,370,45
  [System.Windows.Forms.TextRenderer]::DrawText($g,'trust boundary',$font,$bt,[System.Drawing.Color]::FromArgb(90,90,90),$textFlags)
} elseif ($diagramType -eq 'attack_flow') {
  Box 80 370 190 130 $brushBlue $penBlue 'valid user'
  Box 405 250 220 130 $brushGreen $penGreen $labels[0]
  Box 710 250 220 130 $brushGreen $penGreen $labels[1]
  Box 1015 250 220 130 $brushGreen $penGreen $labels[2]
  Box 1320 370 200 130 $brushGreen $penGreen 'allowed'
  Arrow 270 435 405 315 $penGreen
  Arrow 625 315 710 315 $penGreen
  Arrow 930 315 1015 315 $penGreen
  Arrow 1235 315 1320 435 $penGreen
  Box 80 650 190 120 $brushOrange $penRed 'attacker'
  Box 405 610 220 120 $brushOrange $penRed $labels[3]
  Box 710 610 220 120 $brushOrange $penRed $labels[4]
  Box 1015 610 220 120 $brushOrange $penRed $labels[5]
  Box 1320 650 200 120 $brushOrange $penRed 'exposure'
  Arrow 270 710 405 670 $penRed
  Arrow 625 670 710 670 $penRed
  Arrow 930 670 1015 670 $penRed
  Arrow 1235 670 1320 710 $penRed
} elseif ($diagramType -eq 'takeaway_map') {
  Box 635 335 330 150 $brushOrange $penOrange $labels[0]
  Box 135 210 260 120 $brushBlue $penBlue $labels[1]
  Box 665 150 270 115 $brushGreen $penGreen $labels[2]
  Box 1200 210 260 120 $brushBlue $penBlue $labels[3]
  Box 135 610 260 120 $brushGreen $penGreen $labels[4]
  Box 665 650 270 115 $brushBlue $penBlue $labels[5]
  Box 1200 610 260 120 $brushGreen $penGreen $labels[6]
  Arrow 395 270 635 385 $penBlack
  Arrow 800 265 800 335 $penBlack
  Arrow 1200 270 965 385 $penBlack
  Arrow 395 670 635 435 $penBlack
  Arrow 800 650 800 485 $penBlack
  Arrow 1200 670 965 435 $penBlack
} elseif ($diagramType -eq 'attack_path') {
  Box 70 355 180 130 $brushBlue $penBlue 'attacker / entry'
  Box 375 230 220 135 $brushOrange $penOrange $labels[1]
  Box 690 230 220 135 $brushOrange $penOrange $labels[2]
  Box 1005 230 220 135 $brushOrange $penOrange $labels[3]
  Box 1320 355 210 130 $brushGreen $penGreen 'business impact'
  Arrow 250 420 375 300 $penRed
  Arrow 595 300 690 300 $penRed
  Arrow 910 300 1005 300 $penRed
  Arrow 1225 300 1320 420 $penRed
  Box 420 635 240 120 $brushGreen $penGreen $labels[4]
  Box 760 635 240 120 $brushGreen $penGreen $labels[5]
  Box 1100 635 240 120 $brushGreen $penGreen $labels[6]
  Arrow 540 635 480 365 $penBlack
  Arrow 880 635 800 365 $penBlack
  Arrow 1220 635 1115 365 $penBlack
} elseif ($diagramType -eq 'test_checklist' -or $diagramType -eq 'interview_cards') {
  for ($i = 0; $i -lt 6; $i++) {
    $x = 160 + (($i % 3) * 430)
    $y = 225 + ([math]::Floor($i / 3) * 255)
    Box $x $y 320 150 $brushOrange $penOrange $labels[$i]
    $checkRect = New-Object System.Drawing.Rectangle ($x+18),($y+18),45,45
    [System.Windows.Forms.TextRenderer]::DrawText($g,'✓',$fontTitle,$checkRect,[System.Drawing.Color]::FromArgb(46,125,50),$textFlags)
  }
} elseif ($diagramType -eq 'risk_matrix') {
  Box 145 200 280 130 $brushBlue $penBlue 'finding'
  Box 560 200 280 130 $brushOrange $penOrange 'risk'
  Box 975 200 280 130 $brushGreen $penGreen 'control'
  Arrow 425 265 560 265 $penBlack
  Arrow 840 265 975 265 $penBlack
  for ($i = 0; $i -lt 4; $i++) {
    $y = 430 + ($i * 95)
    Box 120 $y 320 70 $brushOrange $penOrange $labels[$i]
    Box 520 $y 320 70 $brushBlue $penBlue $labels[$i+1]
    Box 920 $y 320 70 $brushGreen $penGreen $labels[$i+2]
  }
} elseif ($diagramType -eq 'trust_boundary' -or $diagramType -eq 'control_map') {
  $boundaryPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(120,120,120)),4
  $boundaryPen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
  $boundaryRect = New-Object System.Drawing.Rectangle 320,185,930,420
  $g.DrawRectangle($boundaryPen,$boundaryRect)
  Box 65 350 190 130 $brushBlue $penBlue 'user / client'
  Box 410 300 210 135 $brushOrange $penOrange $labels[1]
  Box 700 300 210 135 $brushOrange $penOrange $labels[2]
  Box 990 300 210 135 $brushOrange $penOrange $labels[3]
  Box 1330 350 205 130 $brushGreen $penGreen 'protected asset'
  Arrow 255 415 410 365 $penBlack
  Arrow 620 365 700 365 $penBlack
  Arrow 910 365 990 365 $penBlack
  Arrow 1200 365 1330 415 $penBlack
  Box 500 650 230 110 $brushGreen $penGreen $labels[4]
  Box 880 650 230 110 $brushGreen $penGreen $labels[5]
  Arrow 615 650 535 435 $penBlack
  Arrow 995 650 1095 435 $penBlack
} else {
  Box 70 350 190 140 $brushBlue $penBlue $labels[0]
  Arrow 260 420 360 420 $penBlack
  Box 370 310 210 155 $brushOrange $penOrange $labels[1]
  Arrow 580 388 660 388 $penBlack
  Box 670 310 210 155 $brushOrange $penOrange $labels[2]
  Arrow 880 388 960 388 $penBlack
  Box 970 310 210 155 $brushOrange $penOrange $labels[3]
  Arrow 1180 388 1260 388 $penBlack
  Box 1270 350 220 140 $brushGreen $penGreen $labels[4]
  Box 390 635 240 130 $brushGreen $penGreen $labels[5]
  Arrow 510 635 510 465 $penBlack
  Box 760 635 240 130 $brushGreen $penGreen $labels[6]
  Arrow 880 635 880 465 $penBlack
  Box 1130 635 240 130 $brushGreen $penGreen $labels[7]
  Arrow 1250 635 1080 465 $penBlack
  $g.DrawLine($penRed,160,700,375,465)
  $riskRect = New-Object System.Drawing.Rectangle 65,725,220,60
  [System.Windows.Forms.TextRenderer]::DrawText($g,'risk path',$font,$riskRect,[System.Drawing.Color]::Black,$textFlags)
}
$bmp.Save($spec.output,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
''',
        encoding="utf-8",
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), str(spec_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    spec_path.unlink(missing_ok=True)
    script_path.unlink(missing_ok=True)
    if completed.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"PNG sketchnote rendering failed: {completed.stderr.strip() or completed.stdout.strip()}")


def _render_png_spec(output_path: Path, spec: DiagramSpec) -> None:
    """Render a DOCX-compatible PNG from the same semantic spec as the SVG."""
    powershell = shutil.which("powershell")
    if powershell is None:
        raise RuntimeError("PowerShell is required to render PNG sketchnotes on this platform.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = IMAGE_DIR / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    spec_path = tmp_dir / f"{output_path.stem}-v2.json"
    script_path = tmp_dir / f"{output_path.stem}-v2.ps1"
    nodes_by_id = _node_lookup(spec)
    spec_path.write_text(
        json.dumps(
            {
                "title": spec.title,
                "diagram_type": spec.diagram_type,
                "output": str(output_path.resolve()),
                "nodes": [node.__dict__ for node in spec.nodes],
                "groups": [group.__dict__ for group in spec.groups],
                "callouts": spec.callouts or [],
                "legend": [{"kind": kind, "label": label} for kind, label in spec.legend],
                "flows": [
                    {
                        "kind": flow.kind,
                        "label": flow.label,
                        "route": _flow_route_points(nodes_by_id[flow.source], nodes_by_id[flow.target]),
                    }
                    for flow in spec.flows
                ],
            }
        ),
        encoding="utf-8",
    )
    script_path.write_text(
        r'''
param([string]$SpecPath)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$spec = Get-Content -Raw -Path $SpecPath | ConvertFrom-Json
$bmp = New-Object System.Drawing.Bitmap 1600,900
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::FromArgb(255,253,247))
$fontTitle = New-Object System.Drawing.Font 'Comic Sans MS',38,[System.Drawing.FontStyle]::Bold
$font = New-Object System.Drawing.Font 'Comic Sans MS',20,[System.Drawing.FontStyle]::Regular
$fontSmall = New-Object System.Drawing.Font 'Comic Sans MS',14,[System.Drawing.FontStyle]::Regular
$textFlags = [System.Windows.Forms.TextFormatFlags]::HorizontalCenter -bor [System.Windows.Forms.TextFormatFlags]::VerticalCenter -bor [System.Windows.Forms.TextFormatFlags]::WordBreak -bor [System.Windows.Forms.TextFormatFlags]::NoPrefix
function ColorFor($hex) {
  return [System.Drawing.ColorTranslator]::FromHtml([string]$hex)
}
function Palette($name, $part) {
  $map = @{
    blue = @('#eef6ff','#1e66b1')
    orange = @('#fff4df','#df7c18')
    green = @('#eef9ea','#2e7d32')
    yellow = @('#fef8df','#d9a300')
    purple = @('#f5f0ff','#5e3c99')
    red = @('#fff0ef','#d71920')
  }
  if (-not $map.ContainsKey([string]$name)) { $name = 'orange' }
  return ColorFor $map[$name][$part]
}
function FlowColor($kind) {
  if ($kind -eq 'trust') { return ColorFor '#1e66b1' }
  if ($kind -eq 'control') { return ColorFor '#2e7d32' }
  if ($kind -eq 'risk') { return ColorFor '#d71920' }
  return ColorFor '#111111'
}
function PenFor($kind) {
  $pen = New-Object System.Drawing.Pen (FlowColor $kind),4
  $cap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap 6,7
  $pen.CustomEndCap = $cap
  if ($kind -eq 'risk') { $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash }
  return $pen
}
function RoundPath($x,$y,$w,$h,$r) {
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath
  $d = $r * 2
  $path.AddArc($x,$y,$d,$d,180,90)
  $path.AddArc($x+$w-$d,$y,$d,$d,270,90)
  $path.AddArc($x+$w-$d,$y+$h-$d,$d,$d,0,90)
  $path.AddArc($x,$y+$h-$d,$d,$d,90,90)
  $path.CloseFigure()
  return $path
}
function DrawIcon($icon,$x,$y) {
  $pen = New-Object System.Drawing.Pen (ColorFor '#111111'),3
  if ($icon -eq 'user') {
    $g.DrawEllipse($pen,$x+12,$y+4,22,22)
    $g.DrawArc($pen,$x+4,$y+22,38,34,200,140)
  } elseif ($icon -eq 'shield') {
    $pts = @(
      (New-Object System.Drawing.Point ($x+24),($y+2)),
      (New-Object System.Drawing.Point ($x+44),($y+11)),
      (New-Object System.Drawing.Point ($x+36),($y+43)),
      (New-Object System.Drawing.Point ($x+24),($y+51)),
      (New-Object System.Drawing.Point ($x+12),($y+43)),
      (New-Object System.Drawing.Point ($x+4),($y+11))
    )
    $g.DrawPolygon($pen,$pts)
  } elseif ($icon -eq 'db') {
    $g.DrawEllipse($pen,$x+4,$y+6,40,16)
    $g.DrawLine($pen,$x+4,$y+14,$x+4,$y+44)
    $g.DrawLine($pen,$x+44,$y+14,$x+44,$y+44)
    $g.DrawArc($pen,$x+4,$y+36,40,16,0,180)
  } elseif ($icon -eq 'key') {
    $g.DrawEllipse($pen,$x+4,$y+14,22,22)
    $g.DrawLine($pen,$x+26,$y+25,$x+50,$y+25)
    $g.DrawLine($pen,$x+40,$y+25,$x+40,$y+34)
  } elseif ($icon -eq 'alert') {
    $pts = @(
      (New-Object System.Drawing.Point ($x+24),($y+4)),
      (New-Object System.Drawing.Point ($x+46),($y+46)),
      (New-Object System.Drawing.Point ($x+2),($y+46))
    )
    $g.DrawPolygon($pen,$pts)
    $g.DrawLine($pen,$x+24,$y+18,$x+24,$y+32)
    $g.DrawLine($pen,$x+24,$y+38,$x+24,$y+40)
  } else {
    $g.DrawRectangle($pen,$x+8,$y+10,34,34)
  }
}
function Box($node) {
  $fill = New-Object System.Drawing.SolidBrush (Palette $node.color 0)
  $pen = New-Object System.Drawing.Pen (Palette $node.color 1),4
  $path = RoundPath ([int]$node.x) ([int]$node.y) ([int]$node.w) ([int]$node.h) 20
  $g.FillPath($fill,$path)
  $g.DrawPath($pen,$path)
  DrawIcon ([string]$node.icon) ([int]$node.x + 14) ([int]$node.y + 12)
  $rect = New-Object System.Drawing.Rectangle ([int]$node.x + 52),([int]$node.y + 18),([int]$node.w - 62),([int]$node.h - 34)
  [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$node.label,$font,$rect,[System.Drawing.Color]::Black,$textFlags)
}
function GroupBox($group) {
  $stroke = '#2e7d32'
  if ($group.kind -eq 'trust') { $stroke = '#777777' }
  if ($group.kind -eq 'risk') { $stroke = '#d71920' }
  $pen = New-Object System.Drawing.Pen (ColorFor $stroke),4
  if ($group.kind -eq 'trust' -or $group.kind -eq 'risk') { $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash }
  $path = RoundPath ([int]$group.x) ([int]$group.y) ([int]$group.w) ([int]$group.h) 26
  $g.DrawPath($pen,$path)
  $rect = New-Object System.Drawing.Rectangle ([int]$group.x),([int]$group.y + 18),([int]$group.w),40
  [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$group.label,$fontSmall,$rect,(ColorFor '#555555'),$textFlags)
}
function Lane($label,$y,$fillHex,$strokeHex) {
  $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(54,(ColorFor $fillHex)))
  $pen = New-Object System.Drawing.Pen (ColorFor $strokeHex),2
  $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
  $path = RoundPath 48 $y 1504 150 26
  $g.FillPath($brush,$path)
  $g.DrawPath($pen,$path)
  $rect = New-Object System.Drawing.Rectangle 88,($y+15),330,38
  [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$label,$font,$rect,(ColorFor $strokeHex))
}
function Flow($flow) {
  $points = @($flow.route)
  $pen = PenFor ([string]$flow.kind)
  if ($points.Count -ge 2) {
    $drawPoints = New-Object System.Collections.Generic.List[System.Drawing.Point]
    for ($i = 0; $i -lt $points.Count; $i++) {
      $point = @($points[$i])
      $drawPoints.Add((New-Object System.Drawing.Point ([int]$point[0]),([int]$point[1])))
    }
    $g.DrawLines($pen,$drawPoints.ToArray())
  }
  if ($null -ne $flow.label -and [string]$flow.label -ne '') {
    $mid = @($points[[math]::Floor($points.Count / 2)])
    $lx = [int]$mid[0] - 70
    $ly = [int]$mid[1] - 34
    $rect = New-Object System.Drawing.Rectangle $lx,$ly,120,28
    $labelBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255,253,247))
    $g.FillRectangle($labelBrush,$rect)
    [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$flow.label,$fontSmall,$rect,(FlowColor ([string]$flow.kind)),$textFlags)
  }
}
function Callouts() {
  $items = @($spec.callouts)
  for ($i=0; $i -lt $items.Count -and $i -lt 2; $i++) {
    $y = 610 + ($i * 82)
    $path = RoundPath 1250 $y 280 62 14
    $brush = New-Object System.Drawing.SolidBrush (ColorFor '#fef8df')
    $pen = New-Object System.Drawing.Pen (ColorFor '#d9a300'),3
    $g.FillPath($brush,$path)
    $g.DrawPath($pen,$path)
    $rect = New-Object System.Drawing.Rectangle 1264,($y+8),252,48
    [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$items[$i],$fontSmall,$rect,[System.Drawing.Color]::Black,$textFlags)
  }
}
function Legend() {
  $path = RoundPath 45 785 390 105 16
  $g.FillPath([System.Drawing.Brushes]::White,$path)
  $g.DrawPath((New-Object System.Drawing.Pen (ColorFor '#777777'),3),$path)
  $items = @($spec.legend)
  for ($i=0; $i -lt $items.Count; $i++) {
    $item = $items[$i]
    $yy = 810 + ($i * 21)
    $pen = PenFor ([string]$item.kind)
    $g.DrawLine($pen,70,$yy,130,$yy)
    $rect = New-Object System.Drawing.Rectangle 155,($yy-13),250,26
    [System.Windows.Forms.TextRenderer]::DrawText($g,[string]$item.label,$fontSmall,$rect,[System.Drawing.Color]::Black)
  }
}
$titleRect = New-Object System.Drawing.Rectangle 90,28,1420,95
[System.Windows.Forms.TextRenderer]::DrawText($g,[string]$spec.title,$fontTitle,$titleRect,[System.Drawing.Color]::Black,$textFlags)
if ($spec.diagram_type -eq 'chapter_map' -or $spec.diagram_type -eq 'architecture_diagram') {
  Lane 'Security / Governance' 105 '#fef8df' '#d9a300'
  Lane 'Application / Processing' 305 '#fff4df' '#df7c18'
  Lane 'Data / Telemetry' 625 '#eef9ea' '#2e7d32'
}
foreach ($group in @($spec.groups)) { GroupBox $group }
foreach ($flow in @($spec.flows)) { Flow $flow }
foreach ($node in @($spec.nodes)) { Box $node }
Callouts
Legend
$bmp.Save($spec.output,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
''',
        encoding="utf-8",
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), str(spec_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    spec_path.unlink(missing_ok=True)
    script_path.unlink(missing_ok=True)
    if completed.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"PNG sketchnote rendering failed: {completed.stderr.strip() or completed.stdout.strip()}")


def section_sketchnote_svg(chapter: int, section: str, stage: str = "final") -> str:
    """Create an SVG-first semantic sketchnote for one section."""
    return render_svg_spec(_section_diagram_spec(chapter, section, stage))


def generate_sketchnote_image(chapter: int, stage: str = "final") -> Path:
    """Generate and save a deterministic chapter summary SVG sketchnote."""
    generate_sketchnote_prompt(chapter, stage=stage)
    path = image_path_for(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    spec = _chapter_diagram_spec(chapter, stage)
    path.write_text(render_svg_spec(spec), encoding="utf-8")
    _render_png_spec(png_path_for(chapter), spec)
    return png_path_for(chapter)


def generate_section_sketchnote_image(chapter: int, section: str, stage: str = "final") -> Path:
    """Generate and save a deterministic SVG for one section."""
    generate_section_sketchnote_prompt(chapter, section, stage=stage)
    path = section_image_path_for(chapter, section)
    path.parent.mkdir(parents=True, exist_ok=True)
    spec = _section_diagram_spec(chapter, section, stage)
    path.write_text(render_svg_spec(spec), encoding="utf-8")
    _render_png_spec(section_png_path_for(chapter, section), spec)
    return section_png_path_for(chapter, section)


def generate_all_sketchnote_prompts(chapter: int, stage: str = "final") -> list[Path]:
    """Generate chapter summary and section sketchnote prompts."""
    paths = [generate_sketchnote_prompt(chapter, stage=stage)]
    markdown = _chapter_text(chapter, stage)
    for section in SECTION_SKETCHNOTE_SECTIONS:
        if _section_text(markdown, section):
            paths.append(generate_section_sketchnote_prompt(chapter, section, stage=stage))
    return paths


def generate_all_sketchnote_images(chapter: int, stage: str = "final") -> list[Path]:
    """Generate chapter summary and section sketchnote SVGs."""
    metadata = resolve_chapter(chapter)
    paths = [generate_sketchnote_image(chapter, stage=stage)]
    artifacts = [
        DiagramArtifact(
            diagram_id=f"chapter-{chapter:02d}-summary",
            chapter=chapter,
            section="Sketchnote Placeholder",
            title=f"Chapter {chapter:02d} Summary Sketchnote",
            prompt_path=str(prompt_path_for(chapter)),
            image_path=str(png_path_for(chapter)),
            image_type="png",
            diagram_type=diagram_type_for_section("Sketchnote Placeholder"),
            caption=f"Sketchnote summary for {metadata.title}.",
            status="generated" if png_path_for(chapter).exists() else "missing",
        )
    ]
    markdown = _chapter_text(chapter, stage)
    for section in SECTION_SKETCHNOTE_SECTIONS:
        if _section_text(markdown, section):
            image_path = generate_section_sketchnote_image(chapter, section, stage=stage)
            paths.append(image_path)
            artifacts.append(
                DiagramArtifact(
                    diagram_id=f"chapter-{chapter:02d}-{slugify(section)}",
                    chapter=chapter,
                    section=section,
                    title=f"{section} Sketchnote",
                    prompt_path=str(section_prompt_path_for(chapter, section)),
                    image_path=str(section_png_path_for(chapter, section)),
                    image_type="png",
                    diagram_type=diagram_type_for_section(section),
                    caption=f"Sketchnote for Chapter {chapter:02d}: {section}.",
                    status="generated" if image_path.exists() else "missing",
                )
            )
    write_diagram_registry(chapter, artifacts)
    return paths
