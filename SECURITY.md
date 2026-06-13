# Security Policy

## Reporting a Vulnerability

Please do not open a public GitHub issue for security vulnerabilities.

Report suspected vulnerabilities privately to the maintainer:

- GitHub: `@pvass25`

Include:

- Affected version or commit
- Clear reproduction steps
- Impact assessment
- Any relevant logs with secrets removed

The maintainer will acknowledge valid reports as soon as practical and work
with the reporter on responsible disclosure timing.

## Responsible Disclosure

- Give maintainers reasonable time to investigate and patch before public
  disclosure.
- Do not access, modify, or exfiltrate data that does not belong to you.
- Do not run destructive tests against systems you do not own.

## API Key Handling

- API keys must be read from environment variables only.
- Never commit `.env` files or shell history.
- Never paste real API keys into prompts, issues, pull requests, examples, or
  logs.
- The LLM gateway must not log prompts, full responses, or secret values.
- Provider profile files may name environment variables, but must not contain
  secret values.

## Supported Versions

This project is pre-1.0. Security fixes are applied to `main` unless a release
branch is explicitly announced.
