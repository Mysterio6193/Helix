"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type LiveStatus = "connecting" | "open" | "closed" | "error";

export interface LiveEvent {
  type: string;
  data?: Record<string, unknown>;
  room?: string;
}

const WS_URL =
  process.env.NEXT_PUBLIC_WS_BASE
    ? `${process.env.NEXT_PUBLIC_WS_BASE}/api/v1/ws/live`
    : "ws://localhost:8000/api/v1/ws/live";

/**
 * Subscribe to a WebSocket room and get live events.
 * Auto-reconnects with exponential backoff.
 */
export function useLiveRoom(room: string): {
  events: LiveEvent[];
  status: LiveStatus;
  lastEvent: LiveEvent | null;
} {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [status, setStatus] = useState<LiveStatus>("connecting");
  const [lastEvent, setLastEvent] = useState<LiveEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const roomRef = useRef(room);
  roomRef.current = room;

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      retryRef.current = 0;
      setStatus("open");
      // Subscribe to room
      ws.send(JSON.stringify({ action: "subscribe", room: roomRef.current }));
    };

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as LiveEvent;
        if (event.type === "heartbeat") return;
        if (event.type === "subscribed") return;
        setLastEvent(event);
        setEvents((prev) => [...prev.slice(-99), event]);
      } catch {
        // ignore
      }
    };

    ws.onerror = () => setStatus("error");
    ws.onclose = () => {
      setStatus("closed");
      const delay = Math.min(1000 * 2 ** retryRef.current, 8000);
      retryRef.current += 1;
      window.setTimeout(connect, delay);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { events, status, lastEvent };
}

/**
 * Get the latest event of a specific type from a room.
 */
export function useLiveEvent(room: string, eventType: string): LiveEvent | null {
  const { lastEvent } = useLiveRoom(room);
  if (lastEvent && lastEvent.type === eventType) {
    return lastEvent;
  }
  return null;
}
