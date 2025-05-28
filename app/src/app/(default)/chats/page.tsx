'use client';

import { useAtom, useSetAtom } from 'jotai';
import { useRouter } from 'next/navigation';
import { chatSessionsAtom, deleteChatSessionAtom } from '@/store/chat';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Trash } from 'lucide-react';

export default function ChatsPage() {
  const [sessions] = useAtom(chatSessionsAtom);
  const deleteSession = useSetAtom(deleteChatSessionAtom);
  const router = useRouter();
  
  const sessionIds = Object.keys(sessions);
  
  const getLastMessage = (sessionId: string) => {
    const messages = sessions[sessionId]?.messages || [];
    return messages.length > 0 ? messages[messages.length - 1] : null;
  };
  
  const formatDate = (timestamp?: string) => {
    if (!timestamp) return 'Unknown date';
    return new Date(timestamp).toLocaleString();
  };
  
  const navigateToChat = (sessionId: string) => {
    router.push(`/chats/${sessionId}`);
  };
  
  const navigateToHome = () => {
    router.push('/');
  };
  
  const handleDeleteChat = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // Prevent navigating to chat when clicking delete
    if (confirm('Are you sure you want to delete this chat session?')) {
      deleteSession(sessionId);
    }
  };
  
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Your Chat Sessions</h1>
      </div>
      
      {sessionIds.length === 0 ? (
        <div className="text-center p-16 bg-white rounded-lg border border-gray-200 shadow-sm">
          <p className="text-gray-500 mb-6 text-lg">You don&apos;t have any chat sessions yet.</p>
          <Button onClick={navigateToHome} className="text-base px-6 py-5">Start a chat</Button>
        </div>
      ) : (
        <div className="flex flex-col gap-5 h-[calc(100vh-200px)] overflow-y-auto">
          {sessionIds.map((sessionId) => {
            const lastMessage = getLastMessage(sessionId);
            return (
              <Card 
                key={sessionId}
                className="p-6 h-48 hover:bg-gray-50 cursor-pointer transition-colors relative border border-gray-200 shadow-sm"
                onClick={() => navigateToChat(sessionId)}
              >
                <div className="flex justify-between mb-3">
                  <h3 className="font-medium text-lg">Session {sessionId.substring(0, 8)}...</h3>
                  <div className="flex items-center">
                    <p className="text-sm text-gray-500 mr-4">
                      {lastMessage?.timestamp ? formatDate(lastMessage.timestamp) : 'No messages'}
                    </p>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-9 w-9 text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={(e) => handleDeleteChat(e, sessionId)}
                    >
                      <Trash className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
                <p className="text-base text-gray-700 line-clamp-2">
                  {lastMessage?.content || 'No messages in this chat'}
                </p>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
} 