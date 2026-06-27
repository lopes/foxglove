import pytest
from pydantic import ValidationError

from foxglove.models import (
    BATCH_SIZE,
    DEFAULT_MODEL,
    DEFAULT_PASSWORDS,
    EXIT_API_ERROR,
    EXIT_CLI_ERROR,
    EXIT_ENV_ERROR,
    EXIT_PARTIAL,
    EXIT_PLANNING_ERROR,
    EXIT_SUCCESS,
    MAX_FILES,
    SUPPORTED_FORMATS,
    CampaignPlan,
    FileEntry,
    Manifest,
    OperationParameters,
)


def test_supported_formats_contains_exactly_nine_formats():
    expected = frozenset({"pdf", "epdf", "docx", "xlsx", "pptx", "md", "conf", "json", "xml"})
    assert SUPPORTED_FORMATS == expected


def test_supported_formats_is_frozenset():
    assert isinstance(SUPPORTED_FORMATS, frozenset)


def test_max_files_is_200():
    assert MAX_FILES == 200


def test_batch_size_is_50():
    assert BATCH_SIZE == 50


def test_default_model():
    assert DEFAULT_MODEL == "claude-haiku-4-5"


def test_default_passwords():
    assert DEFAULT_PASSWORDS == ("abc123", "root")


def test_exit_codes():
    assert EXIT_SUCCESS == 0
    assert EXIT_CLI_ERROR == 1
    assert EXIT_ENV_ERROR == 2
    assert EXIT_API_ERROR == 3
    assert EXIT_PARTIAL == 4
    assert EXIT_PLANNING_ERROR == 5


def test_file_entry_construction():
    entry = FileEntry(path="it/report.pdf", format="pdf", summary="A report")
    assert entry.path == "it/report.pdf"
    assert entry.format == "pdf"
    assert entry.summary == "A report"


def test_file_entry_is_frozen():
    entry = FileEntry(path="it/report.pdf", format="pdf", summary="A report")
    with pytest.raises(ValidationError):
        entry.path = "other.pdf"


def test_file_entry_rejects_unsupported_format():
    with pytest.raises(ValidationError):
        FileEntry(path="file.exe", format="exe", summary="Bad format")


def test_campaign_plan_construction():
    entries = [
        FileEntry(path="a.pdf", format="pdf", summary="A"),
        FileEntry(path="b.md", format="md", summary="B"),
    ]
    plan = CampaignPlan(files=entries)
    assert len(plan.files) == 2
    assert plan.files[0].path == "a.pdf"


def test_campaign_plan_is_frozen():
    plan = CampaignPlan(files=[])
    with pytest.raises(ValidationError):
        plan.files = []


def test_campaign_plan_accepts_empty_files():
    plan = CampaignPlan(files=[])
    assert plan.files == []


def test_campaign_plan_default_authors_is_empty():
    plan = CampaignPlan(files=[])
    assert plan.authors == []


def test_campaign_plan_with_authors():
    plan = CampaignPlan(
        files=[],
        authors=["Alice Dupont", "Bob Schmidt", "Carla Müller"],
    )
    assert plan.authors == ["Alice Dupont", "Bob Schmidt", "Carla Müller"]


def _make_operation_parameters(**overrides: str | int | list[str]) -> OperationParameters:
    defaults: dict[str, str | int | list[str]] = {
        "base_dir": "/tmp",
        "num_files": 10,
        "formats": ["pdf", "docx"],
        "teams": ["it", "infra"],
        "company": "Acme Corp",
        "file_content": "IT documentation",
        "model": "claude-haiku-4-5",
        "passwords": ["abc123", "root"],
    }
    return OperationParameters(**dict(defaults | overrides))  # type: ignore[arg-type]


def test_operation_parameters_construction():
    params = _make_operation_parameters()
    assert params.base_dir == "/tmp"
    assert params.num_files == 10
    assert params.formats == ["pdf", "docx"]
    assert params.teams == ["it", "infra"]
    assert params.company == "Acme Corp"
    assert params.file_content == "IT documentation"
    assert params.model == "claude-haiku-4-5"
    assert params.passwords == ["abc123", "root"]


def test_operation_parameters_is_frozen():
    params = _make_operation_parameters()
    with pytest.raises(ValidationError):
        params.base_dir = "/other"


def _make_manifest(
    **overrides: str | OperationParameters | list[FileEntry] | list[str],
) -> Manifest:
    defaults: dict[str, str | OperationParameters | list[FileEntry] | list[str]] = {
        "operation": "op_alpha",
        "parameters": _make_operation_parameters(),
        "files": [
            FileEntry(path="it/report.pdf", format="pdf", summary="A report"),
            FileEntry(path="infra/config.conf", format="conf", summary="Config"),
        ],
    }
    return Manifest(**dict(defaults | overrides))  # type: ignore[arg-type]


def test_manifest_construction():
    manifest = _make_manifest()
    assert manifest.operation == "op_alpha"
    assert len(manifest.files) == 2
    assert manifest.parameters.base_dir == "/tmp"


def test_manifest_is_frozen():
    manifest = _make_manifest()
    with pytest.raises(ValidationError):
        manifest.operation = "other"


def test_manifest_json_round_trip():
    original = _make_manifest()
    json_str = original.model_dump_json()
    restored = Manifest.model_validate_json(json_str)
    assert restored == original


def test_manifest_default_authors_is_empty():
    manifest = _make_manifest()
    assert manifest.authors == []


def test_manifest_with_authors():
    manifest = _make_manifest(authors=["Alice", "Bob"])
    assert manifest.authors == ["Alice", "Bob"]
