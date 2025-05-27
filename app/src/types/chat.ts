// Base message interface from store
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  resources?: string[];
  images?: string[];
}

// Extended message with attachments for UI components
export interface ExtendedMessage extends Message {
  attachments?: FileAttachment[];
}

// File attachment interface
export interface FileAttachment {
  file: File;
  type: 'image' | 'audio' | 'other';
  url: string;
  name: string;
}

// Chat session interface
export interface ChatSession {
  messages: Message[];
  isLoading: boolean;
}

// API response types
export interface SendMessageResponse {
  success: boolean;
  data?: {
    message: string;
    session_id: string;
    resources: string[];
    images: string[];
  };
  error?: string;
}

// Component prop types
export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string, attachments: File[]) => void;
  isLoading?: boolean;
  placeholder?: string;
  showModelSelector?: boolean;
  showDeepSearch?: boolean;
  showThink?: boolean;
  maxAttachments?: number;
}

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  attachments?: FileAttachment[];
  resources?: string[];
  images?: string[];
}

// Domain grouping for resources
export interface ResourceDomain {
  domain: string;
  count: number;
} 