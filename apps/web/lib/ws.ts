"use client";

import { useEffect, useRef, useState } from "react";

import { runStreamUrl } from "./api";

export interface StreamEvent {
  type: string;
  ts?: string;
  run_id?: string;
  payload?: Record<string, unknown>;
  [k: string]: unknown;
}

export type StreamStatus = "connecting" | "open" | "closed" | "error";

/**
 * Subscribe to a run's WS event stream and accumulate events in state.
 * Auto-reconnects with backoff while the component is mounted.
 */
export function useRunStream(runId: string | undefined): {
  events: StreamEvent[];
  status: StreamStatus;
  clear: () => void;
} {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      setStatus("connecting");
      const ws = new WebSocket(runStreamUrl(runId));
      wsRef.current = ws;

      ws.onopen = () => {
        retryRef.current = 0;
        setStatus("open");
      };
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as StreamEvent;
          setEvents((prev) => [...prev, data]);
        } catch {
          // ignore non-JSON frames
        }
      };
      ws.onerror = () => setStatus("error");
      ws.onclose = () => {
        setStatus("closed");
        if (cancelled) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 8000);
        retryRef.current += 1;
        window.setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      cancelled = true;
      wsRef.current?.close();
    };
  }, [runId]);

  return { events, status, clear: () => setEvents([]) };
}
