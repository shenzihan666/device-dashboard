import { useState, useEffect, useCallback } from 'react';
import { getState, getEvents, type StateSnapshot, type ConnectionEvent } from '../services/api';

export function useGraphState(appMode: 'live' | 'replay') {
  const [snapshot, setSnapshot] = useState<StateSnapshot>({ servers: [], hosts: [], devices: [], edges: [], brain_servers: [], wecom_clients: [], heartbeat_edges: [] });
  const [events, setEvents] = useState<ConnectionEvent[]>([]);

  const refreshState = useCallback(async () => {
    try {
      const state = await getState();
      setSnapshot(state);
    } catch (e) {
      console.warn('State refresh failed:', e);
    }
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      const evts = await getEvents({ limit: 200 });
      setEvents(evts);
    } catch (e) {
      console.warn('Events load failed:', e);
    }
  }, []);

  const seekTo = useCallback(async (tsNs: number) => {
    try {
      const [state, evts] = await Promise.all([
        getState(tsNs),
        getEvents({ to: tsNs, limit: 100 }),
      ]);
      setSnapshot(state);
      setEvents(evts);
    } catch (e) {
      console.warn('Seek failed:', e);
    }
  }, []);

  useEffect(() => {
    refreshState();
    loadEvents();
  }, [refreshState, loadEvents]);

  return { snapshot, events, setEvents, seekTo, refreshState, loadEvents };
}
