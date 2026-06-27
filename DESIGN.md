# Foxglove — Technical Design Document

This document captures the agreed design decisions for Foxglove v1. It serves as the single source of truth for implementation.


## Glossary

- **honeyfile** — a decoy document produced by `foxglove generate`.
- **honeytoken** — a callback URL/hostname minted on a Thinkst Canary console via `foxglove thinkst create`, optionally embedded into honeyfile content.


## Workflow

```
CLI dispatch (generate | thinkst)
   ├── generate: validation → context ingestion → campaign planning (batched, Pydantic-enforced JSON)
   │             → content generation per honeyfile (sequential, optionally embedding honeytokens)
   │             → file assembly to disk
   └── thinkst:  validation → ThinkstClient call → result rendered to stdout
```


## CLI Interface

The CLI is organised around two subcommands: `generate` (produces honeyfiles) and `thinkst` (manages honeytokens on a Thinkst Canary console).

### `foxglove generate`

```
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 99 \
  --formats pdf,epdf,docx,xlsx,pptx,md,conf,json,xml \
  --teams it,infra,financial \
  --company "mid-sized fintech in Luxembourg..." \
  --file-content "files present information in IT infra..." \
  [--model claude-sonnet-4-20250514] \
  [--passwords foobar,Checkbox1] \
  [--honeytokens https://x.canary.tools/x.gif,host.y.canarytokens.com] \
  [--resume] \
  [--dry-run]
```

#### Parameters

| Parameter        | Required | Validation                                                  | Default                     |
|------------------|----------|-------------------------------------------------------------|-----------------------------|
| `--base-dir`     | Yes      | Must be an existing, writable directory                     | —                           |
| `--operation`    | Yes      | Regex: `^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$` (filesystem-safe) | —                       |
| `--num-files`    | Yes      | Integer, 1–`MAX_FILES` (200)                                | —                           |
| `--formats`      | Yes      | Comma-separated; each must be in supported set              | —                           |
| `--teams`        | Yes      | Comma-separated; each team name max 64 chars                | —                           |
| `--company`      | Yes      | Non-empty string, max 256 chars                             | —                           |
| `--file-content` | Yes      | Non-empty string, max 1024 chars                            | —                           |
| `--model`        | No       | Valid Anthropic model identifier                            | `claude-sonnet-4-20250514`  |
| `--passwords`    | No       | Comma-separated list of passwords for EPDF files            | `["abc123", "root"]`        |
| `--honeytokens`  | No       | Comma-separated callbacks (≤20 entries, each ≤256 chars, no whitespace, no empty entries) | —             |
| `--resume`       | No       | Flag; enables automatic resume without prompt               | `false`                     |
| `--dry-run`      | No       | Flag; outputs plan to screen, writes nothing to disk        | `false`                     |

### `foxglove thinkst <action>`

Manages honeytokens on a Thinkst Canary console. Tokens minted by Foxglove carry the memo prefix `#foxglove`, which `thinkst list` filters on client-side.

```
foxglove thinkst create --console <c> --kind <k> --flock <flock_id> --memo "<text>"
foxglove thinkst list   --console <c> [--flock <flock_id>] [--kind <k>] [--json]
foxglove thinkst remove --console <c> <canarytoken-id>
```

`--console` is the URL prefix in `https://<console>.canary.tools/api/v1/...` and must match `^[a-z0-9-]+$`.

Auth: env var `THINKST_AUTH_TOKEN` sent as `X-Canary-Auth-Token` HTTP header.

Supported `--kind` values (v1, no-extra-params kinds only): `dns`, `http`, `aws-id`, `slack-api`, `qr-code`, `windows-dir`, `wireguard`, `credit-card`, `mysql-dump`, `svn`, `sql`. Kinds requiring file uploads or extra params (`doc-msword`, `cloned-web`, `signed-exe`, …) are rejected with a helpful message.

`thinkst create` prints the new id plus the callback URL/hostname so the operator can copy them into `generate --honeytokens`.

`thinkst list` cursor-loops `/api/v1/canarytokens/paginate`, then filters memos containing `#foxglove` client-side. Default output is `<canarytoken-id> | <kind> | <flock_id> | <memo>`; `--json` switches to a JSON array (one object per token, fields including `created_printable` for scripting).

`thinkst remove` deletes a single id via `/api/v1/canarytoken/delete`. If Canary blocks deletion because of unacknowledged incidents, the runner prompts y/n and on yes retries with `clear_incidents=true`.

### Supported Formats

`pdf`, `epdf`, `docx`, `xlsx`, `pptx`, `md`, `conf`, `json`, `xml`

### Validation Rules

- All parameters are validated before any API call is made.
- If any parameter is invalid, the program exits immediately with an error message and a non-zero exit code.
- If `--formats` contains an unsupported format, the entire run fails (not a partial skip).
- For `generate`, `ANTHROPIC_API_KEY` environment variable must be set; fail immediately at startup if missing.
- For `thinkst`, `THINKST_AUTH_TOKEN` environment variable must be set; fail immediately if missing.


## Constants

| Name        | Value | Description                          |
|-------------|-------|--------------------------------------|
| `MAX_FILES` | 200   | Upper limit for `--num-files`        |
| `BATCH_SIZE`| 50    | Files per planning batch             |


## Exit Codes

| Code | Meaning                                            |
|------|----------------------------------------------------|
| 0    | Success                                            |
| 1    | CLI validation error (bad parameters)              |
| 2    | Environment error (missing API key, etc.)          |
| 3    | API error (network, auth, rate limit)              |
| 4    | Partial completion (some honeyfiles skipped)       |
| 5    | Planning error (LLM returned invalid plan)         |
| 6    | Thinkst API error (auth, 4xx, 5xx, incidents block)|


## Resume Behavior

1. On startup, Foxglove checks if `<base-dir>/<operation>/MANIFEST.json` exists.
2. **If manifest exists and `--resume` is passed:** resume automatically — load manifest, skip files that already exist on disk, generate the rest.
3. **If manifest exists and `--resume` is NOT passed:** prompt the user interactively (y/n). If "yes", resume. If "no", delete all files under the operation root (including manifest) and start fresh.
4. **If no manifest exists and `--resume` is passed:** start fresh with a message: `"New operation <name>; starting generation"`.
5. **If no manifest exists and `--resume` is NOT passed:** start fresh (normal behavior).

On resume, Foxglove loads the manifest and iterates through its entries. If the file exists on disk, skip it. If not, generate it.


## Dry-Run Behavior

- `--dry-run` outputs the campaign plan to stdout. No files are written to disk.
- `--dry-run` combined with `--resume` on an existing operation: shows only the remaining ungenerated files.
- `--dry-run` on a new operation: runs planning and displays the full plan.


## Manifest (`MANIFEST.json`)

Written to `<base-dir>/<operation>/MANIFEST.json`. Always generated on every `generate` run.

```json
{
  "operation": "op_alpha",
  "parameters": {
    "base_dir": "/tmp",
    "num_files": 99,
    "formats": ["pdf", "epdf", "docx", "xlsx", "conf"],
    "teams": ["it", "infra", "financial"],
    "company": "mid-sized fintech in Luxembourg...",
    "file_content": "files present information in IT infra...",
    "model": "claude-sonnet-4-20250514",
    "passwords": ["abc123", "root"],
    "honeytokens": ["https://abc.canary.tools/x.gif"]
  },
  "files": [
    {
      "path": "financial/reports/Q3_2025_Revenue.xlsx",
      "format": "xlsx",
      "summary": "Quarterly revenue breakdown by product line for Q3 2025"
    },
    {
      "path": "it/vpn/vpn_gateway.conf",
      "format": "conf",
      "summary": "VPN gateway configuration for the Luxembourg office"
    },
    {
      "path": "infra/policies/access_control.pdf",
      "format": "epdf",
      "summary": "Physical and logical access control policy. Password: abc123"
    }
  ]
}
```

### Manifest Notes

- `path` is relative to the operation root (`<base-dir>/<operation>/`).
- For `epdf` honeyfiles, the password is included in the `summary` field as: `"<summary>. Password: <password>"`.
- The `parameters` block stores the original CLI parameters for reproducibility and resume validation.
- `parameters.honeytokens` is the list passed via `--honeytokens` (empty list if the flag was omitted). The campaign's honeytoken set is recorded for audit; distribution across individual honeyfiles is LLM-decided and not tracked per-file.


## Duplicate File Path Handling

If the LLM generates duplicate file paths in the plan, Foxglove applies macOS-style deduplication:

- First occurrence: `Report.md`
- Second occurrence: `Report (2).md`
- Third occurrence: `Report (3).md`

Deduplication is applied during plan post-processing, before any files are written.


## Campaign Planning

- Uses Anthropic's structured output via tool use with Pydantic model schemas.
- For operations with more than `BATCH_SIZE` (50) files, planning is split into batches of 50 and merged.
- The LLM prompt is formatted with operator context:
  > Consider files created by `{teams}` for the company `{company}` under this context: `{file_content}`.


## Content Generation

- Sequential (one honeyfile at a time, no concurrency).
- Progress output to stdout:
  ```
  Generating file 68/99: /tmp/op_alpha/foo/bar/foobar.docx
  ```
- On generation or write failure, log the error and continue to the next file:
  ```
  Generating file 83/99: /tmp/op_alpha/foo/bar/foobar.pptx
      Error generating file: <error details>
  ```
- If any honeyfiles were skipped, exit with code 4 (partial completion).
- When `parameters.honeytokens` is non-empty, the per-honeyfile prompt is appended with an instruction asking the LLM to weave each honeytoken naturally into the content (links, references, signatures, footers). Distribution across honeyfiles is LLM-decided; a one-page memo may use none, a directory listing may use several.


## EPDF Password Handling

- A default password list is provided: `["abc123", "root"]`.
- The user can override this list via `--passwords foobar,Checkbox1`.
- During planning, passwords are assigned to EPDF files by cycling through the password list.
- Passwords are recorded in the manifest's summary field for each EPDF entry.
- Encrypted PDFs use the standard `.pdf` extension on disk (not `.epdf`). The `format` field in the manifest distinguishes them. Any `.epdf` extensions from the LLM are normalized to `.pdf` during post-processing.


## Thinkst Canary Integration

### HTTP Layer

- `httpx.Client(base_url=f"https://{console}.canary.tools", timeout=30)`.
- Auth header `X-Canary-Auth-Token: <THINKST_AUTH_TOKEN>`.
- `truststore.inject_into_ssl()` already covers HTTPS verification with the OS cert store.

### Endpoint Mapping

| Action | Endpoint                              | Method | Body / query                                    |
|--------|---------------------------------------|--------|-------------------------------------------------|
| create | `/api/v1/canarytoken/create`          | POST   | `kind`, `memo` (already prefixed `#foxglove `), `flock_id` |
| list   | `/api/v1/canarytokens/paginate`       | GET    | `limit=100`, optional `flock_id`, `cursor`; client-side `#foxglove` and `kind` filter |
| remove | `/api/v1/canarytoken/delete`          | POST   | `canarytoken=<id>`; on incidents-block, retry with `clear_incidents=true` after user confirmation |

### Memo Tagging

Foxglove-created honeytokens have memo `#foxglove <user-supplied-memo>` (plain prefix). The constant `FOXGLOVE_TAG = "#foxglove"` lives in `foxglove.thinkst.__init__`. Listing filters the marker client-side because the Canary search endpoint's behaviour with `#` punctuation is unspecified.

### Honeytoken kinds supported in v1

Limited to no-extra-params kinds whose callback is a URL or hostname: `dns`, `http`, `aws-id`, `slack-api`, `qr-code`, `windows-dir`, `wireguard`, `credit-card`, `mysql-dump`, `svn`, `sql`.


## Format-Specific Generation Notes

| Format | Notes                                                                 |
|--------|-----------------------------------------------------------------------|
| PDF    | Text content with basic formatting                                    |
| EPDF   | Same as PDF, encrypted with a password from the password list         |
| DOCX   | Formatted content: headings, paragraphs, bullet points                |
| XLSX   | Tabular data (rows and columns, not a single text block)              |
| PPTX   | Multiple slides with titles, bullet points, and text                  |
| MD     | Markdown-formatted text                                               |
| CONF   | Generic configuration file format (not tied to specific software)     |
| JSON   | Structured JSON data                                                  |
| XML    | Generic XML data (not tied to specific schema)                        |


## Project Layout

```
foxglove/
├── src/foxglove/
│   ├── __init__.py         # Package exports
│   ├── __main__.py         # Entrypoint (python -m foxglove); dispatches generate vs thinkst
│   ├── cli.py              # Root CLI parser (subcommand dispatch) + generate validation
│   ├── planner.py          # Campaign planning (LLM structured output)
│   ├── generator.py        # Honeyfile content generation orchestration
│   ├── manifest.py         # Manifest read/write
│   ├── models.py           # Pydantic models (CampaignPlan, FileEntry, OperationParameters, …)
│   ├── resume.py           # Resume action logic
│   ├── thinkst/
│   │   ├── __init__.py     # FOXGLOVE_TAG, SUPPORTED_KINDS
│   │   ├── cli.py          # parse_thinkst_args; ThinkstCreateArgs/ListArgs/RemoveArgs
│   │   ├── client.py       # ThinkstClient (httpx); ThinkstApiError, IncidentsBlockedError
│   │   ├── models.py       # Pydantic: CreateTokenResult, TokenSummary
│   │   └── runner.py       # run_thinkst (create / list / remove)
│   └── writers/
│       ├── __init__.py     # Writer dispatch (get_writer)
│       ├── pdf.py          # PDF writer
│       ├── epdf.py         # Encrypted PDF writer
│       ├── docx.py         # DOCX writer
│       ├── xlsx.py         # XLSX writer
│       ├── pptx.py         # PPTX writer
│       ├── md.py           # Markdown writer
│       ├── conf.py         # CONF writer
│       ├── json.py         # JSON writer
│       └── xml.py          # XML writer
├── tests/
│   └── ...                 # Tests organised by behaviour
├── CLAUDE.md
├── DESIGN.md
├── README.md
└── pyproject.toml
```
