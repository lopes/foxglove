# Security Policy

## Reporting a vulnerability

If you discover a vulnerability in Foxglove, please report it privately rather than opening a public issue.

- **Preferred:** [GitHub Security Advisories](https://github.com/lopes/foxglove/security/advisories/new) for this repository.
- **Fallback:** email the maintainer at the address listed on [lopes.id](https://lopes.id).

Please include a description of the issue, steps to reproduce, and the version / commit you tested against. You'll receive an acknowledgement within 7 days.

## Scope

Foxglove is a CLI tool. The components most likely to be in scope for security reports:

- The **Thinkst Canary HTTP client** (`src/foxglove/thinkst/client.py`) — auth handling, URL construction, response parsing.
- **CLI argument validation** (`src/foxglove/cli.py`, `src/foxglove/thinkst/cli.py`) — anything that lets an unsafe value through to the filesystem, the Anthropic SDK, or the Canary API.
- **Writers** (`src/foxglove/writers/`) — file-format generation that could produce malformed output, embed unsanitised input, or write outside the intended directory.
- **Manifest read/write** (`src/foxglove/manifest.py`) — anything that lets a tampered manifest cause unexpected behaviour.

Out of scope:

- The **behavioural intent** of the tool — Foxglove deliberately produces deceptive artifacts. That's the feature, not a bug.
- Issues that require an attacker to already control the operator's shell, env vars, or filesystem.
- Issues in upstream dependencies (`anthropic`, `httpx`, `pydantic`, `python-docx`, etc.) — please report those directly to the relevant project.

## Dual-use considerations

Foxglove is published for **authorised** defensive use: red-team engagements with explicit scope, blue-team detection exercises, MITRE Engage deployments on networks the operator owns or has written permission to deploy on. We will not provide guidance, fixes, or feature requests aimed at:

- Evading detection by EDR/SIEM in unauthorised contexts.
- Hardening the deceptive artifacts against forensic review by victims (i.e., obscuring the operator's identity from an investigation).
- Targeting individuals, infrastructure, or organisations without authorisation.

If your use case requires any of the above, this isn't the tool for you.

## Secrets handling

- Foxglove reads `ANTHROPIC_API_KEY` and (optionally) `THINKST_API_KEY` from the environment. They are never written to `MANIFEST.json`, never logged, and never echoed in error output.
- The `THINKST_API_KEY` is sent to the Canary console as the `X-Canary-Auth-Token` HTTP header over HTTPS (TLS 1.2+, validated against the OS certificate store via `truststore`).
- If you accidentally commit a key to version control, rotate it immediately. For Anthropic: revoke and reissue at console.anthropic.com. For Thinkst: revoke and reissue from your Canary console's Settings → API page (Thinkst keys cannot be modified after creation — only revoked + replaced).
