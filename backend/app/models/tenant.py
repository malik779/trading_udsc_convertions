from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.db.session import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)

    api_key_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    allowed_ips: Mapped[str | None] = mapped_column(String(512))

    plan: Mapped[str] = mapped_column(String(50), default="starter")
    webhook_url: Mapped[str | None] = mapped_column(String(512))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(120))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(120))
    monthly_quota: Mapped[int] = mapped_column(default=10000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    wallets: Mapped[list["Wallet"]] = relationship(back_populates="tenant")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="tenant")
    webhook_deliveries: Mapped[list["WebhookDelivery"]] = relationship(back_populates="tenant")
    usage_records: Mapped[list["TenantUsage"]] = relationship(back_populates="tenant")


class ApiKeyAudit(Base):
    __tablename__ = "api_key_audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column()
    last_two: Mapped[str] = mapped_column(String(4))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
