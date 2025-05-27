import { useState, useRef } from 'react';

export interface FileAttachment {
  file: File;
  type: 'image' | 'audio' | 'other';
  url: string;
  name: string;
}

export function useFileUpload(maxAttachments: number = 5) {
  const [attachments, setAttachments] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getFileType = (file: File): 'image' | 'audio' | 'other' => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('audio/')) return 'audio';
    return 'other';
  };

  const createAttachmentData = (file: File): FileAttachment => {
    const url = URL.createObjectURL(file);
    const type = getFileType(file);
    return {
      file,
      type,
      url,
      name: file.name
    };
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + attachments.length > maxAttachments) {
      alert(`Maximum ${maxAttachments} files allowed`);
      return;
    }
    setAttachments(prev => [...prev, ...files]);
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const clearAttachments = () => {
    setAttachments([]);
  };

  const hasReachedLimit = attachments.length >= maxAttachments;

  const attachmentData = attachments.map(createAttachmentData);

  return {
    attachments,
    attachmentData,
    fileInputRef,
    handleFileUpload,
    triggerFileUpload,
    removeAttachment,
    clearAttachments,
    hasReachedLimit,
    getFileType
  };
} 