"""Controlled multi-agent contract registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentContract:
    """Input, output, and validation contract for one controlled agent."""

    name: str
    role: str | None
    input_contract: str
    output_contract: str
    validation_gate: str
    enabled: bool = True


AGENT_CONTRACTS = [
    AgentContract(
        name="Planner Agent",
        role="planner",
        input_contract="Topic, optional audience, depth, pages, and optional exact chapter count.",
        output_contract="Normalized configs/handbook.yaml registry.",
        validation_gate="Registry must parse and contain numbered chapters with file paths.",
    ),
    AgentContract(
        name="TOC Override Agent",
        role="toc_editor",
        input_contract="Existing handbook.yaml plus user requirements Markdown.",
        output_contract="Updated handbook.yaml or clarification questions without changing the registry.",
        validation_gate="Ambiguous requirements must stop with clarification questions.",
    ),
    AgentContract(
        name="Chapter Writer Agent",
        role="writer",
        input_contract="Chapter brief, generation prompt, and handbook registry metadata.",
        output_contract="Markdown draft in chapters/drafts.",
        validation_gate="Draft must pass required-section and word-count validation.",
    ),
    AgentContract(
        name="Section Patcher Agent",
        role="writer",
        input_contract="Existing chapter plus structured validator failures.",
        output_contract="Only missing or weak sections appended to the same chapter file.",
        validation_gate="Patched chapter must pass validation before the pipeline continues.",
    ),
    AgentContract(
        name="AppSec Reviewer Agent",
        role="reviewer",
        input_contract="Chapter draft and chapter review prompt.",
        output_contract="Review notes in reviews/chapter-NN-review.md.",
        validation_gate="Review file must exist before revision.",
    ),
    AgentContract(
        name="Editor Agent",
        role="editor",
        input_contract="Original draft plus review comments.",
        output_contract="Section patch JSON applied in place to produce reviewed Markdown.",
        validation_gate="Revision must preserve required sections, avoid editorial markers, and keep at least 80% of draft word count.",
    ),
    AgentContract(
        name="Publish Gate Agent",
        role=None,
        input_contract="Draft, reviewed, or final chapter Markdown.",
        output_contract="Deterministic pass/fail publish-quality result.",
        validation_gate="No LLM calls; final artifacts with revision notes, broken fences, or unresolved placeholders fail.",
    ),
    AgentContract(
        name="QA Agent",
        role=None,
        input_contract="Final or reviewed chapter files and chapter state JSON.",
        output_contract="Deterministic handbook QA report.",
        validation_gate="No LLM calls; report must list pass/fail checks.",
    ),
    AgentContract(
        name="Compiler Agent",
        role=None,
        input_contract="Validated final Markdown chapters.",
        output_contract="DOCX or PDF under output/.",
        validation_gate="Pandoc must be installed and compilation must exit successfully.",
    ),
]


def agent_status_rows() -> list[list[str]]:
    """Return agent contract rows for compact CLI output."""
    rows = []
    for contract in AGENT_CONTRACTS:
        rows.append(
            [
                contract.name,
                contract.role or "-",
                "yes" if contract.enabled else "no",
                contract.validation_gate,
            ]
        )
    return rows
