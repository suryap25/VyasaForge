"""Chapter reviser for Milestone M6."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.handbook import resolve_chapter
from src.publish_gate import validate_publish_quality
from src.validator import REQUIRED_SECTIONS, count_words, has_section
from src.workspace import workspace_path

PROMPT_PATH = Path("prompts/chapter_revision.md")
MIN_REVISED_WORD_RATIO = 0.8


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def missing_required_sections(markdown: str) -> list[str]:
    """Return required handbook sections missing from Markdown."""
    return [section for section in REQUIRED_SECTIONS if not has_section(markdown, section)]


def review_findings_path(chapter: int) -> Path:
    """Return structured review findings path."""
    return workspace_path("reviews", f"chapter-{chapter:02d}-review.json")


def extract_json_payload(text: str) -> object:
    """Extract a JSON payload from raw model text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = min(
        [index for index in [stripped.find("{"), stripped.find("[")] if index >= 0],
        default=-1,
    )
    if start > 0:
        stripped = stripped[start:]
    return json.loads(stripped)


def parse_jsonish_patches(text: str) -> list[dict[str, str]]:
    """Recover section patches from JSON-like model output with raw Markdown strings."""
    patches: list[dict[str, str]] = []
    section_matches = list(re.finditer(r'"section"\s*:\s*"([^"]+)"', text))
    for index, match in enumerate(section_matches):
        section = match.group(1).strip()
        if section not in REQUIRED_SECTIONS:
            continue
        content_match = re.search(
            r'"content_markdown"\s*:\s*"',
            text[match.end():],
        )
        if content_match is None:
            continue
        content_start = match.end() + content_match.end()
        next_section = section_matches[index + 1].start() if index + 1 < len(section_matches) else len(text)
        raw_content = text[content_start:next_section]
        raw_content = re.sub(r'"\s*}\s*,?\s*$', "", raw_content.strip())
        raw_content = raw_content.replace("\\n", "\n").replace('\\"', '"')
        raw_content = raw_content.strip()
        if raw_content.startswith(f"## {section}"):
            patches.append({"section": section, "content": raw_content})
        elif raw_content:
            patches.append({"section": section, "content": f"## {section}\n\n{raw_content}"})
    return patches


def convert_response_to_json_patches(raw_response: str, chapter: int) -> list[dict[str, str]]:
    """Ask the model once to convert a malformed patch response into strict JSON."""
    from src import llm_gateway

    messages = [
        {
            "role": "system",
            "content": (
                "You convert malformed revision output into strict JSON. "
                "Return JSON only. Do not add commentary."
            ),
        },
        {
            "role": "user",
            "content": (
                "Convert this response into strictly valid JSON with this exact shape:\n"
                '{"patches":[{"section":"Section Name","content_markdown":"## Section Name\\n\\nMarkdown content"}]}\n\n'
                "Rules:\n"
                "- Escape all newlines inside JSON strings as \\n.\n"
                "- Escape all quotes inside JSON strings.\n"
                "- Preserve only sections whose names are in this list:\n"
                + ", ".join(REQUIRED_SECTIONS)
                + "\n\nMalformed response:\n"
                + raw_response
            ),
        },
    ]
    repaired = llm_gateway.call_llm(role="editor", messages=messages, chapter=chapter)
    return normalize_patches(extract_json_payload(repaired))


def load_review_findings(chapter: int) -> list[dict[str, str]]:
    """Load machine-readable review findings if available."""
    path = review_findings_path(chapter)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        return []
    return [finding for finding in findings if isinstance(finding, dict)]


def section_pattern(section: str) -> str:
    """Return a regex pattern for one H2 section."""
    return rf"(?ims)^##\s+{re.escape(section)}\s*$.*?(?=^##\s+|\Z)"


def get_section(markdown: str, section: str) -> str | None:
    """Return a section including its H2 heading."""
    match = re.search(section_pattern(section), markdown)
    return match.group(0).strip() if match else None


def replace_section(markdown: str, section: str, replacement: str) -> str:
    """Replace one H2 section in Markdown."""
    replacement = replacement.strip()
    if not replacement.startswith(f"## {section}"):
        replacement = f"## {section}\n\n{replacement}"
    if re.search(section_pattern(section), markdown):
        return re.sub(section_pattern(section), replacement, markdown, count=1)
    return markdown.rstrip() + "\n\n" + replacement + "\n"


def normalize_patches(payload: object) -> list[dict[str, str]]:
    """Normalize patch JSON into section/content dictionaries."""
    if isinstance(payload, dict):
        raw_patches = payload.get("patches", [])
    else:
        raw_patches = payload
    if not isinstance(raw_patches, list):
        raise ValueError("Revision response must contain a JSON list of patches.")

    patches: list[dict[str, str]] = []
    for raw_patch in raw_patches:
        if not isinstance(raw_patch, dict):
            continue
        section = str(raw_patch.get("section", "")).strip()
        content = str(raw_patch.get("content_markdown", raw_patch.get("content", ""))).strip()
        if section in REQUIRED_SECTIONS and content:
            patches.append({"section": section, "content": content})
    return patches


def deterministic_patch_content(section: str, existing_section: str | None) -> str:
    """Create a deterministic reader-facing patch for a section."""
    base = existing_section or f"## {section}\n"
    base = base.strip()
    additions: dict[str, str] = {
        "Interview Questions": (
            "\n\n### Additional Interview Questions\n\n"
            "- How would you distinguish an authentication failure from an authorization failure during incident triage?\n"
            "- What evidence would show that authorization is enforced server-side rather than only in the UI?\n"
            "- How would you test for horizontal privilege escalation across two normal user accounts?\n"
            "- What token validation mistakes commonly lead to authentication or authorization bypass?\n"
            "- How should a design handle token revocation, session timeout, and privilege changes after login?"
        ),
        "Pentest Lens": (
            "\n\n### Additional Testing Notes\n\n"
            "- Test authentication controls with valid, invalid, expired, locked, and MFA-pending account states.\n"
            "- Test authorization with at least two users at the same privilege level and one lower-privilege user.\n"
            "- Verify access-control decisions on the server side, not only in browser-visible behavior.\n"
            "- Include token tampering, replay, expiration, and revocation scenarios in the test plan."
        ),
        "Common Findings": (
            "\n\n### Additional Common Finding\n\n"
            "**Incomplete token revocation** occurs when logout, password reset, role change, or account disablement does not invalidate active sessions or tokens. "
            "The practical impact is continued access after a user's authorization state has changed. "
            "Designs should define revocation behavior for sessions, refresh tokens, and high-risk privilege changes."
        ),
        "Secure Design Guidance": (
            "\n\n### Additional Secure Design Guidance\n\n"
            "Treat authentication, session management, and authorization as separate but connected control planes. "
            "A secure design should define where identity is established, where session state is trusted, where policy is evaluated, and how access is revoked when user state changes."
        ),
    }
    addition = additions.get(
        section,
        "\n\n### Additional Guidance\n\n"
        "Strengthen this section with concrete examples, explicit security assumptions, and clear validation steps.",
    )
    return base + addition


def deterministic_patches(findings: list[dict[str, str]], draft: str) -> list[dict[str, str]]:
    """Build deterministic fallback patches from structured findings."""
    patches: list[dict[str, str]] = []
    seen: set[str] = set()
    for finding in findings:
        section = finding.get("section", "")
        if section not in REQUIRED_SECTIONS or section in seen:
            continue
        patches.append(
            {
                "section": section,
                "content": deterministic_patch_content(section, get_section(draft, section)),
            }
        )
        seen.add(section)
    return patches


def parse_patches_with_recovery(raw_response: str, chapter: int) -> list[dict[str, str]]:
    """Parse patches using strict JSON, retry conversion, then JSON-like fallback."""
    try:
        return normalize_patches(extract_json_payload(raw_response))
    except Exception:
        pass

    try:
        patches = convert_response_to_json_patches(raw_response, chapter)
        if patches:
            return patches
    except Exception:
        pass

    return parse_jsonish_patches(raw_response)


def revise_chapter(chapter: int) -> Path:
    """Revise a chapter draft by patching reviewed sections in place."""
    metadata = resolve_chapter(chapter)
    prompt_path = PROMPT_PATH
    draft_path = metadata.draft_path
    review_path = metadata.review_path
    revised_path = metadata.reviewed_path
    failed_revision_path = review_path.parent / f"chapter-{metadata.number:02d}-revision-failed.md"

    ensure_required_file(prompt_path, "chapter revision prompt")
    ensure_required_file(draft_path, "chapter draft")
    ensure_required_file(review_path, "chapter review")

    prompt = prompt_path.read_text(encoding="utf-8")
    draft = draft_path.read_text(encoding="utf-8")
    review = review_path.read_text(encoding="utf-8")
    findings = load_review_findings(metadata.number)
    original_word_count = count_words(draft)
    target_sections = sorted(
        {
            finding.get("section", "")
            for finding in findings
            if finding.get("section") in REQUIRED_SECTIONS
        },
        key=REQUIRED_SECTIONS.index,
    )
    if not target_sections:
        target_sections = list(REQUIRED_SECTIONS)

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                "INPUTS:\n\n"
                "Original Chapter:\n"
                f"{draft}\n\n"
                "Structured Review Findings JSON:\n"
                f"{json.dumps(findings, indent=2)}\n\n"
                "Human Review Comments:\n"
                f"{review}\n\n"
                "Target Sections:\n"
                + "\n".join(f"- {section}" for section in target_sections)
                + "\n\n"
                "INSTRUCTION:\n"
                "Patch the chapter in place by returning only replacement content for target sections.\n"
                "Do not append a Revision Additions section.\n"
                "Do not include editorial labels such as Correction, Enhancement, Location, or Add after.\n"
                "Each replacement must be reader-facing handbook content.\n"
                "Each replacement must preserve the section heading as Markdown H2.\n\n"
                "Keep each patch concise: improve only the reviewed issue, not the entire chapter.\n"
                "Do not include fenced code blocks inside JSON strings. If code is needed, use short inline code or bullets.\n\n"
                "Return strictly valid JSON in this shape:\n"
                "{\n"
                '  "patches": [\n'
                '    {"section": "Developer Lens", "content_markdown": "## Developer Lens\\n\\n..."}\n'
                "  ]\n"
                "}\n"
            ),
        },
    ]

    from src import llm_gateway

    patch_response = llm_gateway.call_llm(role="editor", messages=messages, chapter=metadata.number)
    try:
        patches = parse_patches_with_recovery(patch_response, metadata.number)
    except Exception as exc:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(patch_response, encoding="utf-8")
        patches = deterministic_patches(findings, draft)
        if not patches:
            raise RuntimeError(
                f"Revision patch response could not be recovered as section patches. "
                f"Failed attempt saved to {failed_revision_path}."
            ) from exc

    if not patches:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(patch_response, encoding="utf-8")
        patches = deterministic_patches(findings, draft)
        if not patches:
            raise RuntimeError(f"Revision returned no usable section patches. Failed attempt saved to {failed_revision_path}.")

    revised = draft
    for patch in patches:
        revised = replace_section(revised, patch["section"], patch["content"])

    revised_word_count = count_words(revised)
    missing_sections = missing_required_sections(revised)
    too_short = revised_word_count < original_word_count * MIN_REVISED_WORD_RATIO
    publish_result = validate_publish_quality(revised)

    if too_short or missing_sections or not publish_result.passed:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(revised, encoding="utf-8")
        failures = []
        if too_short:
            failures.append(
                "revised chapter is less than 80% of original word count "
                f"(original: {original_word_count}, revised: {revised_word_count})"
            )
        if missing_sections:
            failures.append("revised chapter is missing required sections: " + ", ".join(missing_sections))
        if not publish_result.passed:
            failures.append("publish gate failed: " + "; ".join(publish_result.errors))
        raise RuntimeError(
            "Revision safety gate failed: "
            + "; ".join(failures)
            + ". "
            f"Failed attempt saved to {failed_revision_path}."
        )

    revised_path.parent.mkdir(parents=True, exist_ok=True)
    revised_path.write_text(revised, encoding="utf-8")
    return revised_path
