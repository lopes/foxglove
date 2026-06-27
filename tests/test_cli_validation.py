from pathlib import Path

from foxglove.cli import CliArgs, CliError, parse_args
from foxglove.models import DEFAULT_MODEL, DEFAULT_PASSWORDS, MAX_FILES, SUPPORTED_FORMATS


def _valid_argv(**overrides: str) -> list[str]:
    defaults = {
        "--base-dir": "/tmp",
        "--operation": "op_alpha",
        "--num-files": "10",
        "--formats": "pdf,docx",
        "--teams": "it,infra",
        "--company": "Acme Corp",
        "--file-content": "IT documentation files",
    }
    merged = defaults | overrides
    return ["generate"] + [item for pair in merged.items() for item in pair]


def test_happy_path_parses_all_required_args():
    result = parse_args(_valid_argv())
    assert isinstance(result, CliArgs)
    assert result.base_dir == "/tmp"
    assert result.operation == "op_alpha"
    assert result.num_files == 10
    assert result.formats == ["pdf", "docx"]
    assert result.teams == ["it", "infra"]
    assert result.company == "Acme Corp"
    assert result.file_content == "IT documentation files"


def test_happy_path_applies_defaults():
    result = parse_args(_valid_argv())
    assert isinstance(result, CliArgs)
    assert result.model == DEFAULT_MODEL
    assert result.passwords == list(DEFAULT_PASSWORDS)
    assert result.resume is False
    assert result.dry_run is False


def test_missing_base_dir_returns_cli_error():
    argv = _valid_argv()
    argv = [a for a in argv if a != "--base-dir" and a != "/tmp"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "base-dir" in result.message


def test_missing_operation_returns_cli_error():
    argv = _valid_argv()
    argv = [a for a in argv if a != "--operation" and a != "op_alpha"]
    result = parse_args(argv)
    assert isinstance(result, CliError)
    assert "operation" in result.message


import pytest


@pytest.mark.parametrize("op", ["op_alpha", "a", "test.op-1", "A1_b2"])
def test_valid_operation_names(op: str):
    result = parse_args(_valid_argv(**{"--operation": op}))
    assert isinstance(result, CliArgs)
    assert result.operation == op


@pytest.mark.parametrize("op", ["", ".starts_dot", "-starts_dash", "has space", "a" * 256])
def test_invalid_operation_names(op: str):
    result = parse_args(_valid_argv(**{"--operation": op}))
    assert isinstance(result, CliError)
    assert "operation" in result.message.lower()


@pytest.mark.parametrize("n", ["1", "100", str(MAX_FILES)])
def test_valid_num_files(n: str):
    result = parse_args(_valid_argv(**{"--num-files": n}))
    assert isinstance(result, CliArgs)
    assert result.num_files == int(n)


@pytest.mark.parametrize("n", ["0", "-1", str(MAX_FILES + 1)])
def test_invalid_num_files(n: str):
    result = parse_args(_valid_argv(**{"--num-files": n}))
    assert isinstance(result, CliError)


def test_non_integer_num_files():
    result = parse_args(_valid_argv(**{"--num-files": "abc"}))
    assert isinstance(result, CliError)


def test_valid_formats_all_supported():
    all_formats = ",".join(sorted(SUPPORTED_FORMATS))
    result = parse_args(_valid_argv(**{"--formats": all_formats}))
    assert isinstance(result, CliArgs)
    assert set(result.formats) == SUPPORTED_FORMATS


def test_invalid_format_returns_error():
    result = parse_args(_valid_argv(**{"--formats": "pdf,exe"}))
    assert isinstance(result, CliError)
    assert "exe" in result.message


def test_empty_formats_returns_error():
    result = parse_args(_valid_argv(**{"--formats": ""}))
    assert isinstance(result, CliError)


def test_valid_teams():
    result = parse_args(_valid_argv(**{"--teams": "it,infra,financial"}))
    assert isinstance(result, CliArgs)
    assert result.teams == ["it", "infra", "financial"]


def test_team_name_exceeding_64_chars_returns_error():
    long_team = "a" * 65
    result = parse_args(_valid_argv(**{"--teams": f"it,{long_team}"}))
    assert isinstance(result, CliError)


def test_company_exceeding_256_chars_returns_error():
    result = parse_args(_valid_argv(**{"--company": "a" * 257}))
    assert isinstance(result, CliError)


def test_empty_company_returns_error():
    result = parse_args(_valid_argv(**{"--company": ""}))
    assert isinstance(result, CliError)


def test_file_content_exceeding_1024_chars_returns_error():
    result = parse_args(_valid_argv(**{"--file-content": "a" * 1025}))
    assert isinstance(result, CliError)


def test_empty_file_content_returns_error():
    result = parse_args(_valid_argv(**{"--file-content": ""}))
    assert isinstance(result, CliError)


def test_custom_model():
    result = parse_args(_valid_argv(**{"--model": "custom-model-id"}))
    assert isinstance(result, CliArgs)
    assert result.model == "custom-model-id"


def test_custom_passwords():
    result = parse_args(_valid_argv(**{"--passwords": "p1,p2,p3"}))
    assert isinstance(result, CliArgs)
    assert result.passwords == ["p1", "p2", "p3"]


def test_resume_flag():
    argv = _valid_argv()
    argv.append("--resume")
    result = parse_args(argv)
    assert isinstance(result, CliArgs)
    assert result.resume is True


def test_dry_run_flag():
    argv = _valid_argv()
    argv.append("--dry-run")
    result = parse_args(argv)
    assert isinstance(result, CliArgs)
    assert result.dry_run is True


def test_base_dir_must_exist(tmp_path: Path):
    result = parse_args(_valid_argv(**{"--base-dir": str(tmp_path)}))
    assert isinstance(result, CliArgs)


def test_base_dir_nonexistent_returns_error():
    result = parse_args(_valid_argv(**{"--base-dir": "/nonexistent/path/xyz"}))
    assert isinstance(result, CliError)
    assert "base-dir" in result.message.lower()


def test_base_dir_file_not_directory_returns_error(tmp_path: Path):
    file_path = tmp_path / "afile.txt"
    file_path.write_text("hello")
    result = parse_args(_valid_argv(**{"--base-dir": str(file_path)}))
    assert isinstance(result, CliError)


def test_base_dir_not_writable_returns_error(tmp_path: Path):
    read_only = tmp_path / "ro"
    read_only.mkdir()
    read_only.chmod(0o444)
    try:
        result = parse_args(_valid_argv(**{"--base-dir": str(read_only)}))
        assert isinstance(result, CliError)
        assert "base-dir" in result.message.lower()
    finally:
        read_only.chmod(0o755)


def test_empty_team_name_returns_error():
    result = parse_args(_valid_argv(**{"--teams": ""}))
    assert isinstance(result, CliError)


def test_team_name_with_empty_entry_returns_error():
    result = parse_args(_valid_argv(**{"--teams": "it,,infra"}))
    assert isinstance(result, CliError)


def test_honeytokens_missing_defaults_to_empty_list():
    result = parse_args(_valid_argv())
    assert isinstance(result, CliArgs)
    assert result.honeytokens == []


def test_honeytokens_single_value():
    result = parse_args(_valid_argv(**{"--honeytokens": "https://a.canary.tools/x"}))
    assert isinstance(result, CliArgs)
    assert result.honeytokens == ["https://a.canary.tools/x"]


def test_honeytokens_multiple_values():
    result = parse_args(
        _valid_argv(**{"--honeytokens": "https://a.canary.tools/x,host.b.com,https://c.com"})
    )
    assert isinstance(result, CliArgs)
    assert result.honeytokens == [
        "https://a.canary.tools/x",
        "host.b.com",
        "https://c.com",
    ]


def test_honeytokens_empty_string_returns_error():
    result = parse_args(_valid_argv(**{"--honeytokens": ""}))
    assert isinstance(result, CliError)
    assert "honeytoken" in result.message.lower()


def test_honeytokens_empty_entry_returns_error():
    result = parse_args(_valid_argv(**{"--honeytokens": "a,,b"}))
    assert isinstance(result, CliError)
    assert "honeytoken" in result.message.lower()


def test_honeytokens_too_many_returns_error():
    tokens = ",".join(f"t{i}" for i in range(21))
    result = parse_args(_valid_argv(**{"--honeytokens": tokens}))
    assert isinstance(result, CliError)
    assert "honeytoken" in result.message.lower()


def test_honeytokens_exactly_20_accepted():
    tokens = ",".join(f"t{i}" for i in range(20))
    result = parse_args(_valid_argv(**{"--honeytokens": tokens}))
    assert isinstance(result, CliArgs)
    assert len(result.honeytokens) == 20


def test_honeytokens_entry_too_long_returns_error():
    too_long = "a" * 257
    result = parse_args(_valid_argv(**{"--honeytokens": f"ok,{too_long}"}))
    assert isinstance(result, CliError)
    assert "honeytoken" in result.message.lower()


def test_honeytokens_entry_with_whitespace_returns_error():
    result = parse_args(_valid_argv(**{"--honeytokens": "ok, with space"}))
    assert isinstance(result, CliError)
    assert "honeytoken" in result.message.lower()
