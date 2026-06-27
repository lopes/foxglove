from pathlib import Path

from foxglove.manifest import manifest_exists, read_manifest, write_manifest
from foxglove.models import FileEntry, Manifest, OperationParameters


def _make_manifest() -> Manifest:
    return Manifest(
        operation="op_alpha",
        parameters=OperationParameters(
            base_dir="/tmp",
            num_files=2,
            formats=["pdf", "conf"],
            teams=["it"],
            company="Acme",
            file_content="docs",
            model="claude-sonnet-4-20250514",
            passwords=["abc123"],
        ),
        files=[
            FileEntry(path="it/report.pdf", format="pdf", summary="A report"),
            FileEntry(path="it/app.conf", format="conf", summary="Config"),
        ],
    )


def test_write_manifest_creates_file(tmp_path: Path):
    manifest = _make_manifest()
    write_manifest(manifest, tmp_path)
    assert (tmp_path / "MANIFEST.json").exists()


def test_write_manifest_round_trips(tmp_path: Path):
    original = _make_manifest()
    write_manifest(original, tmp_path)
    restored = read_manifest(tmp_path)
    assert restored == original


def test_read_manifest_returns_none_when_missing(tmp_path: Path):
    assert read_manifest(tmp_path) is None


def test_manifest_exists_true_when_present(tmp_path: Path):
    write_manifest(_make_manifest(), tmp_path)
    assert manifest_exists(tmp_path) is True


def test_manifest_exists_false_when_missing(tmp_path: Path):
    assert manifest_exists(tmp_path) is False


def test_manifest_round_trips_honeytokens(tmp_path: Path):
    original = Manifest(
        operation="op_honey",
        parameters=OperationParameters(
            base_dir="/tmp",
            num_files=1,
            formats=["md"],
            teams=["it"],
            company="Acme",
            file_content="docs",
            model="claude-sonnet-4-20250514",
            passwords=["abc"],
            honeytokens=["https://a.canary.tools/x", "host.b.com"],
        ),
        files=[FileEntry(path="a.md", format="md", summary="d")],
    )
    write_manifest(original, tmp_path)
    restored = read_manifest(tmp_path)
    assert restored is not None
    assert restored.parameters.honeytokens == ["https://a.canary.tools/x", "host.b.com"]


def test_manifest_default_honeytokens_is_empty_list(tmp_path: Path):
    manifest = _make_manifest()
    assert manifest.parameters.honeytokens == []
    write_manifest(manifest, tmp_path)
    restored = read_manifest(tmp_path)
    assert restored is not None
    assert restored.parameters.honeytokens == []


def test_manifest_round_trips_authors(tmp_path: Path):
    original = Manifest(
        operation="op_authors",
        parameters=OperationParameters(
            base_dir="/tmp", num_files=1, formats=["md"], teams=["it"],
            company="Acme", file_content="docs",
            model="claude-sonnet-4-20250514", passwords=["a"],
        ),
        files=[FileEntry(path="a.md", format="md", summary="d")],
        authors=["Alice Dupont", "Bob Schmidt"],
    )
    write_manifest(original, tmp_path)
    restored = read_manifest(tmp_path)
    assert restored is not None
    assert restored.authors == ["Alice Dupont", "Bob Schmidt"]


def test_manifest_default_authors_is_empty_list_on_disk(tmp_path: Path):
    manifest = _make_manifest()
    write_manifest(manifest, tmp_path)
    restored = read_manifest(tmp_path)
    assert restored is not None
    assert restored.authors == []
