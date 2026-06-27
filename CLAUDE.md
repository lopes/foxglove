# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Foxglove is an AI-powered adversary engagement tool that generates high-fidelity, context-aware **honeyfiles** using Anthropic's Claude, and optionally mints and embeds **honeytokens** from a Thinkst Canary console. It automates creation of convincing fake data for defensive security operations, aligned with the MITRE Engage framework.

### Glossary

- **honeyfile** — a decoy document produced by `foxglove generate` (PDF, DOCX, XLSX, etc.).
- **honeytoken** — a callback URL/hostname minted on a Thinkst Canary console via `foxglove thinkst create`. Honeytokens can be passed to `foxglove generate --honeytokens` so the LLM weaves them into honeyfile content.

**Workflow (two moments):**

1. *Optional* — mint honeytokens via `foxglove thinkst create` and note their callback URLs/hostnames.
2. Generate honeyfiles via `foxglove generate ... [--honeytokens <urls>]`. CLI validation → context ingestion → campaign planning (structured JSON via Pydantic) → content generation per honeyfile → file assembly to disk.

**Supported honeyfile formats:** PDF, Encrypted PDF (EPDF), DOCX, XLSX, PPTX, MD, CONF, JSON, XML.

## Development Commands

```bash
# Install/sync dependencies
uv sync

# Generate honeyfiles
uv run python -m foxglove generate \
  --base-dir /tmp \
  --operation op_alpha \
  --num-files 10 \
  --formats pdf,docx,xlsx \
  --teams it,infra \
  --company "description of target company" \
  --file-content "description of expected file content" \
  [--honeytokens https://x.canary.tools/...,host.y.canarytokens.com]

# Manage honeytokens on a Thinkst Canary console
uv run python -m foxglove thinkst create \
  --console <your-console> --kind dns --flock flock:default --memo "..."
uv run python -m foxglove thinkst list --console <your-console>
uv run python -m foxglove thinkst remove --console <your-console> <canarytoken-id>

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_example.py

# Run a single test by name
uv run pytest -k "test_name"
```

Requires `ANTHROPIC_API_KEY` for the `generate` subcommand and `FOXGLOVE_THINKST_API_KEY` for the `thinkst` subcommands.

## Key Dependencies

- `anthropic` — LLM provider (Claude)
- `pydantic` — structured output enforcement for campaign planning
- `python-docx`, `openpyxl`, `python-pptx` — Office format generation
- `reportlab`, `pypdf` — PDF generation and encryption

## Architecture Notes

- Campaign planning uses Anthropic's native structured output (tool use) with Pydantic model schemas
- Planning is batched in groups of 50 files, then merged
- Encrypted PDFs use passwords from a configurable list (cycled), stored in manifest summaries
- Duplicate file paths from LLM are deduplicated with macOS-style `(N)` suffixes
- Content generation is sequential (no concurrency in v1)
- All CLI parameters are validated before any API call
- See [DESIGN.md](DESIGN.md) for the full technical specification

## Core Philosophy

**TEST-DRIVEN DEVELOPMENT IS NON-NEGOTIABLE.** Every line of production code must be written in response to a failing test. No exceptions.

**Key principles:**

- **TDD strictly:** RED → GREEN → REFACTOR in small increments
- **Functional programming:** immutable data, pure functions, composition
- **Test behavior, not implementation:** tests document expected business behavior
- **No comments:** code must be self-documenting

## Development Workflow

Follow RED-GREEN-REFACTOR in small, known-good increments:

1. **RED:** Write a failing test first — no production code without a failing test
2. **GREEN:** Write the minimum code to make the test pass
3. **REFACTOR:** Assess improvement opportunities (only if it adds value)
4. Each increment must leave the codebase in a working state
5. **After completing each phase:** run the full test suite (`uv run pytest`), report results, and **wait for explicit approval** before proceeding to the next phase
6. **Wait for commit approval** before every commit

## Python Code Style

- **Immutable data only** — no mutation of data structures
- **Pure functions** wherever possible — deterministic, no side effects
- **No nested if/else** — use early returns or composition
- **Prefer comprehensions and functional patterns** (`map`, `filter`, `functools.reduce`) over imperative loops
- **Options objects over positional parameters** — use dataclasses or typed dicts for functions with multiple parameters
- **No `Any` types** — use `object` or `Unknown` patterns if type is truly unknown; leverage type hints strictly
- **Strict type checking** — Pylance is set to strict mode; all code must pass without type errors. Annotate all function parameters, return types, and variables where inference is insufficient. Use protocol types or explicit casts for third-party libraries with incomplete stubs.
- **Use uv** for dependency management

## Testing Principles

- Write tests first (TDD non-negotiable)
- Test through the public API exclusively
- Use factory functions for test data (no mutable shared state in fixtures)
- Tests must document expected business behavior
- No 1:1 mapping between test files and implementation files — organize tests by behavior
- Use real schemas/types in tests, never redefine them

## Output Guardrails

- **Write to files, not chat** — when asked to produce a plan, document, or artifact, persist it to a file
- **Plan-only mode** — when asked for a plan or design only, produce only that artifact; do not write code unless explicitly asked
- **Incremental output** — produce a first draft within 3-4 tool calls, then refine iteratively
