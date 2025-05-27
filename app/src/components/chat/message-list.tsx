'use client';

import { useEffect, useRef } from 'react';
import ChatMessage from '@/components/chat/message';
import { scrollToBottom } from '@/lib/chat-utils';
import type { ExtendedMessage } from '@/types/chat';

interface MessageListProps {
  messages: ExtendedMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom(messagesEndRef.current);
  }, [messages]);

  return (
    <main className="flex-1 p-6 overflow-auto bg-gray-50">
      <div className="max-w-5xl mx-auto space-y-6">
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}-${message.timestamp}`}
            role={message.role}
            content={message.content}
            attachments={message.attachments}
            resources={message.resources}
            images={message.images}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </main>
  );
} 