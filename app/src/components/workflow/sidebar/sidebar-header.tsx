import { Layers } from 'lucide-react';

export function SidebarHeader() {
  return (
    <div className="p-4 border-b border-gray-200 bg-gray-50">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Layers size={20} />
        Workflow Builder
      </h2>
      <p className="text-sm text-gray-600 mt-1">Design your AI agent workflow</p>
    </div>
  );
} 