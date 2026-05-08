import { useState, useCallback, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { Settings as SettingsIcon } from 'lucide-react';
import ConnectionCanvas from './components/canvas/ConnectionCanvas';
import CanvasToolbar from './components/canvas/CanvasToolbar';
import EventFeed from './components/EventFeed';
import Timeline from './components/Timeline';
import DetailDrawer from './components/DetailDrawer';
import SettingsDrawer from './components/SettingsDrawer';
import { useWebSocket } from './hooks/useWebSocket';
import { useGraphState } from './hooks/useGraphState';
import { useLayout } from './hooks/useLayout';
import { useAppSettings } from './hooks/useAppSettings';
import type { ConnectionEvent } from './services/api';

type AppMode = 'live' | 'replay';
type CanvasMode = 'view' | 'edit';

export default function App() {
  const [appMode, setAppMode] = useState<AppMode>('live');
  const [canvasMode, setCanvasMode] = useState<CanvasMode>('view');
  const [selectedEvent, setSelectedEvent] = useState<ConnectionEvent | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { settings: appSettings, update: updateAppSettings } = useAppSettings();

  const { wsStatus, lastEvent } = useWebSocket(appMode === 'live');
  const { snapshot, events, setEvents, seekTo, refreshState, loadEvents } = useGraphState(appMode);
  const { positions, savePosition, resetLayout: clearLayout } = useLayout();

  // Process live events
  useEffect(() => {
    if (lastEvent && appMode === 'live') {
      refreshState();
      loadEvents();
    }
  }, [lastEvent, appMode, refreshState, loadEvents]);

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
      <div className="w-full h-full grid grid-rows-[56px_1fr_80px] grid-cols-[1fr_340px]"
        style={{ gridTemplateAreas: '"topbar topbar" "graph feed" "timeline timeline"' }}>
        {/* Top bar */}
        <header className="flex items-center gap-4 px-5 bg-white border-b border-geist-border z-10"
          style={{ gridArea: 'topbar' }}>
          <span className="text-geist-fg font-semibold text-sm tracking-tight whitespace-nowrap">
            &#x25C8; WeCom AI Connections
          </span>

          <div className="flex gap-0.5 bg-geist-bg-muted rounded-md p-0.5">
            <button
              className={`px-3.5 py-1.5 rounded text-xs font-medium transition-all ${
                appMode === 'live'
                  ? 'bg-white shadow-sm text-geist-fg'
                  : 'text-geist-fg-muted hover:text-geist-fg'
              }`}
              onClick={() => handleSetMode('live')}
            >LIVE</button>
            <button
              className={`px-3.5 py-1.5 rounded text-xs font-medium transition-all ${
                appMode === 'replay'
                  ? 'bg-white shadow-sm text-geist-fg'
                  : 'text-geist-fg-muted hover:text-geist-fg'
              }`}
              onClick={() => handleSetMode('replay')}
            >REPLAY</button>
          </div>

          <button
            aria-label="Settings"
            onClick={() => setSettingsOpen(true)}
            className="p-1.5 rounded-md text-geist-fg-muted hover:text-geist-fg hover:bg-geist-bg-muted transition-colors"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          <div className="ml-auto flex items-center gap-2 text-xs text-geist-fg-muted">
            <span className={`w-2 h-2 rounded-full inline-block ${
              wsStatus === 'connected' ? 'bg-geist-success' :
              wsStatus === 'connecting' ? 'bg-geist-warning animate-pulse' :
              'bg-geist-danger'
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
        <div className="bg-geist-bg-subtle border-l border-geist-border flex flex-col overflow-hidden"
          style={{ gridArea: 'feed' }}>
          <EventFeed events={events} onEventClick={setSelectedEvent} />
        </div>

        {/* Timeline */}
        <div className="bg-geist-bg-subtle border-t border-geist-border flex flex-col px-4 py-1.5"
          style={{ gridArea: 'timeline' }}>
          <Timeline
            events={events}
            appMode={appMode}
            onSeek={handleSeek}
          />
        </div>
      </div>

      {/* Settings drawer (left) */}
      <SettingsDrawer
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={appSettings}
        onUpdate={updateAppSettings}
      />

      {/* Detail drawer (right) */}
      {selectedEvent && (
        <DetailDrawer
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          langsmithEnabled={appSettings.langsmith_enabled}
        />
      )}
    </ReactFlowProvider>
  );
}
