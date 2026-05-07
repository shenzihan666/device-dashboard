import { useState, useCallback, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import ConnectionCanvas from './components/canvas/ConnectionCanvas';
import CanvasToolbar from './components/canvas/CanvasToolbar';
import EventFeed from './components/EventFeed';
import Timeline from './components/Timeline';
import DetailDrawer from './components/DetailDrawer';
import { useWebSocket } from './hooks/useWebSocket';
import { useGraphState } from './hooks/useGraphState';
import { useLayout } from './hooks/useLayout';
import type { ConnectionEvent } from './services/api';

type AppMode = 'live' | 'replay';
type CanvasMode = 'view' | 'edit';

export default function App() {
  const [appMode, setAppMode] = useState<AppMode>('live');
  const [canvasMode, setCanvasMode] = useState<CanvasMode>('view');
  const [selectedEvent, setSelectedEvent] = useState<ConnectionEvent | null>(null);

  const { wsStatus, lastEvent } = useWebSocket(appMode === 'live');
  const { snapshot, events, setEvents, seekTo, refreshState, loadEvents } = useGraphState(appMode);
  const { positions, savePosition, resetLayout: clearLayout } = useLayout();

  // Process live events
  useEffect(() => {
    if (lastEvent && appMode === 'live') {
      refreshState();
    }
  }, [lastEvent, appMode, refreshState]);

  const handleSetMode = useCallback((m: AppMode) => {
    setAppMode(m);
    if (m === 'live') {
      refreshState();
      loadEvents();
    }
  }, [refreshState, loadEvents]);

  const handleSeek = useCallback((tsNs: number) => {
    setAppMode('replay');
    seekTo(tsNs);
  }, [seekTo]);

  return (
    <ReactFlowProvider>
      <div className="w-full h-full grid grid-rows-[48px_1fr_80px] grid-cols-[1fr_340px]"
        style={{ gridTemplateAreas: '"topbar topbar" "graph feed" "timeline timeline"' }}>
        {/* Top bar */}
        <header className="flex items-center gap-3.5 px-4 bg-foundry-bg-secondary border-b border-foundry-border z-10"
          style={{ gridArea: 'topbar' }}>
          <span className="text-foundry-accent font-bold text-[15px] tracking-wide whitespace-nowrap">
            &#x25C8; WeCom AI Connections
          </span>

          <div className="flex gap-0.5 bg-foundry-bg rounded-md p-0.5">
            <button
              className={`px-3.5 py-1 rounded text-xs font-medium transition-all ${appMode === 'live' ? 'bg-[rgba(0,212,255,0.15)] text-foundry-accent' : 'text-foundry-text-dim'}`}
              onClick={() => handleSetMode('live')}
            >LIVE</button>
            <button
              className={`px-3.5 py-1 rounded text-xs font-medium transition-all ${appMode === 'replay' ? 'bg-[rgba(0,212,255,0.15)] text-foundry-accent' : 'text-foundry-text-dim'}`}
              onClick={() => handleSetMode('replay')}
            >REPLAY</button>
          </div>

          <div className="ml-auto flex items-center gap-2 text-xs text-foundry-text-dim">
            <span className={`w-2 h-2 rounded-full inline-block ${
              wsStatus === 'connected' ? 'bg-foundry-green' :
              wsStatus === 'connecting' ? 'bg-foundry-amber animate-pulse' :
              'bg-foundry-red'
            }`} />
            <span>{wsStatus === 'connected' ? 'Connected' : wsStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
          </div>
        </header>

        {/* Graph canvas */}
        <div className="relative overflow-hidden" style={{ gridArea: 'graph' }}>
          <ConnectionCanvas
            snapshot={snapshot}
            positions={positions}
            canvasMode={canvasMode}
            onNodeDragStop={savePosition}
          />
          <CanvasToolbar
            mode={canvasMode}
            onModeChange={setCanvasMode}
            onResetLayout={clearLayout}
          />
        </div>

        {/* Event feed */}
        <div className="bg-foundry-bg-secondary border-l border-foundry-border flex flex-col overflow-hidden"
          style={{ gridArea: 'feed' }}>
          <EventFeed events={events} onEventClick={setSelectedEvent} />
        </div>

        {/* Timeline */}
        <div className="bg-foundry-bg-secondary border-t border-foundry-border flex flex-col px-4 py-1.5"
          style={{ gridArea: 'timeline' }}>
          <Timeline
            events={events}
            appMode={appMode}
            onSeek={handleSeek}
          />
        </div>
      </div>

      {/* Detail drawer */}
      {selectedEvent && (
        <DetailDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
      )}
    </ReactFlowProvider>
  );
}
