# Contributing to Foxglove

Thanks for the interest. Foxglove is small, deliberate, and held to a few strict rules — fewer than most projects, but the ones we have are non-negotiable.

## Development environment

```sh
git clone https://github.com/lopes/foxglove
cd foxglove
uv sync
```

Python 3.14+ and [uv](https://github.com/astral-sh/uv) are required.

## Test-driven development (non-negotiable)

Every line of production code is written in response to a failing test.

1. **RED** — write a failing test that captures the behaviour you want.
2. **GREEN** — write the minimum production code to make it pass.
3. **REFACTOR** — only if it adds clear value.

```sh
uv run pytest              # full suite
uv run pytest -k <name>    # single test
```

If a PR adds production code without a corresponding failing test, it will be sent back. The TDD discipline is what keeps this codebase coherent — every test documents an expected behaviour, not an implementation detail.

## Code style

- **Strict types.** Pylance/pyright in strict mode. No `Any`. Annotate everything where inference is insufficient.
- **Immutable data only.** Frozen dataclasses or frozen Pydantic models. No mutation of shared state.
- **Pure functions** wherever possible. Side effects belong at the edges (CLI dispatch, IO).
- **No nested if/else** — prefer early returns or composition.
- **No comments** unless the *why* is non-obvious (a hidden constraint, an external-library quirk worth flagging). Code must read itself; well-named identifiers are the documentation.
- **Test behaviour, not implementation.** Tests must survive refactors that preserve external contracts.

## Commits

Foxglove uses [Scoped Commits](https://scopedcommits.com/):

```
<scope>: <one-sentence description>

Optional body: explain *why* the change is being made when it isn't obvious
from the diff.
```

Examples (from this repo's history):

- `cli: introduce generate/thinkst subcommands`
- `writers: apply FileMetadata to DOCX, XLSX, PPTX core properties`
- `thinkst: rename --console to --domain-hash`

No conventional-commit type prefixes (`feat:`, `fix:`, `chore:`). The scope identifies the subsystem; comma-separated scopes for multi-area changes; `treewide` or `all` for repository-wide ones.

## Pull requests

- One coherent change per PR. If you find yourself writing "this PR also..." in the description, it should probably be two PRs.
- Run the full suite before opening: `uv run pytest` must be green.
- The PR description should explain *why*, not just *what* — the diff already shows the what.

## Architecture

See [DESIGN.md](DESIGN.md) for the technical specification: workflow, CLI contract, manifest schema, Thinkst integration, exit codes, and project layout.
