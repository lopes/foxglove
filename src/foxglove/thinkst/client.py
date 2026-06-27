from typing import cast

import httpx
from pydantic import ValidationError

from foxglove.thinkst.models import CreateTokenResult


class ThinkstApiError(Exception):
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
