from pathlib import Path

from foxglove.metadata import FileMetadata


def write_conf(content: str, path: Path, *, metadata: FileMetadata | None = None) -> None:
    del metadata
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
