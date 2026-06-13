# Open Source Release Summary

Project name: VyasaForge

Tagline: Forge structured knowledge into publishable documents.

## Files Created

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `CHANGELOG.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/CODEOWNERS`
- `.github/workflows/ci.yml`
- `docs/open-source-readiness.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/release-checklist.md`
- `docs/open-source-summary.md`
- `docs/branding.md`
- `docs/vision.md`
- `docs/rebrand-summary.md`

## Files Modified

- `.gitignore`
- `pyproject.toml`
- `README.md`
- `src/cli.py`
- `src/compiler.py`
- `src/finalizer.py`
- `ROADMAP.md`

## Repository Hardening Completed

- Added Apache-2.0 license.
- Added contribution, security, and code of conduct policies.
- Added GitHub PR and issue templates.
- Added CODEOWNERS with `@pvass25` ownership.
- Added CI workflow with Python 3.11 install, compile, and CLI smoke checks.
- Added future-ready placeholders for ruff, pytest, mypy, and bandit.
- Strengthened `.gitignore` for generated artifacts, local state, logs, outputs,
  and secrets.
- Updated package metadata and console script entrypoint.
- Rebranded public-facing documentation and CLI help to VyasaForge.
- Added `vyasaforge` and `vf` entry points while keeping existing invocation
  paths.

## Files Requiring Manual GitHub Configuration

These steps must be completed manually in the GitHub UI:

- Repository visibility
- Rulesets
- Branch protection
- Required pull request reviews
- CODEOWNER enforcement
- Required CI checks
- Secret scanning
- Push protection
- Release creation

## Maintainer Notes

- `configs/active-handbook.txt` is local workspace state and should not be
  tracked.
- Generated handbook workspaces under `handbooks/` should not be committed.
- Core chapter-generation logic was not intentionally changed during this
  hardening pass.
