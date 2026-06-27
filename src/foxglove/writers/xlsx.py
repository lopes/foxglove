from pathlib import Path

from openpyxl import Workbook


def write_xlsx(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("Failed to create worksheet")
    for row_idx, line in enumerate(content.split("\n"), start=1):
        for col_idx, cell_value in enumerate(line.split(","), start=1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value.strip())
    wb.save(str(path))
