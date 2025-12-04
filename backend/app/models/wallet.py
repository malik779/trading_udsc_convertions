from sqlalchemy import ForeignKey, String, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.db.session import Base
from app.models.enums import Network


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_reference", "network", name="uq_wallet_user_network"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))
    user_reference: Mapped[str] = mapped_column(String(120))
    network: Mapped[Network] = mapped_column()
    address: Mapped[str] = mapped_column(String(256))
    provider_reference: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="wallets")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="wallet")
