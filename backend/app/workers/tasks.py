import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import utcnow
from app.db.session import AsyncSessionLocal
from app.models.enums import Network
from app.models.webhook_delivery import WebhookDelivery
from app.services.deposit_monitor import DepositMonitor
from app.services.webhooks import WebhookService
from app.workers.celery_app import celery_app

settings = get_settings()


@celery_app.task(name="app.workers.tasks.poll_deposits")
def poll_deposits() -> None:
    asyncio.run(_poll_deposits())


async def _poll_deposits() -> None:
    async with AsyncSessionLocal() as session:
        monitor = DepositMonitor(session)
        for network in Network:
            await monitor.run(network)
        await session.commit()


@celery_app.task(name="app.workers.tasks.retry_webhooks")
def retry_webhooks() -> None:
    asyncio.run(_retry_webhooks())


async def _retry_webhooks() -> None:
    now = utcnow()
    max_attempts = len(settings.webhook_retry_backoff_seconds) + 1
    async with AsyncSessionLocal() as session:
        stmt = (
            select(WebhookDelivery)
            .where(
                WebhookDelivery.last_error.isnot(None),
                WebhookDelivery.next_retry_at.isnot(None),
                WebhookDelivery.next_retry_at <= now,
                WebhookDelivery.attempts < max_attempts,
            )
            .options(selectinload(WebhookDelivery.tenant))
            .limit(100)
        )
        deliveries = (await session.execute(stmt)).scalars().all()
        for delivery in deliveries:
            service = WebhookService(session, delivery.tenant)
            await service.retry_delivery(delivery)
        await session.commit()
