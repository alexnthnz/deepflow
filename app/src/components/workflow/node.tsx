import { Handle, Position } from '@xyflow/react';
import { memo } from 'react';
import { Bot, Wrench, Play, Square } from 'lucide-react';

export type NodeType = 'agent' | 'tools' | 'start' | 'end';
export type LayoutDirection = 'horizontal' | 'vertical';

export type ToolType = 'tavily_search' | 'google_search' | 'human_assistance' | 'crawler' | 'rag';

export const AVAILABLE_TOOLS: { value: ToolType; label: string }[] = [
  { value: 'tavily_search', label: 'Tavily Search' },
  { value: 'google_search', label: 'Google Search' },
  { value: 'human_assistance', label: 'Request Human Assistance' },
  { value: 'crawler', label: 'Crawler' },
  { value: 'rag', label: 'RAG' },
];

// Configuration for connection points per node type
export interface ConnectionConfig {
  inputs: Array<{
    id: string;
    position: Position;
    style?: React.CSSProperties;
    label?: string;
  }>;
  outputs: Array<{
    id: string;
    position: Position;
    style?: React.CSSProperties;
    label?: string;
  }>;
}

// Default connection configurations for each node type based on layout direction
const getConnectionConfig = (nodeType: NodeType, layoutDirection: LayoutDirection = 'horizontal'): ConnectionConfig => {
  switch (nodeType) {
    case 'start':
      return {
        inputs: [], // Start nodes have no inputs
        outputs: [
          layoutDirection === 'horizontal' 
            ? { id: 'output', position: Position.Right }
            : { id: 'output', position: Position.Bottom, style: { bottom: -6 } }
        ],
      };
    case 'agent':
      return {
        inputs: [
          layoutDirection === 'horizontal'
            ? { id: 'input', position: Position.Left }
            : { id: 'input', position: Position.Top, style: { top: -6 } }
        ],
        outputs: [
          layoutDirection === 'horizontal'
            ? { id: 'output', position: Position.Right, style: { right: -6 } }
            : { id: 'output', position: Position.Bottom, style: { bottom: -6 } }
        ],
      };
    case 'tools':
      return {
        inputs: [
          layoutDirection === 'horizontal'
            ? { id: 'input', position: Position.Left }
            : { id: 'input', position: Position.Top, style: { top: -6 } }
        ],
        outputs: [
          layoutDirection === 'horizontal'
            ? { id: 'output', position: Position.Right, style: { right: -6 } }
            : { id: 'output', position: Position.Bottom, style: { bottom: -6 } }
        ],
      };
    case 'end':
      return {
        inputs: [
          layoutDirection === 'horizontal'
            ? { id: 'input', position: Position.Left }
            : { id: 'input', position: Position.Top, style: { top: -6 } }
        ],
        outputs: [], // End nodes have no outputs
      };
    default:
      return {
        inputs: [
          layoutDirection === 'horizontal'
            ? { id: 'input', position: Position.Left }
            : { id: 'input', position: Position.Top, style: { top: -6 } }
        ],
        outputs: [
          layoutDirection === 'horizontal'
            ? { id: 'output', position: Position.Right, style: { right: -6 } }
            : { id: 'output', position: Position.Bottom, style: { bottom: -6 } }
        ],
      };
  }
};

interface BaseNodeData {
  name: string;
  description?: string;
  nodeType: NodeType;
  layoutDirection?: LayoutDirection;
  // Optional custom connection configuration
  connectionConfig?: ConnectionConfig;
  [key: string]: unknown; // Add index signature for XYFlow compatibility
}

export interface AgentNodeData extends BaseNodeData {
  nodeType: 'agent';
  prompt: string;
}

export interface ToolsNodeData extends BaseNodeData {
  nodeType: 'tools';
  selectedTools: ToolType[];
  ragDataSource?: string; // Data source for RAG tool
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
  const baseStyles = "px-4 py-3 shadow-md rounded-md border-2 min-w-[140px] min-h-[80px] transition-all duration-200 relative";
  
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
  
  // Get connection configuration (use custom config if provided, otherwise use default with layout direction)
  const connectionConfig = data.connectionConfig || getConnectionConfig(data.nodeType, data.layoutDirection || 'horizontal');

  return (
    <div className={nodeStyles}>
      {/* Render input handles */}
      {connectionConfig.inputs.map((input) => (
        <Handle
          key={`input-${input.id}`}
          type="target"
          position={input.position}
          id={input.id}
          className={`w-3 h-3 ${handleColor} border-2 border-white transition-colors`}
          style={{
            // Default positioning based on position
            ...(input.position === Position.Left && { left: -6 }),
            ...(input.position === Position.Right && { right: -6 }),
            ...(input.position === Position.Top && { top: -6 }),
            ...(input.position === Position.Bottom && { bottom: -6 }),
            // Override with custom styles if provided
            ...input.style,
          }}
        />
      ))}
      
      {/* Node content */}
      <div className="text-center flex flex-col items-center justify-center h-full">
        <div className={`flex items-center justify-center gap-2 text-sm font-bold transition-colors ${textColor}`}>
          {icon}
          <span>{data.name}</span>
        </div>
        {data.description && (
          <div className="text-xs text-gray-500 mt-1 max-w-[120px] truncate">
            {data.description}
          </div>
        )}
        {/* Node type badge */}
        <div className="text-xs font-medium mt-1 opacity-60 uppercase tracking-wide">
          {data.nodeType}
        </div>
      </div>

      {/* Render output handles */}
      {connectionConfig.outputs.map((output) => (
        <Handle
          key={`output-${output.id}`}
          type="source"
          position={output.position}
          id={output.id}
          className={`w-3 h-3 ${handleColor} border-2 border-white transition-colors`}
          style={{
            // Default positioning based on position
            ...(output.position === Position.Left && { left: -6 }),
            ...(output.position === Position.Right && { right: -6 }),
            ...(output.position === Position.Top && { top: -6 }),
            ...(output.position === Position.Bottom && { bottom: -6 }),
            // Override with custom styles if provided
            ...output.style,
          }}
        />
      ))}
    </div>
  );
});

CustomNode.displayName = 'CustomNode';

export default CustomNode; 