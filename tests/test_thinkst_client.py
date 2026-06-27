from collections.abc import Callable

import httpx
import pytest

from foxglove.thinkst.client import IncidentsBlockedError, ThinkstApiError, ThinkstClient
from foxglove.thinkst.models import CreateTokenResult, TokenSummary


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


def _list_response(tokens: list[dict[str, object]], next_cursor: object = None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "result": "success",
            "canarytokens": tokens,
            "cursor": {"next": next_cursor, "next_link": None, "prev": None, "prev_link": None},
        },
    )


def _summary_dict(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "canarytoken": "t-1",
        "kind": "dns",
        "flock_id": "flock:default",
        "memo": "#foxglove memo",
        "created_printable": "2026-06-27 12:00:00 (UTC)",
    }
    return {**base, **overrides}


def test_list_tokens_single_page():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/canarytokens/paginate"
        return _list_response([_summary_dict(canarytoken="t-1"), _summary_dict(canarytoken="t-2")])

    client = _client_with_handler(handler)
    tokens = client.list_tokens()

    assert len(tokens) == 2
    assert all(isinstance(t, TokenSummary) for t in tokens)
    assert tokens[0].canarytoken == "t-1"
    assert tokens[1].canarytoken == "t-2"


def test_list_tokens_follows_cursor():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return _list_response([_summary_dict(canarytoken="page1")], next_cursor="cursor-page2")
        if cursor == "cursor-page2":
            return _list_response([_summary_dict(canarytoken="page2")], next_cursor=None)
        raise AssertionError(f"unexpected cursor {cursor!r}")

    client = _client_with_handler(handler)
    tokens = client.list_tokens()

    assert len(calls) == 2
    assert [t.canarytoken for t in tokens] == ["page1", "page2"]


def test_list_tokens_passes_flock_id_query_param():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _list_response([])

    client = _client_with_handler(handler)
    client.list_tokens(flock_id="flock:specific")

    assert captured[0].url.params.get("flock_id") == "flock:specific"


def test_list_tokens_omits_flock_id_when_none():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _list_response([])

    client = _client_with_handler(handler)
    client.list_tokens()

    assert "flock_id" not in captured[0].url.params


def test_list_tokens_raises_on_error_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "error", "message": "bad auth"})

    client = _client_with_handler(handler)
    with pytest.raises(ThinkstApiError):
        client.list_tokens()


def test_delete_token_posts_to_correct_url():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"result": "success"})

    client = _client_with_handler(handler)
    client.delete_token(canarytoken="tok-1")

    assert len(captured) == 1
    req = captured[0]
    assert req.method == "POST"
    assert req.url.path == "/api/v1/canarytoken/delete"
    body = req.content.decode()
    assert "canarytoken=tok-1" in body
    assert "clear_incidents" not in body


def test_delete_token_with_clear_incidents():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"result": "success"})

    client = _client_with_handler(handler)
    client.delete_token(canarytoken="tok-1", clear_incidents=True)

    body = captured[0].content.decode()
    assert "clear_incidents=true" in body or "clear_incidents=True" in body


def test_delete_token_raises_incidents_blocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": "error",
                "message": "Cannot delete: token has unacknowledged incidents",
            },
        )

    client = _client_with_handler(handler)
    with pytest.raises(IncidentsBlockedError):
        client.delete_token(canarytoken="tok-1")


def test_delete_token_raises_other_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "error", "message": "unknown id"})

    client = _client_with_handler(handler)
    with pytest.raises(ThinkstApiError) as exc:
        client.delete_token(canarytoken="bogus")
    assert not isinstance(exc.value, IncidentsBlockedError)
