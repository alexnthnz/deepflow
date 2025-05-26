import { Handle, Position } from '@xyflow/react';
import { memo } from 'react';
import { Bot, Wrench, Play, Square } from 'lucide-react';

export type NodeType = 'agent' | 'tools' | 'start' | 'end';

export type ToolType = 'tavily_search' | 'google_search' | 'human_assistance' | 'crawler';

export const AVAILABLE_TOOLS: { value: ToolType; label: string }[] = [
  { value: 'tavily_search', label: 'Tavily Search' },
  { value: 'google_search', label: 'Google Search' },
  { value: 'human_assistance', label: 'Request Human Assistance' },
  { value: 'crawler', label: 'Crawler' },
];

interface BaseNodeData {
  name: string;
  description?: string;
  nodeType: NodeType;
  [key: string]: unknown; // Add index signature for XYFlow compatibility
}

export interface AgentNodeData extends BaseNodeData {
  nodeType: 'agent';
  prompt: string;
}

export interface ToolsNodeData extends BaseNodeData {
  nodeType: 'tools';
  selectedTools: ToolType[];
}

export interface SystemNodeData extends BaseNodeData {
  nodeType: 'start' | 'end';
}

export type NodeData = AgentNodeData | ToolsNodeData | SystemNodeData;

interface CustomNodeProps {
  data: NodeData;
  selected?: boolean;
}

const getNodeStyles = (nodeType: NodeType, selected: boolean) => {
  const baseStyles = "px-4 py-2 shadow-md rounded-md border-2 min-w-[120px] transition-all duration-200";
  
  switch (nodeType) {
    case 'agent':
      return `${baseStyles} bg-gradient-to-br from-blue-50 to-blue-100 ${
        selected 
          ? 'border-blue-500 shadow-lg ring-2 ring-blue-200' 
          : 'border-blue-300 hover:border-blue-400'
      }`;
    case 'tools':
      return `${baseStyles} bg-gradient-to-br from-green-50 to-green-100 ${
        selected 
          ? 'border-green-500 shadow-lg ring-2 ring-green-200' 
          : 'border-green-300 hover:border-green-400'
      }`;
    case 'start':
      return `${baseStyles} bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-400 ${
        selected 
          ? 'shadow-lg ring-2 ring-emerald-200' 
          : 'hover:shadow-lg'
      } border-dashed`;
    case 'end':
      return `${baseStyles} bg-gradient-to-br from-red-50 to-red-100 border-red-400 ${
        selected 
          ? 'shadow-lg ring-2 ring-red-200' 
          : 'hover:shadow-lg'
      } border-dashed`;
    default:
      return `${baseStyles} bg-white ${
        selected 
          ? 'border-gray-500 shadow-lg ring-2 ring-gray-200' 
          : 'border-gray-200 hover:border-gray-300'
      }`;
  }
};

const getNodeIcon = (nodeType: NodeType) => {
  switch (nodeType) {
    case 'agent':
      return <Bot size={16} className="text-blue-600" />;
    case 'tools':
      return <Wrench size={16} className="text-green-600" />;
    case 'start':
      return <Play size={16} className="text-emerald-600" />;
    case 'end':
      return <Square size={16} className="text-red-600" />;
    default:
      return null;
  }
};

const getTextColor = (nodeType: NodeType, selected: boolean) => {
  if (selected) {
    switch (nodeType) {
      case 'agent':
        return 'text-blue-700';
      case 'tools':
        return 'text-green-700';
      case 'start':
        return 'text-emerald-700';
      case 'end':
        return 'text-red-700';
      default:
        return 'text-gray-700';
    }
  }
  return 'text-gray-800';
};

const getHandleColor = (nodeType: NodeType) => {
  switch (nodeType) {
    case 'agent':
      return '!bg-blue-500 hover:!bg-blue-600';
    case 'tools':
      return '!bg-green-500 hover:!bg-green-600';
    case 'start':
      return '!bg-emerald-500 hover:!bg-emerald-600';
    case 'end':
      return '!bg-red-500 hover:!bg-red-600';
    default:
      return '!bg-gray-500 hover:!bg-gray-600';
  }
};

const CustomNode = memo(({ data, selected }: CustomNodeProps) => {
  const nodeStyles = getNodeStyles(data.nodeType, selected || false);
  const textColor = getTextColor(data.nodeType, selected || false);
  const handleColor = getHandleColor(data.nodeType);
  const icon = getNodeIcon(data.nodeType);

  return (
    <div className={nodeStyles}>
      {/* Left handle (target/input) - hide for start nodes */}
      {data.nodeType !== 'start' && (
        <Handle
          type="target"
          position={Position.Left}
          id="input"
          className={`w-3 h-3 ${handleColor} border-2 border-white transition-colors`}
          style={{ left: -6 }}
        />
      )}
      
      {/* Node content */}
      <div className="text-center">
        <div className={`flex items-center justify-center gap-2 text-sm font-bold transition-colors ${textColor}`}>
          {icon}
          <span>{data.name}</span>
        </div>
        {data.description && (
          <div className="text-xs text-gray-500 mt-1 max-w-[100px] truncate">
            {data.description}
          </div>
        )}
        {/* Node type badge */}
        <div className="text-xs font-medium mt-1 opacity-60 uppercase tracking-wide">
          {data.nodeType}
        </div>
      </div>

      {/* Right handle (source/output) - hide for end nodes */}
      {data.nodeType !== 'end' && (
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          className={`w-3 h-3 ${handleColor} border-2 border-white transition-colors`}
          style={{ right: -6 }}
        />
      )}
    </div>
  );
});

CustomNode.displayName = 'CustomNode';

export default CustomNode; 