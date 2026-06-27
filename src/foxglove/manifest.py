from pathlib import Path

from pydantic import ValidationError

from foxglove.models import Manifest

MANIFEST_FILENAME = "MANIFEST.json"


def write_manifest(manifest: Manifest, operation_dir: Path) -> None:
    operation_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = operation_dir / MANIFEST_FILENAME
    manifest_path.write_text(manifest.model_dump_json(indent=2))


def read_manifest(operation_dir: Path) -> Manifest | None:
    manifest_path = operation_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        return None
    try:
        return Manifest.model_validate_json(manifest_path.read_text())
    except (ValidationError, ValueError):
        return None


def manifest_exists(operation_dir: Path) -> bool:
    return (operation_dir / MANIFEST_FILENAME).exists()
