from pathlib import Path
from unittest.mock import MagicMock

import pytest

from foxglove.generator import generate_all, generate_file_content, write_generated_file
from foxglove.models import FileEntry, Manifest, OperationParameters


def _make_text_block() -> MagicMock:
    block = MagicMock()
    block.type = "text"
    return block


def _make_text_response(text: str) -> MagicMock:
    block = _make_text_block()
    block.text = text

    from anthropic.types import TextBlock
    real_block = TextBlock(type="text", text=text)

    response = MagicMock()
    response.content = [real_block]
    return response


def _entry(path: str, fmt: str = "md", summary: str = "desc") -> FileEntry:
    return FileEntry(path=path, format=fmt, summary=summary)


def _make_manifest(files: list[FileEntry]) -> Manifest:
    return Manifest(
        operation="op_test",
        parameters=OperationParameters(
            base_dir="/tmp",
            num_files=len(files),
            formats=list({f.format for f in files}),
            teams=["it"],
            company="Acme",
            file_content="docs",
            model="test-model",
            passwords=["pw1"],
        ),
        files=files,
    )


def test_generate_file_content_returns_text():
    client = MagicMock()
    client.messages.create.return_value = _make_text_response("# Report\nContent here")
    entry = _entry("report.md")
    result = generate_file_content(
        client, entry, "test-model",
        company="Acme", teams=["it"], file_content="docs",
    )
    assert result == "# Report\nContent here"


def test_generate_file_content_prompt_includes_context():
    client = MagicMock()
    client.messages.create.return_value = _make_text_response("content")
    entry = _entry("report.md", summary="Quarterly report")
    generate_file_content(
        client, entry, "test-model",
        company="FinCorp", teams=["finance", "it"], file_content="financial docs",
    )
    call_args = client.messages.create.call_args
    prompt_content: str = call_args.kwargs["messages"][0]["content"]
    assert "FinCorp" in prompt_content
    assert "finance" in prompt_content
    assert "financial docs" in prompt_content
    assert "Quarterly report" in prompt_content


def test_generate_file_content_no_honeytokens_omits_instruction():
    client = MagicMock()
    client.messages.create.return_value = _make_text_response("content")
    generate_file_content(
        client, _entry("a.md"), "test-model",
        company="Acme", teams=["it"], file_content="docs",
        honeytokens=[],
    )
    prompt: str = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "honeytoken" not in prompt.lower()


def test_generate_file_content_includes_honeytokens_when_present():
    client = MagicMock()
    client.messages.create.return_value = _make_text_response("content")
    tokens = ["https://a.canary.tools/x.gif", "host.b.canarytokens.com"]
    generate_file_content(
        client, _entry("a.md"), "test-model",
        company="Acme", teams=["it"], file_content="docs",
        honeytokens=tokens,
    )
    prompt: str = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "honeytoken" in prompt.lower()
    for tok in tokens:
        assert tok in prompt


def test_write_generated_file_creates_md(tmp_path: Path):
    entry = _entry("sub/file.md")
    write_generated_file("# Hello", entry, tmp_path)
    assert (tmp_path / "sub" / "file.md").read_text() == "# Hello"


def test_write_generated_file_creates_epdf(tmp_path: Path):
    entry = _entry("secret.pdf", "epdf", "A secret doc. Password: pw1")
    write_generated_file("Secret content", entry, tmp_path)
    assert (tmp_path / "secret.pdf").exists()


def test_generate_all_creates_all_files(tmp_path: Path):
    files = [_entry("a.md"), _entry("b.md"), _entry("c.md")]
    manifest = _make_manifest(files)
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_text_response("Content A"),
        _make_text_response("Content B"),
        _make_text_response("Content C"),
    ]
    failures = generate_all(client, manifest, tmp_path)
    assert failures == 0
    assert (tmp_path / "a.md").read_text() == "Content A"
    assert (tmp_path / "b.md").read_text() == "Content B"
    assert (tmp_path / "c.md").read_text() == "Content C"


def test_generate_all_skips_failed_files(tmp_path: Path):
    files = [_entry("a.md"), _entry("b.md"), _entry("c.md")]
    manifest = _make_manifest(files)
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_text_response("Content A"),
        Exception("API failure"),
        _make_text_response("Content C"),
    ]
    failures = generate_all(client, manifest, tmp_path)
    assert failures == 1
    assert (tmp_path / "a.md").exists()
    assert not (tmp_path / "b.md").exists()
    assert (tmp_path / "c.md").exists()


def test_generate_all_resume_skips_existing(tmp_path: Path):
    files = [_entry("a.md"), _entry("b.md"), _entry("c.md")]
    manifest = _make_manifest(files)
    (tmp_path / "a.md").write_text("Already exists")
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_text_response("Content B"),
        _make_text_response("Content C"),
    ]
    failures = generate_all(client, manifest, tmp_path, resume=True)
    assert failures == 0
    assert (tmp_path / "a.md").read_text() == "Already exists"
    assert client.messages.create.call_count == 2


def test_generate_all_progress_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    files = [_entry("a.md"), _entry("b.md")]
    manifest = _make_manifest(files)
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_text_response("A"),
        _make_text_response("B"),
    ]
    generate_all(client, manifest, tmp_path)
    captured = capsys.readouterr()
    assert "Generating file 1/2:" in captured.out
    assert "Generating file 2/2:" in captured.out


def test_generate_all_resume_progress_skips_existing_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    files = [_entry("a.md"), _entry("b.md"), _entry("c.md")]
    manifest = _make_manifest(files)
    (tmp_path / "a.md").write_text("existing")
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_text_response("B"),
        _make_text_response("C"),
    ]
    generate_all(client, manifest, tmp_path, resume=True)
    captured = capsys.readouterr()
    progress_lines = [l for l in captured.out.splitlines() if "Generating file" in l]
    assert len(progress_lines) == 2
    assert "1/2:" in progress_lines[0]
    assert "2/2:" in progress_lines[1]
