import { Plus, Edit3, Link, BarChart3, LayoutGrid } from 'lucide-react';

export type TabType = 'create' | 'edit' | 'connect' | 'layout' | 'overview';

interface TabNavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

const tabs = [
  { id: 'create' as TabType, label: 'Create', icon: <Plus size={18} />, description: 'Add new nodes' },
  { id: 'edit' as TabType, label: 'Edit', icon: <Edit3 size={18} />, description: 'Modify selection' },
  { id: 'connect' as TabType, label: 'Connect', icon: <Link size={18} />, description: 'Link nodes' },
  { id: 'layout' as TabType, label: 'Layout', icon: <LayoutGrid size={18} />, description: 'Auto arrange' },
  { id: 'overview' as TabType, label: 'Overview', icon: <BarChart3 size={18} />, description: 'View stats' },
];

export function TabNavigation({ activeTab, setActiveTab }: TabNavigationProps) {
  return (
    <div className="border-b border-gray-200 bg-white">
      <nav className="flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-2 py-3 text-sm font-medium border-b-2 transition-all duration-200 group relative ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            title={`${tab.label} - ${tab.description}`}
          >
            <div className="flex flex-col items-center justify-center gap-1">
              <div className={`transition-transform duration-200 ${
                activeTab === tab.id ? 'scale-110' : 'group-hover:scale-105'
              }`}>
                {tab.icon}
              </div>
              <span className="text-xs font-medium leading-none">{tab.label}</span>
            </div>
            
            {/* Tooltip for better UX */}
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
              {tab.description}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
          </button>
        ))}
      </nav>
    </div>
  );
} 