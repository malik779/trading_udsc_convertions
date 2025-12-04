from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Network
from app.models.wallet import Wallet
from app.services.blockchain_provider import BlockchainTransfer, get_provider_router
from app.services.transactions import TransactionService
from app.services.webhooks import WebhookService


class DepositMonitor:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.provider = get_provider_router()

    async def run(self, network: Network) -> None:
        transfers = await self.provider.fetch_confirmed_deposits(network)
        for transfer in transfers:
            await self._process_transfer(transfer)

    async def _process_transfer(self, transfer: BlockchainTransfer) -> None:
        if not transfer.to_address:
            return
        wallet = await self._wallet_by_address(transfer.to_address)
        if not wallet:
            return

        tenant = wallet.tenant
        transaction_service = TransactionService(self.session, tenant)
        transaction = await transaction_service.log_deposit(
            wallet=wallet,
            amount=transfer.amount_usdc,
            tx_hash=transfer.tx_hash,
            from_address=transfer.from_address or "unknown",
            fee=transfer.fee_usdc,
            provider_metadata={"provider": "fireblocks", "tx_hash": transfer.tx_hash},
            idempotency_key=transfer.tx_hash,
        )
        webhook_service = WebhookService(self.session, tenant)
        await webhook_service.send_transaction_update(transaction, "deposit_confirmed")

    async def _wallet_by_address(self, address: str) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.address == address).options(selectinload(Wallet.tenant))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
