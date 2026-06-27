import argparse
import re
from dataclasses import dataclass

from foxglove.cli import CliError
from foxglove.thinkst import SUPPORTED_KINDS

CONSOLE_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9-]+$")
MAX_CONSOLE_LEN: int = 64
MAX_MEMO_LEN: int = 256
THINKST_ACTIONS: frozenset[str] = frozenset({"create", "list", "remove"})


@dataclass(frozen=True)
class ThinkstCreateArgs:
    console: str
    kind: str
    flock_id: str
    memo: str


@dataclass(frozen=True)
class ThinkstListArgs:
    console: str
    flock_id: str | None
    kind: str | None
    json_output: bool


@dataclass(frozen=True)
class ThinkstRemoveArgs:
    console: str
    canarytoken: str


def _validate_console(value: str) -> str | None:
    if not value:
        return "console must not be empty"
    if len(value) > MAX_CONSOLE_LEN:
        return f"console must be at most {MAX_CONSOLE_LEN} characters"
    if not CONSOLE_PATTERN.match(value):
        return f"console must match {CONSOLE_PATTERN.pattern} (lowercase letters, digits, hyphens)"
    return None


def _validate_create(args: argparse.Namespace) -> ThinkstCreateArgs | CliError:
    console_error = _validate_console(args.console)
    if console_error is not None:
        return CliError(message=console_error)

    if args.kind not in SUPPORTED_KINDS:
        supported = ", ".join(sorted(SUPPORTED_KINDS))
        return CliError(
            message=f"unsupported kind '{args.kind}'; supported kinds: {supported}"
        )

    if not args.flock:
        return CliError(message="flock must not be empty")

    if not args.memo:
        return CliError(message="memo must not be empty")
    if len(args.memo) > MAX_MEMO_LEN:
        return CliError(message=f"memo must be at most {MAX_MEMO_LEN} characters")

    return ThinkstCreateArgs(
        console=args.console,
        kind=args.kind,
        flock_id=args.flock,
        memo=args.memo,
    )


def _validate_list(args: argparse.Namespace) -> ThinkstListArgs | CliError:
    console_error = _validate_console(args.console)
    if console_error is not None:
        return CliError(message=console_error)

    if args.kind is not None and args.kind not in SUPPORTED_KINDS:
        supported = ", ".join(sorted(SUPPORTED_KINDS))
        return CliError(
            message=f"unsupported kind '{args.kind}'; supported kinds: {supported}"
        )

    return ThinkstListArgs(
        console=args.console,
        flock_id=args.flock,
        kind=args.kind,
        json_output=args.json,
    )


def _validate_remove(args: argparse.Namespace) -> ThinkstRemoveArgs | CliError:
    console_error = _validate_console(args.console)
    if console_error is not None:
        return CliError(message=console_error)

    if not args.canarytoken:
        return CliError(message="canarytoken id must not be empty")

    return ThinkstRemoveArgs(
        console=args.console,
        canarytoken=args.canarytoken,
    )


def parse_thinkst_args(
    argv: list[str],
) -> "ThinkstCreateArgs | ThinkstListArgs | ThinkstRemoveArgs | CliError":
    if len(argv) < 2:
        return CliError(
            message=f"thinkst requires an action; one of: {', '.join(sorted(THINKST_ACTIONS))}"
        )
    if argv[1] not in THINKST_ACTIONS:
        return CliError(
            message=f"unknown thinkst action '{argv[1]}'; supported: {', '.join(sorted(THINKST_ACTIONS))}"
        )

    parser = argparse.ArgumentParser(prog="foxglove thinkst", exit_on_error=False)
    sub = parser.add_subparsers(dest="action", required=True)

    create = sub.add_parser("create", exit_on_error=False)
    create.add_argument("--console", required=True)
    create.add_argument("--kind", required=True)
    create.add_argument("--flock", required=True)
    create.add_argument("--memo", required=True)

    list_p = sub.add_parser("list", exit_on_error=False)
    list_p.add_argument("--console", required=True)
    list_p.add_argument("--flock", default=None)
    list_p.add_argument("--kind", default=None)
    list_p.add_argument("--json", action="store_true", default=False)

    remove = sub.add_parser("remove", exit_on_error=False)
    remove.add_argument("--console", required=True)
    remove.add_argument("canarytoken")

    try:
        args = parser.parse_args(argv[1:])
    except argparse.ArgumentError as e:
        return CliError(message=str(e))

    if args.action == "create":
        return _validate_create(args)
    if args.action == "list":
        return _validate_list(args)
    if args.action == "remove":
        return _validate_remove(args)
    return CliError(message=f"'{args.action}' is not yet implemented")
