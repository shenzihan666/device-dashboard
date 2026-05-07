import { useState, useEffect, useCallback, useRef } from 'react';
import { getLayout, saveLayout, resetLayout, type NodePosition } from '../services/api';

export function useLayout() {
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const pendingRef = useRef<NodePosition[]>([]);

  useEffect(() => {
    getLayout().then((items) => {
      const map = new Map<string, { x: number; y: number }>();
      items.forEach((p) => map.set(p.node_id, { x: p.x, y: p.y }));
      setPositions(map);
    }).catch(() => {});
  }, []);

  const savePosition = useCallback((nodeId: string, x: number, y: number) => {
    setPositions((prev) => {
      const next = new Map(prev);
      next.set(nodeId, { x, y });
      return next;
    });

    pendingRef.current.push({ node_id: nodeId, x, y });

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const items = [...pendingRef.current];
      pendingRef.current = [];
      saveLayout(items).catch(() => {});
    }, 500);
  }, []);

  const handleResetLayout = useCallback(async () => {
    await resetLayout();
    setPositions(new Map());
  }, []);

  return { positions, savePosition, resetLayout: handleResetLayout };
}
