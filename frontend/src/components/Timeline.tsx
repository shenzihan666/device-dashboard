import { useRef, useEffect, useState, useCallback } from 'react';
import { getTimeRange, getDensity, type ConnectionEvent } from '../services/api';

interface TimelineProps {
  events: ConnectionEvent[];
  appMode: 'live' | 'replay';
  onSeek: (tsNs: number) => void;
}

export default function Timeline({ events, appMode, onSeek }: TimelineProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [minNs, setMinNs] = useState<number | null>(null);
  const [maxNs, setMaxNs] = useState<number | null>(null);
  const [cursorNs, setCursorNs] = useState<number | null>(null);
  const [density, setDensity] = useState<{ ts_ns: number; count: number }[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // Load time range + density on mount
  useEffect(() => {
    getTimeRange().then((range) => {
      if (range.min_ns && range.max_ns) {
        setMinNs(range.min_ns);
        setMaxNs(range.max_ns);
        setCursorNs(range.max_ns);
        getDensity(range.min_ns, range.max_ns, 200).then(setDensity).catch(() => {});
      }
    }).catch(() => {});
  }, []);

  // Update maxNs from latest event in live mode
  useEffect(() => {
    if (appMode === 'live' && events.length > 0) {
      const latestNs = Math.max(...events.map(e => e.ts_ns));
      setMaxNs(prev => {
        if (prev === null || latestNs > prev) return latestNs;
        return prev;
      });
    }
  }, [appMode, events]);

  // Keep cursor at max in live mode
  useEffect(() => {
    if (appMode === 'live' && maxNs) {
      setCursorNs(maxNs);
    }
  }, [appMode, maxNs, events]);

  // Periodic density refresh in live mode
  useEffect(() => {
    if (appMode !== 'live') return;
    const interval = setInterval(async () => {
      try {
        const range = await getTimeRange();
        if (range.min_ns && range.max_ns) {
          setMinNs(range.min_ns);
          setMaxNs(range.max_ns);
          const d = await getDensity(range.min_ns, range.max_ns, 200);
          setDensity(d);
        }
      } catch { /* ignore */ }
    }, 30_000);
    return () => clearInterval(interval);
  }, [appMode]);

  // Draw canvas
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.parentElement!.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = 36;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);

    if (!minNs || !maxNs || minNs >= maxNs) return;
    const range = maxNs - minNs;

    if (density.length > 0) {
      const maxCount = Math.max(...density.map((b) => b.count), 1);
      ctx.fillStyle = 'rgba(37, 99, 235, 0.18)';
      density.forEach((b) => {
        const x = ((b.ts_ns - minNs) / range) * w;
        const bw = Math.max(1, w / density.length);
        const bh = (b.count / maxCount) * (h - 8);
        ctx.fillRect(x, h - 4 - bh, bw, bh);
      });
    }

    // Cursor line
    if (cursorNs !== null) {
      const x = ((cursorNs - minNs) / range) * w;
      ctx.strokeStyle = '#2563eb';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();

      ctx.fillStyle = '#2563eb';
      ctx.beginPath();
      ctx.arc(x, 4, 5, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.strokeStyle = '#ededed';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(w, 0);
    ctx.stroke();
  }, [minNs, maxNs, cursorNs, density]);

  useEffect(() => {
    draw();
  }, [draw]);

  useEffect(() => {
    const handleResize = () => draw();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  const xToNs = useCallback((clientX: number) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, x / canvas.width));
    return minNs! + ratio * (maxNs! - minNs!);
  }, [minNs, maxNs]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!minNs || !maxNs) return;
    setIsDragging(true);
    const ns = Math.round(xToNs(e.clientX));
    setCursorNs(ns);
    onSeek(ns);
  }, [minNs, maxNs, xToNs, onSeek]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !minNs || !maxNs) return;
    const ns = Math.round(xToNs(e.clientX));
    setCursorNs(ns);
    onSeek(ns);
  }, [isDragging, minNs, maxNs, xToNs, onSeek]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const formatTimeDisplay = (ns: number | null) => {
    if (!ns) return '--';
    const d = new Date(ns / 1e6);
    return d.toLocaleString('en-US', { hour12: false });
  };

  const formatTimeRange = () => {
    if (!minNs || !maxNs) return '--';
    const dMin = new Date(minNs / 1e6);
    const dMax = new Date(maxNs / 1e6);
    return `${dMin.toLocaleTimeString('en-US', { hour12: false })} — ${dMax.toLocaleTimeString('en-US', { hour12: false })}`;
  };

  return (
    <>
      <div className="flex items-center gap-2.5 mb-1">
        <span className="font-mono text-xs text-geist-fg">{formatTimeDisplay(cursorNs)}</span>
        <span className="flex-1" />
        <span className="font-mono text-xs text-geist-fg-subtle">{formatTimeRange()}</span>
      </div>
      <div
        className="flex-1 relative cursor-pointer"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <canvas ref={canvasRef} className="w-full h-9 block" />
      </div>
    </>
  );
}
