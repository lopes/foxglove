import re
from pathlib import Path

import anthropic
from anthropic.types import TextBlock

from foxglove.models import FileEntry, Manifest
from foxglove.writers import get_writer


def generate_file_content(
    client: anthropic.Anthropic,
    entry: FileEntry,
    model: str,
    company: str,
    teams: list[str],
    file_content: str,
) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                f"Generate realistic content for a {entry.format} file.\n"
                f"This file belongs to the company: {company}.\n"
                f"It was created by the {', '.join(teams)} team(s).\n"
                f"File context: {file_content}\n"
                f"Specific file description: {entry.summary}\n"
                f"Return only the file content, no explanation."
            ),
        }],
    )
    for block in response.content:
        if isinstance(block, TextBlock):
            return block.text
    return ""


def _extract_epdf_password(summary: str) -> str | None:
    match = re.search(r"Password: (.+)$", summary)
    return match.group(1) if match else None


def write_generated_file(
    content: str,
    entry: FileEntry,
    operation_dir: Path,
) -> None:
    file_path = operation_dir / entry.path
    writer = get_writer(entry.format)
    if entry.format == "epdf":
        password = _extract_epdf_password(entry.summary)
        if password is None:
            raise ValueError(f"No password found in EPDF summary: {entry.summary}")
        writer(content, file_path, password=password)
    else:
        writer(content, file_path)


def generate_all(
    client: anthropic.Anthropic,
    manifest: Manifest,
    operation_dir: Path,
    resume: bool = False,
) -> int:
    to_generate = [
        entry for entry in manifest.files
        if not (resume and (operation_dir / entry.path).exists())
    ]
    total = len(to_generate)
    failures = 0
    for idx, entry in enumerate(to_generate, start=1):
        file_path = operation_dir / entry.path
        print(f"Generating file {idx}/{total}: {file_path}")
        try:
            content = generate_file_content(
                client,
                entry,
                manifest.parameters.model,
                company=manifest.parameters.company,
                teams=manifest.parameters.teams,
                file_content=manifest.parameters.file_content,
            )
            write_generated_file(content, entry, operation_dir)
        except Exception as e:
            print(f"    Error generating file: {e}")
            failures += 1
    return failures
