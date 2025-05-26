'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Settings, Cog, Network, Info, X, Plus, ExternalLink, GitBranch } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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

type SettingsTab = {
  id: string;
  label: string;
  icon: React.ReactNode;
  content: React.ReactNode;
};

function AddMCPServerDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button size="sm" className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add New MCP Server
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add New MCP Server</DialogTitle>
          <DialogDescription>
            DeepFlow uses the standard JSON MCP config to create a new server. Paste your config below and click "Add" to add new servers.
          </DialogDescription>
        </DialogHeader>
        <Textarea 
          placeholder="Paste your MCP server config here..."
          className="min-h-[200px]"
        />
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button>Add</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
    content: (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">MCP Servers</h3>
          <AddMCPServerDialog />
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
      </div>
    ),
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