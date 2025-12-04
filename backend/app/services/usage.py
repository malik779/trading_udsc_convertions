from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.tenant import Tenant
from app.models.tenant_usage import TenantUsage


class UsageService:
    def __init__(self, session: AsyncSession, tenant: Tenant):
        self.session = session
        self.tenant = tenant

    async def increment_or_raise(self) -> None:
        record = await self._get_or_create_current_month()
        if record.request_count >= self.tenant.monthly_quota:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="monthly quota exceeded")
        record.request_count += 1
        record.last_request_at = utcnow()
        await self.session.flush()
        await self.session.commit()

    async def _get_or_create_current_month(self) -> TenantUsage:
        month_start = self._month_start()
        stmt = select(TenantUsage).where(TenantUsage.tenant_id == self.tenant.id, TenantUsage.month_start == month_start)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            return record
        record = TenantUsage(tenant_id=self.tenant.id, month_start=month_start, request_count=0)
        self.session.add(record)
        await self.session.flush()
        return record

    def _month_start(self) -> date:
        today = utcnow().date()
        return today.replace(day=1)
