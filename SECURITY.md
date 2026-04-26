# Security Policy

## Supported Versions

This project is currently a phase 0 MVP. Security fixes are accepted for the main development branch.

| Version | Supported |
| --- | --- |
| v0.3 phase 0 | Yes |
| Earlier experimental snapshots | No |

## Reporting a Vulnerability

Please do not open a public issue for sensitive security reports.

Until a dedicated security email is configured, contact the repository owner privately or use GitHub private vulnerability reporting if enabled for the repository.

When reporting, include:

- A clear description of the vulnerability.
- Steps to reproduce.
- Impact and affected components.
- Whether secrets, local files, uploaded files, generated code, or LLM prompts/responses are involved.

## Security Scope

Relevant areas include:

- LLM API key handling.
- `.env` and local configuration leakage.
- Uploaded file handling.
- Excel sandbox static checks and subprocess execution.
- Arbitrary file read/write risks.
- Tool Registry input validation.
- Agent tool misuse.
- LLM log exposure of sensitive prompt or response data.

## Known MVP Limitations

- This project is not production hardened.
- SQLite is used for local development.
- Uploaded files are stored locally.
- The Excel sandbox is a restricted subprocess, not a container or VM sandbox.
- LLM prompt and response previews are stored in logs for debugging.
- Authentication and department-level authorization are placeholders.

Do not use this MVP with production secrets or sensitive enterprise data without additional hardening.
