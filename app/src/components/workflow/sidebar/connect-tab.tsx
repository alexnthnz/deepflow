import { useState } from 'react';
import { Link, Edit3, Bot, Wrench, Play, Square } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeType, NodeData } from '../node';
import type { TabType } from './tab-navigation';

interface ConnectTabProps {
  nodes: Node[];
  edges: Edge[];
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
  setSelectedEdge: (edge: Edge | null) => void;
  setActiveTab: (tab: TabType) => void;
}

const ALL_NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'agent', label: 'Agent', icon: <Bot size={16} />, color: 'text-blue-600' },
  { value: 'tools', label: 'Tools', icon: <Wrench size={16} />, color: 'text-green-600' },
  { value: 'start', label: 'Start', icon: <Play size={16} />, color: 'text-emerald-600' },
  { value: 'end', label: 'End', icon: <Square size={16} />, color: 'text-red-600' },
];

export function ConnectTab({ nodes, edges, setEdges, setSelectedEdge, setActiveTab }: ConnectTabProps) {
  const [sourceNodeId, setSourceNodeId] = useState('');
  const [targetNodeId, setTargetNodeId] = useState('');

  // Get node type info
  const getNodeTypeInfo = (nodeType: NodeType) => {
    return ALL_NODE_TYPES.find(type => type.value === nodeType) || ALL_NODE_TYPES[0];
  };

  // Add a new edge
  const addEdge = () => {
    if (!sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) return;

    const edgeExists = edges.some(edge => 
      edge.source === sourceNodeId && edge.target === targetNodeId
    );
    
    if (edgeExists) return;

    const newEdge: Edge = {
      id: `edge-${Date.now()}`,
      source: sourceNodeId,
      target: targetNodeId,
      sourceHandle: 'output',
      targetHandle: 'input',
      type: 'smoothstep',
    };

    setEdges((eds) => [...eds, newEdge]);
    setSourceNodeId('');
    setTargetNodeId('');
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Connect Nodes</h3>
        <p className="text-sm text-gray-600 mb-4">Create connections between nodes to define workflow flow</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            From Node
          </label>
          <select
            value={sourceNodeId}
            onChange={(e) => setSourceNodeId(e.target.value)}
            className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose source node...</option>
            {nodes.map((node) => {
              const nodeData = node.data as NodeData;
              const typeInfo = getNodeTypeInfo(nodeData.nodeType);
              return (
                <option key={node.id} value={node.id}>
                  {typeInfo.label}: {nodeData.name}
                </option>
              );
            })}
          </select>
        </div>
        
        <div className="flex justify-center">
          <div className="p-2 bg-gray-100 rounded-full">
            <Link size={16} className="text-gray-600" />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            To Node
          </label>
          <select
            value={targetNodeId}
            onChange={(e) => setTargetNodeId(e.target.value)}
            className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose target node...</option>
            {nodes.map((node) => {
              const nodeData = node.data as NodeData;
              const typeInfo = getNodeTypeInfo(nodeData.nodeType);
              return (
                <option key={node.id} value={node.id}>
                  {typeInfo.label}: {nodeData.name}
                </option>
              );
            })}
          </select>
        </div>
        
        <button
          onClick={addEdge}
          disabled={!sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId}
          className="w-full bg-green-600 text-white px-4 py-3 rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
        >
          <Link size={16} />
          Create Connection
        </button>
      </div>

      {edges.length > 0 && (
        <div className="mt-8">
          <h4 className="font-medium text-gray-900 mb-3">Existing Connections</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {edges.map((edge) => {
              const sourceNode = nodes.find(n => n.id === edge.source);
              const targetNode = nodes.find(n => n.id === edge.target);
              const sourceData = sourceNode?.data as NodeData;
              const targetData = targetNode?.data as NodeData;
              
              return (
                <div key={edge.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="text-sm">
                    <span className="font-medium">{sourceData?.name}</span>
                    <span className="text-gray-500 mx-2">→</span>
                    <span className="font-medium">{targetData?.name}</span>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedEdge(edge);
                      setActiveTab('edit');
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Edit3 size={14} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
} 