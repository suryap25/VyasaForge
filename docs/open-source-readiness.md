# Open Source Readiness Audit

## Scope

This audit reviews repository readiness for a public GitHub release of AppSec
Handbook Agent as a configurable multi-agent handbook generation system.

## Missing Files

The repository was missing standard public-project governance and community
files:

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `CHANGELOG.md`
- GitHub pull request template
- GitHub issue templates
- GitHub CODEOWNERS
- GitHub Actions CI workflow
- Architecture documentation
- Release checklist

These files have been added as part of the release hardening pass.

## Sensitive Files

No hardcoded API keys or obvious credential values were found in the source,
prompt, config, or documentation scan.

Sensitive-risk files and patterns:

- `.env` and `.env.*` must remain ignored.
- `configs/active-handbook.txt` is local state and should not be committed.
- `logs/`, `usage_logs/`, and handbook workspace logs may contain token usage
  metadata and should not be committed.
- Generated chapter files may contain private user-provided context and should
  not be committed.

Provider configuration files may reference environment variable names such as
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GEMINI_API_KEY`. These names are
safe to commit; actual secret values are not.

## Secrets Risk

Current design reads provider API keys from environment variables only. The LLM
gateway logs token usage metadata but does not log prompts or API key values.

Recommended maintainer controls:

- Enable GitHub secret scanning.
- Enable push protection.
- Keep `.env` ignored.
- Review pull requests touching `src/llm_gateway.py`, `configs/`, or
  `prompts/` carefully.

## Generated Artifacts That Should Not Be Committed

The following generated or local paths should remain out of git:

- `handbooks/`
- `chapters/`
- `reviews/`
- `reports/`
- `output/`
- `logs/`
- `state/`
- `usage_logs/`
- `diagrams/`
- `sketchnotes/`
- Python caches and build outputs
- Virtual environments

Example configs should remain commit-eligible, especially
`configs/*.example.json`.

## Packaging Gaps

Observed gaps before hardening:

- Project description was still scaffold-oriented.
- License metadata was missing.
- Author metadata was missing.
- Console script pointed to the old scaffold package entrypoint.

Actions taken:

- Added Apache-2.0 metadata.
- Added author metadata.
- Updated description.
- Pointed console script at `src.cli:app`.

Remaining future improvements:

- Add optional development dependencies for linting and tests.
- Add a dedicated test suite.
- Consider renaming the import package away from `src` in a future breaking
  cleanup.

## CI Gaps

Observed gaps before hardening:

- No GitHub Actions workflow.
- No syntax gate.
- No CLI smoke checks.
- No placeholders for future quality tooling.

Actions taken:

- Added `.github/workflows/ci.yml`.
- CI installs the package, compiles `src`, and runs CLI smoke tests.
- Ruff, pytest, mypy, and bandit placeholders are included without failing CI
  when those tools are not configured.

## Manual GitHub Controls Still Required

These cannot be fully enforced from repository files alone:

- Repository visibility
- Branch protection
- Rulesets
- Required status checks
- Required pull request reviews
- CODEOWNER review enforcement
- Secret scanning and push protection
- Release creation
