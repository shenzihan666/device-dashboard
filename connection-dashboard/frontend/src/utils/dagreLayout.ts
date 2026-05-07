import dagre from 'dagre';
import type { Node, Edge } from '@xyflow/react';

const NODE_SIZES: Record<string, { width: number; height: number }> = {
  server: { width: 220, height: 100 },
  host: { width: 200, height: 90 },
  device: { width: 180, height: 80 },
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
    g.setEdge(edge.source, edge.target);
  });

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
