from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.api.deps import get_tenant
from app.core.config import get_settings
from app.db.session import get_session
from app.models.tenant import Tenant
from app.schemas.billing import CheckoutRequest, CheckoutResponse, PlanRead
from app.services.billing import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()


@router.get("/plans", response_model=list[PlanRead])
async def list_plans() -> list[PlanRead]:
    service = BillingService()
    return [
        PlanRead(id=plan.id, name=plan.name, monthly_price=plan.monthly_price, quota=plan.quota, chains=plan.chains)
        for plan in service.plans()
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    tenant=Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> CheckoutResponse:
    service = BillingService(tenant)
    checkout_url = service.create_checkout_session(payload.plan_id, str(payload.success_url), str(payload.cancel_url))
    await session.commit()
    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_session),
):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="webhook secret missing")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid stripe signature") from exc

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data_object, session)
    elif event_type == "invoice.payment_succeeded":
        await _handle_invoice_paid(data_object, session)

    return {"received": True}


async def _handle_checkout_completed(payload: dict, session: AsyncSession) -> None:
    customer_id = payload.get("customer")
    subscription_id = payload.get("subscription")
    plan_id = payload.get("metadata", {}).get("plan_id")
    if not (customer_id and plan_id):
        return
    tenant = await _tenant_by_customer(session, customer_id)
    if not tenant:
        return
    service = BillingService(tenant)
    service.apply_plan(plan_id, subscription_id)
    await session.commit()


async def _handle_invoice_paid(payload: dict, session: AsyncSession) -> None:
    subscription_id = payload.get("subscription")
    if not subscription_id:
        return
    stmt = select(Tenant).where(Tenant.stripe_subscription_id == subscription_id)
    result = await session.execute(stmt)
    tenant = result.scalar_one_or_none()
    if not tenant:
        return
    lines = payload.get("lines", {}).get("data", [])
    if not lines:
        return
    plan_obj = lines[0].get("plan") or {}
    plan_metadata = plan_obj.get("metadata", {})
    plan_id = plan_metadata.get("plan_id") or plan_obj.get("nickname")
    if not plan_id:
        return
    plan_id = plan_id.lower()
    service = BillingService(tenant)
    service.apply_plan(plan_id, subscription_id)
    await session.commit()


async def _tenant_by_customer(session: AsyncSession, customer_id: str) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.stripe_customer_id == customer_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
