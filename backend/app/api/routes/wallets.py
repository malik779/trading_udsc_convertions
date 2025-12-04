from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant
from app.db.session import get_session
from app.models.enums import Network
from app.schemas.wallet import WalletAssignRequest, WalletRead
from app.services.wallets import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/assign", response_model=WalletRead)
async def assign_wallet(
    payload: WalletAssignRequest,
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session, tenant)
    wallet = await service.assign_address(payload.user_reference, payload.network)
    await session.commit()
    return wallet


@router.get("/{network}/{user_reference}", response_model=WalletRead)
async def get_wallet(
    network: Network,
    user_reference: str,
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session, tenant)
    wallet = await service.get_wallet(user_reference, network)
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")
    return wallet
