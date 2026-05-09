import dagre from 'dagre';
import type { Node, Edge } from '@xyflow/react';

const NODE_SIZES: Record<string, { width: number; height: number }> = {
  server: { width: 220, height: 100 },
  host: { width: 200, height: 90 },
  device: { width: 180, height: 80 },
  brain_server: { width: 220, height: 120 },
  wecom_client: { width: 230, height: 140 },
};

/** Rank priority per node type — lower = higher on the canvas. */
const NODE_RANK: Record<string, number> = {
  brain_server: 0,
  server: 0,
  wecom_client: 1,
  host: 1,
  device: 2,
};

/**
 * Run dagre auto-layout on nodes that don't have saved positions.
 * Nodes with existing positions are kept in place but still participate in graph structure.
 */
export function applyDagreLayout(
  nodes: Node[],
  edges: Edge[],
  savedPositions: Map<string, { x: number; y: number }>,
): Node[] {
  const unsavedNodes = nodes.filter((n) => !savedPositions.has(n.id));

  // If all nodes have positions, just apply them
  if (unsavedNodes.length === 0) {
    return nodes.map((n) => {
      const pos = savedPositions.get(n.id);
      return pos ? { ...n, position: { x: pos.x, y: pos.y } } : n;
    });
  }

  // Run dagre on all nodes to get positions for unsaved ones
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: 'TB',
    nodesep: 80,
    ranksep: 120,
    marginx: 40,
    marginy: 40,
  });

  nodes.forEach((node) => {
    const size = NODE_SIZES[node.type || 'device'] || NODE_SIZES.device;
    g.setNode(node.id, { width: size.width, height: size.height });
  });

  edges.forEach((edge) => {
    // Reverse heartbeat edges for layout: wecom_client→brain_server becomes
    // brain_server→wecom_client so that brain_server ranks higher.
    const isHeartbeat = edge.id.startsWith('hb-edge');
    const src = isHeartbeat ? edge.target : edge.source;
    const tgt = isHeartbeat ? edge.source : edge.target;
    g.setEdge(src, tgt);
  });

  // Add invisible rank-enforcement edges between node types to guarantee
  // the layer order: brain_server (top) → wecom_client (middle) → device (bottom).
  const byType = new Map<string, Node[]>();
  for (const n of nodes) {
    const t = n.type || 'device';
    if (!byType.has(t)) byType.set(t, []);
    byType.get(t)!.push(n);
  }

  const rankGroups: string[][] = [
    ['brain_server', 'server'],
    ['wecom_client', 'host'],
    ['device'],
  ];

  for (let i = 0; i < rankGroups.length - 1; i++) {
    const upper = rankGroups[i].flatMap((t) => byType.get(t) || []);
    const lower = rankGroups[i + 1].flatMap((t) => byType.get(t) || []);
    if (upper.length > 0 && lower.length > 0) {
      // Connect first upper node to first lower node with an invisible edge
      // to enforce rank ordering.
      g.setEdge(upper[0].id, lower[0].id, { style: 'invis' });
    }
  }

  dagre.layout(g);

  return nodes.map((node) => {
    const saved = savedPositions.get(node.id);
    if (saved) {
      return { ...node, position: { x: saved.x, y: saved.y } };
    }
    const dagreNode = g.node(node.id);
    const size = NODE_SIZES[node.type || 'device'] || NODE_SIZES.device;
    return {
      ...node,
      position: {
        x: dagreNode.x - size.width / 2,
        y: dagreNode.y - size.height / 2,
      },
    };
  });
}
