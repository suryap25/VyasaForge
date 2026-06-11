"""Sketchnote prompt and local SVG generation."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

from src.diagrams import DiagramArtifact, write_diagram_registry
from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS

PROMPT_DIR = Path("sketchnotes/prompts")
IMAGE_DIR = Path("sketchnotes/images")
SUPPORTED_STAGES = {"drafts", "reviewed", "final"}
SECTION_SKETCHNOTE_SECTIONS = [
    "Learning Objectives",
    "Conceptual Foundation",
    "Architecture Perspective",
    "AppSec Lens",
    "Developer Lens",
    "Pentest Lens",
    "Common Findings",
    "Secure Design Guidance",
    "Interview Questions",
    "Key Takeaways",
]


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


def sketchnote_prompt(chapter: int, stage: str = "final") -> str:
    """Build a reusable sketchnote image prompt from a chapter."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    learning_objectives = _short_bullets(_section_text(markdown, "Learning Objectives"), limit=5)
    common_findings = _short_bullets(_section_text(markdown, "Common Findings"), limit=5)
    guidance = _short_bullets(_section_text(markdown, "Secure Design Guidance"), limit=5)
    headings = [heading for heading in _headings(markdown) if heading in REQUIRED_SECTIONS]

    lines = [
        f"# Sketchnote Prompt: Chapter {metadata.number:02d} - {metadata.title}",
        "",
        "Create a clean sketchnote-style technical diagram for a handbook chapter.",
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
        "## Required Ideas To Show",
        *[f"- {heading}" for heading in headings[:8]],
        "",
        "## Learning Objectives",
        *[f"- {item}" for item in learning_objectives],
        "",
        "## Common Findings To Visualize",
        *[f"- {item}" for item in common_findings],
        "",
        "## Secure Guidance To Visualize",
        *[f"- {item}" for item in guidance],
        "",
        "## Output Requirement",
        "- Produce one landscape diagram suitable for insertion into a DOCX chapter.",
        "- Keep labels short enough to read when printed.",
        "- Use visual hierarchy: user/context on the left, core concepts in the center, outcomes/guidance on the right.",
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
        "Create one focused sketchnote-style diagram for this handbook section.",
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
    """Create a deterministic sketchnote-style SVG for a chapter."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    headings = [heading for heading in _headings(markdown) if heading in REQUIRED_SECTIONS]
    if len(headings) < 6:
        headings = REQUIRED_SECTIONS[:8]

    title = html.escape(metadata.title)
    center_labels = headings[:4]
    bottom_labels = headings[4:7]
    takeaway = headings[7] if len(headings) > 7 else "Key Takeaways"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
      <path d="M2,2 L10,6 L2,10 z" fill="#111111"/>
    </marker>
    <filter id="paper">
      <feTurbulence type="fractalNoise" baseFrequency="0.025" numOctaves="2" result="noise"/>
      <feColorMatrix type="saturate" values="0"/>
      <feBlend in="SourceGraphic" in2="noise" mode="multiply"/>
    </filter>
  </defs>
  <rect width="1600" height="950" fill="#fffdf7"/>
  <text x="800" y="70" text-anchor="middle" font-size="38" font-family="Comic Sans MS, Segoe Print, Arial" font-weight="700">{title}</text>
  <rect x="315" y="155" width="945" height="430" rx="24" fill="none" stroke="#777777" stroke-width="4" stroke-dasharray="14 12"/>
  <text x="787" y="205" text-anchor="middle" font-size="26" fill="#555555" font-family="Comic Sans MS, Segoe Print, Arial">Chapter Trust Boundary</text>

  {_box(55, 345, 180, 150, "#eef6ff", "#1e66b1", "Reader Context")}
  {_arrow(235, 420, 340, 420)}

  {_box(350, 300, 205, 155, "#fff4df", "#df7c18", center_labels[0])}
  {_arrow(555, 378, 610, 378)}
  {_box(620, 300, 205, 155, "#fff4df", "#df7c18", center_labels[1])}
  {_arrow(825, 378, 880, 378)}
  {_box(890, 300, 205, 155, "#fff4df", "#df7c18", center_labels[2])}
  {_arrow(1095, 378, 1150, 378)}
  {_box(1160, 300, 205, 155, "#fff4df", "#df7c18", center_labels[3])}

  {_box(405, 675, 210, 145, "#eef9ea", "#2e7d32", bottom_labels[0])}
  {_arrow(510, 675, 510, 455)}
  {_box(690, 675, 210, 145, "#eef9ea", "#2e7d32", bottom_labels[1])}
  {_arrow(795, 675, 795, 455)}
  {_box(975, 675, 210, 145, "#eef9ea", "#2e7d32", bottom_labels[2])}
  {_arrow(1080, 675, 1080, 455)}

  {_box(1365, 345, 180, 150, "#f0f7ff", "#1e66b1", takeaway)}
  {_arrow(1365, 420, 1255, 420)}

  <path d="M150 690 C230 610, 270 525, 345 445" fill="none" stroke="#d71920" stroke-width="4" stroke-dasharray="12 10" marker-end="url(#arrow)"/>
  <text x="140" y="735" text-anchor="middle" font-size="24" fill="#d71920" font-family="Comic Sans MS, Segoe Print, Arial">risk path</text>

  <rect x="55" y="800" width="260" height="95" rx="14" fill="#ffffff" stroke="#777777" stroke-width="3"/>
  {_arrow(85, 835, 145, 835)}
  <text x="225" y="844" text-anchor="middle" font-size="22" font-family="Comic Sans MS, Segoe Print, Arial">normal flow</text>
  {_arrow(85, 872, 145, 872, "#d71920", True)}
  <text x="225" y="881" text-anchor="middle" font-size="22" fill="#d71920" font-family="Comic Sans MS, Segoe Print, Arial">risk path</text>
</svg>
'''


def _summary_labels(chapter: int, stage: str) -> tuple[str, list[str]]:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    headings = [heading for heading in _headings(markdown) if heading in REQUIRED_SECTIONS]
    if len(headings) < 6:
        headings = REQUIRED_SECTIONS[:8]
    return metadata.title, ["Reader Context", *headings[:7]]


def _section_labels(chapter: int, section: str, stage: str) -> tuple[str, list[str]]:
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    section_body = _section_text(markdown, section)
    if not section_body:
        raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")
    labels = _concept_labels(
        section_body,
        fallback=[section, "risk", "control", "developer action", "security review"],
        limit=5,
    )
    return f"{metadata.title}: {section}", ["Context", *labels, "Outcome"]


def _render_png(output_path: Path, title: str, labels: list[str]) -> None:
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
        json.dumps({"title": title, "labels": labels, "output": str(output_path.resolve())}),
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
$fontTitle = New-Object System.Drawing.Font 'Arial',26,[System.Drawing.FontStyle]::Bold
$font = New-Object System.Drawing.Font 'Arial',18,[System.Drawing.FontStyle]::Regular
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
$textFlags = [System.Windows.Forms.TextFormatFlags]::HorizontalCenter -bor [System.Windows.Forms.TextFormatFlags]::VerticalCenter -bor [System.Windows.Forms.TextFormatFlags]::WordBreak
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
    """Create a deterministic sketchnote-style SVG for one section."""
    metadata = resolve_chapter(chapter)
    markdown = _chapter_text(chapter, stage)
    section_body = _section_text(markdown, section)
    if not section_body:
        raise ValueError(f"Section '{section}' was not found in chapter {chapter}.")

    labels = _concept_labels(
        section_body,
        fallback=[section, "risk", "control", "developer action", "security review"],
        limit=5,
    )
    title = html.escape(f"{metadata.title}: {section}")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="760" viewBox="0 0 1600 760">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
      <path d="M2,2 L10,6 L2,10 z" fill="#111111"/>
    </marker>
  </defs>
  <rect width="1600" height="760" fill="#fffdf7"/>
  <text x="800" y="70" text-anchor="middle" font-size="34" font-family="Comic Sans MS, Segoe Print, Arial" font-weight="700">{title}</text>
  <rect x="270" y="135" width="1060" height="330" rx="24" fill="none" stroke="#777777" stroke-width="4" stroke-dasharray="14 12"/>
  <text x="800" y="182" text-anchor="middle" font-size="24" fill="#555555" font-family="Comic Sans MS, Segoe Print, Arial">section focus</text>

  {_box(80, 265, 210, 150, "#eef6ff", "#1e66b1", "context")}
  {_arrow(290, 340, 380, 340)}
  {_box(390, 255, 225, 170, "#fff4df", "#df7c18", labels[0])}
  {_arrow(615, 340, 700, 340)}
  {_box(710, 255, 225, 170, "#fff4df", "#df7c18", labels[1])}
  {_arrow(935, 340, 1020, 340)}
  {_box(1030, 255, 225, 170, "#fff4df", "#df7c18", labels[2])}
  {_arrow(1255, 340, 1340, 340)}
  {_box(1350, 265, 190, 150, "#eef9ea", "#2e7d32", "outcome")}

  {_box(390, 545, 225, 135, "#eef9ea", "#2e7d32", labels[3])}
  {_arrow(502, 545, 502, 425)}
  {_box(985, 545, 225, 135, "#fef8df", "#d9a300", labels[4])}
  {_arrow(1097, 545, 1097, 425)}

  <path d="M185 610 C250 560, 310 480, 390 408" fill="none" stroke="#d71920" stroke-width="4" stroke-dasharray="12 10" marker-end="url(#arrow)"/>
  <text x="165" y="655" text-anchor="middle" font-size="23" fill="#d71920" font-family="Comic Sans MS, Segoe Print, Arial">risk path</text>
</svg>
'''


def generate_sketchnote_image(chapter: int, stage: str = "final") -> Path:
    """Generate and save a deterministic chapter summary SVG sketchnote."""
    generate_sketchnote_prompt(chapter, stage=stage)
    path = image_path_for(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sketchnote_svg(chapter, stage=stage), encoding="utf-8")
    title, labels = _summary_labels(chapter, stage)
    _render_png(png_path_for(chapter), title, labels)
    return png_path_for(chapter)


def generate_section_sketchnote_image(chapter: int, section: str, stage: str = "final") -> Path:
    """Generate and save a deterministic SVG for one section."""
    generate_section_sketchnote_prompt(chapter, section, stage=stage)
    path = section_image_path_for(chapter, section)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(section_sketchnote_svg(chapter, section, stage=stage), encoding="utf-8")
    title, labels = _section_labels(chapter, section, stage)
    _render_png(section_png_path_for(chapter, section), title, labels)
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
                    caption=f"Sketchnote for Chapter {chapter:02d}: {section}.",
                    status="generated" if image_path.exists() else "missing",
                )
            )
    write_diagram_registry(chapter, artifacts)
    return paths
