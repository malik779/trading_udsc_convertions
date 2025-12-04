# Crypto Payment SaaS (USDC multi-chain)

A subscription-based crypto payment gateway that exposes a tenant-isolated FastAPI backend (Python 3.11) and a multi-tenant Angular dashboard. The product focuses on institutional-grade USDC deposits/withdrawals across Ethereum (ERC-20), BNB Chain (BEP-20), and Solana (SPL) with webhook-driven settlement and internal point conversion (1 USDC = 1 point).

## Architecture Snapshot

- **Backend (`backend/`)**
  - FastAPI + SQLAlchemy async stack with PostgreSQL and Redis primitives.
  - Multi-tenant models (`Tenant`, `Wallet`, `Transaction`) enforce per-tenant quotas and API authentication.
  - Blockchain abstraction layer (`app/services/blockchain_provider.py`) currently routes to **Fireblocks** for custody-grade address generation and withdrawals. Swappable adapters let you plug Moralis or Alchemy if needed.
  - Event + webhook services manage signed callbacks to tenant platforms with idempotent processing and retry-ready payloads.
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
- Subscription screen for monetization (hook up Stripe/Braintree later) to enforce plan-specific quotas stored on the tenant model.

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
uvicorn app.main:app --reload
```
Configure `.env` with `DATABASE_URL`, `FIREBLOCKS_API_KEY`, etc. Run Alembic migrations (not included yet) to create tables.

### Frontend
```bash
cd frontend
npm install
npm run start
```
The Angular dev server proxies to the FastAPI backend (configure `/api` proxy as needed) and requires you to paste the tenant API key into `localStorage.tenantApiKey` for authenticated calls.

## Next Steps
1. Wire Redis/Celery workers for asynchronous deposit polling + webhook retries.
2. Add Alembic migrations + seed scripts for tenants and plans.
3. Integrate Stripe Billing for plan subscriptions and hook usage counters into rate-limit middleware.
4. Build real blockchain provider adapters (Fireblocks withdrawal signing, Moralis/Alchemy streaming for Solana SPL events).
5. Harden webhook delivery logs + admin UI for replaying failed events.
