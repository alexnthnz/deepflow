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
import { LayoutGrid, Save, Download, Play, AlertTriangle } from 'lucide-react';
import { getLayoutedElements } from '@/lib/layout-utils';
import { LayoutDirection } from '@/components/workflow/node';
import { useWorkflow } from '@/hooks/use-workflow';
import { Button } from '@/components/ui/button';

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
  { 
    id: 'e-start-agent', 
    source: 'start', 
    target: 'agent', 
    sourceHandle: 'output', 
    targetHandle: 'input', 
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#6b7280', strokeWidth: 1 }
  },
  { 
    id: 'e-agent-tools', 
    source: 'agent', 
    target: 'tools', 
    sourceHandle: 'output', 
    targetHandle: 'input', 
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#6b7280', strokeWidth: 1 }
  },
  { 
    id: 'e-tools-agent', 
    source: 'tools', 
    target: 'agent', 
    sourceHandle: 'output', 
    targetHandle: 'input', 
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#6b7280', strokeWidth: 1 }
  },
  { 
    id: 'e-agent-end', 
    source: 'agent', 
    target: 'end', 
    sourceHandle: 'output', 
    targetHandle: 'input', 
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#6b7280', strokeWidth: 1 }
  },
];

export default function WorkflowPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [isLayouting, setIsLayouting] = useState(false);
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('horizontal');
  const reactFlowInstance = useRef<any>(null);
  
  // Undo functionality state
  const [deletedNodeData, setDeletedNodeData] = useState<DeletedNodeData | null>(null);
  const undoTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Backend integration
  const workflow = useWorkflow();
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [executionInput, setExecutionInput] = useState('');
  const [executionResult, setExecutionResult] = useState<any>(null);

  // Load workflow from backend on mount
  useEffect(() => {
    const loadFromBackend = async () => {
      const workflowData = await workflow.load();
      
      if (workflowData && workflowData.nodes.length > 0) {
        // Use loaded workflow
        setNodes(workflowData.nodes);
        setEdges(workflowData.edges);
      } else {
        // Use initial layout if no saved workflow
        try {
          const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(initialNodes, initialEdges);
          setNodes(layoutedNodes);
          setEdges(layoutedEdges);
        } catch (error) {
          console.error('Initial layout failed:', error);
        }
      }
      
      // Center the view after layout is applied
      setTimeout(() => {
        if (reactFlowInstance.current) {
          reactFlowInstance.current.fitView({ padding: 0.1, duration: 800 });
        }
      }, 100);
    };
    
    loadFromBackend();
  }, []); // Only run once on mount

  // Auto-save on changes
  useEffect(() => {
    if (nodes.length > 0 && edges.length >= 0) {
      workflow.markAsChanged();
      workflow.enableAutoSave(nodes, edges);
    }
  }, [nodes, edges, workflow]);

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
      // Allow connections from any source handle (output) to any target handle (input)
      // Source handles should start with 'output' and target handles should start with 'input'
      if (connection.sourceHandle?.startsWith('output') && connection.targetHandle?.startsWith('input')) {
        setEdges((eds) => addEdge(connection, eds));
      }
    },
    [setEdges]
  );

  const isValidConnection = useCallback((connection: Connection | Edge) => {
    // Allow connections from any output handle to any input handle
    return !!(connection.sourceHandle?.startsWith('output') && connection.targetHandle?.startsWith('input'));
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

  // Update edge styles based on selection
  useEffect(() => {
    setEdges((eds) =>
      eds.map((edge) => {
        const isSelected = selectedEdge?.id === edge.id;
        
        return {
          ...edge,
          style: {
            stroke: isSelected ? '#000000' : '#6b7280', // Black when selected, gray when not
            strokeWidth: isSelected ? 2 : 1, // Thicker when selected
          },
          animated: true, // Keep animation always on
        };
      })
    );
  }, [selectedEdge, setEdges]);

  // Update nodes with layout direction
  const updateNodesLayoutDirection = useCallback((direction: LayoutDirection) => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          layoutDirection: direction,
        },
      }))
    );
  }, [setNodes]);

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
          defaultEdgeOptions={{ 
            type: 'smoothstep', 
            animated: true, 
            style: { stroke: '#6b7280', strokeWidth: 1 } 
          }}
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
          
          {/* Workflow Management Panel */}
          <Panel position="top-right" className="m-2">
            <div className="flex flex-col gap-2">
              {/* Workflow Status */}
              <div className="bg-white border border-gray-300 rounded-md px-3 py-2 text-xs text-gray-600 shadow-sm">
                {workflow.hasUnsavedChanges ? (
                  <div className="flex items-center gap-1 text-orange-600">
                    <AlertTriangle size={12} />
                    Unsaved changes
                  </div>
                ) : workflow.lastSaved ? (
                  <div className="text-green-600">
                    Saved {workflow.lastSaved.toLocaleTimeString()}
                  </div>
                ) : (
                  <div className="text-gray-500">No workflow loaded</div>
                )}
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  onClick={() => workflow.save(nodes, edges)}
                                     disabled={workflow.isSaving || (!workflow.hasUnsavedChanges && !!workflow.lastSaved)}
                  size="sm"
                  className="flex items-center gap-1"
                  title="Save workflow"
                >
                  <Save size={14} />
                  {workflow.isSaving ? 'Saving...' : 'Save'}
                </Button>
                
                <Button
                  onClick={() => workflow.load().then(data => {
                    if (data) {
                      setNodes(data.nodes);
                      setEdges(data.edges);
                    }
                  })}
                  disabled={workflow.isLoading}
                  size="sm"
                  variant="outline"
                  className="flex items-center gap-1"
                  title="Load workflow"
                >
                  <Download size={14} />
                  {workflow.isLoading ? 'Loading...' : 'Load'}
                </Button>
                
                <Button
                  onClick={() => setShowExecutionPanel(!showExecutionPanel)}
                  disabled={workflow.isExecuting || nodes.length === 0}
                  size="sm"
                  variant="outline"
                  className="flex items-center gap-1"
                  title="Execute workflow"
                >
                  <Play size={14} />
                  Execute
                </Button>
              </div>
              
              {/* Auto Layout Button */}
              <Button
                onClick={applyQuickLayout}
                disabled={isLayouting || nodes.length === 0}
                size="sm"
                variant="outline"
                className="flex items-center gap-1"
                title="Auto arrange nodes"
              >
                <LayoutGrid size={14} className={isLayouting ? 'animate-spin' : ''} />
                {isLayouting ? 'Layouting...' : 'Auto Layout'}
              </Button>
            </div>
          </Panel>

          {/* Execution Panel */}
          {showExecutionPanel && (
            <Panel position="top-center" className="m-2 w-96">
              <div className="bg-white border border-gray-300 rounded-lg p-4 shadow-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-900">Execute Workflow</h3>
                  <button
                    onClick={() => setShowExecutionPanel(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Input Message
                    </label>
                    <textarea
                      value={executionInput}
                      onChange={(e) => setExecutionInput(e.target.value)}
                      placeholder="Enter your message to process through the workflow..."
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm resize-none"
                      rows={3}
                    />
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      onClick={async () => {
                        if (!executionInput.trim()) return;
                        const result = await workflow.execute(executionInput);
                        setExecutionResult(result);
                        if (result) {
                          setExecutionInput('');
                        }
                      }}
                      disabled={workflow.isExecuting || !executionInput.trim()}
                      size="sm"
                      className="flex items-center gap-1"
                    >
                      <Play size={14} />
                      {workflow.isExecuting ? 'Executing...' : 'Run'}
                    </Button>
                    
                    <Button
                      onClick={() => workflow.validate(nodes, edges)}
                      disabled={workflow.isValidating}
                      size="sm"
                      variant="outline"
                      className="flex items-center gap-1"
                    >
                      {workflow.isValidating ? 'Validating...' : 'Validate'}
                    </Button>
                  </div>
                  
                  {workflow.validationResult && (
                    <div className="text-xs">
                      {workflow.validationResult.is_valid ? (
                        <div className="text-green-600">✓ Workflow is valid</div>
                      ) : (
                        <div className="text-red-600">
                          ✗ {workflow.validationResult.errors.length} error(s) found
                        </div>
                      )}
                    </div>
                  )}
                  
                  {executionResult && (
                    <div className="mt-3 p-2 bg-gray-50 rounded border text-xs">
                      <div className="font-medium mb-1">Execution Result:</div>
                      <div className="text-gray-600">
                        Status: {executionResult.status}<br/>
                        Messages: {executionResult.messages?.length || 0}<br/>
                        Nodes: {executionResult.node_executions?.length || 0}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Panel>
          )}
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
        layoutDirection={layoutDirection}
        setLayoutDirection={setLayoutDirection}
        updateNodesLayoutDirection={updateNodesLayoutDirection}
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