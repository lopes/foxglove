from unittest.mock import MagicMock, patch

import pytest

from foxglove.__main__ import run
from foxglove.models import EXIT_ENV_ERROR, EXIT_SUCCESS, EXIT_THINKST_ERROR
from foxglove.thinkst import FOXGLOVE_TAG
from foxglove.thinkst.client import ThinkstApiError
from foxglove.thinkst.models import CreateTokenResult


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
    monkeypatch.delenv("THINKST_AUTH_TOKEN", raising=False)
    result = run(CREATE_ARGV)
    assert result == EXIT_ENV_ERROR


def test_create_happy_path_returns_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_AUTH_TOKEN", "secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(CREATE_ARGV)

    assert result == EXIT_SUCCESS
    captured = capsys.readouterr()
    assert "tok-123" in captured.out
    assert "abc.canarytokens.com" in captured.out


def test_create_prefixes_memo_with_foxglove_tag(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_AUTH_TOKEN", "secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        run(CREATE_ARGV)

    call_kwargs = mock_client.create_token.call_args.kwargs
    assert call_kwargs["memo"] == f"{FOXGLOVE_TAG} Q3 billing report"
    assert call_kwargs["kind"] == "dns"
    assert call_kwargs["flock_id"] == "flock:default"


def test_create_passes_console_and_token_to_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THINKST_AUTH_TOKEN", "my-secret")
    mock_client = MagicMock()
    mock_client.create_token.return_value = _make_create_result()
    factory = MagicMock(return_value=mock_client)

    with patch("foxglove.thinkst.runner.ThinkstClient", factory):
        run(CREATE_ARGV)

    factory.assert_called_once_with(console="acme", auth_token="my-secret")


def test_create_prints_url_when_present(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("THINKST_AUTH_TOKEN", "secret")
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
    monkeypatch.setenv("THINKST_AUTH_TOKEN", "secret")
    mock_client = MagicMock()
    mock_client.create_token.side_effect = ThinkstApiError("Unauthorized")

    with patch("foxglove.thinkst.runner.ThinkstClient", return_value=mock_client):
        result = run(CREATE_ARGV)

    assert result == EXIT_THINKST_ERROR
