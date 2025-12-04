from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key, hash_api_key
from app.db.session import get_session
from app.models.tenant import Tenant
from app.schemas.tenant import ApiKeyResponse, TenantCreate, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, session: AsyncSession = Depends(get_session)):
    existing_stmt = select(Tenant).where(Tenant.name == payload.name)
    if (await session.execute(existing_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="tenant already exists")

    api_key = generate_api_key()
    tenant = Tenant(
        name=payload.name,
        contact_email=payload.contact_email,
        plan=payload.plan,
        api_key_hash=hash_api_key(api_key),
        webhook_secret=generate_api_key(),
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)

    return ApiKeyResponse(tenant=tenant, api_key=api_key, webhook_secret=tenant.webhook_secret)


@router.get("", response_model=list[TenantRead])
async def list_tenants(session: AsyncSession = Depends(get_session)):
    stmt = select(Tenant)
    tenants = (await session.execute(stmt)).scalars().all()
    return tenants
