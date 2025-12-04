from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant
from app.db.session import get_session
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=dict)
async def overview(tenant=Depends(get_tenant), session: AsyncSession = Depends(get_session)):
    stmt = select(func.coalesce(func.sum(Transaction.amount_usdc), 0)).where(
        Transaction.tenant_id == tenant.id,
        Transaction.type == TransactionType.DEPOSIT,
        Transaction.status == TransactionStatus.CONFIRMED,
    )
    points = (await session.execute(stmt)).scalar_one()

    wallets_stmt = select(func.count(func.distinct(Transaction.wallet_id))).where(Transaction.tenant_id == tenant.id)
    active_wallets = (await session.execute(wallets_stmt)).scalar_one()

    webhook_stmt = select(func.count(Transaction.id)).where(
        Transaction.tenant_id == tenant.id,
        Transaction.status == TransactionStatus.CONFIRMED,
    )
    webhooks = (await session.execute(webhook_stmt)).scalar_one()

    return {"points": float(points), "activeWallets": active_wallets, "webhooks": webhooks}


@router.get("/usage", response_model=list[dict])
async def usage(tenant=Depends(get_tenant), session: AsyncSession = Depends(get_session)):
    since = datetime.utcnow() - timedelta(days=7)
    stmt = (
        select(
            func.date_trunc("day", Transaction.created_at).label("day"),
            func.count(Transaction.id).label("hits"),
            func.sum(case((Transaction.status == TransactionStatus.FAILED, 1), else_=0)).label("failures"),
        )
        .where(Transaction.tenant_id == tenant.id, Transaction.created_at >= since)
        .group_by(func.date_trunc("day", Transaction.created_at))
        .order_by(func.date_trunc("day", Transaction.created_at))
    )
    rows = (await session.execute(stmt)).all()
    payload = []
    for day, hits, failures in rows:
        payload.append(
            {
                "day": day.date().isoformat(),
                "hits": hits,
                "successes": hits - failures,
                "failures": failures,
            }
        )
    return payload
