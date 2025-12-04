from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.enums import Network, TransactionStatus, TransactionType
from app.providers.fireblocks import FireblocksClient


@dataclass
class BlockchainTransfer:
    network: Network
    tx_hash: str
    amount_usdc: Decimal
    from_address: str | None
    to_address: str | None
    fee_usdc: Decimal | None = None


class BlockchainProvider(ABC):
    name: str

    @abstractmethod
    async def generate_deposit_address(self, network: Network, customer_ref: str) -> dict:
        ...

    @abstractmethod
    async def submit_withdrawal(self, network: Network, destination: str, amount: Decimal, idempotency_key: str | None) -> dict:
        ...

    @abstractmethod
    async def fetch_confirmed_deposits(self, network: Network) -> list[BlockchainTransfer]:
        ...


class FireblocksProvider(BlockchainProvider):
    name = "fireblocks"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = FireblocksClient()

    @retry(wait=wait_exponential(multiplier=2, max=10), stop=stop_after_attempt(3))
    async def _post(self, path: str, payload: dict) -> dict:
        return await self.client.post(path, payload)

    async def generate_deposit_address(self, network: Network, customer_ref: str) -> dict:
        payload = {"network": network.value, "customerRefId": customer_ref}
        return await self._post("/v1/addresses", payload)

    async def submit_withdrawal(self, network: Network, destination: str, amount: Decimal, idempotency_key: str | None) -> dict:
        payload = {
            "network": network.value,
            "destination": destination,
            "amount": str(amount),
            "assetId": "USDC",
        }
        if idempotency_key:
            payload["idempotencyKey"] = idempotency_key
        return await self._post("/v1/withdrawals", payload)

    async def fetch_confirmed_deposits(self, network: Network) -> list[BlockchainTransfer]:
        payload = {
            "network": network.value,
            "assetId": "USDC",
            "status": "confirmed",
        }
        response = await self._post("/v1/deposits/query", payload)
        transfers: list[BlockchainTransfer] = []
        for entry in response.get("data", []):
            transfers.append(
                BlockchainTransfer(
                    network=network,
                    tx_hash=entry["txHash"],
                    amount_usdc=Decimal(entry["amount"]),
                    from_address=entry.get("fromAddress") or entry.get("from"),
                    to_address=entry.get("destinationAddress") or entry.get("address"),
                    fee_usdc=Decimal(entry.get("fee", "0") or "0"),
                )
            )
        return transfers


class ProviderRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        # Fireblocks chosen by default for institutional-grade custody
        self.provider: BlockchainProvider = FireblocksProvider()

    async def generate_deposit_address(self, network: Network, customer_ref: str) -> dict:
        return await self.provider.generate_deposit_address(network, customer_ref)

    async def submit_withdrawal(self, network: Network, destination: str, amount: Decimal, idempotency_key: str | None) -> dict:
        return await self.provider.submit_withdrawal(network, destination, amount, idempotency_key)

    async def fetch_confirmed_deposits(self, network: Network) -> list[BlockchainTransfer]:
        return await self.provider.fetch_confirmed_deposits(network)


def get_provider_router() -> ProviderRouter:
    return ProviderRouter()
