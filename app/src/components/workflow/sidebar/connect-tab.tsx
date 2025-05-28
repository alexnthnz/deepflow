import { useState } from 'react';
import { Link, Edit3, Bot, Wrench, Play, Square, Trash2 } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeType, NodeData } from '../node';
import type { TabType } from './tab-navigation';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

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

  // Delete an edge
  const deleteEdge = (edgeId: string) => {
    setEdges((eds) => eds.filter((edge) => edge.id !== edgeId));
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
          <Select
            value={sourceNodeId}
            onValueChange={setSourceNodeId}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Choose source node..." />
            </SelectTrigger>
            <SelectContent>
              {nodes.map((node) => {
                const nodeData = node.data as NodeData;
                const typeInfo = getNodeTypeInfo(nodeData.nodeType);
                const isDisabled = node.id === targetNodeId; // Prevent self-connection
                
                return (
                  <SelectItem 
                    key={node.id} 
                    value={node.id}
                    disabled={isDisabled}
                    className={isDisabled ? 'opacity-50' : ''}
                  >
                    <div className="flex items-center gap-2">
                      <span className={typeInfo.color}>{typeInfo.icon}</span>
                      <span>{typeInfo.label}: {nodeData.name}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
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
          <Select
            value={targetNodeId}
            onValueChange={setTargetNodeId}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Choose target node..." />
            </SelectTrigger>
            <SelectContent>
              {nodes.map((node) => {
                const nodeData = node.data as NodeData;
                const typeInfo = getNodeTypeInfo(nodeData.nodeType);
                const isDisabled = node.id === sourceNodeId; // Prevent self-connection
                
                return (
                  <SelectItem 
                    key={node.id} 
                    value={node.id}
                    disabled={isDisabled}
                    className={isDisabled ? 'opacity-50' : ''}
                  >
                    <div className="flex items-center gap-2">
                      <span className={typeInfo.color}>{typeInfo.icon}</span>
                      <span>{typeInfo.label}: {nodeData.name}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
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
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Existing Connections</h4>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              {edges.length} connection{edges.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="space-y-3">
            {edges.map((edge) => {
              const sourceNode = nodes.find(n => n.id === edge.source);
              const targetNode = nodes.find(n => n.id === edge.target);
              const sourceData = sourceNode?.data as NodeData;
              const targetData = targetNode?.data as NodeData;
              const sourceTypeInfo = getNodeTypeInfo(sourceData?.nodeType);
              const targetTypeInfo = getNodeTypeInfo(targetData?.nodeType);
              
              return (
                <div key={edge.id} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-sm">
                        <div className="flex items-center gap-1">
                          <span className={sourceTypeInfo.color}>{sourceTypeInfo.icon}</span>
                          <span className="font-medium text-gray-900">{sourceData?.name}</span>
                        </div>
                        <span className="text-gray-400">→</span>
                        <div className="flex items-center gap-1">
                          <span className={targetTypeInfo.color}>{targetTypeInfo.icon}</span>
                          <span className="font-medium text-gray-900">{targetData?.name}</span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {sourceTypeInfo.label} to {targetTypeInfo.label} • {edge.type || 'default'} edge
                      </div>
                    </div>
                    <div className="flex items-center gap-1 ml-3">
                      <button
                        onClick={() => {
                          setSelectedEdge(edge);
                          setActiveTab('edit');
                        }}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Edit connection"
                      >
                        <Edit3 size={14} />
                      </button>
                      <button
                        onClick={() => deleteEdge(edge.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Delete connection"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
} 