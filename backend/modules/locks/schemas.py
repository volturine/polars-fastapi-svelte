from pydantic import BaseModel, ConfigDict


class LockAcquireRequest(BaseModel):
    client_id: str
    client_signature: str


class LockHeartbeatRequest(BaseModel):
    client_id: str
    lock_token: str


class LockReleaseRequest(BaseModel):
    client_id: str
    lock_token: str


class LockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    client_id: str
    lock_token: str
    expires_at: str


class LockStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locked: bool
    locked_by_me: bool = False
    client_id: str | None = None
    expires_at: str | None = None
