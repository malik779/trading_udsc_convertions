from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx
from jose import jwt

from app.core.config import get_settings


class FireblocksClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.fireblocks_api_key:
            raise RuntimeError("fireblocks api key missing; set FIREBLOCKS_API_KEY")
        if not self.settings.fireblocks_private_key_path:
            raise RuntimeError("fireblocks private key path missing")

        key_path = Path(self.settings.fireblocks_private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(f"Fireblocks private key not found at {key_path}")
        self._private_key = key_path.read_text().strip()

        self._client = httpx.AsyncClient(base_url=self.settings.fireblocks_api_base, timeout=20.0)

    async def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json_payload=payload)

    async def _request(self, method: str, path: str, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self._build_jwt(method, path, json_payload)
        headers = {
            "X-API-Key": self.settings.fireblocks_api_key,
            "Authorization": f"Bearer {token}",
        }
        response = await self._client.request(method, path, json=json_payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def _build_jwt(self, method: str, path: str, payload: dict[str, Any] | None) -> str:
        nonce = int(time.time() * 1000)
        body_hash = None
        if payload is not None:
            serialized = json.dumps(payload, separators=(",", ":"))
            body_hash = hashlib.sha256(serialized.encode()).hexdigest()

        jwt_body: dict[str, Any] = {
            "uri": path,
            "nonce": nonce,
            "method": method,
        }
        if body_hash:
            jwt_body["bodyHash"] = body_hash

        token = jwt.encode(jwt_body, self._private_key, algorithm="RS256", headers={"kid": self.settings.fireblocks_api_key})
        return token
