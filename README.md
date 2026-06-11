# AppSec Handbook Agent

Configurable document production pipeline for generating an AppSec Authentication and Authorization handbook.

## MVP1 Status

MVP1 supports one chapter end to end:

```text
create brief -> write draft -> validate -> repair -> review -> revise -> finalize -> compile DOCX -> status
```

The current MVP is focused on Chapter 1: Authentication vs Authorization.

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
- `configs/handbook.yaml`
- configured LLM roles and model names
- expected provider environment variables
- whether the required API key variable is present

## MVP1 End-to-End Run

If you deleted `chapters/briefs`, `chapters/drafts`, `chapters/reviewed`, or `chapters/final`, the commands below will recreate the needed folders as files are generated.

Create the Chapter 1 brief:

```powershell
python -m src.cli create-chapter --chapter 1
```

Run the full Chapter 1 pipeline:

```powershell
python -m src.cli run-chapter --chapter 1
```

The pipeline runs these stages:

```text
write-chapter
validate-chapter --stage drafts
repair-chapter --stage drafts, if needed
validate-chapter --stage drafts
review-chapter
revise-chapter
validate-chapter --stage reviewed
finalize-chapter
validate-chapter --stage final
compile-docx
handbook-status
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

Expected MVP1 outputs:

```text
chapters/briefs/chapter-01.md
chapters/drafts/chapter-01.md
chapters/reviewed/chapter-01.md
chapters/final/chapter-01.md
chapters/state/chapter-01.json
reviews/chapter-01-review.md
logs/llm-usage.jsonl
output/AppSec_Authentication_Authorization_Handbook_Phase1.docx
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

Create or refresh structured chapter briefs from `configs/handbook.yaml`:

```powershell
python -m src.cli generate-briefs --chapters 1,2,3 --overwrite
```

Run multiple registered chapters in order:

```powershell
python -m src.cli run-chapters --chapters 1,2,3
```

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
configs/handbook-clarification-questions.md
```

## Phase 5: Chapter Brief Factory

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
PASS: chapters\briefs\chapter-01.md
```

Each brief includes the chapter goal, audience, target word count, required handbook sections, must-cover topics, examples required, references guidance, diagram placeholder expectations, and quality gates.

## Phase 6: Controlled Agent Contracts

Show the controlled multi-agent contract registry:

```powershell
python -m src.cli agent-status
```

This does not call the LLM. It prints each agent, its configured LLM role if any, and the validation gate that controls its output.

## Phase 7: Handbook QA

Run deterministic book-level QA after final chapters exist:

```powershell
python -m src.cli qa-handbook --chapters 1 --stage final
```

Expected output:

```text
PASS: handbook QA
Stage: final
Chapters checked: 1
Wrote QA report: reports\handbook-qa.md
```

The QA report checks chapter validation status, missing sections, weak interview-question sections, sketchnote placeholder issues, duplicate chapter titles, and large chapter-length imbalance. It does not call the LLM.

## Phase 8: Document Compiler v2

Compile a native DOCX with Pandoc, table of contents, and numbered sections:

```powershell
python -m src.cli compile-handbook --chapters 1 --format docx
```

Optional PDF output:

```powershell
python -m src.cli compile-handbook --chapters 1 --format pdf
```

PDF support depends on the local Pandoc PDF toolchain. DOCX remains the primary supported output.

## Phase 9: Sketchnotes

Generate reusable sketchnote prompts from final chapter content:

```powershell
python -m src.cli generate-sketchnote-prompts --chapters 1 --stage final
```

Expected output:

```text
sketchnotes/prompts/chapter-01-prompt.md
```

Generate deterministic local sketchnotes:

```powershell
python -m src.cli generate-sketchnotes --chapters 1 --stage final
```

Expected output:

```text
sketchnotes/images/chapter-01.svg
sketchnotes/images/chapter-01.png
sketchnotes/images/chapter-01/<section>.svg
sketchnotes/images/chapter-01/<section>.png
```

Compile the handbook after sketchnotes exist:

```powershell
python -m src.cli compile-handbook --chapters 1 --format docx
```

The generator keeps SVG source files and also creates DOCX-compatible PNG files. The compiler prefers PNG images and replaces `[SKETCHNOTE DIAGRAM PLACEHOLDER]` with the generated chapter image when it exists. If the image does not exist, the placeholder remains visible.

The normal chapter pipeline now runs sketchnote prompt generation and local image generation before DOCX compilation:

```powershell
python -m src.cli run-chapter --chapter 1
```

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
unresolved sketchnote placeholders at compile time
```

Structured review findings are written beside the human review:

```text
reviews/chapter-01-review.md
reviews/chapter-01-review.json
```

The reviser now expects section-patch JSON and replaces target sections in place. It no longer appends a `Revision Additions` section.

Sketchnote and diagram artifacts are tracked in:

```text
diagrams/chapter-01.json
```

Inspect diagram status:

```powershell
python -m src.cli diagram-status --chapter 1
```

Compile now runs a publish gate before Pandoc. Sketchnotes are compiled from PNG files by default so Pandoc does not require `rsvg-convert` for the normal DOCX path.

## Notes

- `run-chapter` creates the chapter brief automatically before writing.
- LLM prompts and API keys are not written to the usage log.
- Token usage is logged to `logs/llm-usage.jsonl` when available from the provider.
