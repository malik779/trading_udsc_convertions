from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant
from app.db.session import get_session
from app.models.enums import Network, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.common import TransactionRead
from app.schemas.withdrawal import WithdrawalCreate, WithdrawalRead
from app.services.transactions import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
    type: TransactionType | None = Query(default=None),
    network: Network | None = Query(default=None),
    status: TransactionStatus | None = Query(default=None),
    user_reference: str | None = Query(default=None),
    start_date: Annotated[datetime | None, Query(alias="start")] = None,
    end_date: Annotated[datetime | None, Query(alias="end")] = None,
):
    stmt = select(Transaction).where(Transaction.tenant_id == tenant.id)
    if type:
        stmt = stmt.where(Transaction.type == type)
    if network:
        stmt = stmt.where(Transaction.network == network)
    if status:
        stmt = stmt.where(Transaction.status == status)
    if user_reference:
        stmt = stmt.where(Transaction.wallet.has(user_reference=user_reference))
    if start_date:
        stmt = stmt.where(Transaction.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.created_at <= end_date)

    rows = (await session.execute(stmt.order_by(Transaction.created_at.desc()))).scalars().all()
    return rows


@router.post("/withdrawals", response_model=WithdrawalRead)
async def create_withdrawal(
    payload: WithdrawalCreate,
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
):
    service = TransactionService(session, tenant)
    trx = await service.create_withdrawal(payload)
    await session.commit()
    return trx
