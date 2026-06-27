import pytest

from foxglove.cli import CliError, parse_args
from foxglove.thinkst import SUPPORTED_KINDS
from foxglove.thinkst.cli import ThinkstCreateArgs


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
