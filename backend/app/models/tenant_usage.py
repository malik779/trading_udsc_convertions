from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.db.session import Base


class TenantUsage(Base):
    __tablename__ = "tenant_usage"
    __table_args__ = (UniqueConstraint("tenant_id", "month_start", name="uq_tenant_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    month_start: Mapped[date] = mapped_column(Date())
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    last_request_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="usage_records")
