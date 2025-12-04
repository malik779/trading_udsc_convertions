from pydantic import AnyUrl, BaseModel, Field


class PlanRead(BaseModel):
    id: str
    name: str
    monthly_price: int
    quota: int
    chains: int


class CheckoutRequest(BaseModel):
    plan_id: str = Field(..., description="Plan identifier, e.g. starter")
    success_url: AnyUrl
    cancel_url: AnyUrl


class CheckoutResponse(BaseModel):
    checkout_url: AnyUrl
