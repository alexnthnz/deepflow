import { Link, Bot, Wrench, Play, Square } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeType, NodeData } from '../node';

interface OverviewTabProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  nodes: Node[];
  edges: Edge[];
}

const ALL_NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'agent', label: 'Agent', icon: <Bot size={16} />, color: 'text-blue-600' },
  { value: 'tools', label: 'Tools', icon: <Wrench size={16} />, color: 'text-green-600' },
  { value: 'start', label: 'Start', icon: <Play size={16} />, color: 'text-emerald-600' },
  { value: 'end', label: 'End', icon: <Square size={16} />, color: 'text-red-600' },
];

export function OverviewTab({ selectedNode, selectedEdge, nodes, edges }: OverviewTabProps) {
  // Get node type info
  const getNodeTypeInfo = (nodeType: NodeType) => {
    return ALL_NODE_TYPES.find(type => type.value === nodeType) || ALL_NODE_TYPES[0];
  };

  // Get node statistics by type
  const getNodeStatsByType = () => {
    const stats = nodes.reduce((acc, node) => {
      const nodeData = node.data as NodeData;
      const nodeType = nodeData.nodeType || 'unknown';
      acc[nodeType] = (acc[nodeType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return stats;
  };

  const nodeStats = getNodeStatsByType();

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Workflow Overview</h3>
        <p className="text-sm text-gray-600 mb-4">Summary of your workflow structure</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{nodes.length}</div>
          <div className="text-sm text-blue-600">Total Nodes</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{edges.length}</div>
          <div className="text-sm text-green-600">Connections</div>
        </div>
      </div>

      {/* Node Type Breakdown */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Node Types</h4>
        <div className="space-y-3">
          {ALL_NODE_TYPES.map((type) => {
            const count = nodeStats[type.value] || 0;
            return (
              <div key={type.value} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-md bg-white`}>
                    <div className={type.color}>
                      {type.icon}
                    </div>
                  </div>
                  <span className="font-medium text-gray-900">{type.label}</span>
                </div>
                <span className="text-lg font-bold text-gray-600">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Selection */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Current Selection</h4>
        <div className="p-3 bg-gray-50 rounded-lg">
          {selectedNode ? (
            <div className="flex items-center gap-3">
              <div className={getNodeTypeInfo((selectedNode.data as NodeData).nodeType).color}>
                {getNodeTypeInfo((selectedNode.data as NodeData).nodeType).icon}
              </div>
              <div>
                <div className="font-medium">{(selectedNode.data as NodeData).name}</div>
                <div className="text-sm text-gray-600">
                  {getNodeTypeInfo((selectedNode.data as NodeData).nodeType).label} Node
                </div>
              </div>
            </div>
          ) : selectedEdge ? (
            <div className="flex items-center gap-3">
              <Link size={16} className="text-gray-600" />
              <div>
                <div className="font-medium">Connection</div>
                <div className="text-sm text-gray-600">Edge selected</div>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-2">
              No selection
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 