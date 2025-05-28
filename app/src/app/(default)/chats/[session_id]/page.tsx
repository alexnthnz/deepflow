'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useAtom, useSetAtom } from 'jotai';

import { sendMessage } from '@/actions/chat';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { 
  getChatSessionAtom, 
  addMessageAtom, 
  setLoadingAtom, 
  initChatSessionAtom,
  Message
} from '@/store/chat';
import { Mic, MicOff, Trash2, Image as ImageIcon, Music } from 'lucide-react';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { toast } from 'sonner';
import ChatMessage from '@/components/chat/message';

// Extended Message type to include attachments
interface ExtendedMessage extends Message {
  attachments?: {
      type: 'image' | 'audio' | 'other';
      url: string;
      name: string;
  }[];
}

export default function ChatPage() {
  const params = useParams();
  const session_id = params.session_id as string;
  
  const MAX_ATTACHMENTS = 5; // Maximum number of attachments allowed
  
  const AVAILABLE_MODELS = [
    { id: 'claude-3.5-sonnet-v2', name: 'Claude 3.5 Sonnet v2' },
    { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
    { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet' },
    { id: 'claude-3-haiku', name: 'Claude 3 Haiku' },
  ] as const;
  
  type ModelId = typeof AVAILABLE_MODELS[number]['id'];
  
  const [inputValue, setInputValue] = useState('');
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [attachments, setAttachments] = useState<File[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Create a ref for the message container
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Memoize the session atom to prevent recreation on each render
  const sessionAtom = useMemo(() => getChatSessionAtom(session_id), [session_id]);
  
  // Initialize Jotai atoms
  const [session] = useAtom(sessionAtom);
  const addMessage = useSetAtom(addMessageAtom);
  const setLoading = useSetAtom(setLoadingAtom);
  const initSession = useSetAtom(initChatSessionAtom);

  // Extract values from session atom
  const { messages, isLoading } = session;
  
  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // On page load, add the initial message from the server if this is a new conversation
  useEffect(() => {
    // Skip initialization if we already have messages
    if (sessionInitialized || messages.length > 0) return;
    
    // Just initialize the session without relying on URL parameters
    initSession({ sessionId: session_id });
    
    setSessionInitialized(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session_id, messages.length]);

  // Clean up recording resources when component unmounts
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // Helper function to create object URLs from files
  const createAttachmentData = (file: File) => {
    const url = URL.createObjectURL(file);
    const type = getFileType(file);
    return {
      type,
      url,
      name: file.name
    };
  };

  // Create a cleanup function for object URLs
  useEffect(() => {
    return () => {
      // Cleanup object URLs when component unmounts
      attachments.forEach(file => {
        URL.revokeObjectURL(URL.createObjectURL(file));
      });
    };
  }, []);

  // Handle sending a message in the chat
  const handleSendMessage = async () => {
    if ((!inputValue.trim() && attachments.length === 0) || isLoading) return;
    
    setLoading({ sessionId: session_id, isLoading: true });
    
    // Create attachment data for display in the UI
    const attachmentData = attachments.map(createAttachmentData);
    
    // Use default message text if there's no input but there are attachments
    const messageContent = inputValue.trim() || (attachments.length > 0 ? "Refer to the following content:" : "");
    
    // Add user message immediately to the UI
    const userMessage: ExtendedMessage = {
      role: 'user',
      content: messageContent,
      attachments: attachmentData,
      timestamp: new Date().toISOString()
    };
    
    addMessage({ sessionId: session_id, message: userMessage });
    setInputValue(''); // Clear input right away
    
    try {
      // Call the server action with attachments
      const result = await sendMessage({
        content: messageContent,
        is_new_chat: false,
        session_id: session_id,
        attachments: attachments
      });
      
      // Clear attachments after sending
      setAttachments([]);
      
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
      
      addMessage({ sessionId: session_id, message: assistantMessage });
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      addMessage({
        sessionId: session_id,
        message: {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: new Date().toISOString()
        }
      });
      
      // Clear attachments on error
      setAttachments([]);
    } finally {
      setLoading({ sessionId: session_id, isLoading: false });
    }
  };

  // Maximum number of audio attachments allowed
  const hasReachedAttachmentLimit = attachments.length >= MAX_ATTACHMENTS;

  // Start audio recording
  const startRecording = async () => {
    // Don't allow recording if attachment limit reached
    if (hasReachedAttachmentLimit) return;
    
    try {
      audioChunksRef.current = [];
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        // Create a File object from the blob with a unique name
        const timestamp = Date.now();
        const audioFile = new File([audioBlob], `audio_recording_${timestamp}.wav`, {
          type: 'audio/wav',
          lastModified: timestamp
        });
        
        // Add audio file to attachments
        setAttachments(prev => [...prev, audioFile]);
        
        // Clean up
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
        
        setRecordingTime(0);
        setIsRecording(false);
      };
      
      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
    }
  };
  
  // Stop audio recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };
  
  // Toggle recording state
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Format recording time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Function to handle image upload
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    const files = Array.from(e.target.files);
    const totalFiles = attachments.length + files.length;
    
    if (totalFiles > MAX_ATTACHMENTS) {
      toast.error('File limit exceeded', {
        description: `You can only upload a maximum of ${MAX_ATTACHMENTS} files (images or audio). You currently have ${attachments.length} ${attachments.length === 1 ? 'file' : 'files'} and selected ${files.length} new ${files.length === 1 ? 'file' : 'files'}.`,
        style: {
          color: '#000',
          backgroundColor: '#fff',
        },
        className: 'font-medium'
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    
    // Add files to attachments
    setAttachments(prev => [...prev, ...files]);
    
    // Reset the file input so the same file can be selected again
    if (fileInputRef.current) fileInputRef.current.value = '';
  };
  
  // Function to trigger file input click
  const triggerFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  // Function to get file type (image or audio)
  const getFileType = (file: File): 'image' | 'audio' | 'other' => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('audio/')) return 'audio';
    return 'other';
  };

  // Function to discard a specific recording by index
  const discardRecording = (index: number) => {
    setAttachments(prev => {
      const updated = [...prev];
      updated.splice(index, 1);
      return updated;
    });
  };

  const [selectedModel, setSelectedModel] = useState<ModelId>(AVAILABLE_MODELS[0].id);
  const [isDeepSearchEnabled, setIsDeepSearchEnabled] = useState(false);
  const [isThinkEnabled, setIsThinkEnabled] = useState(false);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Chat messages container */}
      <main className="flex-1 p-6 overflow-auto bg-gray-50">
        <div className="max-w-5xl mx-auto space-y-6">
          {messages
            .slice()
            .map((message, index) => (
              <ChatMessage
                key={index}
                role={message.role}
                content={message.content}
                attachments={(message as ExtendedMessage).attachments}
                resources={message.resources}
                images={message.images}
              />
            ))}
          
          {isLoading && (
            <div className="flex justify-start mb-4">
              <Card className="px-4 py-3 bg-gray-100 max-w-[80%]">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce" />
                  <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce delay-150" />
                  <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce delay-300" />
                </div>
              </Card>
            </div>
          )}
          
          {/* Invisible element to scroll to */}
          <div ref={messagesEndRef} />
        </div>
      </main>
      
      {/* Input area */}
      <footer className="bg-gray-50 p-6">
        <div className="max-w-5xl mx-auto">
          {/* Hidden file input for image uploads */}
          <input 
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            className="hidden"
            multiple
            max={MAX_ATTACHMENTS}
          />

          {isRecording && (
            <div className="text-sm text-gray-500 mb-2 flex items-center">
              <div className="relative h-2 w-2 mr-2">
                <div className="absolute inset-0 rounded-full bg-red-500" />
                <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75" />
              </div>
              Recording... {formatTime(recordingTime)}
            </div>
          )}
          
          {hasReachedAttachmentLimit && (
            <div className="text-xs text-amber-600">
              Maximum of {MAX_ATTACHMENTS} attachments reached. Delete an attachment to add more.
            </div>
          )}
          <div className="flex items-center bg-white rounded-lg shadow border px-4 py-2 gap-2 flex-col">            
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 w-full py-2">
                {attachments.map((file, index) => {
                  const fileType = getFileType(file);
                  return (
                    <div key={file.name} className="relative group">
                      <div className="relative h-12 w-12 overflow-hidden rounded-md border border-gray-200 shadow-sm">
                        {fileType === 'image' ? (
                          <img 
                            src={URL.createObjectURL(file)}
                            alt={file.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center bg-blue-50">
                            <Music size={24} className="text-blue-600" />
                          </div>
                        )}
                        <button 
                          type="button" 
                          onClick={() => discardRecording(index)}
                          className="absolute top-0 right-0 p-0.5 bg-black/50 hover:bg-black/70 rounded-bl-md opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="Remove attachment"
                        >
                          <Trash2 size={12} className="text-white" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {/* Input */}
            <Textarea
              className="flex-1 bg-transparent outline-none border-none focus:border-none focus:ring-0 focus:shadow-none px-3 py-2 text-base resize-none min-h-[40px] max-h-32 rounded-full shadow-none focus-visible:ring-0"
              placeholder="How can Deepflow help?"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={isLoading || isRecording}
            />
            <div className="flex flex-row items-center gap-2 justify-between w-full">
              <div className="flex flex-row items-center gap-2">
                <button
                  type="button"
                  onClick={triggerFileUpload}
                  className={`w-10 h-10 flex items-center justify-center rounded-full transition ${
                    hasReachedAttachmentLimit 
                      ? 'bg-gray-100 cursor-not-allowed' 
                      : 'hover:bg-gray-100'
                  }`}
                  disabled={isLoading || isRecording || hasReachedAttachmentLimit}
                  title={hasReachedAttachmentLimit 
                    ? `Maximum ${MAX_ATTACHMENTS} files allowed` 
                    : "Upload image"}
                >
                  <ImageIcon 
                    size={20} 
                    className={hasReachedAttachmentLimit ? "text-gray-400" : "text-gray-500"} 
                  />
                </button>
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={`relative w-10 h-10 flex items-center justify-center rounded-full transition ${
                    isRecording 
                      ? 'bg-red-500 hover:bg-red-600 text-white' 
                      : hasReachedAttachmentLimit
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'hover:bg-gray-100 text-gray-500'
                  }`}
                  disabled={isLoading || hasReachedAttachmentLimit}
                  title={
                    hasReachedAttachmentLimit
                      ? `Maximum ${MAX_ATTACHMENTS} files allowed`
                      : isRecording 
                        ? "Stop recording" 
                        : "Record audio"
                  }
                >
                  {isRecording ? (
                    <>
                      <div className="absolute inset-0 rounded-full bg-red-500/50">
                        <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-25" />
                      </div>
                      <MicOff size={20} className="relative z-10" />
                    </>
                  ) : (
                    <Mic size={20} />
                  )}
                </button>
                {/* Action buttons */}
                <button
                  type="button"
                  onClick={() => setIsDeepSearchEnabled(!isDeepSearchEnabled)}
                  className={`px-4 py-1 rounded-full text-sm font-medium transition ${
                    isDeepSearchEnabled
                      ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  DeepSearch
                </button>
                <button
                  type="button"
                  onClick={() => setIsThinkEnabled(!isThinkEnabled)}
                  className={`px-4 py-1 rounded-full text-sm font-medium transition ${
                    isThinkEnabled
                      ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Think
                </button>
              </div>
              <div className="flex flex-row items-center gap-2">
                <Select 
                  value={selectedModel} 
                  onValueChange={(value) => setSelectedModel(value as ModelId)}
                >
                  <SelectTrigger className="min-w-[100px] px-2 rounded-full bg-white border-none shadow-none focus:ring-0 focus:border-none">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_MODELS.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <button
                  onClick={handleSendMessage}
                  disabled={(inputValue.trim() === '' && attachments.length === 0) || isLoading || isRecording}
                  className="w-10 h-10 flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:bg-gray-300 disabled:text-gray-400 ml-1"
                  title="Send"
                >
                  <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
} 