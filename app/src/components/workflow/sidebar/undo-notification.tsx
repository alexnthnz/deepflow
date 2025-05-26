import { Trash2, Undo2, X } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { NodeData } from '../node';

interface DeletedNodeData {
  node: Node;
  connectedEdges: Edge[];
  timestamp: number;
}

interface UndoNotificationProps {
  deletedNodeData: DeletedNodeData | null;
  showUndoNotification: boolean;
  onUndo: () => void;
  onDismiss: () => void;
}

export function UndoNotification({ 
  deletedNodeData, 
  showUndoNotification, 
  onUndo, 
  onDismiss 
}: UndoNotificationProps) {
  if (!showUndoNotification || !deletedNodeData) {
    return null;
  }

  return (
    <div className="absolute bottom-4 left-4 right-4 bg-gray-900 text-white p-4 rounded-lg shadow-lg border border-gray-700 z-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-1 bg-gray-700 rounded">
            <Trash2 size={16} />
          </div>
          <div>
            <p className="text-sm font-medium">
              Deleted "{(deletedNodeData.node.data as NodeData).name}"
            </p>
            <p className="text-xs text-gray-300">
              {deletedNodeData.connectedEdges.length} connection{deletedNodeData.connectedEdges.length !== 1 ? 's' : ''} removed
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onUndo}
            className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
          >
            <Undo2 size={14} />
            Undo
          </button>
          <button
            onClick={onDismiss}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
      <div className="mt-2 bg-gray-700 rounded-full h-1 overflow-hidden">
        <div 
          className="h-full bg-blue-500 transition-all duration-[10000ms] ease-linear"
          style={{ width: showUndoNotification ? '0%' : '100%' }}
        />
      </div>
    </div>
  );
} 