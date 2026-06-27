from collections.abc import Callable

import httpx
import pytest

from foxglove.thinkst.client import ThinkstApiError, ThinkstClient
from foxglove.thinkst.models import CreateTokenResult


def _client_with_handler(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    console: str = "acme",
    auth_token: str = "secret",
) -> ThinkstClient:
    return ThinkstClient(
        console=console,
        auth_token=auth_token,
        transport=httpx.MockTransport(handler),
    )


def _success_response(token_fields: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"result": "success", "canarytoken": token_fields},
    )


def test_create_token_posts_to_correct_url():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _success_response({
            "canarytoken": "tok-1",
            "kind": "dns",
            "flock_id": "flock:default",
            "memo": "test",
            "hostname": "abc.canarytokens.com",
        })

    client = _client_with_handler(handler, console="acme")
    client.create_token(kind="dns", memo="test", flock_id="flock:default")

    assert len(captured) == 1
    req = captured[0]
    assert str(req.url) == "https://acme.canary.tools/api/v1/canarytoken/create"
    assert req.method == "POST"


def test_create_token_sends_auth_header():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _success_response({
            "canarytoken": "tok-1",
            "kind": "dns",
            "flock_id": "flock:default",
            "memo": "test",
            "hostname": "abc.canarytokens.com",
        })

    client = _client_with_handler(handler, auth_token="my-secret-token")
    client.create_token(kind="dns", memo="test", flock_id="flock:default")

    assert captured[0].headers["X-Canary-Auth-Token"] == "my-secret-token"


def test_create_token_sends_form_body():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _success_response({
            "canarytoken": "tok-1",
            "kind": "dns",
            "flock_id": "flock:default",
            "memo": "the memo",
            "hostname": "abc.canarytokens.com",
        })

    client = _client_with_handler(handler)
    client.create_token(kind="dns", memo="the memo", flock_id="flock:default")

    body = captured[0].content.decode()
    assert "kind=dns" in body
    assert "flock_id=flock%3Adefault" in body
    assert "memo=the+memo" in body or "memo=the%20memo" in body


def test_create_token_returns_parsed_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return _success_response({
            "canarytoken": "tok-42",
            "kind": "dns",
            "flock_id": "flock:default",
            "memo": "hi",
            "hostname": "abc.canarytokens.com",
        })

    client = _client_with_handler(handler)
    result = client.create_token(kind="dns", memo="hi", flock_id="flock:default")

    assert isinstance(result, CreateTokenResult)
    assert result.canarytoken == "tok-42"
    assert result.kind == "dns"
    assert result.flock_id == "flock:default"
    assert result.memo == "hi"
    assert result.hostname == "abc.canarytokens.com"
    assert result.url is None


def test_create_token_parses_url_field_for_http_kind():
    def handler(request: httpx.Request) -> httpx.Response:
        return _success_response({
            "canarytoken": "tok-99",
            "kind": "http",
            "flock_id": "flock:default",
            "memo": "web bug",
            "url": "https://abc.canarytokens.com/tok99.gif",
        })

    client = _client_with_handler(handler)
    result = client.create_token(kind="http", memo="web bug", flock_id="flock:default")

    assert result.url == "https://abc.canarytokens.com/tok99.gif"
    assert result.hostname is None


def test_create_token_raises_on_error_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"result": "error", "message": "invalid kind"},
        )

    client = _client_with_handler(handler)
    with pytest.raises(ThinkstApiError, match="invalid kind"):
        client.create_token(kind="dns", memo="m", flock_id="flock:default")


def test_create_token_raises_on_http_4xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"result": "error", "message": "Unauthorized"})

    client = _client_with_handler(handler)
    with pytest.raises(ThinkstApiError):
        client.create_token(kind="dns", memo="m", flock_id="flock:default")
