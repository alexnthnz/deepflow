'use client';

import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Mic,
  MicOff,
  Trash2,
  Image as ImageIcon,
  Music,
} from 'lucide-react';
import { useFileUpload } from '@/hooks/use-file-upload';
import { useAudioRecording } from '@/hooks/use-audio-recording';
import { AVAILABLE_MODELS, type ModelId } from '@/lib/constants';
import type { MessageInputProps } from '@/types/chat';

export function MessageInput({
  value,
  onChange,
  onSend,
  isLoading = false,
  placeholder = "How can Deepflow help?",
  showModelSelector = true,
  showDeepSearch = false,
  showThink = false,
  maxAttachments = 5
}: MessageInputProps) {
  const [selectedModel, setSelectedModel] = useState<ModelId>('claude-3.5-sonnet-v2');
  const [isDeepSearchEnabled, setIsDeepSearchEnabled] = useState(false);
  const [isThinkEnabled, setIsThinkEnabled] = useState(false);

  const {
    attachments,
    attachmentData,
    fileInputRef,
    handleFileUpload,
    triggerFileUpload,
    removeAttachment,
    clearAttachments,
    hasReachedLimit,
    getFileType
  } = useFileUpload(maxAttachments);

  const {
    isRecording,
    recordingTime,
    formatTime,
    toggleRecording
  } = useAudioRecording();

  const handleSend = async () => {
    if ((!value.trim() && attachments.length === 0) || isLoading || isRecording) return;
    
    // Handle audio recording if in progress
    if (isRecording) {
      const audioFile = await toggleRecording();
      if (audioFile) {
        // Add audio file to attachments before sending
        onSend(value, [...attachments, audioFile]);
      }
    } else {
      onSend(value, attachments);
    }
    
    clearAttachments();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRecordingToggle = async () => {
    const audioFile = await toggleRecording();
    if (audioFile) {
      // Add the recorded audio file to attachments
      const fileList = new DataTransfer();
      fileList.items.add(audioFile);
      const event = {
        target: { files: fileList.files }
      } as React.ChangeEvent<HTMLInputElement>;
      handleFileUpload(event);
    }
  };

  return (
    <div className="bg-gray-50 p-6 w-full">
      <div className="max-w-5xl mx-auto">
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="image/*,audio/*"
          className="hidden"
          multiple
          max={maxAttachments}
        />

        {/* Recording indicator */}
        {isRecording && (
          <div className="text-sm text-gray-500 mb-2 flex items-center">
            <div className="relative h-2 w-2 mr-2">
              <div className="absolute inset-0 rounded-full bg-red-500" />
              <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75" />
            </div>
            Recording... {formatTime(recordingTime)}
          </div>
        )}

        {/* Attachment limit warning */}
        {hasReachedLimit && (
          <div className="text-xs text-amber-600 mb-2">
            Maximum of {maxAttachments} attachments reached. Delete an attachment to add more.
          </div>
        )}

        <div className="flex items-center bg-white rounded-lg shadow border px-4 py-2 gap-2 flex-col">
          {/* Attachments preview */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 w-full py-2">
              {attachmentData.map((attachment, index) => (
                <div key={attachment.name} className="relative group">
                  <div className="relative h-12 w-12 overflow-hidden rounded-md border border-gray-200 shadow-sm">
                    {attachment.type === 'image' ? (
                      <img
                        src={attachment.url}
                        alt={attachment.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center bg-blue-50">
                        <Music size={24} className="text-blue-600" />
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => removeAttachment(index)}
                      className="absolute top-0 right-0 p-0.5 bg-black/50 hover:bg-black/70 rounded-bl-md opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="Remove attachment"
                    >
                      <Trash2 size={12} className="text-white" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Text input */}
          <Textarea
            className="flex-1 bg-transparent outline-none border-none focus:border-none focus:ring-0 focus:shadow-none px-3 py-2 text-base resize-none min-h-[40px] max-h-32 rounded-full shadow-none focus-visible:ring-0"
            placeholder={placeholder}
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isRecording}
          />

          {/* Controls */}
          <div className="flex flex-row items-center gap-2 justify-between w-full">
            <div className="flex flex-row items-center gap-2">
              {/* File upload button */}
              <button
                type="button"
                onClick={triggerFileUpload}
                className={`w-10 h-10 flex items-center justify-center rounded-full transition ${
                  hasReachedLimit
                    ? 'bg-gray-100 cursor-not-allowed'
                    : 'hover:bg-gray-100'
                }`}
                disabled={isLoading || isRecording || hasReachedLimit}
                title={hasReachedLimit ? `Maximum ${maxAttachments} files allowed` : "Upload file"}
              >
                <ImageIcon
                  size={20}
                  className={hasReachedLimit ? "text-gray-400" : "text-gray-500"}
                />
              </button>

              {/* Recording button */}
              <button
                type="button"
                onClick={handleRecordingToggle}
                className={`relative w-10 h-10 flex items-center justify-center rounded-full transition ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : hasReachedLimit
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'hover:bg-gray-100 text-gray-500'
                }`}
                disabled={isLoading || hasReachedLimit}
                title={
                  hasReachedLimit
                    ? `Maximum ${maxAttachments} files allowed`
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

              {/* Optional feature toggles */}
              {showDeepSearch && (
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
              )}

              {showThink && (
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
              )}
            </div>

            <div className="flex flex-row items-center gap-2">
              {/* Model selector */}
              {showModelSelector && (
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
              )}

              {/* Send button */}
              <button
                onClick={handleSend}
                disabled={(value.trim() === '' && attachments.length === 0) || isLoading || isRecording}
                className="w-10 h-10 flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:bg-gray-300 disabled:text-gray-400 ml-1"
                title="Send"
              >
                {isLoading ? (
                  <div className="h-5 w-5 border-2 border-t-transparent border-white rounded-full animate-spin" />
                ) : (
                  <svg width="20" height="20" fill="none" viewBox="0 0 24 24">
                    <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 