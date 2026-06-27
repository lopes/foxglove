import json
import os
import sys

from foxglove.models import EXIT_ENV_ERROR, EXIT_SUCCESS, EXIT_THINKST_ERROR
from foxglove.thinkst import FOXGLOVE_TAG
from foxglove.thinkst.cli import ThinkstCreateArgs, ThinkstListArgs
from foxglove.thinkst.client import ThinkstApiError, ThinkstClient
from foxglove.thinkst.models import CreateTokenResult, TokenSummary

AUTH_TOKEN_ENV: str = "THINKST_AUTH_TOKEN"


def run_thinkst(args: "ThinkstCreateArgs | ThinkstListArgs") -> int:
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
        return _run_list(args, client)
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


def _print_create_result(result: CreateTokenResult) -> None:
    callback = result.url or result.hostname or "(no callback returned)"
    print(f"canarytoken: {result.canarytoken}")
    print(f"kind:        {result.kind}")
    print(f"flock:       {result.flock_id}")
    print(f"memo:        {result.memo}")
    print(f"callback:    {callback}")
