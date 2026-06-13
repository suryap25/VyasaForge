# Release Checklist

Use this checklist before publishing a public GitHub release.

## Repository Checks

- [ ] Run CI successfully on `main`.
- [ ] Run local syntax checks:

  ```powershell
  python -m compileall src
  ```

- [ ] Run CLI smoke checks:

  ```powershell
  python -m src.cli --help
  python -m src.cli doctor
  python -m src.cli list-providers
  python -m src.cli agent-status
  ```

- [ ] Verify example configs do not contain secrets.
- [ ] Verify `.env`, generated handbooks, logs, reviews, output files, and local
      state are not committed.
- [ ] Verify `README.md` commands still match current CLI behavior.
- [ ] Verify `CHANGELOG.md` includes release notes.

## Functional Spot Checks

- [ ] Install locally with `python -m pip install -e .`.
- [ ] Run `python -m src.cli doctor`.
- [ ] Validate at least one non-LLM command.
- [ ] If API keys are available, run a small provider smoke test.
- [ ] If Pandoc is available, compile a known final chapter fixture.

## GitHub Checks

- [ ] Enable branch protection or rulesets.
- [ ] Require pull request review.
- [ ] Require CODEOWNER review.
- [ ] Require CI status checks.
- [ ] Enable secret scanning and push protection.
- [ ] Confirm repository visibility.

## Release

- [ ] Create a signed or annotated tag.
- [ ] Create GitHub release notes.
- [ ] Attach any intended release artifacts.
- [ ] Confirm install instructions from a clean checkout.
