import { Undo2, X, Trash2 } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';

interface DeletedNodeData {
  node: Node;
  connectedEdges: Edge[];
  timestamp: number;
}

interface GlobalUndoNotificationProps {
  deletedNodeData: DeletedNodeData | null;
  onUndo: () => void;
  onDismiss: () => void;
}

export function GlobalUndoNotification({ 
  deletedNodeData, 
  onUndo, 
  onDismiss 
}: GlobalUndoNotificationProps) {
  if (!deletedNodeData) return null;

  return (
    <>
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white p-4 rounded-lg shadow-lg border border-gray-700 z-50 min-w-[320px]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1 bg-gray-700 rounded">
              <Trash2 size={16} />
            </div>
            <div>
              <p className="text-sm font-medium">
                Deleted &quot;{(deletedNodeData.node.data as any).name}&quot;
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
            className="h-full bg-blue-500 transition-all duration-[10000ms] ease-linear w-0"
            style={{ animation: 'countdown 10s linear forwards' }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Press <kbd className="px-1 py-0.5 bg-gray-700 rounded text-xs">Ctrl+Z</kbd> to undo
        </p>
      </div>

      <style jsx>{`
        @keyframes countdown {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </>
  );
} 