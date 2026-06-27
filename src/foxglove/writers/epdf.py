from io import BytesIO
from pathlib import Path
from collections.abc import Sequence

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate
from pypdf import PdfReader, PdfWriter


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


def write_epdf(content: str, path: Path, password: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(list(_content_to_flowables(content)))

    reader = PdfReader(BytesIO(buffer.getvalue()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)

    with open(path, "wb") as f:
        writer.write(f)
