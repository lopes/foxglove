from datetime import UTC, datetime

from foxglove.metadata import FileMetadata


def _pdf_date(dt: datetime) -> str:
    return "D:" + dt.astimezone(UTC).strftime("%Y%m%d%H%M%SZ")


def to_pdf_metadata(metadata: FileMetadata) -> dict[str, str]:
    return {
        "/Author": metadata.author,
        "/Creator": metadata.author,
        "/CreationDate": _pdf_date(metadata.created_at),
        "/ModDate": _pdf_date(metadata.modified_at),
    }
