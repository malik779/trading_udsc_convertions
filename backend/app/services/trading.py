from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Network


@dataclass
class MarketQuote:
    network: Network
    bid: Decimal
    ask: Decimal


class TreasuryService:
    """Lightweight treasury helper to keep USDC float consistent across chains."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def rebalance(self, quotes: Iterable[MarketQuote]) -> dict[str, Decimal]:
        adjustments: dict[str, Decimal] = {}
        for quote in quotes:
            mid = (quote.bid + quote.ask) / 2
            adjustments[quote.network.value] = mid
        return adjustments
