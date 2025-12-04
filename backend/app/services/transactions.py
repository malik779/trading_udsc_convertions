from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.enums import Network, TransactionStatus, TransactionType
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.schemas.common import TransactionRead
from app.schemas.withdrawal import WithdrawalCreate
from app.services.blockchain_provider import get_provider_router


class TransactionService:
    def __init__(self, session: AsyncSession, tenant: Tenant):
        self.session = session
        self.tenant = tenant
        self.provider = get_provider_router()

    async def log_deposit(
        self,
        wallet: Wallet,
        amount: Decimal,
        tx_hash: str,
        from_address: str,
        fee: Decimal | None,
        provider_metadata: dict | None,
        idempotency_key: str | None,
    ) -> Transaction:
        existing = None
        if idempotency_key:
            existing = await self._by_idempotency(idempotency_key)
        if existing:
            return existing

        trx = Transaction(
            tenant_id=self.tenant.id,
            wallet_id=wallet.id,
            type=TransactionType.DEPOSIT,
            network=wallet.network,
            status=TransactionStatus.CONFIRMED,
            amount_usdc=amount,
            fee_usdc=fee,
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=wallet.address,
            provider_metadata=provider_metadata,
            idempotency_key=idempotency_key,
        )
        self.session.add(trx)
        await self.session.flush()
        return trx

    async def create_withdrawal(self, payload: WithdrawalCreate) -> Transaction:
        wallet = await self._wallet_for_user(payload.user_reference, payload.network)
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")

        trx = Transaction(
            tenant_id=self.tenant.id,
            wallet_id=wallet.id,
            type=TransactionType.WITHDRAWAL,
            network=payload.network,
            status=TransactionStatus.PENDING,
            amount_usdc=payload.amount_usdc,
            to_address=payload.destination_address,
            idempotency_key=payload.idempotency_key,
        )
        self.session.add(trx)
        await self.session.flush()

        provider_response = await self.provider.submit_withdrawal(
            payload.network,
            payload.destination_address,
            payload.amount_usdc,
            payload.idempotency_key,
        )
        trx.status = TransactionStatus.BROADCASTED
        trx.tx_hash = provider_response.get("txHash")
        trx.provider_metadata = provider_response
        trx.updated_at = utcnow()
        return trx

    async def _by_idempotency(self, key: str) -> Transaction | None:
        stmt = select(Transaction).where(
            Transaction.tenant_id == self.tenant.id,
            Transaction.idempotency_key == key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _wallet_for_user(self, user_reference: str, network: Network) -> Wallet | None:
        stmt = select(Wallet).where(
            Wallet.tenant_id == self.tenant.id,
            Wallet.user_reference == user_reference,
            Wallet.network == network,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
