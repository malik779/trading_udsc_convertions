from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.enums import Network, TransactionStatus, TransactionType


@dataclass
class BlockchainTransfer:
    network: Network
    tx_hash: str
    amount_usdc: Decimal
    from_address: str
    to_address: str
    fee_usdc: Decimal | None = None


class BlockchainProvider(ABC):
    name: str

    @abstractmethod
    async def generate_deposit_address(self, network: Network, customer_ref: str) -> dict:
        ...

    @abstractmethod
    async def submit_withdrawal(self, network: Network, destination: str, amount: Decimal, idempotency_key: str | None) -> dict:
        ...


class FireblocksProvider(BlockchainProvider):
    name = "fireblocks"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = httpx.AsyncClient(base_url="https://api.fireblocks.io")

    @retry(wait=wait_exponential(multiplier=2, max=10), stop=stop_after_attempt(3))
    async def _post(self, path: str, payload: dict) -> dict:
        headers = {"X-API-Key": self.settings.fireblocks_api_key}
        response = await self.client.post(path, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

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


class ProviderRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        # Fireblocks chosen by default for institutional-grade custody
        self.provider: BlockchainProvider = FireblocksProvider()

    async def generate_deposit_address(self, network: Network, customer_ref: str) -> dict:
        return await self.provider.generate_deposit_address(network, customer_ref)

    async def submit_withdrawal(self, network: Network, destination: str, amount: Decimal, idempotency_key: str | None) -> dict:
        return await self.provider.submit_withdrawal(network, destination, amount, idempotency_key)


def get_provider_router() -> ProviderRouter:
    return ProviderRouter()
