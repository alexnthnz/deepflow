import { Node, Edge } from '@xyflow/react';
import { useState, useEffect, useRef } from 'react';
import { 
  SidebarHeader, 
  TabNavigation, 
  CreateTab, 
  EditTab, 
  ConnectTab, 
  OverviewTab, 
  UndoNotification,
  type TabType 
} from './sidebar/index';

interface SidebarProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  nodes: Node[];
  edges: Edge[];
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
  setSelectedNode: (node: Node | null) => void;
  setSelectedEdge: (edge: Edge | null) => void;
  onDeleteNode?: (node: Node) => void; // Optional callback for external deletion handling
}

interface DeletedNodeData {
  node: Node;
  connectedEdges: Edge[];
  timestamp: number;
}

function Sidebar({ 
  selectedNode, 
  selectedEdge,
  nodes,
  edges,
  setNodes, 
  setEdges,
  setSelectedNode,
  setSelectedEdge,
  onDeleteNode
}: SidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('create');
  
  // Undo functionality state
  const [deletedNodeData, setDeletedNodeData] = useState<DeletedNodeData | null>(null);
  const [showUndoNotification, setShowUndoNotification] = useState(false);
  const undoTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-switch to edit tab when something is selected
  useState(() => {
    if ((selectedNode || selectedEdge) && activeTab === 'create') {
      setActiveTab('edit');
    }
  });

  // Cleanup undo timeout on unmount
  useEffect(() => {
    return () => {
      if (undoTimeoutRef.current) {
        clearTimeout(undoTimeoutRef.current);
      }
    };
  }, []);

  // Handle node deletion with undo functionality (for sidebar button)
  const handleDeleteNode = (nodeToDelete: Node) => {
    // Use external callback if provided, otherwise handle internally
    if (onDeleteNode) {
      onDeleteNode(nodeToDelete);
      setSelectedNode(null);
      return;
    }

    // Internal deletion handling with undo
    deleteNodeWithUndo(nodeToDelete);
  };

  // Internal function to delete node with undo functionality
  const deleteNodeWithUndo = (nodeToDelete: Node) => {
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

    // Set the deleted node data and show notification
    setDeletedNodeData(deletionData);
    setShowUndoNotification(true);

    // Remove the node and its edges
    setNodes((nds) => nds.filter((node) => node.id !== nodeToDelete.id));
    setEdges((eds) => eds.filter((edge) => 
      edge.source !== nodeToDelete.id && edge.target !== nodeToDelete.id
    ));
    setSelectedNode(null);

    // Set timeout to clear undo data after 10 seconds
    undoTimeoutRef.current = setTimeout(() => {
      setDeletedNodeData(null);
      setShowUndoNotification(false);
    }, 10000);
  };

  // Undo node deletion
  const undoNodeDeletion = () => {
    if (!deletedNodeData) return;

    // Clear the timeout
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }

    // Restore the node and its edges
    setNodes((nds) => [...nds, deletedNodeData.node]);
    setEdges((eds) => [...eds, ...deletedNodeData.connectedEdges]);

    // Clear undo data and hide notification
    setDeletedNodeData(null);
    setShowUndoNotification(false);
  };

  // Dismiss undo notification
  const dismissUndo = () => {
    if (undoTimeoutRef.current) {
      clearTimeout(undoTimeoutRef.current);
    }
    setDeletedNodeData(null);
    setShowUndoNotification(false);
  };

  return (
    <div className="w-[380px] bg-white border-l border-gray-200 flex flex-col h-full">
      <SidebarHeader />
      
      <TabNavigation activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'create' && (
          <CreateTab setNodes={setNodes} />
        )}

        {activeTab === 'edit' && (
          <EditTab 
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            nodes={nodes}
            setNodes={setNodes}
            setEdges={setEdges}
            setSelectedEdge={setSelectedEdge}
            onDeleteNode={handleDeleteNode}
          />
        )}

        {activeTab === 'connect' && (
          <ConnectTab 
            nodes={nodes}
            edges={edges}
            setEdges={setEdges}
            setSelectedEdge={setSelectedEdge}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'overview' && (
          <OverviewTab 
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            nodes={nodes}
            edges={edges}
          />
        )}
      </div>

      <UndoNotification 
        deletedNodeData={deletedNodeData}
        showUndoNotification={showUndoNotification}
        onUndo={undoNodeDeletion}
        onDismiss={dismissUndo}
      />
    </div>
  );
}

export default Sidebar; 