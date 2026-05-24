"""Event Webhook System — Outbound webhooks with signatures, retries, delivery tracking.

Features:
- HMAC-SHA256 signature verification
- Exponential backoff retries
- Delivery logging
- Event filtering
- Webhook health monitoring
- Circuit breaker pattern for failing endpoints
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.core.redis import get_redis

log = get_logger("helix.webhooks")
settings = get_settings()


@dataclass
class WebhookEndpoint:
    """A configured webhook endpoint."""
    id: str
    url: str
    secret: str
    events: list[str]  # e.g., ["experiment.completed", "run.finished"]
    active: bool = True
    retry_count: int = 3
    timeout: int = 30
    headers: dict[str, str] | None = None
    created_at: float = 0.0


class WebhookDeliverer:
    """Deliver events to webhook endpoints."""

    def __init__(self) -> None:
        self._redis_prefix = "helix:webhook:"

    def _signature(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def deliver(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Deliver an event to a webhook endpoint."""
        if not endpoint.active:
            return {"success": False, "error": "Endpoint inactive"}

        # Check circuit breaker
        if await self._is_circuit_open(endpoint.id):
            return {"success": False, "error": "Circuit breaker open"}

        # Build payload
        delivery = {
            "event_id": f"evt_{int(time.time() * 1000)}_{hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:8]}",
            "event_type": event_type,
            "timestamp": time.time(),
            "data": payload,
        }
        body = json.dumps(delivery, default=str)

        # Sign payload
        signature = self._signature(body, endpoint.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": endpoint.id,
            "User-Agent": "Helix-Webhook/1.0",
        }
        if endpoint.headers:
            headers.update(endpoint.headers)

        # Attempt delivery with retries
        last_error = None
        for attempt in range(endpoint.retry_count):
            try:
                async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                    resp = await client.post(endpoint.url, headers=headers, content=body)

                if resp.status_code < 500:
                    # Success or client error (don't retry 4xx)
                    success = 200 <= resp.status_code < 300
                    await self._record_delivery(endpoint.id, delivery["event_id"], success, resp.status_code)

                    if success:
                        await self._close_circuit(endpoint.id)
                        return {
                            "success": True,
                            "event_id": delivery["event_id"],
                            "status_code": resp.status_code,
                            "attempts": attempt + 1,
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                            "event_id": delivery["event_id"],
                        }

                last_error = f"HTTP {resp.status_code}"

            except Exception as exc:
                last_error = str(exc)

            if attempt < endpoint.retry_count - 1:
                delay = 2 ** attempt  # Exponential backoff
                log.warning("webhook_retry", endpoint=endpoint.id, attempt=attempt + 1, delay=delay)
                await asyncio.sleep(delay)

        # All retries exhausted
        await self._record_delivery(endpoint.id, delivery["event_id"], False, 0, last_error)
        await self._trip_circuit(endpoint.id)

        return {
            "success": False,
            "error": f"Failed after {endpoint.retry_count} attempts: {last_error}",
            "event_id": delivery["event_id"],
        }

    async def broadcast(
        self,
        event_type: str,
        payload: dict[str, Any],
        endpoints: list[WebhookEndpoint],
    ) -> list[dict[str, Any]]:
        """Broadcast an event to multiple endpoints."""
        import asyncio

        filtered = [
            ep for ep in endpoints
            if ep.active and (not ep.events or event_type in ep.events or "*" in ep.events)
        ]

        tasks = [self.deliver(ep, event_type, payload) for ep in filtered]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if isinstance(r, dict) else {"success": False, "error": str(r)}
            for r in results
        ]

    async def _is_circuit_open(self, endpoint_id: str) -> bool:
        """Check if circuit breaker is open for an endpoint."""
        try:
            redis = get_redis()
            key = f"{self._redis_prefix}circuit:{endpoint_id}"
            value = await redis.get(key)
            if value:
                return int(value) > time.time()
        except Exception:
            pass
        return False

    async def _trip_circuit(self, endpoint_id: str) -> None:
        """Open circuit breaker for 5 minutes."""
        try:
            redis = get_redis()
            key = f"{self._redis_prefix}circuit:{endpoint_id}"
            await redis.setex(key, 300, str(int(time.time()) + 300))
            log.warning("webhook_circuit_tripped", endpoint=endpoint_id)
        except Exception:
            pass

    async def _close_circuit(self, endpoint_id: str) -> None:
        """Close circuit breaker."""
        try:
            redis = get_redis()
            key = f"{self._redis_prefix}circuit:{endpoint_id}"
            await redis.delete(key)
        except Exception:
            pass

    async def _record_delivery(
        self,
        endpoint_id: str,
        event_id: str,
        success: bool,
        status_code: int,
        error: str | None = None,
    ) -> None:
        """Record delivery attempt for monitoring."""
        try:
            redis = get_redis()
            key = f"{self._redis_prefix}deliveries:{endpoint_id}"
            delivery = {
                "event_id": event_id,
                "success": success,
                "status_code": status_code,
                "error": error,
                "timestamp": time.time(),
            }
            await redis.lpush(key, json.dumps(delivery))
            await redis.ltrim(key, 0, 999)  # Keep last 1000
        except Exception:
            pass

    async def get_delivery_stats(self, endpoint_id: str) -> dict[str, Any]:
        """Get delivery statistics for an endpoint."""
        try:
            redis = get_redis()
            key = f"{self._redis_prefix}deliveries:{endpoint_id}"
            deliveries_raw = await redis.lrange(key, 0, -1)

            deliveries = [json.loads(d) for d in deliveries_raw]
            total = len(deliveries)
            successful = sum(1 for d in deliveries if d["success"])

            return {
                "total": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": round(successful / total, 4) if total > 0 else 0,
                "recent": deliveries[:10],
            }
        except Exception as exc:
            return {"error": str(exc)}


class WebhookManager:
    """Manage webhook endpoints."""

    def __init__(self) -> None:
        self._redis_key = "helix:webhooks:endpoints"
        self.deliverer = WebhookDeliverer()

    async def register(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """Register a new webhook endpoint."""
        redis = get_redis()
        endpoint.created_at = time.time()
        await redis.hset(self._redis_key, endpoint.id, json.dumps(endpoint.__dict__))
        log.info("webhook_registered", endpoint_id=endpoint.id, url=endpoint.url)
        return endpoint

    async def unregister(self, endpoint_id: str) -> bool:
        """Remove a webhook endpoint."""
        redis = get_redis()
        result = await redis.hdel(self._redis_key, endpoint_id)
        return result > 0

    async def list_endpoints(self) -> list[WebhookEndpoint]:
        """List all registered endpoints."""
        redis = get_redis()
        data = await redis.hgetall(self._redis_key)
        endpoints = []
        for ep_data in data.values():
            if isinstance(ep_data, bytes):
                ep_data = ep_data.decode()
            ep_dict = json.loads(ep_data)
            endpoints.append(WebhookEndpoint(**ep_dict))
        return endpoints

    async def get_endpoint(self, endpoint_id: str) -> WebhookEndpoint | None:
        """Get a specific endpoint."""
        redis = get_redis()
        data = await redis.hget(self._redis_key, endpoint_id)
        if data:
            if isinstance(data, bytes):
                data = data.decode()
            return WebhookEndpoint(**json.loads(data))
        return None

    async def trigger_event(self, event_type: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Trigger an event to all matching endpoints."""
        endpoints = await self.list_endpoints()
        return await self.deliverer.broadcast(event_type, payload, endpoints)


# Global instance
_manager: WebhookManager | None = None


def get_webhook_manager() -> WebhookManager:
    global _manager
    if _manager is None:
        _manager = WebhookManager()
    return _manager
