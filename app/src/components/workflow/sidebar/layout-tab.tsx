import { useState } from 'react';
import { LayoutGrid, RefreshCw, ArrowRight, ArrowDown, ArrowLeft, ArrowUp } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import { getLayoutedElements, layoutDirections, updateLayoutDirection } from '@/lib/layout-utils';

interface LayoutTabProps {
  nodes: Node[];
  edges: Edge[];
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
}

const directionIcons = {
  'RIGHT': <ArrowRight size={16} />,
  'DOWN': <ArrowDown size={16} />,
  'LEFT': <ArrowLeft size={16} />,
  'UP': <ArrowUp size={16} />,
};

const edgeTypes = [
  { value: 'default', label: 'Bezier', description: 'Smooth curved edges (default)' },
  { value: 'straight', label: 'Straight', description: 'Direct straight lines' },
  { value: 'step', label: 'Step', description: 'Right-angled step edges' },
  { value: 'smoothstep', label: 'Smooth Step', description: 'Rounded step edges' },
  { value: 'simplebezier', label: 'Simple Bezier', description: 'Simple curved edges' },
] as const;

export function LayoutTab({ nodes, edges, setNodes, setEdges }: LayoutTabProps) {
  const [isLayouting, setIsLayouting] = useState(false);
  const [layoutDirection, setLayoutDirection] = useState<keyof typeof layoutDirections>('RIGHT');
  const [selectedEdgeType, setSelectedEdgeType] = useState<string>('smoothstep');

  const applyLayoutAndEdgeType = async () => {
    if (nodes.length === 0) return;
    
    setIsLayouting(true);
    try {
      // Apply layout first
      updateLayoutDirection(layoutDirection);
      const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(nodes, edges);
      
      // Apply edge type to all edges (both existing and layouted)
      const edgesWithType = layoutedEdges.map((edge) => ({
        ...edge,
        type: selectedEdgeType,
      }));
      
      setNodes(layoutedNodes);
      setEdges(edgesWithType);
    } catch (error) {
      console.error('Layout failed:', error);
    } finally {
      setIsLayouting(false);
    }
  };

  const handleDirectionChange = (direction: keyof typeof layoutDirections) => {
    setLayoutDirection(direction);
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Auto Layout & Styling</h3>
        <p className="text-sm text-gray-600 mb-4">Configure layout direction and edge style, then apply both together</p>
      </div>

      <div className="space-y-6">
        {/* Layout Direction Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Layout Direction
          </label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(layoutDirections).map(([key, label]) => (
              <button
                key={key}
                onClick={() => handleDirectionChange(key as keyof typeof layoutDirections)}
                className={`flex items-center justify-center gap-2 p-3 rounded-md border transition-colors ${
                  layoutDirection === key
                    ? 'bg-blue-50 border-blue-300 text-blue-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {directionIcons[key as keyof typeof directionIcons]}
                <span className="text-xs font-medium">{label.split(' ')[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Edge Type Configuration Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Edge Style
          </label>
          <div className="space-y-2">
            {edgeTypes.map((edgeType) => (
              <button
                key={edgeType.value}
                onClick={() => setSelectedEdgeType(edgeType.value)}
                className={`w-full text-left p-3 rounded-md border transition-colors ${
                  selectedEdgeType === edgeType.value
                    ? 'bg-green-50 border-green-300 text-green-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-sm">{edgeType.label}</div>
                    <div className="text-xs text-gray-500">{edgeType.description}</div>
                  </div>
                  {selectedEdgeType === edgeType.value && (
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Combined Apply Button */}
        <div className="pt-2">
          <button
            onClick={applyLayoutAndEdgeType}
            disabled={isLayouting || nodes.length === 0}
            className="w-full bg-gradient-to-r from-purple-600 to-green-600 text-white px-4 py-3 rounded-md hover:from-purple-700 hover:to-green-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium transition-all duration-200 shadow-md"
          >
            {isLayouting ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <LayoutGrid size={16} />
            )}
            {isLayouting ? 'Applying Layout & Style...' : 'Apply Layout & Edge Style'}
          </button>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Arranges nodes in {layoutDirections[layoutDirection].toLowerCase()} direction with {edgeTypes.find(e => e.value === selectedEdgeType)?.label.toLowerCase()} edges
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-start gap-2">
            <LayoutGrid size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Layout Tips:</p>
              <ul className="text-xs space-y-1 text-blue-700">
                <li>• Choose your preferred direction and edge style first</li>
                <li>• Single click applies both layout and styling</li>
                <li>• You can still manually adjust positions after</li>
                <li>• Works best with connected workflows</li>
              </ul>
            </div>
          </div>
        </div>

        {nodes.length === 0 && (
          <div className="text-center py-4">
            <LayoutGrid size={24} className="text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Add some nodes to use auto layout</p>
          </div>
        )}
      </div>
    </div>
  );
} 