# Contributing to VyasaForge

Thank you for contributing to VyasaForge.

VyasaForge is a configurable multi-agent document production system designed to transform structured knowledge into publishable documents through planning, writing, review, validation, repair, and publishing workflows.

## Before You Contribute

Please:

* Search existing issues before opening a new one.
* Open an issue before making large architectural changes.
* Discuss roadmap-altering changes before implementation.
* Keep pull requests focused on a single concern.

---

# Development Philosophy

VyasaForge follows several core principles:

1. Provider Agnostic

   * Core logic must not depend on a specific LLM provider.
   * All model interactions belong behind the LLM Gateway abstraction.

2. Deterministic First

   * Prefer validators, contracts, and repair workflows over prompt-only enforcement.

3. Small Changes

   * Large refactors should be split into multiple pull requests.

4. Documentation as Code

   * Prompts, schemas, validators, templates, and contracts are considered source code.

---

# Branch Strategy

Protected branch:

```text
main
```

Use short-lived feature branches:

```text
feature/brief-factory
feature/chapter-planner
feature/research-agent

fix/compiler-regression
fix/state-persistence

docs/roadmap-update
docs/security-guide
```

---

# Pull Request Process

For significant changes:

1. Open an issue first.
2. Create a feature branch.
3. Implement the change.
4. Run validation.
5. Open a pull request.

Required validation:

```powershell
python -m compileall src
python -m src.cli --help
python -m src.cli doctor
```

If applicable:

```powershell
python -m src.cli handbook-status
python -m src.cli validate-chapter --chapter 1 --stage final
```

---

# Coding Standards

* Use type hints where practical.
* Avoid hidden side effects.
* Prefer explicit configuration over hardcoded values.
* Preserve provider-agnostic boundaries.
* Keep modules focused and testable.
* Do not commit generated artifacts.

---

# Prompt Standards

Prompts are production assets.

Prompt changes should define:

* Input contract
* Output contract
* Expected format
* Failure handling
* Validation expectations

Avoid:

* Prompt-only validation
* Hidden assumptions
* Provider-specific wording

unless explicitly required.

---

# Documentation Standards

Update documentation whenever behavior changes.

Potential files:

```text
README.md
docs/architecture.md
docs/roadmap.md
docs/open-source-summary.md
docs/rebrand-summary.md
```

---

# Security Guidelines

Never commit:

```text
.env
API keys
Provider secrets
Generated private documents
Customer data
Usage logs containing secrets
```

Secrets must be supplied through environment variables.

---

# Generated Artifacts

Do not commit:

```text
chapters/drafts/
chapters/reviewed/
chapters/final/
output/
logs/
state/
```

unless intentionally updating sample content.

---

# Questions?

Open a GitHub Discussion before opening a large architectural pull request.
