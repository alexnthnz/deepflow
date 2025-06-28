'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Settings, Cog, Network, Info, X, Plus, ExternalLink, GitBranch, Loader2, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { addMCPServerConfig, getCachedMCPConfigs, validateMCPConfig, deleteMCPConfig } from '@/actions/mcp';
import type { MCPCachedConfig, MCPServerConfig } from '@/types/mcp';

type SettingsTab = {
  id: string;
  label: string;
  icon: React.ReactNode;
  content: React.ReactNode;
};

function AddMCPServerDialog({ onServerAdded }: { onServerAdded?: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [configText, setConfigText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddServer = async () => {
    if (!configText.trim()) {
      setError('Please enter a valid MCP server configuration');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Parse the JSON config
      let config: MCPServerConfig;
      try {
        config = JSON.parse(configText);
      } catch (e) {
        throw new Error('Invalid JSON format. Please check your configuration.');
      }

      // Validate the config format
      const validation = await validateMCPConfig(config);
      if (!validation.success) {
        throw new Error(validation.error || 'Invalid configuration format');
      }

      // Add the MCP server
      const result = await addMCPServerConfig(config);
      
      if (result.success && result.data) {
        toast.success(`MCP server "${result.data.server_name}" added successfully!`, {
          description: `Discovered ${result.data.tools_discovered} tools`,
        });
        
        // Reset form and close dialog
        setConfigText('');
        setIsOpen(false);
        
        // Trigger refresh of cached configs
        onServerAdded?.();
      } else {
        throw new Error(result.error || 'Failed to add MCP server');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add MCP server';
      setError(errorMessage);
      toast.error('Failed to add MCP server', {
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (!open) {
      // Reset form when closing
      setConfigText('');
      setError(null);
    }
  };

  const exampleConfig = {
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
    timeout_seconds: 30
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add New MCP Server
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-w-[90vw] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Add New MCP Server</DialogTitle>
          <DialogDescription>
            DeepFlow uses the standard JSON MCP config to create a new server. Paste your config below and click &quot;Add&quot; to add new servers.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 overflow-hidden">
          <div className="space-y-2">
            <Label htmlFor="mcp-config">MCP Server Configuration (JSON)</Label>
            <Textarea 
              id="mcp-config"
              placeholder="Paste your MCP server config here..."
              className="min-h-[200px] max-h-[300px] font-mono text-sm resize-none w-full"
              style={{ maxWidth: '100%', overflow: 'auto' }}
              value={configText}
              onChange={(e) => setConfigText(e.target.value)}
            />
            {error && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>
          
          <div className="rounded-lg bg-gray-50 p-3">
            <Label className="text-xs font-medium text-gray-600">Example Configuration:</Label>
            <pre className="mt-1 text-xs text-gray-700 overflow-x-auto">
              {JSON.stringify(exampleConfig, null, 2)}
            </pre>
          </div>
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => setIsOpen(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleAddServer}
            disabled={isLoading || !configText.trim()}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Add Server
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function MCPServerList({ configs, onRefresh }: { configs: MCPCachedConfig[]; onRefresh: () => void }) {
  const [deletingServer, setDeletingServer] = useState<string | null>(null);

  const handleDeleteServer = async (serverName: string) => {
    setDeletingServer(serverName);
    
    try {
      const result = await deleteMCPConfig(serverName);
      
      if (result.success) {
        toast.success(`MCP server "${serverName}" deleted successfully!`);
        onRefresh(); // Refresh the list after deletion
      } else {
        throw new Error(result.error || 'Failed to delete MCP server');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete MCP server';
      toast.error('Failed to delete MCP server', {
        description: errorMessage,
      });
    } finally {
      setDeletingServer(null);
    }
  };
  if (configs.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-sm">No MCP servers configured yet.</p>
        <p className="text-xs mt-1">Add your first MCP server to get started.</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'working':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'inactive':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-3">
      {configs.map((config) => (
        <div
          key={config.cache_key}
          className="rounded-lg border p-4 space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon(config.status)}
              <h4 className="font-medium">{config.name || config.server_name}</h4>
              <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                {config.transport}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {config.tools_count} tools
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                disabled={deletingServer === config.server_name}
                onClick={() => handleDeleteServer(config.server_name)}
              >
                {deletingServer === config.server_name ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground space-y-1">
            {config.command && (
              <div>
                <span className="font-medium">Command:</span> {config.command}
                {config.args && config.args.length > 0 && (
                  <span className="ml-1">{config.args.join(' ')}</span>
                )}
              </div>
            )}
            {config.url && (
              <div>
                <span className="font-medium">URL:</span> {config.url}
              </div>
            )}
            <div>
              <span className="font-medium">Added:</span> {formatDate(config.discovered_at)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function MCPTabContent() {
  const [configs, setConfigs] = useState<MCPCachedConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConfigs = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await getCachedMCPConfigs();
      if (result.success && result.data) {
        setConfigs(result.data.configs);
      } else {
        throw new Error(result.error || 'Failed to load MCP configurations');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load configurations';
      setError(errorMessage);
      toast.error('Failed to load MCP configurations', {
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">MCP Servers</h3>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadConfigs}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Refresh
          </Button>
          <AddMCPServerDialog onServerAdded={loadConfigs} />
        </div>
      </div>
      
      <p className="text-sm text-muted-foreground">
        The Model Context Protocol boosts DeepFlow by integrating external tools for tasks like private domain searches, web browsing, food ordering, and more.{' '}
        <a 
          href="#" 
          className="inline-flex items-center gap-1 text-primary hover:underline"
          onClick={(e) => {
            e.preventDefault();
            window.open('https://docs.deepflow.com/mcp', '_blank');
          }}
        >
          Click here to learn more about MCP
          <ExternalLink className="h-3 w-3" />
        </a>
      </p>

      {error ? (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      ) : (
        <MCPServerList configs={configs} onRefresh={loadConfigs} />
      )}
    </div>
  );
}

function WorkflowTabContent() {
  const router = useRouter();
  
  const handleOpenWorkflow = () => {
    router.push('/workflow');
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Workflow Management</h3>
        <DialogClose asChild>
          <Button
            size="sm"
            className="flex items-center gap-2"
            onClick={handleOpenWorkflow}
          >
            <GitBranch className="h-4 w-4" />
            Open Workflow
          </Button>
        </DialogClose>
      </div>
      <p className="text-sm text-muted-foreground">
        Access and manage your workflow settings and configurations. Click the button above to open the full workflow interface.
      </p>
    </div>
  );
}

const settingsTabs: SettingsTab[] = [
  {
    id: 'general',
    label: 'General',
    icon: <Cog className="h-4 w-4" />,
    content: (
      <div className="space-y-6">
        <h3 className="text-lg font-medium">General</h3>
        
        {/* Allow acceptance of plans */}
        <div className="flex items-center justify-between">
          <Label htmlFor="allow-plans" className="font-medium">Allow acceptance of plans</Label>
          <Switch id="allow-plans" />
        </div>

        {/* Max plan iteration */}
        <div className="space-y-2">
          <Label htmlFor="max-iterations" className="font-medium">Max plan iteration</Label>
          <Input 
            id="max-iterations"
            type="number"
            defaultValue={1}
            min={1}
            className="max-w-[200px]"
          />
          <p className="text-sm text-muted-foreground">
            Set to 1 for single-step planning. Set to 2 or more to enable re-planning.
          </p>
        </div>

        {/* Max steps of a research plan */}
        <div className="space-y-2">
          <Label htmlFor="max-steps" className="font-medium">Max steps of a research plan</Label>
          <Input 
            id="max-steps"
            type="number"
            min={1}
            defaultValue={3}
            className="max-w-[200px]"
          />
          <p className="text-sm text-muted-foreground">
            By default, each research plan has 3 steps.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: 'mcp',
    label: 'MCP',
    icon: <Network className="h-4 w-4" />,
    content: <MCPTabContent />,
  },
  {
    id: 'workflow',
    label: 'Workflow',
    icon: <GitBranch className="h-4 w-4" />,
    content: <WorkflowTabContent />,
  },
  {
    id: 'about',
    label: 'About',
    icon: <Info className="h-4 w-4" />,
    content: (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">About DeepFlow</h3>
        <p className="text-sm text-muted-foreground">
          Information about the application and system.
        </p>
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">Version Information</h4>
            <p className="text-sm text-muted-foreground">
              DeepFlow v1.0.0
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">System Information</h4>
            <p className="text-sm text-muted-foreground">
              Built with Next.js and Tailwind CSS
            </p>
          </div>
        </div>
      </div>
    ),
  },
];

export function SettingsDialog() {
  const [activeTab, setActiveTab] = useState(settingsTabs[0].id);

  const handleSave = () => {
    // Add save functionality here
    console.log('Saving settings...');
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[825px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-5 gap-6">
          {/* Menu List - 2/5 width */}
          <div className="col-span-2 space-y-1 border-r pr-6">
            {settingsTabs.map((tab) => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? "secondary" : "ghost"}
                className="w-full justify-start gap-2"
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                {tab.label}
              </Button>
            ))}
          </div>
          {/* Content Area - 3/5 width */}
          <div className="col-span-3 min-h-[500px]">
            {settingsTabs.find((tab) => tab.id === activeTab)?.content}
          </div>
        </div>
        <hr />
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={handleSave}>Save changes</Button>
        </DialogFooter>
        <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogClose>
      </DialogContent>
    </Dialog>
  );
} 