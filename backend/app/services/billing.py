from __future__ import annotations

from dataclasses import dataclass

import stripe
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.tenant import Tenant


@dataclass(frozen=True)
class PlanTier:
    id: str
    name: str
    monthly_price: int
    quota: int
    chains: int
    price_id: str


class BillingService:
    def __init__(self, tenant: Tenant | None = None) -> None:
        self.settings = get_settings()
        self.tenant = tenant
        self._plans = self._build_plan_matrix()
        if self.settings.stripe_api_key:
            stripe.api_key = self.settings.stripe_api_key

    def plans(self) -> list[PlanTier]:
        return list(self._plans.values())

    def create_checkout_session(self, plan_id: str, success_url: str, cancel_url: str) -> str:
        if not self.tenant:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant context required")
        self._require_stripe()
        plan = self._plan(plan_id)
        customer_id = self.tenant.stripe_customer_id or self._create_customer()
        metadata = {"plan_id": plan.id, "tenant_id": str(self.tenant.id)}
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": plan.price_id, "quantity": 1}],
            customer=customer_id,
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"metadata": metadata},
            metadata=metadata,
        )
        url = session.get("url")
        if not url:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="stripe session missing url")
        return url

    def apply_plan(self, plan_id: str, subscription_id: str | None = None) -> None:
        if not self.tenant:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant context required")
        plan = self._plan(plan_id)
        self.tenant.plan = plan.id
        self.tenant.monthly_quota = plan.quota
        if subscription_id:
            self.tenant.stripe_subscription_id = subscription_id

    def _create_customer(self) -> str:
        self._require_stripe()
        customer = stripe.Customer.create(email=self.tenant.contact_email, name=self.tenant.name)
        self.tenant.stripe_customer_id = customer.get("id")
        return self.tenant.stripe_customer_id

    def _plan(self, plan_id: str) -> PlanTier:
        try:
            return self._plans[plan_id]
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found") from exc

    def _build_plan_matrix(self) -> dict[str, PlanTier]:
        mapping = {
            "starter": PlanTier("starter", "Starter", 199, 250_000, 3, self.settings.stripe_price_starter),
            "growth": PlanTier("growth", "Growth", 499, 1_000_000, 5, self.settings.stripe_price_growth),
            "enterprise": PlanTier("enterprise", "Enterprise", 1499, 10_000_000, 10, self.settings.stripe_price_enterprise),
        }
        return mapping

    def _require_stripe(self) -> None:
        if not self.settings.stripe_api_key:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="stripe api key missing")
        for plan in self._plans.values():
            if not plan.price_id:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"missing stripe price for {plan.id}")
