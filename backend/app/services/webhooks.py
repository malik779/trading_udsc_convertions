import json
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import sign_payload, utcnow
from app.models.enums import TransactionStatus
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.webhook_delivery import WebhookDelivery


class WebhookService:
    def __init__(self, session: AsyncSession, tenant: Tenant):
        self.session = session
        self.tenant = tenant
        self.settings = get_settings()
        self.client = httpx.AsyncClient()

    async def send_transaction_update(self, transaction: Transaction, event_type: str) -> None:
        if not self.tenant.webhook_url:
            return

        payload = {
            "user_reference": transaction.wallet.user_reference if transaction.wallet else None,
            "network": transaction.network.value,
            "amount_usdc": str(transaction.amount_usdc),
            "tx_hash": transaction.tx_hash,
            "timestamp": transaction.updated_at.isoformat(),
            "event_type": event_type,
            "status": transaction.status.value,
        }
        delivery = WebhookDelivery(
            tenant_id=self.tenant.id,
            transaction_id=transaction.id,
            url=self.tenant.webhook_url,
            event_type=event_type,
            payload=payload,
            attempts=0,
        )
        self.session.add(delivery)
        await self.session.flush()
        delivery.attempts += 1

        status_code, error = await self._dispatch(self.tenant.webhook_url, payload)
        delivery.status_code = status_code
        if error:
            delivery.last_error = error
            delivery.next_retry_at = self._schedule_next_retry(delivery.attempts)
        else:
            delivery.last_error = None
            delivery.next_retry_at = None

    async def _dispatch(self, url: str, payload: dict[str, Any]) -> tuple[int | None, str | None]:
        body = json.dumps(payload)
        signature = sign_payload(self.tenant.webhook_secret, body.encode())
        headers = {
            "X-Signature": signature,
            "Content-Type": "application/json",
        }
        try:
            response = await self.client.post(url, content=body, headers=headers, timeout=10.0)
            return response.status_code, None if response.is_success else response.text
        except httpx.HTTPError as exc:
            return None, str(exc)

    def _schedule_next_retry(self, attempts: int):
        backoffs = self.settings.webhook_retry_backoff_seconds
        idx = min(attempts - 1, len(backoffs) - 1)
        return utcnow() + timedelta(seconds=backoffs[idx])

    async def retry_delivery(self, delivery: WebhookDelivery) -> None:
        target_url = delivery.url or self.tenant.webhook_url
        if not target_url:
            return
        delivery.attempts += 1
        status_code, error = await self._dispatch(target_url, delivery.payload)
        delivery.status_code = status_code
        if error:
            delivery.last_error = error
            delivery.next_retry_at = self._schedule_next_retry(delivery.attempts)
        else:
            delivery.last_error = None
            delivery.next_retry_at = None

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
