from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import Network, TransactionStatus, TransactionType


class Pagination(BaseModel):
    limit: int = Field(ge=1, le=200, default=50)
    cursor: str | None = None


class TransactionBase(BaseModel):
    type: TransactionType
    network: Network
    amount_usdc: Decimal = Field(gt=0)
    fee_usdc: Decimal | None = Field(default=None, ge=0)


class TransactionRead(TransactionBase):
    id: int
    status: TransactionStatus
    tx_hash: str | None
    user_reference: str | None
    from_address: str | None
    to_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True
