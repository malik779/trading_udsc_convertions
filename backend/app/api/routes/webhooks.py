from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant
from app.core.security import validate_signature
from app.db.session import get_session
from app.models.enums import TransactionStatus
from app.models.tenant import Tenant
from app.models.wallet import Wallet
from app.schemas.webhook import DepositEvent
from app.services.transactions import TransactionService
from app.services.webhooks import WebhookService
from app.services.wallets import WalletService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/provider/deposit")
async def provider_deposit(
    request: Request,
    payload: DepositEvent,
    signature: str = Header(alias="X-Provider-Signature"),
    session: AsyncSession = Depends(get_session),
):
    # Provider signature validation would use provider-specific secret per network
    validate_signature("provider-shared-secret", await request.body(), signature)

    stmt = select(Wallet).where(
        Wallet.address == payload.deposit_address,
        Wallet.tenant_id == payload.tenant_id,
    )
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")

    tenant = await session.get(Tenant, wallet.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant missing")

    trx_service = TransactionService(session, tenant)
    transaction = await trx_service.log_deposit(
        wallet=wallet,
        amount=Decimal(str(payload.amount_usdc)),
        tx_hash=payload.tx_hash,
        from_address=payload.from_address,
        fee=Decimal(\"0\"),
        provider_metadata=payload.model_dump(),
        idempotency_key=payload.tx_hash,
    )

    webhook_service = WebhookService(session, tenant)
    await webhook_service.send_transaction_update(transaction, payload.event_type)
    await session.commit()
    return {"id": transaction.id, "status": transaction.status}


@router.post("/tenant/withdrawal-callback")
async def tenant_withdrawal_callback(
    payload: dict,
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
):
    service = WebhookService(session, tenant)
    trx = await service.handle_provider_event(payload)
    await session.commit()
    return {"id": trx.id, "status": trx.status}
