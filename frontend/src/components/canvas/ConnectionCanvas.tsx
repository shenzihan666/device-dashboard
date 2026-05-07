import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  MarkerType,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ServerNode from './ServerNode';
import HostNode from './HostNode';
import DeviceNode from './DeviceNode';
import { applyDagreLayout } from '../../utils/dagreLayout';
import type { StateSnapshot } from '../../services/api';

const nodeTypes: NodeTypes = {
  server: ServerNode,
  host: HostNode,
  device: DeviceNode,
};

interface ConnectionCanvasProps {
  snapshot: StateSnapshot;
  positions: Map<string, { x: number; y: number }>;
  canvasMode: 'view' | 'edit';
  onNodeDragStop: (nodeId: string, x: number, y: number) => void;
}

function buildNodeId(type: string, id: string): string {
  return `${type}::${id}`;
}

export default function ConnectionCanvas({
  snapshot,
  positions,
  canvasMode,
  onNodeDragStop,
}: ConnectionCanvasProps) {
  const { nodes, edges } = useMemo(() => {
    const rawNodes: Node[] = [
      ...snapshot.servers.map((s) => ({
        id: buildNodeId('server', s.url),
        type: 'server' as const,
        data: {
          label: s.url.replace('http://', '').replace('/chat', ''),
          url: s.url,
          deviceCount: s.device_count,
        },
        position: { x: 0, y: 0 },
      })),
      ...snapshot.hosts.map((h) => ({
        id: buildNodeId('host', h.name),
        type: 'host' as const,
        data: {
          label: h.name,
          status: h.status,
          deviceCount: h.device_count,
        },
        position: { x: 0, y: 0 },
      })),
      ...snapshot.devices.map((d) => ({
        id: buildNodeId('device', d.serial),
        type: 'device' as const,
        data: {
          label: d.serial.slice(-6),
          serial: d.serial,
          host: d.host,
          aiUrl: d.ai_url,
          status: d.status,
        },
        position: { x: 0, y: 0 },
      })),
    ];

    const rawEdges: Edge[] = snapshot.edges.map((e, i) => {
      const isDeviceHost = e.type === 'device_host';
      const fromId = isDeviceHost
        ? buildNodeId('device', e.from)
        : buildNodeId('server', e.to);
      const toId = isDeviceHost
        ? buildNodeId('host', e.to)
        : buildNodeId('device', e.from);

      const edgeColor = e.status === 'offline'
        ? '#dc2626'
        : isDeviceHost
          ? '#9ca3af'
          : '#16a34a';

      return {
        id: `edge-${i}-${e.from}-${e.to}`,
        source: fromId,
        target: toId,
        type: 'default',
        style: {
          stroke: edgeColor,
          strokeWidth: isDeviceHost ? 1.5 : 2,
          strokeDasharray: isDeviceHost ? '5,5' : 'none',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
          width: 16,
          height: 16,
        },
        animated: !isDeviceHost && e.status !== 'offline',
      };
    });

    const layoutedNodes = applyDagreLayout(rawNodes, rawEdges, positions);
    return { nodes: layoutedNodes, edges: rawEdges };
  }, [snapshot, positions]);

  const handleDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
    onNodeDragStop(node.id, node.position.x, node.position.y);
  }, [onNodeDragStop]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      nodesDraggable={canvasMode === 'edit'}
      nodesConnectable={false}
      elementsSelectable={true}
      panOnDrag={true}
      zoomOnScroll={true}
      onNodeDragStop={handleDragStop}
      fitView
      minZoom={0.1}
      maxZoom={2}
      attributionPosition="bottom-left"
    >
      <Background variant={BackgroundVariant.Dots} gap={16} size={1.5} color="#cbd5e1" />
      <Controls />
      <MiniMap
        nodeColor={(node) => {
          if (node.type === 'server') return '#3B82F6';
          if (node.type === 'host') return '#10B981';
          return '#7c3aed';
        }}
        nodeBorderRadius={6}
        maskColor="rgba(0, 0, 0, 0.1)"
        pannable
        zoomable
        position="bottom-right"
      />
    </ReactFlow>
  );
}
