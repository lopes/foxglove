from io import BytesIO
from pathlib import Path
from collections.abc import Sequence

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet


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


def write_pdf(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(list(_content_to_flowables(content)))
    path.write_bytes(buffer.getvalue())
