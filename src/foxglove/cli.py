import argparse
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from foxglove.models import DEFAULT_MODEL, DEFAULT_PASSWORDS, MAX_FILES, SUPPORTED_FORMATS

if TYPE_CHECKING:
    from foxglove.thinkst.cli import ThinkstCreateArgs, ThinkstListArgs

OPERATION_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$")
SUBCOMMANDS: frozenset[str] = frozenset({"generate", "thinkst"})


@dataclass(frozen=True)
class CliArgs:
    base_dir: str
    operation: str
    num_files: int
    formats: list[str]
    teams: list[str]
    company: str
    file_content: str
    model: str
    passwords: list[str]
    resume: bool
    dry_run: bool


@dataclass(frozen=True)
class CliError:
    message: str


def _add_generate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--num-files", required=True, type=int)
    parser.add_argument("--formats", required=True)
    parser.add_argument("--teams", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--file-content", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--passwords", default=None)
    parser.add_argument("--resume", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)


def _validate_generate(args: argparse.Namespace) -> CliArgs | CliError:
    if not os.path.isdir(args.base_dir):
        return CliError(message=f"base-dir is not an existing directory: '{args.base_dir}'")

    if not os.access(args.base_dir, os.W_OK):
        return CliError(message=f"base-dir is not writable: '{args.base_dir}'")

    if not OPERATION_PATTERN.match(args.operation):
        return CliError(message=f"Invalid operation name: '{args.operation}'")

    if not 1 <= args.num_files <= MAX_FILES:
        return CliError(message=f"num-files must be between 1 and {MAX_FILES}")

    formats = args.formats.split(",")
    invalid_formats = [f for f in formats if f not in SUPPORTED_FORMATS]
    if invalid_formats or formats == [""]:
        return CliError(message=f"Unsupported formats: {', '.join(invalid_formats or ['(empty)'])}")

    teams = args.teams.split(",")
    empty_teams = [t for t in teams if t == ""]
    if empty_teams:
        return CliError(message="Team names must not be empty")
    long_teams = [t for t in teams if len(t) > 64]
    if long_teams:
        return CliError(message=f"Team names exceed 64 chars: {', '.join(long_teams)}")

    if not args.company:
        return CliError(message="company must not be empty")
    if len(args.company) > 256:
        return CliError(message="company must be at most 256 characters")

    if not args.file_content:
        return CliError(message="file-content must not be empty")
    if len(args.file_content) > 1024:
        return CliError(message="file-content must be at most 1024 characters")

    passwords = args.passwords.split(",") if args.passwords else list(DEFAULT_PASSWORDS)

    return CliArgs(
        base_dir=args.base_dir,
        operation=args.operation,
        num_files=args.num_files,
        formats=formats,
        teams=teams,
        company=args.company,
        file_content=args.file_content,
        model=args.model,
        passwords=passwords,
        resume=args.resume,
        dry_run=args.dry_run,
    )


def parse_args(argv: list[str]) -> "CliArgs | ThinkstCreateArgs | ThinkstListArgs | CliError":
    if not argv:
        return CliError(
            message="no subcommand given; use 'foxglove generate ...' or 'foxglove thinkst ...'"
        )
    if argv[0] not in SUBCOMMANDS:
        if argv[0].startswith("--"):
            return CliError(
                message=(
                    "the flat invocation 'foxglove --base-dir ...' is no longer supported; "
                    "use 'foxglove generate --base-dir ...' instead"
                )
            )
        return CliError(message=f"unknown command '{argv[0]}'; use 'generate' or 'thinkst'")

    if argv[0] == "thinkst":
        from foxglove.thinkst.cli import parse_thinkst_args
        return parse_thinkst_args(argv)

    parser = argparse.ArgumentParser(prog="foxglove generate", exit_on_error=False)
    _add_generate_arguments(parser)
    try:
        args = parser.parse_args(argv[1:])
    except argparse.ArgumentError as e:
        return CliError(message=str(e))
    return _validate_generate(args)
