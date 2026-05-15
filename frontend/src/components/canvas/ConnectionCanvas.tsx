import { useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  MarkerType,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ServerNode from './ServerNode';
import HostNode from './HostNode';
import DeviceNode from './DeviceNode';
import BrainServerNode from './BrainServerNode';
import WeComClientNode from './WeComClientNode';
import WeComDeviceNode from './WeComDeviceNode';
import { applyDagreLayout } from '../../utils/dagreLayout';
import type { DataSourcesState, StateSnapshot } from '../../services/api';

const nodeTypes: NodeTypes = {
  server: ServerNode,
  host: HostNode,
  device: DeviceNode,
  brain_server: BrainServerNode,
  wecom_client: WeComClientNode,
  wecom_device: WeComDeviceNode,
};

interface ConnectionCanvasProps {
  snapshot: StateSnapshot;
  dataSources: DataSourcesState;
  positions: Map<string, { x: number; y: number }>;
  canvasMode: 'view' | 'edit';
  onNodeDragStop: (nodeId: string, x: number, y: number) => void;
}

function buildNodeId(type: string, id: string): string {
  return `${type}::${id}`;
}

export default function ConnectionCanvas({
  snapshot,
  dataSources,
  positions,
  canvasMode,
  onNodeDragStop,
}: ConnectionCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    const p2pOn = dataSources.point_to_point_enabled;

    const rawNodes: Node[] = [
      ...(p2pOn ? (snapshot.brain_servers || []).map((bs) => ({
        id: buildNodeId('brain_server', bs.instance_id),
        type: 'brain_server' as const,
        data: {
          label: bs.name,
          state: bs,
        },
        position: { x: 0, y: 0 },
      })) : []),
      ...(p2pOn ? (snapshot.wecom_clients || []).map((wc) => ({
        id: buildNodeId('wecom_client', wc.instance_id),
        type: 'wecom_client' as const,
        data: {
          label: wc.name,
          state: wc,
        },
        position: { x: 0, y: 0 },
      })) : []),
      ...(p2pOn ? (snapshot.wecom_clients || []).flatMap((wc) =>
        (wc.devices || []).map((dev) => ({
          id: `wecom_device::${wc.instance_id}/${dev.serial}`,
          type: 'wecom_device' as const,
          data: {
            label: dev.serial.slice(-6),
            device: dev,
          },
          position: { x: 0, y: 0 },
        }))
      ) : []),
    ];

    const rawEdges: Edge[] = [];

    // Heartbeat edges (wecom_client -> brain_server)
    const hbEdges: Edge[] = p2pOn ? (snapshot.heartbeat_edges || []).map((e, i) => {
      const edgeColor = e.status === 'offline' ? '#dc2626' : '#3b82f6';
      return {
        id: `hb-edge-${i}-${e.from}-${e.to}`,
        source: e.from,
        target: e.to,
        sourceHandle: 'src-top',
        type: 'default',
        style: {
          stroke: edgeColor,
          strokeWidth: 2,
          strokeDasharray: '6,4',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
          width: 16,
          height: 16,
        },
        animated: e.status !== 'offline',
      };
    }) : [];

    // Edges: wecom_client -> wecom_device (per-device links)
    const wcDeviceEdges: Edge[] = p2pOn ? (snapshot.wecom_clients || []).flatMap((wc) =>
      (wc.devices || []).map((dev, di) => ({
        id: `wc-dev-${wc.instance_id}-${dev.serial}-${di}`,
        source: buildNodeId('wecom_client', wc.instance_id),
        target: `wecom_device::${wc.instance_id}/${dev.serial}`,
        sourceHandle: 'src-bottom',
        type: 'default',
        style: {
          stroke: dev.running ? '#3b82f6' : '#9ca3af',
          strokeWidth: 1.5,
          strokeDasharray: '5,5',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: dev.running ? '#3b82f6' : '#9ca3af',
          width: 14,
          height: 14,
        },
        animated: dev.running === true,
      }))
    ) : [];

    const allEdges = [...rawEdges, ...hbEdges, ...wcDeviceEdges];

    setNodes(applyDagreLayout(rawNodes, allEdges, positions));
    setEdges(allEdges);
  }, [snapshot, dataSources, positions, setNodes, setEdges]);

  const handleDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
    onNodeDragStop(node.id, node.position.x, node.position.y);
  }, [onNodeDragStop]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
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
          if (node.type === 'brain_server') return '#f97316';
          if (node.type === 'wecom_client') return '#3b82f6';
          if (node.type === 'wecom_device') return '#8b5cf6';
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
