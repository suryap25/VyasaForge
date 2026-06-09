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

## Notes

- `run-chapter` creates the chapter brief automatically before writing.
- LLM prompts and API keys are not written to the usage log.
- Token usage is logged to `logs/llm-usage.jsonl` when available from the provider.
