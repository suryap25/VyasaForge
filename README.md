# VyasaForge

Forge structured knowledge into publishable documents.

**Plan. Write. Review. Publish.**

VyasaForge is a configurable multi-agent documentation production CLI. It can
plan, write, review, validate, repair, finalize, and compile structured
documents such as handbooks, guides, runbooks, PRDs, architecture docs,
security playbooks, and technical manuals.

The AppSec Authentication & Authorization Handbook is the first example use
case. It is not the product boundary.

## Pipeline

```text
Topic -> TOC -> Briefs -> Drafts -> Review -> Validation -> Repair -> Finalization -> DOCX
```

The current implementation supports:

- topic-driven TOC planning
- chapter brief generation
- configurable LLM-backed writing
- deterministic validation and repair
- reviewer and revision agents with safety gates
- final Markdown stages
- DOCX/PDF compilation through Pandoc
- provider abstraction through LiteLLM
- per-handbook workspaces
- state and token usage tracking

Visual/sketchnote/diagram generation has been removed. The current focus is
reliable text generation, review, validation, finalization, and document
compilation.

## Installation

From the project root:

```powershell
python -m pip install -e .
```

This installs the CLI entry points:

```powershell
vyasaforge --help
vf --help
```

On Windows, if `vf` is not found after installation, add your user Python
Scripts directory to `PATH`, for example:

```text
C:\Users\<you>\AppData\Roaming\Python\Python314\Scripts
```

The legacy module invocation remains supported:

```powershell
python -m src.cli --help
```

## Prerequisites

Install Pandoc and make sure it is available on `PATH`:

```powershell
pandoc --version
```

Pandoc is required for native DOCX compilation. If Pandoc is missing,
VyasaForge stops at compilation instead of producing a lower-quality fallback.

Set the provider API key in your shell. For Claude/Anthropic:

```powershell
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

API keys are read from environment variables only. Do not put secrets in config
files.

## Quick Start

Initialize local workspace folders and run diagnostics:

```powershell
vf init
```

Plan a document from a topic:

```powershell
vf plan --topic "Cloud Security focussing on AWS"
```

Generate chapter briefs:

```powershell
vf generate-briefs
```

Run the full pipeline for Chapter 1:

```powershell
vf run-chapter --chapter 1
```

Check status:

```powershell
vf handbook-status
```

Compile final chapters into DOCX:

```powershell
vf compile-docx --chapters 1
```

The same workflow also works with the legacy module path:

```powershell
python -m src.cli plan-handbook --topic "Cloud Security focussing on AWS"
python -m src.cli generate-briefs
python -m src.cli run-chapter --chapter 1
python -m src.cli compile-docx --chapters 1
```

## Workspaces

Each planned document gets its own workspace:

```text
handbooks/<document-name>/
  handbook.yaml
  chapters/
  reviews/
  reports/
  output/
  logs/
```

For example:

```powershell
vf plan --topic "Cloud Security focussing on AWS"
```

creates and activates:

```text
handbooks/aws-cloud-security/
```

Expected outputs include:

```text
handbooks/<document-name>/handbook.yaml
handbooks/<document-name>/chapters/briefs/chapter-01.md
handbooks/<document-name>/chapters/drafts/chapter-01.md
handbooks/<document-name>/chapters/reviewed/chapter-01.md
handbooks/<document-name>/chapters/final/chapter-01.md
handbooks/<document-name>/chapters/state/chapter-01.json
handbooks/<document-name>/reviews/chapter-01-review.md
handbooks/<document-name>/logs/llm-usage.jsonl
handbooks/<document-name>/output/<document-name>.docx
```

Global provider/model settings remain in `configs/`.

## Common Commands

Diagnostics:

```powershell
vf doctor
vf list-providers
vf provider-status
```

Provider switching:

```powershell
vf use-provider --profile anthropic_haiku
vf use-provider --profile openai_gpt
vf use-provider --profile gemini_flash
vf use-provider --profile ollama_local
```

Workspace management:

```powershell
vf list-handbooks
vf use-handbook --name aws-cloud-security
```

Planning and TOC updates:

```powershell
vf plan --topic "AppSec Authentication and Authorization"
vf plan --topic "OAuth 2.0 for Developers" --chapters 6
vf update-toc --input user_requirements.md
```

Chapter pipeline:

```powershell
vf generate-briefs --chapters 1,2,3 --overwrite
vf validate-brief --chapter 1
vf write-chapter --chapter 1
vf validate-chapter --chapter 1 --stage drafts
vf repair-chapter --chapter 1 --stage drafts
vf review-chapter --chapter 1
vf revise-chapter --chapter 1
vf finalize-chapter --chapter 1 --source reviewed
```

Compilation and reporting:

```powershell
vf compile-docx --chapters 1
vf compile-handbook --chapters 1 --format docx
vf compile-handbook --chapters 1 --format pdf
vf handbook-status
vf llm-usage --chapter 1
vf qa-handbook --chapters 1 --stage final
```

Run multiple chapters:

```powershell
vf run-chapters --chapters 1,2,3
```

`run-chapters` compiles once at the end after all requested chapters complete.

## Safety Gates

VyasaForge uses deterministic gates around agent output:

- required section validation
- word count checks
- fenced code block checks
- publish-quality checks
- revision safety gates
- handbook-level QA

If revision fails the safety gate, the pipeline can fall back to a validated
draft so the document can still progress to finalization.

## Open Source

Useful project documents:

- [Architecture](docs/architecture.md)
- [Branding](docs/branding.md)
- [Vision](docs/vision.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Notes

- AppSec prompts and configs remain as the first sample use case.
- LLM prompts and API keys are not written to usage logs.
- Token usage is logged to `handbooks/<document-name>/logs/llm-usage.jsonl`
  when a workspace is active.
