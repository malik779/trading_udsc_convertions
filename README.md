# Crypto Payment SaaS (USDC multi-chain)

A subscription-based crypto payment gateway that exposes a tenant-isolated FastAPI backend (Python 3.11) and a multi-tenant Angular dashboard. The product focuses on institutional-grade USDC deposits/withdrawals across Ethereum (ERC-20), BNB Chain (BEP-20), and Solana (SPL) with webhook-driven settlement and internal point conversion (1 USDC = 1 point).

## Architecture Snapshot

- **Backend (`backend/`)**
  - FastAPI + SQLAlchemy async stack with PostgreSQL and Redis primitives, fully managed via Alembic migrations (`alembic/`).
  - Multi-tenant models (`Tenant`, `Wallet`, `Transaction`, `WebhookDelivery`, `TenantUsage`) enforce API-key auth, per-plan quotas, and signed webhook delivery retries.
  - Blockchain abstraction layer (`app/services/blockchain_provider.py`) targets **Fireblocks** with RSA-signed requests; adapters can swap in Moralis/Alchemy without touching business logic.
  - Celery workers (`app/workers/`) poll deposits across networks and replay failed webhooks using Redis as broker/result store.
  - Billing service integrates Stripe Checkout + webhooks to upgrade tenants and raise quotas automatically.
  - Treasury/trading helper (`services/trading.py`) prepared for future liquidity balancing (e.g., cross-exchange hedging, automated spreads).

- **Frontend (`frontend/`)**
  - Angular 17 dashboard with routing for Overview, API Logs, and Subscription management.
  - Multi-tenant experience: API key storage in browser, filterable transaction tables, usage analytics placeholders, and subscription checkout UI.

- **Security**
  - API key authentication on every call (`X-API-Key`) + optional `Idempotency-Key` header to dedupe requests.
  - Webhooks are HMAC signed per-tenant; provider callbacks also validate signatures.
  - No plaintext secrets logged; hashing for stored API keys.

## Why Fireblocks?
Fireblocks offers institutional custody, policy controls, and MPC wallets, making it the safest default for a multi-tenant SaaS that must segregate user balances while staying compliant. The provider router still exposes a clean interface so you can inject Moralis/Alchemy for event streaming if your cost model demands it.

## Key Backend Endpoints (prefix `/v1`)
| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/tenants` | Provision tenant + return API key & webhook secret |
| POST | `/wallets/assign` | Allocate deterministic deposit addresses per user/network |
| GET | `/transactions` | Filterable ledger (type, network, user, status, dates) |
| POST | `/transactions/withdrawals` | Create withdrawal with idempotency + provider broadcast |
| GET | `/metrics`, `/metrics/usage` | Dashboard stats + 7-day usage insights |
| GET | `/billing/plans` | Publish subscription tiers + quotas to the UI |
| POST | `/billing/checkout` | Create tenant-scoped Stripe checkout session |
| POST | `/billing/webhook` | Stripe event intake (checkout + invoice webhooks) |
| POST | `/webhooks/provider/deposit` | Receive blockchain provider deposit notices |
| POST | `/webhooks/tenant/withdrawal-callback` | Update withdrawal lifecycle events |

Each confirmed deposit triggers internal point minting and a signed webhook payload:
```deposit_confirmed payload
{
  "user_reference": "customer-123",
  "network": "ethereum",
  "amount_usdc": "250.00",
  "tx_hash": "0xabc...",
  "timestamp": "2025-12-04T12:30:00Z",
  "event_type": "deposit_confirmed",
  "status": "confirmed"
}
```

## Frontend Highlights
- Overview cards (points, active wallets, delivered webhooks) backed by `/metrics`.
- Filterable transaction + logs tables hitting `/transactions` with query params.
- Subscription screen pulls `/billing/plans` and launches tenant-authenticated Stripe checkout flows; Angular dev server proxies `/api` during local development.

## Trading & Value-Add Enhancements
- Treasury balancing service prepared for multi-network liquidity so you can automatically rebalance USDC inventory when one chain receives high inflows.
- Extendable metrics endpoints for SLA dashboards, success/failure hit ratios, and rate-limit audits.
- Ready spots to add quote APIs (e.g., `/v1/trading/quotes`) layering OTC pricing, spread controls, and automatic hedging.

## Getting Started

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```
Configure `.env` using `.env.example` (database, Redis, Fireblocks keys, Stripe prices).

### Frontend
```bash
cd frontend
npm install
npm run start
```
The Angular dev server (via `proxy.conf.json`) forwards `/api` to `http://localhost:8080`. Store the tenant API key in `localStorage.tenantApiKey` so the interceptor can forward it as `X-API-Key`.

### Workers
```bash
cd backend
celery -A app.workers.celery_app.celery_app worker -B --loglevel=info
```
Beat schedules two jobs:
- `poll_deposits`: hits the provider per network, logs deposits, and triggers signed tenant webhooks.
- `retry_webhooks`: replays failed deliveries according to the configured exponential backoff.

## Next Steps
1. Flesh out provider adapters for Moralis/Alchemy streams to reduce latency on Solana SPL events.
2. Build tenant-facing webhook delivery UI (replay button, filtering, status charts).
3. Add automated AML/compliance hooks (Travel Rule payloads, OFAC screening) into the deposit monitor.
4. Expand trading module with RFQ quoting + spread controls for instant conversions.
5. Harden Stripe flow with customer portal links + dunning emails for failed invoices.
