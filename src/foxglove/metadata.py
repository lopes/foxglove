import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class FileMetadata:
    author: str
    created_at: datetime
    modified_at: datetime


def build_file_metadata(
    authors: list[str],
    *,
    rng: random.Random,
    now: datetime | None = None,
) -> FileMetadata:
    modified_at = now if now is not None else datetime.now(UTC)
    delta = timedelta(
        days=rng.randint(1, 25),
        hours=rng.randint(1, 24),
        seconds=rng.randint(1, 60),
    )
    created_at = modified_at - delta
    author = rng.choice(authors) if authors else ""
    return FileMetadata(author=author, created_at=created_at, modified_at=modified_at)
