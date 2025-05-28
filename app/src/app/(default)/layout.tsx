'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { PlusCircle, History, GitBranch } from 'lucide-react';
import { SettingsDialog } from '@/components/settings';

export default function DefaultLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // Check if we're on the chats route or a specific chat session
  const isChatsRoute = pathname === '/chats';
  const isChatSessionRoute = pathname.startsWith('/chats/');
  const isHomeRoute = pathname === '/';
  const isWorkflowRoute = pathname === '/workflow';

  return (
    <div className="flex flex-col overflow-hidden w-full h-screen">
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white">
        <div className="flex h-16 items-center justify-between px-4">
          <button 
            onClick={() => router.push('/')}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <GitBranch className="h-4 w-4" />
            <h1 className="text-xl font-semibold">DeepFlow</h1>
          </button>
          <div className="flex items-center gap-2">
            <SettingsDialog />
            {(isChatSessionRoute || isHomeRoute) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/chats')}
                className="flex items-center gap-2"
              >
                <History className="h-4 w-4" />
                History
              </Button>
            )}
            {(isChatsRoute || isChatSessionRoute || isWorkflowRoute) && (
              <Button
                variant="default"
                size="sm"
                onClick={() => router.push('/')}
                className="flex items-center gap-2"
              >
                <PlusCircle className="h-4 w-4" />
                New Chat
              </Button>
            )}
          </div>
        </div>
      </header>
      <main className="flex-grow overflow-hidden h-full">
        {children}
      </main>
    </div>
  );
}
