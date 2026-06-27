import os
import sys

from foxglove.models import EXIT_ENV_ERROR, EXIT_SUCCESS, EXIT_THINKST_ERROR
from foxglove.thinkst import FOXGLOVE_TAG
from foxglove.thinkst.cli import ThinkstCreateArgs
from foxglove.thinkst.client import ThinkstApiError, ThinkstClient
from foxglove.thinkst.models import CreateTokenResult

AUTH_TOKEN_ENV: str = "THINKST_AUTH_TOKEN"


def run_thinkst(args: ThinkstCreateArgs) -> int:
    auth_token = os.environ.get(AUTH_TOKEN_ENV)
    if not auth_token:
        print(
            f"Error: {AUTH_TOKEN_ENV} environment variable is not set",
            file=sys.stderr,
        )
        return EXIT_ENV_ERROR

    client = ThinkstClient(console=args.console, auth_token=auth_token)
    try:
        result = client.create_token(
            kind=args.kind,
            memo=f"{FOXGLOVE_TAG} {args.memo}",
            flock_id=args.flock_id,
        )
    except ThinkstApiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_THINKST_ERROR
    finally:
        client.close()

    _print_create_result(result)
    return EXIT_SUCCESS


def _print_create_result(result: CreateTokenResult) -> None:
    callback = result.url or result.hostname or "(no callback returned)"
    print(f"canarytoken: {result.canarytoken}")
    print(f"kind:        {result.kind}")
    print(f"flock:       {result.flock_id}")
    print(f"memo:        {result.memo}")
    print(f"callback:    {callback}")
