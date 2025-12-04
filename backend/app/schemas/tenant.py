from pydantic import BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    contact_email: EmailStr
    plan: str = Field(default="starter")


class TenantRead(BaseModel):
    id: int
    name: str
    contact_email: EmailStr
    plan: str
    monthly_quota: int
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyResponse(BaseModel):
    tenant: TenantRead
    api_key: str
    webhook_secret: str
