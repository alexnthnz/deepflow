import { Trash2, Unlink, MousePointer, Bot, Wrench, Play, Square, X } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeType, ToolType, NodeData, AgentNodeData, ToolsNodeData } from '../node';
import { AVAILABLE_TOOLS } from '../node';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface EditTabProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  nodes: Node[];
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
  setSelectedEdge: (edge: Edge | null) => void;
  onDeleteNode?: (node: Node) => void;
}

const ALL_NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'agent', label: 'Agent', icon: <Bot size={16} />, color: 'text-blue-600' },
  { value: 'tools', label: 'Tools', icon: <Wrench size={16} />, color: 'text-green-600' },
  { value: 'start', label: 'Start', icon: <Play size={16} />, color: 'text-emerald-600' },
  { value: 'end', label: 'End', icon: <Square size={16} />, color: 'text-red-600' },
];

export function EditTab({ 
  selectedNode, 
  selectedEdge, 
  nodes, 
  setNodes, 
  setEdges, 
  setSelectedEdge, 
  onDeleteNode 
}: EditTabProps) {
  // Get node type info
  const getNodeTypeInfo = (nodeType: NodeType) => {
    return ALL_NODE_TYPES.find(type => type.value === nodeType) || ALL_NODE_TYPES[0];
  };

  // Update node data
  const updateNodeData = (field: string, value: string | NodeType | ToolType[]) => {
    if (!selectedNode) return;

    setNodes((nds) =>
      nds.map((node) =>
        node.id === selectedNode.id
          ? { ...node, data: { ...node.data, [field]: value } }
          : node
      )
    );
  };

  // Update edge source or target
  const updateEdgeConnection = (field: 'source' | 'target', nodeId: string) => {
    if (!selectedEdge) return;

    // Prevent self-connections
    if (field === 'source' && nodeId === selectedEdge.target) return;
    if (field === 'target' && nodeId === selectedEdge.source) return;

    setEdges((eds) =>
      eds.map((edge) =>
        edge.id === selectedEdge.id
          ? { ...edge, [field]: nodeId }
          : edge
      )
    );

    // Update the selected edge to reflect the change
    setSelectedEdge({ ...selectedEdge, [field]: nodeId });
  };

  // Remove selected node (prevent deletion of start/end nodes)
  const removeNode = () => {
    if (!selectedNode) return;
    
    if (selectedNode.data.nodeType === 'start' || selectedNode.data.nodeType === 'end') {
      return;
    }

    // Use external callback if provided
    if (onDeleteNode) {
      onDeleteNode(selectedNode);
      return;
    }
  };

  // Remove selected edge
  const removeEdge = () => {
    if (!selectedEdge) return;
    setEdges((eds) => eds.filter((edge) => edge.id !== selectedEdge.id));
    setSelectedEdge(null);
  };

  // Handle tool selection for existing tools node
  const handleExistingToolToggle = (tool: ToolType) => {
    if (!selectedNode || !currentNode || currentNode.data.nodeType !== 'tools') return;
    
    const currentTools = (currentNode.data as ToolsNodeData).selectedTools || [];
    const newTools = currentTools.includes(tool)
      ? currentTools.filter((t: ToolType) => t !== tool)
      : [...currentTools, tool];
    
    updateNodeData('selectedTools', newTools);
  };

  // Get the current node data from the nodes array to ensure we have the latest data
  const currentNode = selectedNode ? nodes.find(n => n.id === selectedNode.id) : null;
  const nodeData = currentNode?.data as NodeData;

  return (
    <div className="p-4 space-y-6">
      {selectedNode && currentNode ? (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className={`p-2 rounded-md bg-gray-100`}>
              <div className={getNodeTypeInfo(nodeData.nodeType).color}>
                {getNodeTypeInfo(nodeData.nodeType).icon}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Edit Node</h3>
              <p className="text-sm text-gray-600">
                {getNodeTypeInfo(nodeData.nodeType).label}: {nodeData.name}
              </p>
            </div>
          </div>

          {(() => {
            const isSystemNode = nodeData.nodeType === 'start' || nodeData.nodeType === 'end';
            
            return (
              <div className="space-y-4">
                {isSystemNode && (
                  <div className="bg-amber-50 border border-amber-200 rounded-md p-3 mb-4">
                    <p className="text-sm text-amber-700">
                      <strong>System Node:</strong> This node is part of the workflow structure and has limited editing options.
                    </p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    value={nodeData.name || ''}
                    onChange={(e) => updateNodeData('name', e.target.value)}
                    className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter node name"
                    readOnly={isSystemNode}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={nodeData.description || ''}
                    onChange={(e) => updateNodeData('description', e.target.value)}
                    className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter node description"
                    rows={2}
                    readOnly={isSystemNode}
                  />
                </div>

                {/* Agent-specific fields */}
                {nodeData.nodeType === 'agent' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Agent Instructions
                    </label>
                    <div className="border border-gray-300 rounded-md overflow-hidden">
                      <MDEditor
                        value={(nodeData as AgentNodeData).prompt || ''}
                        onChange={(value) => updateNodeData('prompt', value || '')}
                        preview="edit"
                        hideToolbar={false}
                        height={200}
                        data-color-mode="light"
                        textareaProps={{
                          placeholder: "Define what this agent should do...\n\nYou can use **markdown** formatting:\n- **Bold text**\n- *Italic text*\n- `Code snippets`\n- Lists and more!"
                        }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Provide clear instructions for the AI agent&apos;s behavior and goals. Markdown formatting is supported.
                    </p>
                  </div>
                )}

                {/* Tools-specific fields */}
                {nodeData.nodeType === 'tools' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Available Tools
                    </label>
                    <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-md p-3">
                      {AVAILABLE_TOOLS.map((tool) => {
                        const isSelected = ((nodeData as ToolsNodeData).selectedTools || []).includes(tool.value);
                        return (
                          <label key={tool.value} className="flex items-center space-x-3 cursor-pointer p-2 rounded hover:bg-gray-50">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleExistingToolToggle(tool.value)}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700 flex-1">{tool.label}</span>
                          </label>
                        );
                      })}
                    </div>
                    {((nodeData as ToolsNodeData).selectedTools || []).length > 0 && (
                      <div className="mt-3">
                        <div className="text-xs text-gray-500 mb-2">
                          Selected ({((nodeData as ToolsNodeData).selectedTools || []).length}):
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {((nodeData as ToolsNodeData).selectedTools || []).map((toolValue: ToolType) => {
                            const tool = AVAILABLE_TOOLS.find(t => t.value === toolValue);
                            return (
                              <span key={toolValue} className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                {tool?.label}
                                <button
                                  onClick={() => handleExistingToolToggle(toolValue)}
                                  className="hover:text-green-900"
                                >
                                  <X size={12} />
                                </button>
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* RAG Data Source Input */}
                    {((nodeData as ToolsNodeData).selectedTools || []).includes('rag') && (
                      <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-md">
                        <label className="block text-sm font-medium text-purple-700 mb-2">
                          RAG Data Source *
                        </label>
                        <input
                          type="text"
                          value={(nodeData as ToolsNodeData).ragDataSource || ''}
                          onChange={(e) => updateNodeData('ragDataSource', e.target.value)}
                          className="w-full rounded-md border border-purple-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                          placeholder="Enter data source URL or path"
                        />
                        <p className="text-xs text-purple-600 mt-1">
                          Specify the data source for RAG (e.g., document URL, database connection, file path)
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {!isSystemNode && (
                  <button
                    onClick={removeNode}
                    className="w-full bg-red-600 text-white px-4 py-3 rounded-md hover:bg-red-700 flex items-center justify-center gap-2 font-medium"
                  >
                    <Trash2 size={16} />
                    Delete Node
                  </button>
                )}
              </div>
            );
          })()}
        </div>
      ) : selectedEdge ? (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Connection</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Node
              </label>
              <Select
                value={selectedEdge.source}
                onValueChange={(value) => updateEdgeConnection('source', value)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose source node..." />
                </SelectTrigger>
                <SelectContent>
                  {nodes.map((node) => {
                    const nodeData = node.data as NodeData;
                    const typeInfo = getNodeTypeInfo(nodeData.nodeType);
                    const isDisabled = node.id === selectedEdge.target; // Prevent self-connection
                    
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
                <Unlink size={16} className="text-gray-600" />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Node
              </label>
              <Select
                value={selectedEdge.target}
                onValueChange={(value) => updateEdgeConnection('target', value)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose target node..." />
                </SelectTrigger>
                <SelectContent>
                  {nodes.map((node) => {
                    const nodeData = node.data as NodeData;
                    const typeInfo = getNodeTypeInfo(nodeData.nodeType);
                    const isDisabled = node.id === selectedEdge.source; // Prevent self-connection
                    
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
            
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-sm text-blue-800">
                <strong>Connection Info:</strong> You can change the source and target nodes of this connection. 
                Self-connections are not allowed.
              </p>
            </div>
            
            <button
              onClick={removeEdge}
              className="w-full bg-red-600 text-white px-4 py-3 rounded-md hover:bg-red-700 flex items-center justify-center gap-2 font-medium"
            >
              <Unlink size={16} />
              Remove Connection
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <MousePointer className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nothing Selected</h3>
          <p className="text-gray-600">Click on a node or connection to edit its properties</p>
        </div>
      )}
    </div>
  );
} 