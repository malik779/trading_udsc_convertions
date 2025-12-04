from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Crypto Payment SaaS"
    api_v1_prefix: str = "/v1"
    admin_email: str = "ops@cryptoservice.io"

    database_url: str = "postgresql+asyncpg://crypto:changeme@localhost:5432/crypto"
    sqlalchemy_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_url: str = "redis://localhost:6379/2"

    fireblocks_api_key: str = ""
    fireblocks_private_key_path: str = ""
    moralis_api_key: str = ""
    alchemy_api_key: str = ""

    webhook_signing_secret_bytes: int = 32
    webhook_retry_backoff_seconds: List[int] = [60, 120, 300]

    auth_hmac_algo: str = "sha256"
    auth_token_ttl_minutes: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
