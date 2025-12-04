from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.db.session import get_session
from app.models.tenant import Tenant


async def get_tenant(
    request: Request,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing api key")

    stmt = select(Tenant).where(Tenant.is_active.is_(True))
    result = await session.execute(stmt)
    tenants = result.scalars().all()
    for tenant in tenants:
        if verify_api_key(api_key, tenant.api_key_hash):
            request.state.tenant = tenant
            return tenant

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")


async def get_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    return idempotency_key
