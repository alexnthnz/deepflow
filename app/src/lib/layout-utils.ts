import ELK from 'elkjs/lib/elk.bundled.js';
import { Node, Edge, Position } from '@xyflow/react';

const elk = new ELK();

// ELK layout options
const elkOptions = {
  'elk.algorithm': 'layered',
  'elk.layered.spacing.nodeNodeBetweenLayers': '100',
  'elk.spacing.nodeNode': '80',
  'elk.direction': 'RIGHT',
  'elk.layered.nodePlacement.strategy': 'SIMPLE',
  'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
  'elk.layered.spacing.edgeNodeBetweenLayers': '50',
  'elk.spacing.edgeNode': '30',
  'elk.spacing.edgeEdge': '20',
  'elk.layered.spacing.baseValue': '50',
};

export const getLayoutedElements = async (nodes: Node[], edges: Edge[]) => {
  const isHorizontal = elkOptions['elk.direction'] === 'RIGHT';
  
  const graph = {
    id: 'root',
    layoutOptions: elkOptions,
    children: nodes.map((node) => ({
      id: node.id,
      width: 200,
      height: 100,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layoutedGraph = await elk.layout(graph);

  const layoutedNodes = nodes.map((node) => {
    const layoutedNode = layoutedGraph.children?.find((lgNode) => lgNode.id === node.id);
    
    return {
      ...node,
      targetPosition: isHorizontal ? Position.Left : Position.Top,
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
      position: {
        x: layoutedNode?.x ?? 0,
        y: layoutedNode?.y ?? 0,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export const layoutDirections = {
  'RIGHT': 'Left to Right',
  'DOWN': 'Top to Bottom',
  'LEFT': 'Right to Left',
  'UP': 'Bottom to Top',
} as const;

export const updateLayoutDirection = (direction: keyof typeof layoutDirections) => {
  elkOptions['elk.direction'] = direction;
}; 