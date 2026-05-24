"""WebSocket endpoint for real-time updates with room-based subscriptions."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from helix.services.ws_manager import manager

log = logging.getLogger("helix.ws")

router = APIRouter()


@router.websocket("/ws/live")
async def live_websocket(websocket: WebSocket):
    """Real-time updates WebSocket with room subscriptions.

    Clients send:
      {"action": "subscribe",   "room": "experiments"}
      {"action": "unsubscribe", "room": "experiments"}

    Available rooms: dashboard, experiments, browser, intelligence
    """
    await manager.connect(websocket)

    try:
        while True:
            # Wait for messages with a heartbeat timeout
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(), timeout=30.0
                )
                await manager.handle_message(websocket, raw)
            except TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("ws_error")
    finally:
        manager.disconnect(websocket)
