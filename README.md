# Foxglove

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

Foxglove is an AI-powered adversary engagement tool designed to automatically generate high-fidelity, context-aware decoy files.

Strongly inspired by Cliff Stoll's 1986 story, *[The Cuckoo's Egg](https://lopes.id/log/review-cuckoos-egg/)*, Foxglove automates the creation of convincing fake data to buy defenders time, track adversaries, and map their behavior.

By strategically placing these files in your environment, you align with the **MITRE Engage** framework to *Expose* adversary presence, *Affect* their movement, and *Elicit* actionable intelligence. Once an adversary interacts with these files, defenders can trigger alerts, deploy embedded honeytokens, mislead the attacker with fake intelligence, or simply delay their lateral movement.

> [!NOTE]
> Foxglove is designed for authorized adversary engagement, defensive research, and authorized penetration testing. Do not use this tool on networks where you do not have explicit permission to deploy deceptive artifacts.


## How it Works
Creating convincing decoy files manually is tedious and repetitive. Foxglove leverages Anthropic's Claude to handle this dynamically:

1. **Context Ingestion:** The agent reads operator-defined parameters: base directory, operation name, target file count, file formats, and the specific narrative context (e.g., mimicked teams, corporate environment, tech stack).
2. **Campaign Planning (Structured Data):** The LLM generates a structured roadmap of the decoys, defining realistic file paths, names, types, and summaries. This step forces a structured JSON output enforced via Pydantic, guaranteeing the LLM's response maps perfectly to internal data objects. For encrypted files, passwords are assigned and stored in the manifest.
3. **Content Generation:** Foxglove iterates through the parsed plan, prompting the LLM to write convincing, context-aligned content for each specific file.
4. **File Assembly:** The tool compiles the generated text into the requested formats and writes them to the target operation directory.

Operators can easily review the generated directory and manually inject specific honeytokens (like canary tokens or fake AWS keys) into the highest-value decoys.


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
```sh
uv run python -m foxglove \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 99 \
  --formats pdf,epdf,docx,xlsx,conf \
  --teams it,infra,financial \
  --company "mid-sized fintech in Luxembourg, focusing at lending money to people, <50 employees" \
  --file-content "files present information in IT infra, from stack used (MS-AD, zabbix, Cisco ISE, Jamf), including some credentials and old URLs/IP addresses. financial info in the file server includes financial reports and confidential board decision and tax info."
```

This generates a structured directory at `/tmp/op_alpha` containing subfolders and 99 context-aware files mimicking a mid-sized Luxembourg fintech.

### Parameters
| Parameter        | Required | Description                                         | Default                    |
|------------------|----------|-----------------------------------------------------|----------------------------|
| `--base-dir`     | Yes      | Existing, writable directory for output              | —                          |
| `--operation`    | Yes      | Operation name (filesystem-safe identifier)          | —                          |
| `--num-files`    | Yes      | Number of files to generate (1–200)                  | —                          |
| `--formats`      | Yes      | Comma-separated formats (pdf,epdf,docx,xlsx,pptx,md,conf,json,xml) | —     |
| `--teams`        | Yes      | Comma-separated team names for context               | —                          |
| `--company`      | Yes      | Company description for context (max 256 chars)      | —                          |
| `--file-content` | Yes      | Description of expected content (max 1024 chars)     | —                          |
| `--model`        | No       | Anthropic model identifier                           | `claude-sonnet-4-20250514` |
| `--passwords`    | No       | Comma-separated passwords for encrypted PDFs         | `abc123,root`              |
| `--resume`       | No       | Resume a previously interrupted operation             | `false`                    |
| `--dry-run`      | No       | Show plan without writing files                       | `false`                    |

### Dry Run
Preview the campaign plan without creating any files:

```sh
uv run python -m foxglove \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 10 \
  --formats md,conf,json \
  --teams infosec \
  --company "small IT company" \
  --file-content "internal documentation" \
  --dry-run
```

### Resume
If generation is interrupted, resume where you left off:

```sh
uv run python -m foxglove \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 10 \
  --formats md,conf,json \
  --teams infosec \
  --company "small IT company" \
  --file-content "internal documentation" \
  --resume
```

### Exit Codes
| Code | Meaning                                    |
|------|--------------------------------------------|
| 0    | Success                                    |
| 1    | CLI validation error                       |
| 2    | Environment error (missing API key)        |
| 3    | API error (network, auth, rate limit)      |
| 4    | Partial completion (some files failed)     |
| 5    | Planning error (invalid LLM response)      |


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
