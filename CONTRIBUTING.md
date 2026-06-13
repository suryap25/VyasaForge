# Contributing

Thank you for helping improve VyasaForge. This project is a configurable
multi-agent document production system, so contribution quality matters for
both software behavior and generated writing quality.

## Branch Strategy

- `main` is the protected release branch.
- Use short-lived feature branches from `main`.
- Prefer branch names like `feature/brief-schema`, `fix/compiler-output`, or
  `docs/release-checklist`.
- Keep pull requests focused on one concern.

## Pull Request Process

1. Open an issue first for large behavior changes, new agents, provider changes,
   compiler changes, or prompt contract changes.
2. Keep generated artifacts out of the pull request.
3. Include a clear summary, validation steps, and any known limitations.
4. Run the local checks before requesting review:

   ```powershell
   python -m compileall src
   python -m src.cli --help
   python -m src.cli doctor
   ```

5. Maintainer review is required before merge.

## Coding Standards

- Keep changes small, explicit, and reviewable.
- Preserve provider-agnostic boundaries. Application logic must not call a
  vendor SDK directly.
- Do not log prompts, API keys, or generated secrets.
- Prefer deterministic validators and gates over unbounded agent behavior.
- Avoid changing chapter-generation behavior in repository hardening changes.
- Use type hints for new Python interfaces where practical.

## Prompt Standards

- Prompts are source code for this project.
- Prompt changes must describe input contracts, output contracts, and failure
  handling.
- Avoid prompts that ask the model to guess missing user intent.
- Keep provider-specific wording out of prompts unless the prompt is explicitly
  provider-facing.
- Do not include real secrets, proprietary customer data, or private generated
  content in prompts.

## Documentation Standards

- Update `README.md` for user-visible commands.
- Update `docs/architecture.md` for architectural changes.
- Update `docs/roadmap.md` for phase or milestone changes.
- Add troubleshooting notes when a change introduces a new dependency or setup
  requirement.

## Generated Artifacts

Do not commit generated handbook workspaces, chapter drafts, reviews, output
documents, logs, local state, or API usage records.
