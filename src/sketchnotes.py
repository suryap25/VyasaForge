"""Graphviz-backed architecture diagram generation.

The public function names retain the earlier sketchnote terminology because the
CLI and compiler depend on them. Rendering is now Graphviz-first and produces
native SVG and PNG architecture diagrams.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from src.diagrams import DiagramArtifact, write_diagram_registry
from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS

PROMPT_DIR = Path("diagrams/prompts")
IMAGE_DIR = Path("diagrams/images")
SPEC_DIR = Path("diagrams/specs")
DIAGRAM_PLAN_PROMPT = Path("prompts/diagram_plan.md")
SUPPORTED_STAGES = {"drafts", "reviewed", "final"}

SECTION_DIAGRAM_SECTIONS = [
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

ALLOWED_LAYERS = {
    "user",
    "security",
    "processing",
    "storage",
    "integration",
    "infrastructure",
    "risk",
    "outcome",
}
ALLOWED_ICONS = {"user", "lock", "shield", "db", "key", "gear", "alert", "box"}
ALLOWED_FLOW_KINDS = {"normal", "trust", "control", "risk"}
ALLOWED_DIAGRAM_TYPES = {
    "architecture_diagram",
    "concept_diagram",
    "attack_flow",
    "control_map",
    "takeaway_map",
    "chapter_map",
}

LAYER_STYLES = {
    "user": ("#eef6ff", "#1e66b1"),
    "security": ("#fef8df", "#d9a300"),
    "processing": ("#fff4df", "#df7c18"),
    "storage": ("#eef9ea", "#2e7d32"),
    "integration": ("#eef6ff", "#1e66b1"),
    "infrastructure": ("#f5f0ff", "#5e3c99"),
    "risk": ("#fff0ef", "#d71920"),
    "outcome": ("#eef9ea", "#2e7d32"),
}
EDGE_STYLES = {
    "normal": ("#111111", "solid"),
    "trust": ("#1e66b1", "solid"),
    "control": ("#2e7d32", "solid"),
    "risk": ("#d71920", "dashed"),
}
LAYER_LABELS = {
    "user": "Users / Entry",
    "security": "Security / Governance",
    "processing": "Application / Processing",
    "storage": "Data / Telemetry",
    "integration": "External Integrations",
    "infrastructure": "Infrastructure",
    "risk": "Risk / Attack Path",
    "outcome": "Outcome",
}


def prompt_path_for(chapter: int) -> Path:
    return PROMPT_DIR / f"chapter-{chapter:02d}-prompt.md"


def image_path_for(chapter: int) -> Path:
    return IMAGE_DIR / f"chapter-{chapter:02d}.svg"


def png_path_for(chapter: int) -> Path:
    return IMAGE_DIR / f"chapter-{chapter:02d}.png"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def section_prompt_path_for(chapter: int, section: str) -> Path:
    return PROMPT_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.md"


def section_image_path_for(chapter: int, section: str) -> Path:
    return IMAGE_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.svg"


def section_png_path_for(chapter: int, section: str) -> Path:
    return IMAGE_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.png"


def spec_path_for(chapter: int) -> Path:
    return SPEC_DIR / f"chapter-{chapter:02d}.json"


def section_spec_path_for(chapter: int, section: str) -> Path:
    return SPEC_DIR / f"chapter-{chapter:02d}" / f"{slugify(section)}.json"


def preferred_image_path_for(chapter: int) -> Path:
    png_path = png_path_for(chapter)
    return png_path if png_path.exists() else image_path_for(chapter)


def preferred_section_image_path_for(chapter: int, section: str) -> Path:
    png_path = section_png_path_for(chapter, section)
    return png_path if png_path.exists() else section_image_path_for(chapter, section)


def section_sketchnote_sections() -> list[str]:
    """Compatibility name used by compiler.py."""
    return list(SECTION_DIAGRAM_SECTIONS)


def diagram_type_for_section(section: str) -> str:
    return SECTION_DIAGRAM_TYPES.get(section, "architecture_diagram")


def chapter_path_for(chapter: int, stage: str) -> Path:
    if stage not in SUPPORTED_STAGES:
        available = ", ".join(sorted(SUPPORTED_STAGES))
        raise ValueError(f"Unknown diagram stage '{stage}'. Available stages: {available}")
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


def _plain_text(markdown: str) -> str:
    text = re.sub(r"(?ms)^```.*?^```", " ", markdown)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>\[\]()]|https?://\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_label(value: str, fallback: str = "Concept", max_words: int = 4) -> str:
    cleaned = re.sub(r"`([^`]+)`", r"\1", str(value))
    cleaned = re.sub(r"[*_#>\[\]()]|https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    words = cleaned.split()
    if not words:
        return fallback
    return " ".join(words[:max_words])


def _stable_id(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or fallback


def _extract_json_object(text: str) -> dict[str, Any]:
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
        raise ValueError("Diagram plan must be a JSON object.")
    return parsed


def _fallback_components(title: str, diagram_type: str) -> list[dict[str, str]]:
    topic = title.casefold()
    if "oauth" in topic:
        labels = ["User", "Client App", "Auth Server", "Token", "Resource API", "Protected Data"]
    elif "jwt" in topic or "token" in topic:
        labels = ["Issuer", "JWT Claims", "Signature", "JWKS", "API", "Validation"]
    elif diagram_type == "attack_flow":
        labels = ["Valid User", "Normal Request", "Policy Check", "Allowed", "Attacker", "Data Exposure"]
    else:
        labels = ["User", "Authenticate", "Identity", "Authorize", "Policy Check", "Protected Resource"]

    layers = ["user", "processing", "processing", "security", "processing", "outcome"]
    icons = ["user", "key", "user", "shield", "gear", "db"]
    if diagram_type == "attack_flow":
        layers = ["user", "processing", "security", "outcome", "risk", "risk"]
        icons = ["user", "box", "shield", "db", "alert", "db"]

    return [
        {
            "id": _stable_id(label, f"node_{index + 1}"),
            "label": label,
            "layer": layers[index],
            "icon": icons[index],
        }
        for index, label in enumerate(labels)
    ]


def _fallback_plan(title: str, diagram_type: str) -> dict[str, Any]:
    components = _fallback_components(title, diagram_type)
    flows = [
        {
            "from": components[index]["id"],
            "to": components[index + 1]["id"],
            "label": None,
            "kind": "risk" if components[index]["layer"] == "risk" else "normal",
        }
        for index in range(len(components) - 1)
    ]
    return {
        "title": title,
        "diagram_type": diagram_type,
        "trust_boundaries": ["Application Trust Boundary"],
        "components": components,
        "flows": flows,
        "callouts": [],
    }


def _sanitize_plan(raw_plan: dict[str, Any], title: str, diagram_type: str) -> dict[str, Any]:
    plan_type = raw_plan.get("diagram_type") if raw_plan.get("diagram_type") in ALLOWED_DIAGRAM_TYPES else diagram_type
    raw_components = raw_plan.get("components", [])
    components: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    if isinstance(raw_components, list):
        for index, component in enumerate(raw_components):
            if not isinstance(component, dict):
                continue
            label = _clean_label(str(component.get("label", "")), fallback=f"Concept {index + 1}")
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
            components.append({"id": component_id, "label": label, "layer": layer, "icon": icon})
            if len(components) >= 10:
                break

    if len(components) < 4:
        return _fallback_plan(title, plan_type)

    ids = {component["id"] for component in components}
    raw_flows = raw_plan.get("flows", [])
    flows: list[dict[str, str | None]] = []
    if isinstance(raw_flows, list):
        for flow in raw_flows:
            if not isinstance(flow, dict):
                continue
            source = _stable_id(str(flow.get("from", "")), "")
            target = _stable_id(str(flow.get("to", "")), "")
            if source not in ids or target not in ids or source == target:
                continue
            kind = str(flow.get("kind", "normal")).lower()
            if kind not in ALLOWED_FLOW_KINDS:
                kind = "normal"
            label = _clean_label(str(flow.get("label", "")), fallback="", max_words=3) if flow.get("label") else None
            flows.append({"from": source, "to": target, "label": label, "kind": kind})
            if len(flows) >= 10:
                break

    if not flows:
        flows = _fallback_plan(title, plan_type)["flows"]

    trust_boundaries = raw_plan.get("trust_boundaries", [])
    if not isinstance(trust_boundaries, list):
        trust_boundaries = []
    callouts = raw_plan.get("callouts", [])
    if not isinstance(callouts, list):
        callouts = []

    return {
        "title": title,
        "diagram_type": plan_type,
        "trust_boundaries": [_clean_label(item, "Trust Boundary", max_words=5) for item in trust_boundaries[:2]],
        "components": components,
        "flows": flows,
        "callouts": [_clean_label(item, "Key idea", max_words=8) for item in callouts[:3]],
    }


def _plan_prompt() -> str:
    if not DIAGRAM_PLAN_PROMPT.exists():
        raise FileNotFoundError(f"Missing diagram planning prompt: {DIAGRAM_PLAN_PROMPT}")
    return DIAGRAM_PLAN_PROMPT.read_text(encoding="utf-8")


def _planned_diagram(
    chapter: int,
    title: str,
    diagram_type: str,
    section: str,
    body: str,
    output_path: Path,
) -> dict[str, Any]:
    from src import llm_gateway

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
                    body[:9000],
                ]
            ),
        },
    ]
    response = llm_gateway.call_llm(role="planner", messages=messages, chapter=chapter)
    plan = _sanitize_plan(_extract_json_object(response), title=title, diagram_type=diagram_type)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_path.with_suffix(".failed.txt").unlink(missing_ok=True)
    return plan


def _diagram_plan(chapter: int, section: str, stage: str) -> dict[str, Any]:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    if section == "Sketchnote Placeholder":
        body = markdown
        output_path = spec_path_for(chapter)
    else:
        body = _section_text(markdown, section)
        if not body:
            raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")
        output_path = section_spec_path_for(chapter, section)

    diagram_type = diagram_type_for_section(section)
    try:
        return _planned_diagram(chapter, metadata.title, diagram_type, section, body, output_path)
    except Exception as exc:
        if output_path.exists():
            print(f"Diagram planner unavailable for chapter {chapter} ({section}); using cached plan. Reason: {exc}")
            return json.loads(output_path.read_text(encoding="utf-8"))
        failure_path = output_path.with_suffix(".failed.txt")
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(str(exc), encoding="utf-8")
        print(f"Diagram planner unavailable for chapter {chapter} ({section}); using fallback plan. Reason: {exc}")
        return _fallback_plan(metadata.title, diagram_type)


def _graphviz_available() -> tuple[bool, str | None]:
    if shutil.which("dot") is None:
        return (False, "Graphviz executable 'dot' was not found on PATH.")
    try:
        import graphviz  # noqa: F401
    except ImportError:
        return (False, "Python package 'graphviz' is not installed.")
    return (True, None)


def assert_graphviz_available() -> None:
    available, reason = _graphviz_available()
    if not available:
        raise RuntimeError(f"{reason} Install Graphviz and run `python -m pip install -e .`.")


def _node_label(component: dict[str, str]) -> str:
    icon_label = {
        "user": "User",
        "lock": "Control",
        "shield": "Policy",
        "db": "Data",
        "key": "Key",
        "gear": "Process",
        "alert": "Risk",
        "box": "System",
    }.get(component.get("icon", "box"), "System")
    return f"{component['label']}\\n({icon_label})"


def _flow_legend_text(index: int, flow: dict[str, Any], component_labels: dict[str, str]) -> str:
    source = component_labels.get(str(flow.get("from", "")), str(flow.get("from", "")))
    target = component_labels.get(str(flow.get("to", "")), str(flow.get("to", "")))
    flow_label = _clean_label(str(flow.get("label") or ""), fallback="", max_words=4)
    kind = str(flow.get("kind", "normal"))
    description = f"{source} -> {target}"
    if flow_label:
        description = f"{description}: {flow_label}"
    return f"{index}. {kind}: {description}"


def _legend_label(flows: list[dict[str, Any]], components: list[dict[str, str]]) -> str:
    component_labels = {component["id"]: component["label"] for component in components}
    lines = ["Flow Legend"]
    lines.extend(_flow_legend_text(index, flow, component_labels) for index, flow in enumerate(flows, start=1))
    lines.extend(
        [
            "",
            "black = normal flow",
            "blue = trust/config",
            "green = control/success",
            "red dashed = risk/attack",
        ]
    )
    return "\\l".join(lines) + "\\l"


def _add_cluster(graph: Any, layer: str, components: list[dict[str, str]]) -> None:
    if not components:
        return
    fill, stroke = LAYER_STYLES.get(layer, LAYER_STYLES["processing"])
    with graph.subgraph(name=f"cluster_{layer}") as cluster:
        cluster.attr(
            label=LAYER_LABELS.get(layer, layer.title()),
            color=stroke,
            penwidth="1.5",
            style="rounded,dashed",
            bgcolor=fill,
            fontname="Segoe UI",
            fontsize="16",
        )
        for component in components:
            cluster.node(
                component["id"],
                label=_node_label(component),
                shape="box",
                style="rounded,filled",
                fillcolor=fill,
                color=stroke,
                penwidth="2",
                fontname="Segoe UI",
                fontsize="14",
                margin="0.18,0.12",
            )


def _render_graphviz(plan: dict[str, Any], svg_path: Path, png_path: Path) -> Path:
    assert_graphviz_available()
    from graphviz import Digraph

    svg_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    graph = Digraph(
        name=slugify(str(plan.get("title") or "diagram")),
        graph_attr={
            "rankdir": "LR",
            "splines": "ortho",
            "overlap": "false",
            "pad": "0.35",
            "nodesep": "0.55",
            "ranksep": "0.85",
            "bgcolor": "#fffdf7",
            "fontname": "Segoe UI",
            "fontsize": "22",
            "label": str(plan.get("title") or "Architecture Diagram"),
            "labelloc": "t",
        },
        node_attr={"fontname": "Segoe UI"},
        edge_attr={"fontname": "Segoe UI", "fontsize": "11", "arrowsize": "0.8"},
    )

    components = list(plan.get("components", []))
    by_layer: dict[str, list[dict[str, str]]] = {layer: [] for layer in ALLOWED_LAYERS}
    for component in components:
        by_layer.setdefault(component["layer"], []).append(component)

    for layer in ["user", "security", "processing", "storage", "integration", "infrastructure", "risk", "outcome"]:
        _add_cluster(graph, layer, by_layer.get(layer, []))

    flows = [flow for flow in plan.get("flows", []) if isinstance(flow, dict)]
    for index, flow in enumerate(flows, start=1):
        color, style = EDGE_STYLES.get(str(flow.get("kind", "normal")), EDGE_STYLES["normal"])
        graph.edge(
            str(flow["from"]),
            str(flow["to"]),
            label=str(index),
            color=color,
            fontcolor=color,
            style=style,
            penwidth="2",
            fontsize="13",
        )

    if flows:
        graph.node(
            "flow_legend",
            label=_legend_label(flows, components),
            shape="box",
            style="rounded,filled",
            fillcolor="#ffffff",
            color="#777777",
            penwidth="1.5",
            fontname="Segoe UI",
            fontsize="11",
            margin="0.18,0.12",
        )

    if plan.get("callouts"):
        callout_label = "\\n".join(str(item) for item in plan["callouts"][:3])
        graph.node(
            "callouts",
            label=callout_label,
            shape="note",
            style="filled",
            fillcolor="#fef8df",
            color="#d9a300",
            fontname="Segoe UI",
            fontsize="12",
        )

    base = svg_path.with_suffix("")
    rendered_svg = Path(graph.render(filename=str(base), format="svg", cleanup=True))
    if rendered_svg.resolve() != svg_path.resolve():
        rendered_svg.replace(svg_path)
    base_png = png_path.with_suffix("")
    rendered_png = Path(graph.render(filename=str(base_png), format="png", cleanup=True))
    if rendered_png.resolve() != png_path.resolve():
        rendered_png.replace(png_path)
    return png_path


def sketchnote_prompt(chapter: int, stage: str = "final") -> str:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    concepts = [heading for heading in REQUIRED_SECTIONS if f"## {heading}" in markdown][:8]
    lines = [
        f"# Diagram Plan Prompt: Chapter {metadata.number:02d} - {metadata.title}",
        "",
        "Create a Visio-style architecture diagram plan for this chapter.",
        "",
        "## Source Stage",
        stage,
        "",
        "## Concepts",
        *[f"- {concept}" for concept in concepts],
        "",
        "The renderer uses Graphviz. Keep labels short and architecture-level.",
        "",
    ]
    return "\n".join(lines)


def generate_sketchnote_prompt(chapter: int, stage: str = "final") -> Path:
    path = prompt_path_for(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sketchnote_prompt(chapter, stage), encoding="utf-8")
    return path


def section_sketchnote_prompt(chapter: int, section: str, stage: str = "final") -> str:
    metadata = resolve_chapter(chapter)
    return "\n".join(
        [
            f"# Diagram Plan Prompt: Chapter {metadata.number:02d} - {section}",
            "",
            f"Create a Visio-style architecture diagram plan for section: {section}.",
            f"Source stage: {stage}",
            "",
            "The renderer uses Graphviz. Keep labels short and architecture-level.",
            "",
        ]
    )


def generate_section_sketchnote_prompt(chapter: int, section: str, stage: str = "final") -> Path:
    path = section_prompt_path_for(chapter, section)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(section_sketchnote_prompt(chapter, section, stage), encoding="utf-8")
    return path


def sketchnote_svg(chapter: int, stage: str = "final") -> str:
    generate_sketchnote_image(chapter, stage)
    return image_path_for(chapter).read_text(encoding="utf-8")


def section_sketchnote_svg(chapter: int, section: str, stage: str = "final") -> str:
    generate_section_sketchnote_image(chapter, section, stage)
    return section_image_path_for(chapter, section).read_text(encoding="utf-8")


def generate_sketchnote_image(chapter: int, stage: str = "final") -> Path:
    generate_sketchnote_prompt(chapter, stage)
    plan = _diagram_plan(chapter, "Sketchnote Placeholder", stage)
    return _render_graphviz(plan, image_path_for(chapter), png_path_for(chapter))


def generate_section_sketchnote_image(chapter: int, section: str, stage: str = "final") -> Path:
    generate_section_sketchnote_prompt(chapter, section, stage)
    plan = _diagram_plan(chapter, section, stage)
    return _render_graphviz(plan, section_image_path_for(chapter, section), section_png_path_for(chapter, section))


def generate_all_sketchnote_prompts(chapter: int, stage: str = "final") -> list[Path]:
    paths = [generate_sketchnote_prompt(chapter, stage=stage)]
    markdown = _chapter_text(chapter, stage)
    for section in SECTION_DIAGRAM_SECTIONS:
        if _section_text(markdown, section):
            paths.append(generate_section_sketchnote_prompt(chapter, section, stage=stage))
    return paths


def generate_all_sketchnote_images(chapter: int, stage: str = "final") -> list[Path]:
    metadata = resolve_chapter(chapter)
    paths = [generate_sketchnote_image(chapter, stage=stage)]
    artifacts = [
        DiagramArtifact(
            diagram_id=f"chapter-{chapter:02d}-summary",
            chapter=chapter,
            section="Sketchnote Placeholder",
            title=f"Chapter {chapter:02d} Architecture Diagram",
            prompt_path=str(prompt_path_for(chapter)),
            image_path=str(png_path_for(chapter)),
            image_type="png",
            diagram_type=diagram_type_for_section("Sketchnote Placeholder"),
            caption=f"Architecture diagram for {metadata.title}.",
            status="generated" if png_path_for(chapter).exists() else "missing",
        )
    ]

    markdown = _chapter_text(chapter, stage)
    for section in SECTION_DIAGRAM_SECTIONS:
        if _section_text(markdown, section):
            image_path = generate_section_sketchnote_image(chapter, section, stage=stage)
            paths.append(image_path)
            artifacts.append(
                DiagramArtifact(
                    diagram_id=f"chapter-{chapter:02d}-{slugify(section)}",
                    chapter=chapter,
                    section=section,
                    title=f"{section} Architecture Diagram",
                    prompt_path=str(section_prompt_path_for(chapter, section)),
                    image_path=str(section_png_path_for(chapter, section)),
                    image_type="png",
                    diagram_type=diagram_type_for_section(section),
                    caption=f"Architecture diagram for Chapter {chapter:02d}: {section}.",
                    status="generated" if image_path.exists() else "missing",
                )
            )
    write_diagram_registry(chapter, artifacts)
    return paths
