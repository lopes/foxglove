import json
from pathlib import Path

from foxglove.writers import get_writer
from foxglove.writers.md import write_md
from foxglove.writers.json import write_json
from foxglove.writers.xml import write_xml
from foxglove.writers.conf import write_conf
from foxglove.writers.pdf import write_pdf
from foxglove.writers.epdf import write_epdf
from foxglove.writers.docx import write_docx
from foxglove.writers.xlsx import write_xlsx
from foxglove.writers.pptx import write_pptx


def test_write_md_creates_file_with_correct_content(tmp_path: Path):
    target = tmp_path / "test.md"
    write_md("# Hello\nWorld", target)
    assert target.read_text() == "# Hello\nWorld"


def test_write_md_creates_parent_directories(tmp_path: Path):
    target = tmp_path / "deep" / "nested" / "file.md"
    write_md("content", target)
    assert target.exists()
    assert target.read_text() == "content"


def test_write_json_creates_valid_json(tmp_path: Path):
    target = tmp_path / "data.json"
    write_json('{"key": "value", "count": 42}', target)
    with open(target) as f:
        data = json.load(f)
    assert data == {"key": "value", "count": 42}


def test_write_xml_preserves_content(tmp_path: Path):
    target = tmp_path / "data.xml"
    content = "<root><item>data</item></root>"
    write_xml(content, target)
    assert target.read_text() == content


def test_write_conf_preserves_content(tmp_path: Path):
    target = tmp_path / "app.conf"
    content = "[section]\nkey=value\nother=123"
    write_conf(content, target)
    assert target.read_text() == content


def test_write_pdf_creates_valid_pdf(tmp_path: Path):
    target = tmp_path / "report.pdf"
    write_pdf("Some report content about quarterly results", target)
    raw = target.read_bytes()
    assert raw[:4] == b"%PDF"
    assert target.stat().st_size > 0


def test_write_epdf_creates_encrypted_pdf(tmp_path: Path):
    target = tmp_path / "secret.pdf"
    write_epdf("Secret content", target, password="abc123")
    assert target.exists()
    from pypdf import PdfReader
    reader = PdfReader(target, password="abc123")
    assert len(reader.pages) >= 1


def test_write_epdf_requires_password_to_read(tmp_path: Path):
    import pytest
    from pypdf import PdfReader
    target = tmp_path / "locked.pdf"
    write_epdf("Locked content", target, password="mypass")
    reader = PdfReader(target)
    with pytest.raises(Exception):
        reader.pages[0].extract_text()


def test_write_docx_creates_valid_docx(tmp_path: Path):
    from docx import Document
    target = tmp_path / "doc.docx"
    write_docx("# Heading\nParagraph text\n- bullet one\n- bullet two", target)
    assert target.exists()
    doc = Document(str(target))
    assert len(doc.paragraphs) > 0


def test_write_xlsx_creates_valid_spreadsheet(tmp_path: Path):
    from openpyxl import load_workbook
    target = tmp_path / "data.xlsx"
    write_xlsx("Name,Age\nAlice,30\nBob,25", target)
    assert target.exists()
    wb = load_workbook(target)
    ws = wb.active
    assert ws is not None
    assert ws.cell(row=1, column=1).value == "Name"
    assert ws.cell(row=1, column=2).value == "Age"
    assert ws.cell(row=2, column=1).value == "Alice"
    assert ws.cell(row=2, column=2).value == "30"


def test_write_pptx_creates_valid_presentation(tmp_path: Path):
    from pptx import Presentation
    target = tmp_path / "slides.pptx"
    write_pptx("Slide 1 Title\nBullet A\nBullet B\n---\nSlide 2 Title\nContent", target)
    assert target.exists()
    prs = Presentation(str(target))
    assert len(prs.slides) == 2


import pytest


def test_get_writer_returns_correct_functions():
    assert get_writer("md") == write_md
    assert get_writer("json") == write_json
    assert get_writer("xml") == write_xml
    assert get_writer("conf") == write_conf
    assert get_writer("pdf") == write_pdf
    assert get_writer("docx") == write_docx
    assert get_writer("xlsx") == write_xlsx
    assert get_writer("pptx") == write_pptx


def test_get_writer_epdf_returns_callable():
    writer = get_writer("epdf")
    assert callable(writer)


def test_get_writer_unknown_format_raises():
    with pytest.raises(ValueError):
        get_writer("exe")


from datetime import UTC, datetime

from foxglove.metadata import FileMetadata

FIXED_MODIFIED = datetime(2026, 6, 27, 15, 30, 0, tzinfo=UTC)
FIXED_CREATED = datetime(2026, 6, 10, 9, 0, 0, tzinfo=UTC)


def _meta(author: str = "Alice Dupont") -> FileMetadata:
    return FileMetadata(
        author=author, created_at=FIXED_CREATED, modified_at=FIXED_MODIFIED,
    )


def _to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _ts_close(a: datetime, b: datetime, tol_seconds: float = 2.0) -> bool:
    return abs((_to_naive_utc(a) - _to_naive_utc(b)).total_seconds()) < tol_seconds


def test_docx_writer_sets_author_and_timestamps(tmp_path: Path):
    from docx import Document
    target = tmp_path / "doc.docx"
    write_docx("# Hello", target, metadata=_meta("Alice Dupont"))
    doc = Document(str(target))
    props = doc.core_properties
    assert props.author == "Alice Dupont"
    assert props.last_modified_by == "Alice Dupont"
    assert _ts_close(props.created, FIXED_CREATED)
    assert _ts_close(props.modified, FIXED_MODIFIED)


def test_docx_writer_without_metadata_uses_library_defaults(tmp_path: Path):
    from docx import Document
    target = tmp_path / "doc.docx"
    write_docx("# Hello", target)
    doc = Document(str(target))
    assert doc.core_properties.author != "Alice Dupont"


def test_xlsx_writer_sets_creator_and_timestamps(tmp_path: Path):
    from openpyxl import load_workbook
    target = tmp_path / "sheet.xlsx"
    write_xlsx("Name,Age\nAlice,30", target, metadata=_meta("Bob Schmidt"))
    wb = load_workbook(target)
    assert wb.properties.creator == "Bob Schmidt"
    assert wb.properties.lastModifiedBy == "Bob Schmidt"
    assert wb.properties.created is not None
    assert wb.properties.modified is not None
    assert _ts_close(wb.properties.created, FIXED_CREATED)
    assert _ts_close(wb.properties.modified, FIXED_MODIFIED)


def test_pptx_writer_sets_author_and_timestamps(tmp_path: Path):
    from pptx import Presentation
    target = tmp_path / "deck.pptx"
    write_pptx("Title\nLine A", target, metadata=_meta("Carla Müller"))
    prs = Presentation(str(target))
    props = prs.core_properties
    assert props.author == "Carla Müller"
    assert props.last_modified_by == "Carla Müller"
    assert _ts_close(props.created, FIXED_CREATED)
    assert _ts_close(props.modified, FIXED_MODIFIED)


def test_docx_writer_empty_author_still_sets_timestamps(tmp_path: Path):
    from docx import Document
    target = tmp_path / "doc.docx"
    write_docx("# Hi", target, metadata=_meta(author=""))
    doc = Document(str(target))
    assert _ts_close(doc.core_properties.modified, FIXED_MODIFIED)
