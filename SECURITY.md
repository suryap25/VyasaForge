# Security Policy

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Instead, report them privately to the maintainer:

GitHub:
@suryap25

When reporting a vulnerability, include:

* Affected version or commit hash
* Reproduction steps
* Expected behavior
* Actual behavior
* Impact assessment
* Relevant logs with sensitive information removed

The maintainer will acknowledge valid reports as soon as practical and coordinate responsible disclosure.

---

# Responsible Disclosure

Please:

* Allow reasonable time for investigation and remediation.
* Avoid public disclosure before a fix is available.
* Avoid destructive testing.
* Do not access, modify, or exfiltrate data you do not own.

---

# Secrets Management

VyasaForge is designed to work with multiple LLM providers.

Secrets must:

* Be supplied through environment variables.
* Never be committed to Git.
* Never appear in examples, prompts, issues, pull requests, or documentation.

Examples:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

---

# Prompt Safety

Prompts are considered source code.

Contributors should:

* Avoid embedding secrets.
* Avoid embedding proprietary information.
* Avoid logging full prompts containing sensitive data.

---

# Supported Versions

Current support policy:

| Version        | Supported   |
| -------------- | ----------- |
| main           | Yes         |
| latest release | Yes         |
| older releases | Best effort |

Until version 1.0, security fixes will generally be applied directly to the main branch.
