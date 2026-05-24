"""WebSocket connection manager with room-based subscriptions.

Rooms represent resource types that clients can subscribe to:
  - "dashboard"       — live overview metrics, signals, run updates
  - "experiments"     — experiment status changes, new results
  - "browser"         — browser session state, action results
  - "intelligence"    — new signals, anomaly detections

Clients send a subscribe message: {"subscribe": "room_name"}
They can unsubscribe: {"unsubscribe": "room_name"}
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

log = logging.getLogger("helix.ws_manager")


class WebSocketManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._client_rooms: dict[WebSocket, set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and assign to default room."""
        await websocket.accept()
        self._add_to_room(websocket, "_all")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a client from all rooms."""
        rooms = self._client_rooms.pop(websocket, set())
        for room in rooms:
            self._rooms.get(room, set()).discard(websocket)

    def _add_to_room(self, websocket: WebSocket, room: str) -> None:
        self._rooms[room].add(websocket)
        self._client_rooms[websocket].add(room)

    def _remove_from_room(self, websocket: WebSocket, room: str) -> None:
        self._rooms.get(room, set()).discard(websocket)
        self._client_rooms.get(websocket, set()).discard(room)

    async def handle_message(self, websocket: WebSocket, raw: str) -> None:
        """Parse and handle a subscription message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        action = data.get("action")
        room = data.get("room", "")

        if action == "subscribe" and room:
            self._add_to_room(websocket, room)
            await websocket.send_json({"type": "subscribed", "room": room})
        elif action == "unsubscribe" and room:
            self._remove_from_room(websocket, room)
            await websocket.send_json({"type": "unsubscribed", "room": room})

    async def broadcast(self, room: str, event_type: str, data: dict[str, Any]) -> None:
        """Send an event to all clients in a room."""
        payload = json.dumps({"type": event_type, "data": data, "room": room})
        disconnected: set[WebSocket] = set()
        for client in self._rooms.get(room, set()):
            try:
                await client.send_text(payload)
            except Exception:
                disconnected.add(client)
        # Also broadcast to _all room
        for client in self._rooms.get("_all", set()):
            if client not in disconnected:
                try:
                    await client.send_text(payload)
                except Exception:
                    disconnected.add(client)
        for client in disconnected:
            self.disconnect(client)

    async def broadcast_to_all(self, event_type: str, data: dict[str, Any]) -> None:
        """Send an event to all connected clients regardless of room."""
        payload = json.dumps({"type": event_type, "data": data, "room": "_all"})
        disconnected: set[WebSocket] = set()
        for client in list(self._client_rooms.keys()):
            try:
                await client.send_text(payload)
            except Exception:
                disconnected.add(client)
        for client in disconnected:
            self.disconnect(client)


# Singleton
manager = WebSocketManager()
