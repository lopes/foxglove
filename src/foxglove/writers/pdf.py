from io import BytesIO
from pathlib import Path
from collections.abc import Sequence

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet

from foxglove.metadata import FileMetadata
from foxglove.writers._pdf_metadata import to_pdf_metadata


def _content_to_flowables(content: str) -> Sequence[Flowable]:
    styles = getSampleStyleSheet()
    flowables: list[Flowable] = [
        Paragraph(line, styles["Normal"])
        for line in content.split("\n")
        if line.strip()
    ]
    if not flowables:
        flowables = [Paragraph(" ", styles["Normal"])]
    return flowables


def write_pdf(content: str, path: Path, *, metadata: FileMetadata | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(list(_content_to_flowables(content)))
    if metadata is None:
        path.write_bytes(buffer.getvalue())
        return
    reader = PdfReader(BytesIO(buffer.getvalue()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(to_pdf_metadata(metadata))
    with open(path, "wb") as f:
        writer.write(f)
