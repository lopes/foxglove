import random
from datetime import UTC, datetime, timedelta

from foxglove.metadata import FileMetadata, build_file_metadata

FIXED_NOW = datetime(2026, 6, 27, 15, 0, 0, tzinfo=UTC)


def test_metadata_picks_author_from_pool():
    rng = random.Random(0)
    meta = build_file_metadata(
        ["Alice", "Bob", "Carla"], rng=rng, now=FIXED_NOW,
    )
    assert meta.author in {"Alice", "Bob", "Carla"}


def test_metadata_empty_pool_returns_empty_author():
    rng = random.Random(0)
    meta = build_file_metadata([], rng=rng, now=FIXED_NOW)
    assert meta.author == ""


def test_metadata_modified_at_equals_provided_now():
    rng = random.Random(0)
    meta = build_file_metadata(["Alice"], rng=rng, now=FIXED_NOW)
    assert meta.modified_at == FIXED_NOW


def test_metadata_created_at_is_before_modified_at():
    rng = random.Random(0)
    meta = build_file_metadata(["Alice"], rng=rng, now=FIXED_NOW)
    assert meta.created_at < meta.modified_at


def test_metadata_created_at_within_canarytokens_jitter_range():
    rng = random.Random(0)
    meta = build_file_metadata(["Alice"], rng=rng, now=FIXED_NOW)
    delta = meta.modified_at - meta.created_at
    assert timedelta(days=1) <= delta <= timedelta(days=26, hours=1)


def test_metadata_is_deterministic_with_seeded_rng():
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    m1 = build_file_metadata(["Alice", "Bob"], rng=rng1, now=FIXED_NOW)
    m2 = build_file_metadata(["Alice", "Bob"], rng=rng2, now=FIXED_NOW)
    assert m1 == m2


def test_metadata_default_now_close_to_real_now():
    rng = random.Random(0)
    before = datetime.now(UTC)
    meta = build_file_metadata(["Alice"], rng=rng)
    after = datetime.now(UTC)
    assert before <= meta.modified_at <= after


def test_file_metadata_is_frozen():
    import dataclasses
    meta = FileMetadata(
        author="Alice", created_at=FIXED_NOW - timedelta(days=10), modified_at=FIXED_NOW,
    )
    try:
        meta.author = "Bob"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("FileMetadata should be frozen")
