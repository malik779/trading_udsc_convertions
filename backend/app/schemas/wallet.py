from pydantic import BaseModel, Field

from app.models.enums import Network


class WalletAssignRequest(BaseModel):
    user_reference: str = Field(min_length=1, max_length=120)
    network: Network


class WalletRead(BaseModel):
    id: int
    user_reference: str
    network: Network
    address: str

    class Config:
        from_attributes = True
