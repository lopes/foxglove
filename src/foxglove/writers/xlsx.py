from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook
from openpyxl.writer.excel import ExcelWriter

from foxglove.metadata import FileMetadata


def _to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def write_xlsx(content: str, path: Path, *, metadata: FileMetadata | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("Failed to create worksheet")
    for row_idx, line in enumerate(content.split("\n"), start=1):
        for col_idx, cell_value in enumerate(line.split(","), start=1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value.strip())
    if metadata is None:
        wb.save(str(path))
        return
    wb.properties.creator = metadata.author
    wb.properties.lastModifiedBy = metadata.author
    wb.properties.created = _to_naive_utc(metadata.created_at)
    wb.properties.modified = _to_naive_utc(metadata.modified_at)
    with ZipFile(str(path), "w", ZIP_DEFLATED, allowZip64=True) as archive:
        ExcelWriter(wb, archive).save()
