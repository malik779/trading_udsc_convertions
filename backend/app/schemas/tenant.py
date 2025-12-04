from pydantic import AnyUrl, BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    contact_email: EmailStr
    plan: str = Field(default="starter")
    webhook_url: AnyUrl | None = None


class TenantRead(BaseModel):
    id: int
    name: str
    contact_email: EmailStr
    plan: str
    monthly_quota: int
    is_active: bool
    webhook_url: AnyUrl | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None

    class Config:
        from_attributes = True


class ApiKeyResponse(BaseModel):
    tenant: TenantRead
    api_key: str
    webhook_secret: str
