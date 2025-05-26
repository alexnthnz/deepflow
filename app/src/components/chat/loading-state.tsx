'use client';

import ChatMessage from '@/components/chat/message';

interface LoadingStateProps {
  userMessage: string;
}

export function LoadingState({ userMessage }: LoadingStateProps) {
  return (
    <main className="flex-1 p-6 overflow-auto bg-gray-50">
      <div className="max-w-5xl mx-auto space-y-6">
        <ChatMessage
          role="user"
          content={userMessage}
          attachments={[]}
          resources={[]}
          images={[]}
        />
      </div>
    </main>
  );
} 