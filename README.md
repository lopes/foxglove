# Foxglove

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

<p align="center">
  <img src="assets/foxglove-logo.svg" alt="Foxglove" width="160">
</p>

**Foxglove generates high-fidelity decoy documents — *honeyfiles* — and optionally mints and embeds Thinkst Canary callbacks — *honeytokens* — into them.** It pairs Anthropic's Claude (for context-aware content) with Thinkst Canary (for verifiable detonations), so defenders can drop authentic-looking bait into their environments and get real alerts the moment an adversary touches it.

Inspired by Cliff Stoll's *[The Cuckoo's Egg](https://lopes.id/log/review-cuckoos-egg/)*, Foxglove aligns with the **MITRE Engage** framework to *Expose*, *Affect*, and *Elicit* adversary behaviour through deception.

> [!NOTE]
> **A name with history.** Foxglove was previously called **Antlion** — both names capture the same idea (a lure that punishes intrusion), through different metaphors. The project was renamed on **26 June 2026** to align with its "poisonous flower" theme: *Digitalis purpurea* is striking to look at and toxic to anyone who handles it carelessly. Bait that looks innocent, then bites.

> [!IMPORTANT]
> Foxglove is for **authorised** adversary engagement, defensive research, and authorised penetration testing only. Do not deploy deceptive artifacts on networks where you don't have explicit permission.


## Glossary

- **honeyfile** — a decoy document produced by `foxglove generate` (PDF, DOCX, XLSX, etc.).
- **honeytoken** — a callback URL/hostname minted on a Thinkst Canary console via `foxglove thinkst create`. Honeytokens can be passed to `foxglove generate --honeytokens` so the LLM weaves them naturally into honeyfile content.


## Prerequisites

- **Python 3.14+**
- **[uv](https://github.com/astral-sh/uv)** for dependency management
- **Anthropic API key** (required for `generate`)
- **Thinkst Canary API key** (optional — only required for `thinkst` subcommands; see [API role](#which-thinkst-api-role) below)


## Installation

```sh
git clone https://github.com/lopes/foxglove
cd foxglove
uv sync
```


## Environment Setup

```sh
# Required for foxglove generate
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional — only for foxglove thinkst subcommands
export THINKST_API_KEY="..."
```

Both follow the standard `<VENDOR>_API_KEY` pattern. Most operators already have `ANTHROPIC_API_KEY` exported for other Claude tools — the same value works here.

### Which Thinkst API role?

Foxglove needs an **Admin** key (create/delete canarytokens are full API operations per Thinkst's role matrix). Prefer **flock-scoped Admin** over console-scoped — smaller blast radius if the key ever leaks. See [Thinkst — How does the API work?](https://help.canary.tools/hc/en-gb/articles/360012727537-How-does-the-API-work) and [Flock API Keys](https://help.canary.tools/hc/en-gb/articles/7111549805213-Flock-API-Keys).


## Supported Formats

`PDF`, `Encrypted PDF` (password-protected), `DOCX`, `XLSX`, `PPTX`, `Markdown`, `CONF`, `JSON`, `XML`


## Usage

The CLI has two subcommands:

```
foxglove generate ...    # produce a directory of honeyfiles
foxglove thinkst ...     # mint / list / remove honeytokens on a Canary console
```

### Use case 1 — Generate a honeyfile directory (Anthropic only)

Quickest path to value. Drop a credible-looking IT documentation tree into `/tmp/op_alpha`.

```sh
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 20 \
  --formats pdf,docx,xlsx,md,conf \
  --teams it,infra,financial \
  --company "mid-sized fintech in Luxembourg, ~50 employees" \
  --file-content "internal IT and finance docs: stack details (MS-AD, Zabbix, Cisco ISE, Jamf), quarterly reports, access policies"
```

Result: 20 honeyfiles under `/tmp/op_alpha/`, plus a `MANIFEST.json` recording the campaign parameters, the LLM-generated authors pool, and the file list. Each document carries plausible metadata (author drawn from the pool, created/modified timestamps jittered 1–25 days apart, filesystem mtime aligned).

### Use case 2 — Preview a campaign before committing (dry run)

For larger operations, preview the LLM's plan without writing anything to disk or running content generation.

```sh
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_preview \
  --num-files 100 \
  --formats pdf,epdf,docx,xlsx,pptx,md \
  --teams legal,hr,finance,engineering \
  --company "global SaaS, ~2000 employees, Series D" \
  --file-content "corporate documents covering legal contracts, HR policies, payroll, and engineering runbooks" \
  --dry-run
```

The dry-run prints every planned file (path, format, summary) so you can sanity-check coverage and tone before paying for the full content-generation pass. Pair with `--resume` later to continue from where you left off if interrupted.

### Use case 3 — The twofold workflow (honeytoken → honeyfile)

The marquee use case. Mint a Thinkst callback, then weave it into the generated content so the LLM places it as a plausible link, contact reference, or footer URL. When the adversary opens the document and follows the link, your Canary console alerts.

```sh
# 1) Mint a callback on your Canary console
uv run python -m foxglove thinkst create \
  --domain-hash <your-domain-hash> \
  --kind dns \
  --flock flock:default \
  --memo "decoy quarterly report deployment"
#  → prints the canarytoken id + callback hostname

# 2) Generate honeyfiles, embedding the callback
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation q3_decoys \
  --num-files 5 \
  --formats pdf,docx,xlsx \
  --teams finance,executive \
  --company "..." \
  --file-content "Q3 board pack, revenue breakdown, strategy memos" \
  --honeytokens <callback-hostname-from-step-1>

# 3) (later) audit foxglove-tagged honeytokens on the console
uv run python -m foxglove thinkst list --domain-hash <your-domain-hash>

# 4) (end of engagement) clean up
uv run python -m foxglove thinkst remove --domain-hash <your-domain-hash> <canarytoken-id>
```

Tokens minted by Foxglove are tagged in their memo with `#foxglove` so `thinkst list` filters cleanly to just the ones it created. Pass `--json` to `thinkst list` if you want machine-readable output for scripting cleanup.


## How it Works

1. **Context Ingestion** — operator-defined parameters (target environment, teams, content theme) flow into a Pydantic-validated campaign object.
2. **Campaign Planning** — Claude produces a structured roadmap of file paths, formats, and summaries plus a small pool of culturally-coherent author names. Pydantic-enforced JSON guarantees the LLM output maps cleanly into internal types.
3. **Content Generation** — Foxglove iterates through the plan, asking Claude to write believable per-file content. When `--honeytokens` is set, the LLM is instructed to weave them naturally into the text — never as an out-of-band block.
4. **File Assembly** — the writers (`python-docx`, `openpyxl`, `python-pptx`, `reportlab`, `pypdf`) materialise each format with realistic document metadata (author, created/modified timestamps jittered like real authoring lifecycles) and the filesystem mtime aligned to match.

For full architectural detail — exit codes, manifest schema, resume/dry-run semantics, Canary endpoint mapping, supported honeytoken kinds — see [DESIGN.md](DESIGN.md).


## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: strict TDD, scoped commits, immutable data, no comments unless the *why* is non-obvious.


## Security

For vulnerability reports and disclosure practices, see [SECURITY.md](SECURITY.md).


## License

MIT — see [LICENSE](LICENSE).
