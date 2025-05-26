import { useState, useEffect, useMemo } from 'react';
import { useAtom, useSetAtom } from 'jotai';
import { sendMessage } from '@/actions/chat';
import { 
  getChatSessionAtom, 
  addMessageAtom, 
  setLoadingAtom, 
  initChatSessionAtom 
} from '@/store/chat';
import type { ExtendedMessage, Message } from '@/types/chat';

export function useChatSession(sessionId: string) {
  const [sessionInitialized, setSessionInitialized] = useState(false);
  
  // Memoize the session atom to prevent recreation on each render
  const sessionAtom = useMemo(() => getChatSessionAtom(sessionId), [sessionId]);
  
  // Initialize Jotai atoms
  const [session] = useAtom(sessionAtom);
  const addMessage = useSetAtom(addMessageAtom);
  const setLoading = useSetAtom(setLoadingAtom);
  const initSession = useSetAtom(initChatSessionAtom);

  // Extract values from session atom
  const { messages, isLoading } = session;

  // Initialize session on first load
  useEffect(() => {
    if (sessionInitialized || messages.length > 0) return;
    
    initSession({ sessionId });
    setSessionInitialized(true);
  }, [sessionId, messages.length, sessionInitialized, initSession]);

  const sendChatMessage = async (content: string, attachments: File[] = []) => {
    if ((!content.trim() && attachments.length === 0) || isLoading) return;
    
    setLoading({ sessionId, isLoading: true });
    
    // Create attachment data for display in the UI
    const attachmentData = attachments.map(file => ({
      file,
      type: file.type.startsWith('image/') ? 'image' as const : 
            file.type.startsWith('audio/') ? 'audio' as const : 'other' as const,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    
    // Use default message text if there's no input but there are attachments
    const messageContent = content.trim() || (attachments.length > 0 ? "Refer to the following content:" : "");
    
    // Add user message immediately to the UI
    const userMessage: ExtendedMessage = {
      role: 'user',
      content: messageContent,
      attachments: attachmentData,
      timestamp: new Date().toISOString()
    };
    
    addMessage({ sessionId, message: userMessage });
    
    try {
      // Call the server action with attachments
      const result = await sendMessage({
        content: messageContent,
        is_new_chat: false,
        session_id: sessionId,
        attachments: attachments
      });
      
      if (!result.success || !result.data) {
        throw new Error(result.error || 'Failed to send message');
      }
      
      // Get data directly from the response
      const { message } = result.data;
      
      // Add assistant's response to the messages
      const assistantMessage: Message = {
        role: 'assistant',
        content: message,
        resources: result.data.resources,
        images: result.data.images,
        timestamp: new Date().toISOString()
      };
      
      addMessage({ sessionId, message: assistantMessage });
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      addMessage({
        sessionId,
        message: {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: new Date().toISOString()
        }
      });
    } finally {
      setLoading({ sessionId, isLoading: false });
    }
  };

  return {
    messages,
    isLoading,
    sendMessage: sendChatMessage,
    sessionInitialized
  };
} 