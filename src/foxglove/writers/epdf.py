from io import BytesIO
from pathlib import Path
from collections.abc import Sequence

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate
from pypdf import PdfReader, PdfWriter

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


def write_epdf(
    content: str,
    path: Path,
    password: str,
    *,
    metadata: FileMetadata | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(list(_content_to_flowables(content)))

    reader = PdfReader(BytesIO(buffer.getvalue()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if metadata is not None:
        writer.add_metadata(to_pdf_metadata(metadata))
    writer.encrypt(password)

    with open(path, "wb") as f:
        writer.write(f)
