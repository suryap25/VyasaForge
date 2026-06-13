# AppSec Handbook Agent Roadmap

Goal:
Build a configurable long-form technical document production system. The AppSec Authentication and Authorization handbook is the first use case.

## Current Capability

The utility can:

- Plan a handbook TOC from a topic.
- Update the TOC from user requirements with clarification handling.
- Generate structured chapter briefs.
- Generate chapter drafts with configurable LLM providers.
- Validate required structure and word count.
- Repair missing sections and unbalanced code fences.
- Review chapters with a reviewer role.
- Revise chapters with safety gates.
- Optionally apply expert enhancement and reference enrichment.
- Finalize chapters from selected sources.
- Run deterministic chapter and handbook QA.
- Compile DOCX/PDF through Pandoc.
- Track per-chapter state and LLM token usage.
- Switch model providers through provider profiles.
- Manage multiple handbook workspaces under `handbooks/<handbook-name>/`.

Removed:

- Sketchnote generation.
- Diagram generation.
- Diagram QA and DOCX insertion.

## Active Pipeline

```text
plan-handbook
use-handbook / list-handbooks
generate-briefs
run-chapter / run-chapters
  create-chapter
  write-chapter
  validate drafts
  repair drafts if needed
  review-chapter
  revise-chapter
  validate reviewed
  expert-enhance-chapter
  add-references
  finalize-chapter
  validate final
  qa-handbook
  compile-docx
  handbook-status
  llm-usage
```

## Next Priorities

1. Reliability hardening for multi-chapter runs.
2. Better failure recovery and resumability from chapter state.
3. Better cost reporting per run instead of all-time log totals.
4. Stronger TOC and brief schemas.
5. Better reference quality gates.
6. Improved DOCX styling and front matter.
7. Full handbook generation across all planned chapters.
8. Workspace cleanup/archive commands.

## Out Of Scope

Visual diagram generation is intentionally out of scope for the current utility.
