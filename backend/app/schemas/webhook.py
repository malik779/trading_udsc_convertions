from datetime import datetime
from pydantic import BaseModel


class WebhookDelivery(BaseModel):
    id: int
    url: str
    event_type: str
    payload: dict
    status_code: int | None
    attempts: int
    last_error: str | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepositEvent(BaseModel):
    tenant_id: int
    user_reference: str
    network: str
    amount_usdc: float
    tx_hash: str
    deposit_address: str
    from_address: str
    timestamp: datetime
    event_type: str = "deposit_confirmed"
