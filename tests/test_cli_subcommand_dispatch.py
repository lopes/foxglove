from foxglove.cli import CliArgs, CliError, parse_args


def _generate_argv(prefix: list[str]) -> list[str]:
    return prefix + [
        "--base-dir", "/tmp",
        "--operation", "op_alpha",
        "--num-files", "1",
        "--formats", "md",
        "--teams", "it",
        "--company", "Acme",
        "--file-content", "docs",
    ]


def test_generate_subcommand_parses_args():
    result = parse_args(_generate_argv(["generate"]))
    assert isinstance(result, CliArgs)
    assert result.operation == "op_alpha"


def test_no_subcommand_returns_error():
    result = parse_args([])
    assert isinstance(result, CliError)


def test_legacy_flat_invocation_returns_error():
    result = parse_args(_generate_argv([]))
    assert isinstance(result, CliError)
    assert "generate" in result.message.lower()


def test_unknown_subcommand_returns_error():
    result = parse_args(["wat"])
    assert isinstance(result, CliError)
