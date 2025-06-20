import { Link, Bot, Wrench, Play, Square, Activity, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeType, NodeData } from '../node';
import { useWorkflow } from '@/hooks/use-workflow';

interface OverviewTabProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  nodes: Node[];
  edges: Edge[];
}

const ALL_NODE_TYPES: { value: NodeType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'agent', label: 'Agent', icon: <Bot size={16} />, color: 'text-blue-600' },
  { value: 'tools', label: 'Tools', icon: <Wrench size={16} />, color: 'text-green-600' },
  { value: 'start', label: 'Start', icon: <Play size={16} />, color: 'text-emerald-600' },
  { value: 'end', label: 'End', icon: <Square size={16} />, color: 'text-red-600' },
];

const getNodeIcon = (nodeType: string) => {
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
      return <Square size={16} className="text-gray-600" />;
  }
};

export function OverviewTab({ selectedNode, selectedEdge, nodes, edges }: OverviewTabProps) {
  const workflow = useWorkflow();
  
  // Get node type info
  const getNodeTypeInfo = (nodeType: NodeType) => {
    return ALL_NODE_TYPES.find(type => type.value === nodeType) || ALL_NODE_TYPES[0];
  };

  // Get node statistics by type
  const getNodeStatsByType = () => {
    const stats = nodes.reduce((acc, node) => {
      const nodeData = node.data as NodeData;
      const nodeType = nodeData.nodeType || 'unknown';
      acc[nodeType] = (acc[nodeType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return stats;
  };

  const nodeStats = getNodeStatsByType();

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Workflow Overview</h3>
        <p className="text-sm text-gray-600 mb-4">Summary of your workflow structure and status</p>
      </div>

      {/* Workflow Status */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={16} className="text-blue-600" />
          <h4 className="font-medium text-blue-900">Workflow Status</h4>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-blue-700">Status:</span>
            <span className="font-medium">
              {workflow.hasUnsavedChanges ? (
                <span className="text-orange-600">Modified</span>
              ) : workflow.lastSaved ? (
                <span className="text-green-600">Saved</span>
              ) : (
                <span className="text-gray-500">New</span>
              )}
            </span>
          </div>
          
          {workflow.lastSaved && (
            <div className="flex justify-between">
              <span className="text-blue-700">Last Saved:</span>
              <span className="font-medium text-blue-900">
                {workflow.lastSaved.toLocaleString()}
              </span>
            </div>
          )}
          
          {workflow.validationResult && (
            <div className="flex justify-between">
              <span className="text-blue-700">Validation:</span>
              <span className={`font-medium flex items-center gap-1 ${
                workflow.validationResult.is_valid ? 'text-green-600' : 'text-red-600'
              }`}>
                {workflow.validationResult.is_valid ? (
                  <>
                    <CheckCircle size={12} />
                    Valid
                  </>
                ) : (
                  <>
                    <XCircle size={12} />
                    {workflow.validationResult.errors.length} error(s)
                  </>
                )}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Graph Statistics */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <Activity size={16} />
          Graph Statistics
        </h4>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{nodes.length}</div>
            <div className="text-xs text-gray-600">Total Nodes</div>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-600">{edges.length}</div>
            <div className="text-xs text-gray-600">Connections</div>
          </div>
        </div>
      </div>

      {/* Node Type Breakdown */}
      {Object.keys(nodeStats).length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Node Types</h4>
          <div className="space-y-2">
            {Object.entries(nodeStats).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-2">
                  {getNodeIcon(type)}
                  <span className="text-sm font-medium capitalize">{type}</span>
                </div>
                <span className="text-sm font-bold text-gray-700">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Results */}
      {workflow.validationResult && !workflow.validationResult.is_valid && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle size={16} className="text-red-600" />
            <h4 className="font-medium text-red-900">Validation Issues</h4>
          </div>
          
          {workflow.validationResult.errors.length > 0 && (
            <div className="mb-3">
              <div className="text-sm font-medium text-red-800 mb-1">Errors:</div>
              <ul className="text-sm text-red-700 space-y-1">
                {workflow.validationResult.errors.map((error, index) => (
                  <li key={index} className="flex items-start gap-1">
                    <span className="text-red-500">•</span>
                    <span>{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {workflow.validationResult.warnings.length > 0 && (
            <div>
              <div className="text-sm font-medium text-yellow-800 mb-1">Warnings:</div>
              <ul className="text-sm text-yellow-700 space-y-1">
                {workflow.validationResult.warnings.map((warning, index) => (
                  <li key={index} className="flex items-start gap-1">
                    <span className="text-yellow-500">•</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Current Selection */}
      {(selectedNode || selectedEdge) && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Current Selection</h4>
          
                     {selectedNode && (
             <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
               <div className="flex items-center gap-2 mb-2">
                 {getNodeIcon((selectedNode.data as NodeData).nodeType)}
                 <span className="font-medium text-blue-900">
                   {(selectedNode.data as NodeData).name}
                 </span>
               </div>
               <div className="text-sm text-blue-700">
                 Type: {(selectedNode.data as NodeData).nodeType}
               </div>
               {(selectedNode.data as NodeData).description && (
                 <div className="text-sm text-blue-600 mt-1">
                   {(selectedNode.data as NodeData).description}
                 </div>
               )}
             </div>
           )}
          
          {selectedEdge && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="font-medium text-green-900 mb-1">Edge Connection</div>
              <div className="text-sm text-green-700">
                From: {selectedEdge.source} → To: {selectedEdge.target}
              </div>
              {selectedEdge.label && (
                <div className="text-sm text-green-600 mt-1">
                  Label: {selectedEdge.label}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <div className="pt-4 border-t border-gray-200">
        <h4 className="font-medium text-gray-900 mb-3">Quick Actions</h4>
        <div className="space-y-2">
          <button
            onClick={() => workflow.validate(nodes, edges)}
            disabled={workflow.isValidating || nodes.length === 0}
            className="w-full text-left px-3 py-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md text-sm font-medium text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {workflow.isValidating ? 'Validating...' : 'Validate Workflow'}
          </button>
          
          <button
            onClick={() => workflow.save(nodes, edges)}
            disabled={workflow.isSaving || (!workflow.hasUnsavedChanges && !!workflow.lastSaved)}
            className="w-full text-left px-3 py-2 bg-green-50 hover:bg-green-100 border border-green-200 rounded-md text-sm font-medium text-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {workflow.isSaving ? 'Saving...' : 'Save Workflow'}
          </button>
        </div>
      </div>
    </div>
  );
} 