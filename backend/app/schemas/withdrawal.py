from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.enums import Network, TransactionStatus


class WithdrawalCreate(BaseModel):
    user_reference: str
    network: Network
    destination_address: str = Field(min_length=10, max_length=256)
    amount_usdc: Decimal = Field(gt=0)
    idempotency_key: str | None = Field(default=None, max_length=64)


class WithdrawalRead(BaseModel):
    id: int
    network: Network
    amount_usdc: Decimal
    status: TransactionStatus
    tx_hash: str | None

    class Config:
        from_attributes = True
