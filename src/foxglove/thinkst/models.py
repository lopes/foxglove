from pydantic import BaseModel


class CreateTokenResult(BaseModel):
    model_config = {"frozen": True, "extra": "ignore"}

    canarytoken: str
    kind: str
    flock_id: str
    memo: str
    url: str | None = None
    hostname: str | None = None
