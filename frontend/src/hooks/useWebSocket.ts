import { useState, useEffect, useRef, useCallback } from 'react';
import type { ConnectionEvent } from '../services/api';

type WsStatus = 'connected' | 'connecting' | 'disconnected';

export function useWebSocket(active: boolean) {
  const [wsStatus, setWsStatus] = useState<WsStatus>('disconnected');
  const [lastEvent, setLastEvent] = useState<ConnectionEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (!active) return;
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws/live`;
    setWsStatus('connecting');

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus('connected');
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = undefined;
      }
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'event' && msg.payload) {
          setLastEvent(msg.payload);
        }
        if (msg.type === 'heartbeat_update') {
          setLastEvent({ kind: 'heartbeat_update', ...msg } as ConnectionEvent);
        }
      } catch { /* ignore parse errors */ }
    };

    ws.onclose = () => {
      setWsStatus('disconnected');
      wsRef.current = null;
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [active]);

  useEffect(() => {
    if (active) {
      connect();
    } else {
      wsRef.current?.close();
      wsRef.current = null;
      setWsStatus('disconnected');
    }
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [active, connect]);

  return { wsStatus, lastEvent };
}
