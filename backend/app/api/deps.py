from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_api_key
from app.db.session import get_session
from app.models.tenant import Tenant
from app.services.usage import UsageService


async def get_tenant(
    request: Request,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing api key")

    stmt = select(Tenant).where(
        Tenant.api_key_hash == hash_api_key(api_key),
        Tenant.is_active.is_(True),
    )
    result = await session.execute(stmt)
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")

    request.state.tenant = tenant
    usage = UsageService(session, tenant)
    await usage.increment_or_raise()
    return tenant


async def get_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    return idempotency_key
