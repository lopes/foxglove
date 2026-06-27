import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import TextBlock, ToolUseBlock

from foxglove.__main__ import run
from foxglove.models import EXIT_SUCCESS, Manifest


def _make_plan_response(files: list[dict[str, str]]) -> MagicMock:
    block = ToolUseBlock(
        id="toolu_test",
        type="tool_use",
        name="campaign_plan",
        input={"files": files},
    )
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "tool_use"
    return response


def _make_content_response(text: str) -> MagicMock:
    block = TextBlock(type="text", text=text)
    response = MagicMock()
    response.content = [block]
    return response


PLAN_FILES = [
    {"path": "it/notes.md", "format": "md", "summary": "Team notes"},
    {"path": "it/config.conf", "format": "conf", "summary": "App config"},
    {"path": "it/data.json", "format": "json", "summary": "API response"},
    {"path": "infra/setup.conf", "format": "conf", "summary": "Infra setup"},
    {"path": "infra/readme.md", "format": "md", "summary": "Readme"},
]

CONTENT_RESPONSES = [
    "# Team Notes\nImportant items",
    "[app]\nport=8080\ndebug=false",
    '{"status": "ok", "count": 42}',
    "[network]\ngateway=10.0.0.1",
    "# Infrastructure Readme\nSetup instructions",
]


def _base_argv(tmp_path: Path) -> list[str]:
    return [
        "generate",
        "--base-dir", str(tmp_path),
        "--operation", "op_integration",
        "--num-files", "5",
        "--formats", "md,conf,json",
        "--teams", "it,infra",
        "--company", "TestCorp",
        "--file-content", "integration test docs",
    ]


def test_end_to_end_creates_all_files_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_plan_response(PLAN_FILES),
        *[_make_content_response(c) for c in CONTENT_RESPONSES],
    ]

    with patch("foxglove.__main__.anthropic.Anthropic", return_value=mock_client):
        result = run(_base_argv(tmp_path))

    assert result == EXIT_SUCCESS

    op_dir = tmp_path / "op_integration"
    manifest_path = op_dir / "MANIFEST.json"
    assert manifest_path.exists()

    manifest = Manifest.model_validate_json(manifest_path.read_text())
    assert manifest.operation == "op_integration"
    assert len(manifest.files) == 5

    for entry in manifest.files:
        file_path = op_dir / entry.path
        assert file_path.exists(), f"Missing: {entry.path}"
        assert file_path.stat().st_size > 0

    assert (op_dir / "it" / "data.json").exists()
    data = json.loads((op_dir / "it" / "data.json").read_text())
    assert data["status"] == "ok"


def test_resume_regenerates_only_missing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_plan_response(PLAN_FILES),
        *[_make_content_response(c) for c in CONTENT_RESPONSES],
    ]

    with patch("foxglove.__main__.anthropic.Anthropic", return_value=mock_client):
        run(_base_argv(tmp_path))

    op_dir = tmp_path / "op_integration"
    (op_dir / "it" / "notes.md").unlink()
    (op_dir / "infra" / "readme.md").unlink()

    mock_client_2 = MagicMock()
    mock_client_2.messages.create.side_effect = [
        _make_content_response("# Regenerated notes"),
        _make_content_response("# Regenerated readme"),
    ]

    with patch("foxglove.__main__.anthropic.Anthropic", return_value=mock_client_2):
        result = run([*_base_argv(tmp_path), "--resume"])

    assert result == EXIT_SUCCESS
    assert mock_client_2.messages.create.call_count == 2
    assert (op_dir / "it" / "notes.md").read_text() == "# Regenerated notes"
    assert (op_dir / "infra" / "readme.md").read_text() == "# Regenerated readme"
    assert (op_dir / "it" / "config.conf").exists()


def test_dry_run_creates_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_plan_response(PLAN_FILES)

    with patch("foxglove.__main__.anthropic.Anthropic", return_value=mock_client):
        result = run([*_base_argv(tmp_path), "--dry-run"])

    assert result == EXIT_SUCCESS

    op_dir = tmp_path / "op_integration"
    assert not op_dir.exists(), "Operation dir should not be created in dry-run"

    assert mock_client.messages.create.call_count == 1


def test_dry_run_prints_plan_to_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_plan_response(PLAN_FILES)

    with patch("foxglove.__main__.anthropic.Anthropic", return_value=mock_client):
        run([*_base_argv(tmp_path), "--dry-run"])

    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out
    assert "op_integration" in captured.out
    assert str(tmp_path / "op_integration") in captured.out
    for entry_data in PLAN_FILES:
        assert entry_data["path"] in captured.out
