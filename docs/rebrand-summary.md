# Rebrand Summary

## Files Updated

- `pyproject.toml`
- `README.md`
- `src/cli.py`
- `src/compiler.py`
- `src/finalizer.py`
- `src/appsec_handbook_agent/__init__.py`
- `src/appsec_handbook_agent/cli.py`
- `CONTRIBUTING.md`
- `ROADMAP.md`
- `docs/architecture.md`
- `docs/open-source-readiness.md`
- `docs/open-source-summary.md`
- `docs/roadmap.md`
- `CHANGELOG.md`

## Files Added

- `docs/branding.md`
- `docs/vision.md`
- `docs/rebrand-summary.md`

## Branding Changes Made

- Product name changed to `VyasaForge`.
- Tagline added: `Forge structured knowledge into publishable documents.`
- Motto added: `Plan. Write. Review. Publish.`
- User-facing docs now describe the project as a general-purpose documentation
  production CLI.
- Domain-specific generated examples are kept as local generated artifacts when
  present, but the tracked repository defaults are now generic.
- Default prompts and required sections were generalized for multi-domain
  document types.

## CLI Changes Made

- Added `vyasaforge` console script.
- Added `vf` console script.
- Kept `appsec-handbook-agent` console script for backward compatibility.
- Kept `python -m src.cli` working.
- Added `vf init` as a non-destructive setup/diagnostic command.
- Added `vf plan` as a friendly alias for `plan-handbook`.

## Remaining Manual Steps

- Update GitHub repository name and description if desired.
- Update GitHub topics.
- Update repository social preview image if one is used.
- Confirm branch protection and CODEOWNER enforcement after the rebrand.
- Publish release notes announcing the VyasaForge name.
