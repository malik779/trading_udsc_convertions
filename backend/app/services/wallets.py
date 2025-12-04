from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Network
from app.models.tenant import Tenant
from app.models.wallet import Wallet
from app.services.blockchain_provider import get_provider_router


class WalletService:
    def __init__(self, session: AsyncSession, tenant: Tenant):
        self.session = session
        self.tenant = tenant
        self.provider = get_provider_router()

    async def assign_address(self, user_reference: str, network: Network) -> Wallet:
        wallet = await self._get_wallet(user_reference, network)
        if wallet:
            return wallet

        provider_payload = await self.provider.generate_deposit_address(network, user_reference)
        wallet = Wallet(
            tenant_id=self.tenant.id,
            user_reference=user_reference,
            network=network,
            address=provider_payload.get("address"),
            provider_reference=provider_payload.get("id"),
        )
        self.session.add(wallet)
        await self.session.flush()
        return wallet

    async def _get_wallet(self, user_reference: str, network: Network) -> Wallet | None:
        stmt = select(Wallet).where(
            Wallet.tenant_id == self.tenant.id,
            Wallet.user_reference == user_reference,
            Wallet.network == network,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_wallet(self, user_reference: str, network: Network) -> Wallet | None:
        return await self._get_wallet(user_reference, network)
