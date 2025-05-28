import { useState } from 'react';
import { Plus, Bot, Wrench, X } from 'lucide-react';
import type { NodeType, ToolType, NodeData } from '../node';
import { AVAILABLE_TOOLS } from '../node';
import MDEditor from '@uiw/react-md-editor';
import '@uiw/react-md-editor/markdown-editor.css';
import { Node } from '@xyflow/react';

interface CreateTabProps {
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
}

const NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string; description: string }[] = [
  { 
    value: 'agent', 
    label: 'Agent', 
    icon: <Bot size={16} />, 
    color: 'text-blue-600',
    description: 'AI agent with custom instructions'
  },
  { 
    value: 'tools', 
    label: 'Tools', 
    icon: <Wrench size={16} />, 
    color: 'text-green-600',
    description: 'Collection of available tools'
  },
];

const ALL_NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'agent', label: 'Agent', icon: <Bot size={16} />, color: 'text-blue-600' },
  { value: 'tools', label: 'Tools', icon: <Wrench size={16} />, color: 'text-green-600' },
  { value: 'start', label: 'Start', icon: <Plus size={16} />, color: 'text-emerald-600' },
  { value: 'end', label: 'End', icon: <X size={16} />, color: 'text-red-600' },
];

export function CreateTab({ setNodes }: CreateTabProps) {
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeDescription, setNewNodeDescription] = useState('');
  const [newNodeType, setNewNodeType] = useState<NodeType>('agent');
  const [newAgentPrompt, setNewAgentPrompt] = useState('');
  const [newToolsSelection, setNewToolsSelection] = useState<ToolType[]>([]);

  // Get node type info
  const getNodeTypeInfo = (nodeType: NodeType) => {
    return ALL_NODE_TYPES.find(type => type.value === nodeType) || ALL_NODE_TYPES[0];
  };

  // Handle tool selection for new tools node
  const handleNewToolToggle = (tool: ToolType) => {
    setNewToolsSelection(prev => 
      prev.includes(tool) 
        ? prev.filter(t => t !== tool)
        : [...prev, tool]
    );
  };

  // Add a new node
  const addNode = () => {
    if (!newNodeName.trim()) return;

    let nodeData: NodeData;
    
    if (newNodeType === 'agent') {
      nodeData = {
        name: newNodeName,
        description: newNodeDescription || undefined,
        nodeType: 'agent',
        prompt: newAgentPrompt
      };
    } else if (newNodeType === 'tools') {
      nodeData = {
        name: newNodeName,
        description: newNodeDescription || undefined,
        nodeType: 'tools',
        selectedTools: newToolsSelection
      };
    } else {
      nodeData = {
        name: newNodeName,
        description: newNodeDescription || undefined,
        nodeType: newNodeType
      } as NodeData;
    }

    const newNode: Node = {
      id: `node-${Date.now()}`,
      position: { 
        x: Math.random() * 400 + 100, 
        y: Math.random() * 300 + 100 
      },
      data: nodeData,
      type: 'custom',
    };

    setNodes((nds) => [...nds, newNode]);
    
    // Reset form
    setNewNodeName('');
    setNewNodeDescription('');
    setNewNodeType('agent');
    setNewAgentPrompt('');
    setNewToolsSelection([]);
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Add New Node</h3>
        <p className="text-sm text-gray-600 mb-4">Choose a node type and configure its properties</p>
      </div>

      {/* Node Type Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Choose Node Type
        </label>
        <div className="grid grid-cols-1 gap-3">
          {NODE_TYPES.map((type) => (
            <button
              key={type.value}
              onClick={() => setNewNodeType(type.value)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                newNodeType === type.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-md ${
                  newNodeType === type.value ? 'bg-blue-100' : 'bg-gray-100'
                }`}>
                  <div className={type.color}>
                    {type.icon}
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{type.label}</h4>
                  <p className="text-sm text-gray-600 mt-1">{type.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Node Configuration */}
      <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900">Configure {getNodeTypeInfo(newNodeType).label}</h4>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Name *
          </label>
          <input
            type="text"
            value={newNodeName}
            onChange={(e) => setNewNodeName(e.target.value)}
            className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder={`Enter ${newNodeType} name`}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={newNodeDescription}
            onChange={(e) => setNewNodeDescription(e.target.value)}
            className="w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Brief description (optional)"
            rows={2}
          />
        </div>

        {/* Agent-specific fields */}
        {newNodeType === 'agent' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agent Instructions *
            </label>
            <div className="border border-gray-300 rounded-md overflow-hidden">
              <MDEditor
                value={newAgentPrompt}
                onChange={(value) => setNewAgentPrompt(value || '')}
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
        {newNodeType === 'tools' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Available Tools *
            </label>
            <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-md p-3">
              {AVAILABLE_TOOLS.map((tool) => (
                <label key={tool.value} className="flex items-center space-x-3 cursor-pointer p-2 rounded hover:bg-gray-50">
                  <input
                    type="checkbox"
                    checked={newToolsSelection.includes(tool.value)}
                    onChange={() => handleNewToolToggle(tool.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 flex-1">{tool.label}</span>
                </label>
              ))}
            </div>
            {newToolsSelection.length > 0 && (
              <div className="mt-3">
                <div className="text-xs text-gray-500 mb-2">Selected ({newToolsSelection.length}):</div>
                <div className="flex flex-wrap gap-2">
                  {newToolsSelection.map((toolValue) => {
                    const tool = AVAILABLE_TOOLS.find(t => t.value === toolValue);
                    return (
                      <span key={toolValue} className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                        {tool?.label}
                        <button
                          onClick={() => handleNewToolToggle(toolValue)}
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
          </div>
        )}
        
        <button
          onClick={addNode}
          disabled={
            !newNodeName.trim() || 
            (newNodeType === 'agent' && !newAgentPrompt.trim()) ||
            (newNodeType === 'tools' && newToolsSelection.length === 0)
          }
          className="w-full bg-blue-600 text-white px-4 py-3 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
        >
          <Plus size={16} />
          Create {getNodeTypeInfo(newNodeType).label}
        </button>
      </div>
    </div>
  );
} 