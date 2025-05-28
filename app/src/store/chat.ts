import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';

// Message type definitions
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string; // Store as ISO string instead of Date object
  resources?: string[];
  images?: string[];
}

// Session chat state interface
export interface ChatSession {
  messages: Message[];
  isLoading: boolean;
}

// Create an atom to store all chat sessions by their session_id
export const chatSessionsAtom = atomWithStorage<Record<string, ChatSession>>(
  'chat-sessions',
  {}
);

// Helper atoms and getter/setter functions

// Get a specific chat session by ID
export const getChatSessionAtom = (sessionId: string) => {
  // Create a new atom for this session ID
  return atom((get) => {
    const sessions = get(chatSessionsAtom);
    return sessions[sessionId] || { messages: [], isLoading: false };
  });
};

// Add a message to a chat session
export const addMessageAtom = atom(
  null,
  (get, set, { sessionId, message }: { sessionId: string; message: Message }) => {
    const sessions = get(chatSessionsAtom);
    const session = sessions[sessionId] || { messages: [], isLoading: false };
    
    // Ensure timestamp is an ISO string
    const messageWithStringTimestamp = {
      ...message,
      timestamp: message.timestamp || new Date().toISOString()
    };
    
    set(chatSessionsAtom, {
      ...sessions,
      [sessionId]: {
        ...session,
        messages: [...session.messages, messageWithStringTimestamp],
      },
    });
  }
);

// Set loading state for a chat session
export const setLoadingAtom = atom(
  null,
  (get, set, { sessionId, isLoading }: { sessionId: string; isLoading: boolean }) => {
    const sessions = get(chatSessionsAtom);
    const session = sessions[sessionId] || { messages: [], isLoading: false };
    
    set(chatSessionsAtom, {
      ...sessions,
      [sessionId]: {
        ...session,
        isLoading,
      },
    });
  }
);

// Create or initialize a chat session
export const initChatSessionAtom = atom(
  null,
  (get, set, { 
    sessionId, 
    initialMessage, 
    initialUserMessage,
    initialResources,
    initialImages 
  }: { 
    sessionId: string; 
    initialMessage?: string;
    initialUserMessage?: string;
    initialResources?: string[];
    initialImages?: string[];
  }) => {
    const sessions = get(chatSessionsAtom);
    
    // Don't override existing session if it already exists and has messages
    if (sessions[sessionId] && sessions[sessionId].messages.length > 0) return;
    
    const initialMessages: Message[] = [];
    
    // Add the user message first if provided
    if (initialUserMessage) {
      initialMessages.push({ 
        role: 'user', 
        content: initialUserMessage, 
        timestamp: new Date().toISOString() 
      });
    }
    
    // Then add the assistant's response if provided
    if (initialMessage) {
      initialMessages.push({ 
        role: 'assistant', 
        content: initialMessage,
        resources: initialResources,
        images: initialImages,
        timestamp: new Date().toISOString() 
      });
    }
    
    set(chatSessionsAtom, {
      ...sessions,
      [sessionId]: {
        messages: initialMessages,
        isLoading: false,
      },
    });
  }
);

// Delete a chat session
export const deleteChatSessionAtom = atom(
  null,
  (get, set, sessionId: string) => {
    const sessions = get(chatSessionsAtom);
    const remainingSessions = { ...sessions };
    delete remainingSessions[sessionId];
    
    set(chatSessionsAtom, remainingSessions);
  }
); 