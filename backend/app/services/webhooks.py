import json
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import sign_payload
from app.models.enums import TransactionStatus
from app.models.tenant import Tenant
from app.models.transaction import Transaction


class WebhookService:
    def __init__(self, session: AsyncSession, tenant: Tenant):
        self.session = session
        self.tenant = tenant
        self.settings = get_settings()
        self.client = httpx.AsyncClient()

    async def send_transaction_update(self, transaction: Transaction, event_type: str) -> None:
        payload = {
            "user_reference": transaction.wallet.user_reference if transaction.wallet else None,
            "network": transaction.network.value,
            "amount_usdc": str(transaction.amount_usdc),
            "tx_hash": transaction.tx_hash,
            "timestamp": transaction.updated_at.isoformat(),
            "event_type": event_type,
            "status": transaction.status.value,
        }
        await self._dispatch(payload)

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload)
        signature = sign_payload(self.tenant.webhook_secret, body.encode())
        headers = {
            "X-Signature": signature,
            "Content-Type": "application/json",
        }
        # TODO: fetch webhook URLs per tenant; single URL to keep example concise
        webhook_url = "https://tenant.app/webhooks/crypto"
        await self.client.post(webhook_url, content=body, headers=headers)

    async def handle_provider_event(self, provider_payload: dict[str, Any]) -> Transaction:
        tx_hash = provider_payload["tx_hash"]
        stmt = select(Transaction).where(Transaction.tx_hash == tx_hash)
        result = await self.session.execute(stmt)
        transaction = result.scalar_one_or_none()
        if not transaction:
            raise ValueError("unknown transaction")

        status_map = {
            "pending": TransactionStatus.PENDING,
            "broadcasted": TransactionStatus.BROADCASTED,
            "confirmed": TransactionStatus.CONFIRMED,
            "failed": TransactionStatus.FAILED,
        }
        new_status = status_map.get(provider_payload["status"].lower())
        if new_status and new_status != transaction.status:
            transaction.status = new_status
            transaction.tx_hash = provider_payload.get("tx_hash", transaction.tx_hash)
            await self.send_transaction_update(transaction, f"withdrawal_{new_status.value}")
        return transaction
