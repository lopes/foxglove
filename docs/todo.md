# Foxglove Implementation Todo

## Progress Tracker

- [x] **Phase 0:** Project scaffolding (pyproject.toml, dirs, uv sync)
- [x] **Phase 1:** Pydantic models in `src/models.py`
- [x] **Phase 2:** CLI parsing in `src/cli.py`
- [x] **Phase 3:** File writers (`src/write_*.py`)
- [x] **Phase 4:** Manifest read/write in `src/manifest.py`
- [x] **Phase 5:** Plan post-processing (dedup, passwords, merge)
- [x] **Phase 6:** Campaign planner in `src/planner.py`
- [x] **Phase 7:** Content generator in `src/generator.py`
- [x] **Phase 8:** Resume & dry-run logic
- [x] **Phase 9:** Entrypoint orchestration in `src/foxglove.py`
- [x] **Phase 10:** Integration smoke tests

## Detailed Increments

### Phase 0: Project Scaffolding
- [x] 0.1 Update `pyproject.toml` with all deps
- [x] 0.2 Run `uv sync`
- [x] 0.3 Create `src/`, `tests/` directories
- [x] 0.4 Move `main.py` → `src/foxglove.py`, confirm `uv run pytest` runs

### Phase 1: Pydantic Models
- [x] 1.1 `SUPPORTED_FORMATS` frozenset
- [x] 1.2 `MAX_FILES`, `BATCH_SIZE` constants
- [x] 1.3 `DEFAULT_MODEL`, `DEFAULT_PASSWORDS` constants
- [x] 1.4 Exit code constants (0–5)
- [x] 1.5 `FileEntry` frozen model with format validator
- [x] 1.6 `CampaignPlan` frozen model
- [x] 1.7 `OperationParameters` frozen model
- [x] 1.8 `Manifest` frozen model with JSON round-trip

### Phase 2: CLI Parsing
- [x] 2.1 Happy path — all required args, defaults applied
- [x] 2.2 Missing required arg → `CliError`
- [x] 2.3 `--operation` regex validation
- [x] 2.4 `--num-files` range 1–`MAX_FILES`
- [x] 2.5 `--formats` against `SUPPORTED_FORMATS`
- [x] 2.6 `--teams` max 64 chars per team
- [x] 2.7 `--company` max 256, `--file-content` max 1024
- [x] 2.8 Optional params: `--model`, `--passwords`, `--resume`, `--dry-run`
- [x] 2.9 `--base-dir` existing writable directory

### Phase 3: File Writers
- [x] 3.1–3.2 `write_md` + nested dir creation
- [x] 3.3 `write_json`
- [x] 3.4 `write_xml`
- [x] 3.5 `write_conf`
- [x] 3.6 `write_pdf` (reportlab)
- [x] 3.7 `write_epdf` (reportlab + pypdf)
- [x] 3.8 `write_docx` (python-docx)
- [x] 3.9 `write_xlsx` (openpyxl)
- [x] 3.10 `write_pptx` (python-pptx)
- [x] 3.11 `get_writer` dispatch function

### Phase 4: Manifest
- [x] 4.1 `write_manifest` creates `MANIFEST.json`
- [x] 4.2 `read_manifest` returns `Manifest` or `None`
- [x] 4.3 `manifest_exists` returns bool

### Phase 5: Plan Post-Processing
- [x] 5.1 `deduplicate_paths` — macOS-style `(N)` suffixes
- [x] 5.2 `assign_epdf_passwords` — cycled from password list
- [x] 5.3 `merge_plans` — concatenate file lists
- [x] 5.4 `post_process_plan` — compose merge → dedup → passwords

### Phase 6: Campaign Planner
- [x] 6.1 `compute_batches` — batch count calculation
- [x] 6.2 `build_planning_prompt` — formatted prompt string
- [x] 6.3 `plan_batch` — single batch (mocked API)
- [x] 6.4 `plan_campaign` — full orchestration (mocked, 2 batches)
- [x] 6.5 API error handling → `PlanningError`
- [x] 6.6 Invalid LLM response → `PlanningError`

### Phase 7: Content Generator
- [x] 7.1 `generate_file_content` — single file content (mocked API)
- [x] 7.2 `write_generated_file` — dispatch to correct writer
- [x] 7.3 `generate_all` — sequential loop
- [x] 7.4 Error resilience — skip failed, continue
- [x] 7.5 Resume — skip existing files
- [x] 7.6 Progress output

### Phase 8: Resume & Dry-Run
- [x] 8.1 `determine_resume_action` pure function
- [x] 8.2 Dry-run new operation — plan printed, no files
- [x] 8.3 Dry-run + resume — show remaining only

### Phase 9: Entrypoint
- [x] 9.1 Bad CLI args → exit 1
- [x] 9.2 Missing API key → exit 2
- [x] 9.3 Full run (mocked) → exit 0, files created
- [x] 9.4 Partial completion → exit 4
- [x] 9.5 Planning error → exit 5
- [x] 9.6 API error → exit 3

### Phase 10: Integration
- [x] 10.1 End-to-end with mocked LLM (5 files, 3 formats)
- [x] 10.2 Resume integration test
- [x] 10.3 Dry-run integration test
