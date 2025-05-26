'use client';

import { useCallback, useState, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  ConnectionMode,
  NodeMouseHandler,
  EdgeMouseHandler,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomNode from '@/components/workflow/node';
import Sidebar from '@/components/workflow/sidebar';
import { Undo2, X, Trash2 } from 'lucide-react';

const nodeTypes = {
  custom: CustomNode,
};

interface DeletedNodeData {
  node: Node;
  connectedEdges: Edge[];
  timestamp: number;
}

const initialNodes: Node[] = [
  {
    id: 'start',
    position: { x: 100, y: 100 },
    data: { 
      name: 'START',
      description: 'Starting point',
      nodeType: 'start'
    },
    type: 'custom',
  },
  {
    id: 'agent',
    position: { x: 300, y: 100 },
    data: { 
      name: 'Main Agent',
      description: 'Primary AI Agent',
      nodeType: 'agent',
      prompt: 'You are a helpful AI assistant that can use various tools to help users accomplish their tasks.'
    },
    type: 'custom',
  },
  {
    id: 'tools',
    position: { x: 500, y: 100 },
    data: { 
      name: 'Tool Suite',
      description: 'Available Tools',
      nodeType: 'tools',
      selectedTools: ['tavily_search', 'google_search']
    },
    type: 'custom',
  },
  {
    id: 'end',
    position: { x: 700, y: 100 },
    data: { 
      name: 'END',
      description: 'End point',
      nodeType: 'end'
    },
    type: 'custom',
  },
];

const initialEdges: Edge[] = [
  { id: 'e-start-agent', source: 'start', target: 'agent', sourceHandle: 'output', targetHandle: 'input', type: 'smoothstep' },
  { id: 'e-agent-tools', source: 'agent', target: 'tools', sourceHandle: 'output', targetHandle: 'input', type: 'smoothstep' },
  { id: 'e-tools-agent', source: 'tools', target: 'agent', sourceHandle: 'output', targetHandle: 'input', type: 'smoothstep' },
  { id: 'e-agent-end', source: 'agent', target: 'end', sourceHandle: 'output', targetHandle: 'input', type: 'smoothstep' },
];

export default function WorkflowPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  
  // Undo functionality state
  const [deletedNodeData, setDeletedNodeData] = useState<DeletedNodeData | null>(null);
  const undoTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const onConnect = useCallback(
    (connection: Connection) => {
      // Ensure proper connection: source handle to target handle
      if (connection.sourceHandle === 'output' && connection.targetHandle === 'input') {
        setEdges((eds) => addEdge(connection, eds));
      }
    },
    [setEdges]
  );

  const isValidConnection = useCallback((connection: Connection | Edge) => {
    // Only allow connections from output handles to input handles
    return connection.sourceHandle === 'output' && connection.targetHandle === 'input';
  }, []);

  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNode(node);
    setSelectedEdge(null); // Clear edge selection when node is selected
  }, []);

  const onEdgeClick: EdgeMouseHandler = useCallback((event, edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null); // Clear node selection when edge is selected
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
  }, []);

  // Cleanup undo timeout on unmount
  useEffect(() => {
    return () => {
      if (undoTimeoutRef.current) {
        clearTimeout(undoTimeoutRef.current);
      }
    };
  }, []);

  // Handle node deletion with undo functionality
  const handleDeleteNode = useCallback((nodeToDelete: Node) => {
    // Store the node and its connected edges for undo
    const connectedEdges = edges.filter((edge) => 
      edge.source === nodeToDelete.id || edge.target === nodeToDelete.id
    );
    
    const deletionData: DeletedNodeData = {
      node: nodeToDelete,
      connectedEdges,
      timestamp: Date.now()
    };

    // Clear any existing undo timeout
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }

    // Set the deleted node data
    setDeletedNodeData(deletionData);

    // Remove the node and its edges
    setNodes((nds) => nds.filter((node) => node.id !== nodeToDelete.id));
    setEdges((eds) => eds.filter((edge) => 
      edge.source !== nodeToDelete.id && edge.target !== nodeToDelete.id
    ));

    // Set timeout to clear undo data after 10 seconds
    undoTimeoutRef.current = setTimeout(() => {
      setDeletedNodeData(null);
    }, 10000);
  }, [edges, setNodes, setEdges]);

  // Undo node deletion
  const undoNodeDeletion = useCallback(() => {
    if (!deletedNodeData) return;

    // Clear the timeout
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }

    // Restore the node and its edges
    setNodes((nds) => [...nds, deletedNodeData.node]);
    setEdges((eds) => [...eds, ...deletedNodeData.connectedEdges]);

    // Clear undo data
    setDeletedNodeData(null);
  }, [deletedNodeData, setNodes, setEdges]);

  // Handle keyboard shortcuts (only undo, no automatic deletion)
  const onKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'z' && (event.ctrlKey || event.metaKey)) {
      // Handle Ctrl+Z / Cmd+Z for undo
      event.preventDefault();
      undoNodeDeletion();
    }
    // Note: Delete/Backspace keys are intentionally not handled here
    // Users must use the "Delete Node" button in the sidebar for intentional deletion
  }, [undoNodeDeletion]);

  return (
    <div className="flex w-full h-full relative" onKeyDown={onKeyDown} tabIndex={0}>
      <div className="flex-1 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          connectionMode={ConnectionMode.Loose}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={{ type: 'smoothstep' }}
          fitView
          deleteKeyCode={null} // Disable default delete behavior completely
          multiSelectionKeyCode={null} // Disable multi-selection for simplicity
          nodesConnectable={true}
          nodesDraggable={true}
          elementsSelectable={true}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
      <Sidebar 
        selectedNode={selectedNode} 
        selectedEdge={selectedEdge}
        nodes={nodes}
        edges={edges}
        setNodes={setNodes}
        setEdges={setEdges}
        setSelectedNode={setSelectedNode}
        setSelectedEdge={setSelectedEdge}
        onDeleteNode={handleDeleteNode}
      />

      {/* Global Undo Notification */}
      {deletedNodeData && (
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white p-4 rounded-lg shadow-lg border border-gray-700 z-50 min-w-[320px]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-1 bg-gray-700 rounded">
                <Trash2 size={16} />
              </div>
              <div>
                <p className="text-sm font-medium">
                  Deleted "{(deletedNodeData.node.data as any).name}"
                </p>
                <p className="text-xs text-gray-300">
                  {deletedNodeData.connectedEdges.length} connection{deletedNodeData.connectedEdges.length !== 1 ? 's' : ''} removed
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={undoNodeDeletion}
                className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                <Undo2 size={14} />
                Undo
              </button>
              <button
                onClick={() => setDeletedNodeData(null)}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="mt-2 bg-gray-700 rounded-full h-1 overflow-hidden">
            <div 
              className="h-full bg-blue-500 transition-all duration-[10000ms] ease-linear w-0"
              style={{ animation: 'countdown 10s linear forwards' }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Press <kbd className="px-1 py-0.5 bg-gray-700 rounded text-xs">Ctrl+Z</kbd> to undo
          </p>
        </div>
      )}

      <style jsx>{`
        @keyframes countdown {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
} 