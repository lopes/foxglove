import json
import os
import sys

from foxglove.models import EXIT_ENV_ERROR, EXIT_SUCCESS, EXIT_THINKST_ERROR
from foxglove.thinkst import FOXGLOVE_TAG
from foxglove.thinkst.cli import ThinkstCreateArgs, ThinkstListArgs, ThinkstRemoveArgs
from foxglove.thinkst.client import IncidentsBlockedError, ThinkstApiError, ThinkstClient
from foxglove.thinkst.models import CreateTokenResult, TokenSummary

AUTH_TOKEN_ENV: str = "THINKST_AUTH_TOKEN"


def run_thinkst(
    args: "ThinkstCreateArgs | ThinkstListArgs | ThinkstRemoveArgs",
) -> int:
    auth_token = os.environ.get(AUTH_TOKEN_ENV)
    if not auth_token:
        print(
            f"Error: {AUTH_TOKEN_ENV} environment variable is not set",
            file=sys.stderr,
        )
        return EXIT_ENV_ERROR

    client = ThinkstClient(console=args.console, auth_token=auth_token)
    try:
        if isinstance(args, ThinkstCreateArgs):
            return _run_create(args, client)
        if isinstance(args, ThinkstListArgs):
            return _run_list(args, client)
        return _run_remove(args, client)
    finally:
        client.close()


def _run_create(args: ThinkstCreateArgs, client: ThinkstClient) -> int:
    try:
        result = client.create_token(
            kind=args.kind,
            memo=f"{FOXGLOVE_TAG} {args.memo}",
            flock_id=args.flock_id,
        )
    except ThinkstApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_THINKST_ERROR

    _print_create_result(result)
    return EXIT_SUCCESS


def _run_list(args: ThinkstListArgs, client: ThinkstClient) -> int:
    try:
        tokens = client.list_tokens(flock_id=args.flock_id)
    except ThinkstApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_THINKST_ERROR

    filtered = [t for t in tokens if FOXGLOVE_TAG in t.memo]
    if args.kind is not None:
        filtered = [t for t in filtered if t.kind == args.kind]

    if args.json_output:
        print(json.dumps([t.model_dump() for t in filtered], indent=2))
    else:
        for t in filtered:
            print(f"{t.canarytoken} | {t.kind} | {t.flock_id} | {t.memo}")

    return EXIT_SUCCESS


def _run_remove(args: ThinkstRemoveArgs, client: ThinkstClient) -> int:
    try:
        client.delete_token(canarytoken=args.canarytoken)
    except IncidentsBlockedError as e:
        print(f"Cannot delete: {e}", file=sys.stderr)
        answer = input(
            f"Token {args.canarytoken} has unacknowledged incidents. "
            "Clear and delete anyway? (y/n): "
        ).strip().lower()
        if answer != "y":
            return EXIT_THINKST_ERROR
        try:
            client.delete_token(canarytoken=args.canarytoken, clear_incidents=True)
        except ThinkstApiError as e2:
            print(f"Error: {e2}", file=sys.stderr)
            return EXIT_THINKST_ERROR
    except ThinkstApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_THINKST_ERROR

    print(f"deleted: {args.canarytoken}")
    return EXIT_SUCCESS


def _print_create_result(result: CreateTokenResult) -> None:
    callback = result.url or result.hostname or "(no callback returned)"
    print(f"canarytoken: {result.canarytoken}")
    print(f"kind:        {result.kind}")
    print(f"flock:       {result.flock_id}")
    print(f"memo:        {result.memo}")
    print(f"callback:    {callback}")
