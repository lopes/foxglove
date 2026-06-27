import pytest

from foxglove.cli import CliError, parse_args
from foxglove.thinkst import SUPPORTED_KINDS
from foxglove.thinkst.cli import ThinkstCreateArgs, ThinkstListArgs, ThinkstRemoveArgs


def _create_argv(**overrides: str) -> list[str]:
    defaults = {
        "--console": "acme",
        "--kind": "dns",
        "--flock": "flock:default",
        "--memo": "Q3 billing report",
    }
    merged = defaults | overrides
    return ["thinkst", "create"] + [item for pair in merged.items() for item in pair]


def test_create_happy_path_parses_all_args():
    result = parse_args(_create_argv())
    assert isinstance(result, ThinkstCreateArgs)
    assert result.console == "acme"
    assert result.kind == "dns"
    assert result.flock_id == "flock:default"
    assert result.memo == "Q3 billing report"


def test_create_missing_console_returns_error():
    argv = [a for a in _create_argv() if a != "--console" and a != "acme"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "console" in result.message.lower()


def test_create_missing_kind_returns_error():
    argv = [a for a in _create_argv() if a != "--kind" and a != "dns"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "kind" in result.message.lower()


def test_create_missing_flock_returns_error():
    argv = [a for a in _create_argv() if a != "--flock" and a != "flock:default"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "flock" in result.message.lower()


def test_create_missing_memo_returns_error():
    argv = [a for a in _create_argv() if a != "--memo" and a != "Q3 billing report"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "memo" in result.message.lower()


@pytest.mark.parametrize("console", ["acme", "acme-corp", "acme123", "a"])
def test_valid_console_values(console: str):
    result = parse_args(_create_argv(**{"--console": console}))
    assert isinstance(result, ThinkstCreateArgs)
    assert result.console == console


@pytest.mark.parametrize("console", ["", "Acme", "acme.corp", "acme_corp", "acme corp", "a" * 65])
def test_invalid_console_values(console: str):
    result = parse_args(_create_argv(**{"--console": console}))
    assert isinstance(result, CliError)
    assert "console" in result.message.lower()


@pytest.mark.parametrize("kind", sorted(SUPPORTED_KINDS))
def test_all_supported_kinds_accepted(kind: str):
    result = parse_args(_create_argv(**{"--kind": kind}))
    assert isinstance(result, ThinkstCreateArgs)
    assert result.kind == kind


@pytest.mark.parametrize("kind", ["doc-msword", "cloned-web", "signed-exe", "unknown"])
def test_unsupported_kinds_rejected(kind: str):
    result = parse_args(_create_argv(**{"--kind": kind}))
    assert isinstance(result, CliError)
    assert "kind" in result.message.lower()


def test_empty_memo_returns_error():
    result = parse_args(_create_argv(**{"--memo": ""}))
    assert isinstance(result, CliError)
    assert "memo" in result.message.lower()


def test_long_memo_returns_error():
    result = parse_args(_create_argv(**{"--memo": "a" * 257}))
    assert isinstance(result, CliError)
    assert "memo" in result.message.lower()


def test_memo_at_max_length_accepted():
    result = parse_args(_create_argv(**{"--memo": "a" * 256}))
    assert isinstance(result, ThinkstCreateArgs)


def test_empty_flock_returns_error():
    result = parse_args(_create_argv(**{"--flock": ""}))
    assert isinstance(result, CliError)
    assert "flock" in result.message.lower()


def _list_argv(extra: list[str] | None = None) -> list[str]:
    return ["thinkst", "list", "--console", "acme"] + (extra or [])


def test_list_happy_path():
    result = parse_args(_list_argv())
    assert isinstance(result, ThinkstListArgs)
    assert result.console == "acme"
    assert result.flock_id is None
    assert result.kind is None
    assert result.json_output is False


def test_list_missing_console_returns_error():
    result = parse_args(["thinkst", "list"])
    assert isinstance(result, CliError)
    assert "console" in result.message.lower()


def test_list_with_flock():
    result = parse_args(_list_argv(["--flock", "flock:abc"]))
    assert isinstance(result, ThinkstListArgs)
    assert result.flock_id == "flock:abc"


def test_list_with_kind():
    result = parse_args(_list_argv(["--kind", "dns"]))
    assert isinstance(result, ThinkstListArgs)
    assert result.kind == "dns"


def test_list_with_invalid_kind_returns_error():
    result = parse_args(_list_argv(["--kind", "not-a-kind"]))
    assert isinstance(result, CliError)
    assert "kind" in result.message.lower()


def test_list_with_json_flag():
    result = parse_args(_list_argv(["--json"]))
    assert isinstance(result, ThinkstListArgs)
    assert result.json_output is True


def test_list_invalid_console_returns_error():
    result = parse_args(["thinkst", "list", "--console", "Acme.Corp"])
    assert isinstance(result, CliError)
    assert "console" in result.message.lower()


def test_remove_happy_path():
    result = parse_args(["thinkst", "remove", "--console", "acme", "tok-abc"])
    assert isinstance(result, ThinkstRemoveArgs)
    assert result.console == "acme"
    assert result.canarytoken == "tok-abc"


def test_remove_missing_id_returns_error():
    result = parse_args(["thinkst", "remove", "--console", "acme"])
    assert isinstance(result, CliError)


def test_remove_missing_console_returns_error():
    result = parse_args(["thinkst", "remove", "tok-abc"])
    assert isinstance(result, CliError)
    assert "console" in result.message.lower()


def test_remove_empty_id_returns_error():
    result = parse_args(["thinkst", "remove", "--console", "acme", ""])
    assert isinstance(result, CliError)
