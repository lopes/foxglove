# Foxglove

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

Foxglove is an AI-powered adversary engagement tool that automatically generates high-fidelity, context-aware **honeyfiles** and optionally mints and embeds **honeytokens** from a Thinkst Canary console.

Strongly inspired by Cliff Stoll's 1986 story, *[The Cuckoo's Egg](https://lopes.id/log/review-cuckoos-egg/)*, Foxglove automates the creation of convincing fake data to buy defenders time, track adversaries, and map their behavior.

By strategically placing honeyfiles in your environment, you align with the **MITRE Engage** framework to *Expose* adversary presence, *Affect* their movement, and *Elicit* actionable intelligence. Once an adversary interacts with these files, defenders can trigger alerts via embedded honeytokens, mislead the attacker with fake intelligence, or simply delay their lateral movement.

> [!NOTE]
> Foxglove is designed for authorized adversary engagement, defensive research, and authorized penetration testing. Do not use this tool on networks where you do not have explicit permission to deploy deceptive artifacts.


## Glossary

- **honeyfile** — a decoy document produced by `foxglove generate` (PDF, DOCX, XLSX, etc.).
- **honeytoken** — a callback URL/hostname minted on a Thinkst Canary console via `foxglove thinkst create`. Honeytokens can be passed to `foxglove generate --honeytokens` so the LLM weaves them into honeyfile content as plausible links, references, or footers.


## How it Works
Creating convincing honeyfiles manually is tedious and repetitive. Foxglove uses a two-moment workflow:

**Moment 1 (optional) — Mint honeytokens.** Run `foxglove thinkst create` once per callback. Each call prints a `canarytoken` id plus a URL/hostname; note these for the next moment. Honeyfiles created by Foxglove are tagged in their memo with `#foxglove` so they're easy to list and remove later.

**Moment 2 — Generate honeyfiles.** Run `foxglove generate ... [--honeytokens <urls>]` to produce a directory of context-aware honeyfiles. Behind the scenes:

1. **Context Ingestion:** the agent reads operator-defined parameters (base directory, operation name, target file count, formats, mimicked teams, corporate context).
2. **Campaign Planning (Structured Data):** the LLM generates a structured roadmap of the honeyfiles — realistic file paths, names, types, and summaries — enforced via Pydantic for a guaranteed-shape JSON. EPDF passwords are assigned and stored in the manifest.
3. **Content Generation:** Foxglove iterates through the plan, prompting the LLM to write context-aligned content per honeyfile. If `--honeytokens` was given, the LLM is instructed to weave them naturally into the text as links, references, or footers.
4. **File Assembly:** the tool compiles the generated text into the requested formats and writes them to the operation directory.


## Supported File Formats
`PDF`, `Encrypted PDF`, `DOCX`, `XLSX`, `PPTX`, `Markdown`, `CONF`, `JSON`, `XML`


## Tech Stack
- **LLM Provider:** `anthropic` (Claude Sonnet 4)
- **Data Validation:** `pydantic` (structured output enforcement during planning)
- **Office Formats:** `python-docx`, `openpyxl`, `python-pptx`
- **PDF Handling:** `reportlab` (generation), `pypdf` (encryption)
- **Package Management:** `uv`


## Installation
Requires [uv](https://github.com/astral-sh/uv) and Python 3.14+.

```sh
git clone https://github.com/lopes/foxglove
cd foxglove
uv sync
```

Set your Anthropic API key:
```sh
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```


## Usage

The CLI is structured around two subcommands: `generate` (honeyfiles) and `thinkst` (honeytokens on a Thinkst Canary console).

### `foxglove generate`
```sh
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 99 \
  --formats pdf,epdf,docx,xlsx,conf \
  --teams it,infra,financial \
  --company "mid-sized fintech in Luxembourg, focusing at lending money to people, <50 employees" \
  --file-content "files present information in IT infra, from stack used (MS-AD, zabbix, Cisco ISE, Jamf), including some credentials and old URLs/IP addresses. financial info in the file server includes financial reports and confidential board decision and tax info." \
  [--honeytokens https://x.canary.tools/x.gif,host.y.canarytokens.com]
```

This generates a structured directory at `/tmp/op_alpha` containing subfolders and 99 context-aware honeyfiles. When `--honeytokens` is given, the LLM is instructed to weave each token naturally into honeyfile content (as links, references, contact details, or footers).

#### Parameters
| Parameter        | Required | Description                                                                                 | Default                    |
|------------------|----------|---------------------------------------------------------------------------------------------|----------------------------|
| `--base-dir`     | Yes      | Existing, writable directory for output                                                     | —                          |
| `--operation`    | Yes      | Operation name (filesystem-safe identifier)                                                 | —                          |
| `--num-files`    | Yes      | Number of honeyfiles to generate (1–200)                                                    | —                          |
| `--formats`      | Yes      | Comma-separated formats (pdf,epdf,docx,xlsx,pptx,md,conf,json,xml)                          | —                          |
| `--teams`        | Yes      | Comma-separated team names for context                                                      | —                          |
| `--company`      | Yes      | Company description for context (max 256 chars)                                             | —                          |
| `--file-content` | Yes      | Description of expected content (max 1024 chars)                                            | —                          |
| `--model`        | No       | Anthropic model identifier                                                                  | `claude-sonnet-4-20250514` |
| `--passwords`    | No       | Comma-separated passwords for encrypted PDFs                                                | `abc123,root`              |
| `--resume`       | No       | Resume a previously interrupted operation                                                   | `false`                    |
| `--dry-run`      | No       | Show plan without writing honeyfiles                                                        | `false`                    |
| `--honeytokens`  | No       | Comma-separated callback URLs/hostnames to weave into honeyfile content (≤20 entries, ≤256 chars each, no whitespace) | —             |

#### Dry Run
Preview the campaign plan without creating any honeyfiles:

```sh
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 10 \
  --formats md,conf,json \
  --teams infosec \
  --company "small IT company" \
  --file-content "internal documentation" \
  --dry-run
```

#### Resume
If generation is interrupted, resume where you left off by appending `--resume` to the same `generate` invocation.

### `foxglove thinkst`

Mints, lists, and removes honeytokens on a Thinkst Canary console. Foxglove tags each honeytoken's memo with `#foxglove` so you can later list and remove only the ones it created.

Required env var: `THINKST_AUTH_TOKEN` (your Canary API auth token).

`--console` is the URL prefix of your console: in `https://acme.canary.tools/api/v1/...`, the console is `acme`.

```sh
# Mint a honeytoken
uv run python -m foxglove thinkst create \
  --console acme \
  --kind dns \
  --flock flock:default \
  --memo "Q3 billing report"

# List Foxglove-tagged honeytokens
uv run python -m foxglove thinkst list --console acme [--flock flock:abc] [--kind dns] [--json]

# Remove one by id
uv run python -m foxglove thinkst remove --console acme <canarytoken-id>
```

Supported `--kind` values (v1, callback-only): `dns`, `http`, `aws-id`, `slack-api`, `qr-code`, `windows-dir`, `wireguard`, `credit-card`, `mysql-dump`, `svn`, `sql`.

### Exit Codes
| Code | Meaning                                            |
|------|----------------------------------------------------|
| 0    | Success                                            |
| 1    | CLI validation error                               |
| 2    | Environment error (missing API key)                |
| 3    | API error (network, auth, rate limit)              |
| 4    | Partial completion (some honeyfiles failed)        |
| 5    | Planning error (invalid LLM response)              |
| 6    | Thinkst API error (auth, 4xx, 5xx, incidents block)|


## Development
```sh
uv run pytest              # Run all tests
uv run pytest -k "test_x"  # Run specific test
```

See [DESIGN.md](DESIGN.md) for the full technical specification and [CLAUDE.md](CLAUDE.md) for development guidelines.


## Known Limitations
- **Context Window Constraints:** For large operations (100+ files), Foxglove batches the campaign planning phase in groups of 50 to maintain output quality.
- **Sequential Generation:** Files are generated one at a time (no concurrency in v1).


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
