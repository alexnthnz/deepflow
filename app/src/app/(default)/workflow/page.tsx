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
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomNode from '@/components/workflow/node';
import Sidebar from '@/components/workflow/sidebar';
import { GlobalUndoNotification } from '@/components/workflow/global-undo-notification';
import { LayoutGrid } from 'lucide-react';
import { getLayoutedElements } from '@/lib/layout-utils';

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
  const [isLayouting, setIsLayouting] = useState(false);
  const reactFlowInstance = useRef<any>(null);
  
  // Undo functionality state
  const [deletedNodeData, setDeletedNodeData] = useState<DeletedNodeData | null>(null);
  const undoTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Apply initial layout on mount
  useEffect(() => {
    const applyInitialLayout = async () => {
      try {
        const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(initialNodes, initialEdges);
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
        // Center the view after layout is applied
        setTimeout(() => {
          if (reactFlowInstance.current) {
            reactFlowInstance.current.fitView({ padding: 0.1, duration: 800 });
          }
        }, 100);
      } catch (error) {
        console.error('Initial layout failed:', error);
      }
    };
    
    applyInitialLayout();
  }, []); // Only run once on mount

  // Quick layout function for the panel button
  const applyQuickLayout = async () => {
    if (nodes.length === 0 || isLayouting) return;
    
    setIsLayouting(true);
    try {
      const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(nodes, edges);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      // Center the view after layout is applied
      setTimeout(() => {
        if (reactFlowInstance.current) {
          reactFlowInstance.current.fitView({ padding: 0.1, duration: 800 });
        }
      }, 100);
    } catch (error) {
      console.error('Quick layout failed:', error);
    } finally {
      setIsLayouting(false);
    }
  };

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

  // Handle ReactFlow initialization
  const onInit = useCallback((instance: any) => {
    reactFlowInstance.current = instance;
  }, []);

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
          onInit={onInit}
          deleteKeyCode={null} // Disable default delete behavior completely
          multiSelectionKeyCode={null} // Disable multi-selection for simplicity
          nodesConnectable={true}
          nodesDraggable={true}
          elementsSelectable={true}
        >
          <Background />
          <Controls />
          <MiniMap />
          
          {/* Quick Layout Panel */}
          <Panel position="top-right" className="m-2">
            <button
              onClick={applyQuickLayout}
              disabled={isLayouting || nodes.length === 0}
              className="bg-white border border-gray-300 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
              title="Auto arrange nodes"
            >
              <LayoutGrid size={16} className={isLayouting ? 'animate-spin' : ''} />
              {isLayouting ? 'Layouting...' : 'Auto Layout'}
            </button>
          </Panel>
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
      <GlobalUndoNotification
        deletedNodeData={deletedNodeData}
        onUndo={undoNodeDeletion}
        onDismiss={() => setDeletedNodeData(null)}
      />
    </div>
  );
} 