from sqlalchemy import DateTime, ForeignKey, Numeric, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.db.session import Base
from app.models.enums import Network, TransactionStatus, TransactionType


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    wallet_id: Mapped[int | None] = mapped_column(ForeignKey("wallets.id"), nullable=True)

    type: Mapped[TransactionType] = mapped_column()
    network: Mapped[Network] = mapped_column()
    status: Mapped[TransactionStatus] = mapped_column(default=TransactionStatus.PENDING)

    amount_usdc: Mapped[Numeric] = mapped_column(Numeric(38, 6))
    fee_usdc: Mapped[Numeric | None] = mapped_column(Numeric(38, 6))

    tx_hash: Mapped[str | None] = mapped_column(String(256), index=True)
    from_address: Mapped[str | None] = mapped_column(String(256))
    to_address: Mapped[str | None] = mapped_column(String(256))

    provider_metadata: Mapped[dict | None] = mapped_column(JSON)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), index=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="transactions")
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
