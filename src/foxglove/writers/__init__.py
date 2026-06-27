from collections.abc import Callable

from foxglove.writers.conf import write_conf
from foxglove.writers.docx import write_docx
from foxglove.writers.epdf import write_epdf
from foxglove.writers.json import write_json
from foxglove.writers.md import write_md
from foxglove.writers.pdf import write_pdf
from foxglove.writers.pptx import write_pptx
from foxglove.writers.xlsx import write_xlsx
from foxglove.writers.xml import write_xml

_WRITERS: dict[str, Callable[..., None]] = {
    "md": write_md,
    "json": write_json,
    "xml": write_xml,
    "conf": write_conf,
    "pdf": write_pdf,
    "epdf": write_epdf,
    "docx": write_docx,
    "xlsx": write_xlsx,
    "pptx": write_pptx,
}


def get_writer(fmt: str) -> Callable[..., None]:
    if fmt not in _WRITERS:
        raise ValueError(f"No writer for format: {fmt}")
    return _WRITERS[fmt]
