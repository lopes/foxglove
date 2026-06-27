from unittest.mock import MagicMock, patch

import pytest

from foxglove.__main__ import run
from foxglove.models import EXIT_ENV_ERROR, EXIT_SUCCESS, EXIT_THINKST_ERROR
from foxglove.thinkst import FOXGLOVE_TAG
from foxglove.thinkst.client import IncidentsBlockedError, ThinkstApiError
from foxglove.thinkst.models import CreateTokenResult, TokenSummary


CREATE_ARGV = [
    "thinkst", "create",
    "--console", "acme",
    "--kind", "dns",
    "--flock", "flock:default",
    "--memo", "Q3 billing report",
]


def _make_create_result(**overrides: object) -> CreateTokenResult:
    defaults = {
        "canarytoken": "tok-123",
        "kind": "dns",
        "flock_id": "flock:default",
        "memo": f"{FOXGLOVE_TAG} Q3 billing report",
        "hostname": "abc.canarytokens.com",
        "url": None,
    }
    return CreateTokenResult.model_validate({**defaults, **overrides})


def test_create_missing_auth_token_returns_env_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("THINKST_API_KEY", raising=False)
    result = run(CREATE_ARGV)
    assert result == EXIT_ENV_ERROR


def test_create_happy_path_returns_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(CREATE_ARGV)

    assert result == EXIT_SUCCESS
    captured = capsys.readouterr()
    assert "tok-123" in captured.out
    assert "abc.canarytokens.com" in captured.out


def test_create_prefixes_memo_with_foxglove_tag(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(CREATE_ARGV)

    call_kwargs = mock_client.create_token.call_args.kwargs
    assert call_kwargs["memo"] == f"{FOXGLOVE_TAG} Q3 billing report"
    assert call_kwargs["kind"] == "dns"
    assert call_kwargs["flock_id"] == "flock:default"


def test_create_passes_console_and_token_to_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "my-secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()
    factory = MagicMock(return_value=mock_client)

    with patch("foxglove.thinkst.runner.ThinkstClient", factory):
        run(CREATE_ARGV)

    factory.assert_called_once_with(console="acme", auth_token="my-secret")


def test_create_prints_url_when_present(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result(
        kind="http",
        hostname=None,
        url="https://abc.canarytokens.com/x.gif",
    )

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(CREATE_ARGV)

    captured = capsys.readouterr()
    assert "https://abc.canarytokens.com/x.gif" in captured.out


def test_create_api_error_returns_thinkst_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.create_token.side_effect = ThinkstApiError("Unauthorized")

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(CREATE_ARGV)

    assert result == EXIT_THINKST_ERROR


LIST_ARGV = ["thinkst", "list", "--console", "acme"]


def _summary(**overrides: object) -> TokenSummary:
    base: dict[str, object] = {
        "canarytoken": "t-1",
        "kind": "dns",
        "flock_id": "flock:default",
        "memo": f"{FOXGLOVE_TAG} marketing folder",
        "created_printable": "2026-06-27 12:00:00 (UTC)",
    }
    return TokenSummary.model_validate({**base, **overrides})


def test_list_missing_auth_token_returns_env_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("THINKST_API_KEY", raising=False)
    result = run(LIST_ARGV)
    assert result == EXIT_ENV_ERROR


def test_list_filters_to_foxglove_tagged_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.return_value = [
        _summary(canarytoken="ours", memo=f"{FOXGLOVE_TAG} mine"),
        _summary(canarytoken="someone-else", memo="other team's token"),
        _summary(canarytoken="ours-2", memo=f"{FOXGLOVE_TAG} second one"),
    ]

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(LIST_ARGV)

    assert result == EXIT_SUCCESS
    captured = capsys.readouterr()
    assert "ours" in captured.out
    assert "ours-2" in captured.out
    assert "someone-else" not in captured.out


def test_list_empty_result_succeeds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.return_value = []

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(LIST_ARGV)

    assert result == EXIT_SUCCESS


def test_list_passes_flock_to_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.return_value = []

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(LIST_ARGV + ["--flock", "flock:abc"])

    mock_client.list_tokens.assert_called_once_with(flock_id="flock:abc")


def test_list_filters_by_kind_client_side(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.return_value = [
        _summary(canarytoken="d1", kind="dns", memo=f"{FOXGLOVE_TAG} a"),
        _summary(canarytoken="h1", kind="http", memo=f"{FOXGLOVE_TAG} b"),
    ]

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(LIST_ARGV + ["--kind", "dns"])

    captured = capsys.readouterr()
    assert "d1" in captured.out
    assert "h1" not in captured.out


def test_list_json_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    import json
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.return_value = [
        _summary(canarytoken="t-json", memo=f"{FOXGLOVE_TAG} hi"),
    ]

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(LIST_ARGV + ["--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["canarytoken"] == "t-json"
    assert data[0]["memo"] == f"{FOXGLOVE_TAG} hi"
    assert "created_printable" in data[0]


def test_list_api_error_returns_thinkst_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.list_tokens.side_effect = ThinkstApiError("server down")

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(LIST_ARGV)

    assert result == EXIT_THINKST_ERROR


REMOVE_ARGV = ["thinkst", "remove", "--console", "acme", "tok-x"]


def test_remove_missing_auth_token_returns_env_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("THINKST_API_KEY", raising=False)
    result = run(REMOVE_ARGV)
    assert result == EXIT_ENV_ERROR


def test_remove_happy_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.delete_token.return_value = None

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(REMOVE_ARGV)

    assert result == EXIT_SUCCESS
    mock_client.delete_token.assert_called_once_with(canarytoken="tok-x")
    captured = capsys.readouterr()
    assert "tok-x" in captured.out


def test_remove_incidents_blocked_user_confirms_yes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    mock_client = MagicMock()
    mock_client.delete_token.side_effect = [
        IncidentsBlockedError("token has unacknowledged incidents"),
        None,
    ]

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(REMOVE_ARGV)

    assert result == EXIT_SUCCESS
    assert mock_client.delete_token.call_count == 2
    second_call = mock_client.delete_token.call_args_list[1].kwargs
    assert second_call == {"canarytoken": "tok-x", "clear_incidents": True}


def test_remove_incidents_blocked_user_denies(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    mock_client = MagicMock()
    mock_client.delete_token.side_effect = IncidentsBlockedError("blocked")

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(REMOVE_ARGV)

    assert result == EXIT_THINKST_ERROR
    assert mock_client.delete_token.call_count == 1


def test_remove_other_api_error_returns_thinkst_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_API_KEY", "secret")
    mock_client = MagicMock()
    mock_client.delete_token.side_effect = ThinkstApiError("unknown id")

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(REMOVE_ARGV)

    assert result == EXIT_THINKST_ERROR
