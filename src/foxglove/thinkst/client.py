from typing import cast

import httpx
from pydantic import ValidationError

from foxglove.thinkst.models import CreateTokenResult, TokenSummary

LIST_PAGE_LIMIT: int = 100


class ThinkstApiError(Exception):
    pass


class IncidentsBlockedError(ThinkstApiError):
    pass


class ThinkstClient:
    def __init__(
        self,
        *,
        console: str,
        auth_token: str,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=f"https://{console}.canary.tools",
            timeout=timeout,
            transport=transport,
            headers={"X-Canary-Auth-Token": auth_token},
        )

    def create_token(self, *, kind: str, memo: str, flock_id: str) -> CreateTokenResult:
        response = self._client.post(
            "/api/v1/canarytoken/create",
            data={"kind": kind, "memo": memo, "flock_id": flock_id},
        )
        payload = self._parse_payload(response)
        token = payload.get("canarytoken")
        if not isinstance(token, dict):
            raise ThinkstApiError("create response missing 'canarytoken' object")
        try:
            return CreateTokenResult.model_validate(token)
        except ValidationError as e:
            raise ThinkstApiError(f"create response shape invalid: {e}") from e

    def list_tokens(self, *, flock_id: str | None = None) -> list[TokenSummary]:
        results: list[TokenSummary] = []
        cursor: str | None = None
        while True:
            params: dict[str, str | int] = {"limit": LIST_PAGE_LIMIT}
            if flock_id is not None:
                params["flock_id"] = flock_id
            if cursor is not None:
                params["cursor"] = cursor

            response = self._client.get(
                "/api/v1/canarytokens/paginate",
                params=params,
            )
            payload = self._parse_payload(response)

            tokens_raw = payload.get("canarytokens") or payload.get("tokens") or []
            if not isinstance(tokens_raw, list):
                raise ThinkstApiError(
                    "paginate response missing 'canarytokens'/'tokens' array"
                )

            for raw in tokens_raw:
                try:
                    results.append(TokenSummary.model_validate(raw))
                except ValidationError:
                    continue

            cursor_obj = payload.get("cursor")
            if not isinstance(cursor_obj, dict):
                break
            next_cursor = cursor_obj.get("next")
            if not isinstance(next_cursor, str) or not next_cursor:
                break
            cursor = next_cursor

        return results

    def delete_token(self, *, canarytoken: str, clear_incidents: bool = False) -> None:
        data: dict[str, str] = {"canarytoken": canarytoken}
        if clear_incidents:
            data["clear_incidents"] = "true"
        response = self._client.post(
            "/api/v1/canarytoken/delete",
            data=data,
        )
        try:
            self._parse_payload(response)
        except ThinkstApiError as e:
            if "incident" in str(e).lower():
                raise IncidentsBlockedError(str(e)) from e
            raise

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ThinkstClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _parse_payload(response: httpx.Response) -> dict[str, object]:
        try:
            payload = response.json()
        except ValueError as e:
            raise ThinkstApiError(
                f"non-JSON response (HTTP {response.status_code})"
            ) from e
        if not isinstance(payload, dict):
            raise ThinkstApiError(
                f"expected JSON object, got {type(payload).__name__}"
            )
        body = cast(dict[str, object], payload)
        if response.status_code >= 400:
            message = body.get("message") or f"HTTP {response.status_code}"
            raise ThinkstApiError(str(message))
        if body.get("result") != "success":
            message = body.get("message") or "unknown error"
            raise ThinkstApiError(str(message))
        return body
