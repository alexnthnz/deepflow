import { Plus, Edit3, Link, BarChart3 } from 'lucide-react';

export type TabType = 'create' | 'edit' | 'connect' | 'overview';

interface TabNavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

const tabs = [
  { id: 'create' as TabType, label: 'Create', icon: <Plus size={16} />, description: 'Add new nodes' },
  { id: 'edit' as TabType, label: 'Edit', icon: <Edit3 size={16} />, description: 'Modify selection' },
  { id: 'connect' as TabType, label: 'Connect', icon: <Link size={16} />, description: 'Link nodes' },
  { id: 'overview' as TabType, label: 'Overview', icon: <BarChart3 size={16} />, description: 'View stats' },
];

export function TabNavigation({ activeTab, setActiveTab }: TabNavigationProps) {
  return (
    <div className="border-b border-gray-200 bg-white">
      <nav className="flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-3 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
            title={tab.description}
          >
            <div className="flex items-center justify-center gap-1">
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
            </div>
          </button>
        ))}
      </nav>
    </div>
  );
} 