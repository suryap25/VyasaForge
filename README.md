# AppSec Handbook Agent

Configurable document production pipeline for generating long-form technical handbooks. The AppSec Authentication and Authorization handbook is the first supported use case.

## Current Status

The utility supports topic-driven handbook planning and chapter generation:

```text
topic -> handbook TOC -> chapter briefs -> write -> validate -> repair -> review -> revise -> enhance -> references -> finalize -> QA -> compile DOCX/PDF -> status
```

The visual/sketchnote/diagram generation layer has been removed. The current focus is reliable text generation, review, validation, finalization, and document compilation.

Each planned handbook gets its own workspace:

```text
handbooks/<handbook-name>/
  handbook.yaml
  chapters/
  reviews/
  reports/
  output/
  logs/
```

Global provider/model settings remain in `configs/`.

## Prerequisites

Install Python dependencies from the project root:

```powershell
cd C:\Users\surya\Developer\devEnv\appsec-handbook-agent
python -m pip install -e .
```

Install Pandoc and make sure it is available on `PATH`:

```powershell
pandoc --version
```

Pandoc is required for native DOCX compilation. If Pandoc is missing, the pipeline stops at `compile-docx` instead of creating a lower-quality fallback DOCX.

Set the provider API key in your shell. For Claude/Anthropic:

```powershell
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

The API key is read from the environment only. Do not put secrets in config files.

## Check Configuration

Run diagnostics before calling the model:

```powershell
python -m src.cli doctor
```

This checks:

- `configs/phase1.example.json`
- the active handbook registry under `handbooks/<handbook-name>/handbook.yaml`
- configured LLM roles and model names
- expected provider environment variables
- whether the required API key variable is present

## End-to-End Run

If you deleted folders inside a handbook workspace, such as `handbooks/<handbook-name>/chapters/briefs`, `chapters/drafts`, `chapters/reviewed`, or `chapters/final`, the commands below will recreate the needed folders as files are generated.

Plan a handbook from a topic:

```powershell
python -m src.cli plan-handbook --topic "AppSec Authentication and Authorization"
```

This creates and activates a workspace such as:

```text
handbooks/appsec-authentication-authorization/
```

For a topic like:

```powershell
python -m src.cli plan-handbook --topic "Cloud Security focusing on AWS"
```

The workspace name is normalized to:

```text
handbooks/aws-cloud-security/
```

Generate chapter briefs:

```powershell
python -m src.cli generate-briefs
```

Run the full Chapter 1 pipeline:

```powershell
python -m src.cli run-chapter --chapter 1
```

The pipeline runs these stages:

```text
create-chapter
write-chapter
validate-chapter --stage drafts
repair-chapter --stage drafts, if needed
validate-chapter --stage drafts
review-chapter
revise-chapter
validate-chapter --stage reviewed
expert-enhance-chapter
add-references
finalize-chapter
validate-chapter --stage final
qa-handbook --stage final
compile-docx
handbook-status
llm-usage
```

If revision fails the safety gate, the pipeline falls back to finalizing the validated draft so MVP1 can still complete.

Draft repair handles missing required sections and can deterministically close an unbalanced fenced code block. If the LLM repair call is unavailable, the repairer falls back to local section scaffolds so the pipeline can continue with clear placeholders for later enrichment.

## Verify Outputs

Validate each stage:

```powershell
python -m src.cli validate-chapter --chapter 1 --stage drafts
python -m src.cli validate-chapter --chapter 1 --stage reviewed
python -m src.cli validate-chapter --chapter 1 --stage final
```

Show state and dashboard:

```powershell
python -m src.cli show-state --chapter 1
python -m src.cli handbook-status
```

Expected outputs:

```text
handbooks/<handbook-name>/handbook.yaml
handbooks/<handbook-name>/chapters/briefs/chapter-01.md
handbooks/<handbook-name>/chapters/drafts/chapter-01.md
handbooks/<handbook-name>/chapters/reviewed/chapter-01.md
handbooks/<handbook-name>/chapters/enhanced/chapter-01.md
handbooks/<handbook-name>/chapters/referenced/chapter-01.md
handbooks/<handbook-name>/chapters/final/chapter-01.md
handbooks/<handbook-name>/chapters/state/chapter-01.json
handbooks/<handbook-name>/reviews/chapter-01-review.md
handbooks/<handbook-name>/logs/llm-usage.jsonl
handbooks/<handbook-name>/output/<handbook-name>.docx
```

## Useful Individual Commands

```powershell
python -m src.cli test-model --role writer
python -m src.cli generate-briefs --chapters 1,2 --overwrite
python -m src.cli write-chapter --chapter 1
python -m src.cli repair-chapter --chapter 1 --stage drafts
python -m src.cli review-chapter --chapter 1
python -m src.cli revise-chapter --chapter 1
python -m src.cli finalize-chapter --chapter 1 --source reviewed
python -m src.cli finalize-chapter --chapter 1 --source drafts
python -m src.cli compile-docx --chapters 1
python -m src.cli diff-chapter --chapter 1 --from-stage drafts --to-stage final
python -m src.cli llm-usage --chapter 1
```

## Configurable Engine Commands

List and switch handbook workspaces:

```powershell
python -m src.cli list-handbooks
python -m src.cli use-handbook --name aws-cloud-security
```

Create or refresh structured chapter briefs from the active handbook registry:

```powershell
python -m src.cli generate-briefs --chapters 1,2,3 --overwrite
```

Run multiple registered chapters in order:

```powershell
python -m src.cli run-chapters --chapters 1,2,3
```

This compiles once at the end after all requested chapters complete.

Plan a new handbook TOC from a topic:

```powershell
python -m src.cli plan-handbook --topic "AppSec Authentication and Authorization"
```

The planner chooses the recommended chapter count when `--chapters` is omitted. Optional constraints can guide the recommendation:

```powershell
python -m src.cli plan-handbook `
  --topic "Cloud Security for Product Security Engineers" `
  --audience "AppSec Engineers, Developers" `
  --depth intermediate `
  --pages 120
```

Use `--chapters` only when you want to force an exact chapter count:

```powershell
python -m src.cli plan-handbook --topic "OAuth 2.0 for Developers" --chapters 6
```

Update the TOC from user requirements:

```powershell
python -m src.cli update-toc --input user_requirements.md
```

If the requirements are ambiguous, the TOC is not changed. Clarification questions are written to:

```text
handbooks/<handbook-name>/configs/handbook-clarification-questions.md
```

## Chapter Brief Factory

Generate execution contracts from the current handbook registry:

```powershell
python -m src.cli generate-briefs --chapters 1,2,3 --overwrite
```

Validate a generated brief:

```powershell
python -m src.cli validate-brief --chapter 1
```

Expected output:

```text
PASS: handbooks\<handbook-name>\chapters\briefs\chapter-01.md
```

Each brief includes the chapter goal, audience, target word count, required handbook sections, must-cover topics, examples required, references guidance, and quality gates.

## Controlled Agent Contracts

Show the controlled multi-agent contract registry:

```powershell
python -m src.cli agent-status
```

This does not call the LLM. It prints each agent, its configured LLM role if any, and the validation gate that controls its output.

## Handbook QA

Run deterministic book-level QA after final chapters exist:

```powershell
python -m src.cli qa-handbook --chapters 1 --stage final
```

Expected output:

```text
PASS: handbook QA
Stage: final
Chapters checked: 1
Wrote QA report: handbooks\<handbook-name>\reports\handbook-qa.md
```

The QA report checks chapter validation status, missing sections, weak interview-question sections, duplicate chapter titles, and large chapter-length imbalance. It does not call the LLM.

## Document Compiler

Compile a native DOCX with Pandoc, table of contents, and numbered sections:

```powershell
python -m src.cli compile-handbook --chapters 1 --format docx
```

Optional PDF output:

```powershell
python -m src.cli compile-handbook --chapters 1 --format pdf
```

PDF support depends on the local Pandoc PDF toolchain. DOCX remains the primary supported output.

## M21-M25: Publish Reliability

Run the publish-quality gate against a chapter stage:

```powershell
python -m src.cli publish-gate --chapter 1 --stage final
```

The gate rejects structural and publishing problems such as:

```text
Revision Additions
Correction / Enhancement process markers
unbalanced code fences
duplicate required sections
```

Structured review findings are written beside the human review:

```text
handbooks/<handbook-name>/reviews/chapter-01-review.md
handbooks/<handbook-name>/reviews/chapter-01-review.json
```

The reviser now expects section-patch JSON and replaces target sections in place. It no longer appends a `Revision Additions` section.

Compile now runs a publish gate before Pandoc.

## Notes

- `run-chapter` creates the chapter brief automatically before writing.
- LLM prompts and API keys are not written to the usage log.
- Token usage is logged to `handbooks/<handbook-name>/logs/llm-usage.jsonl` when a handbook workspace is active.
