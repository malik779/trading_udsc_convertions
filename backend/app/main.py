from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import billing, metrics, tenants, transactions, wallets, webhooks
from app.core.config import get_settings


settings = get_settings()


def get_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    api = FastAPI()
    app.include_router(tenants.router, prefix=settings.api_v1_prefix)
    app.include_router(wallets.router, prefix=settings.api_v1_prefix)
    app.include_router(transactions.router, prefix=settings.api_v1_prefix)
    app.include_router(metrics.router, prefix=settings.api_v1_prefix)
    app.include_router(billing.router, prefix=settings.api_v1_prefix)
    app.include_router(webhooks.router, prefix=settings.api_v1_prefix)

    return app


app = get_app()
