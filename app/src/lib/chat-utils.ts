import { ResourceDomain } from '@/types/chat';

/**
 * Groups resources by domain and counts them
 */
export function groupResourcesByDomain(resources: string[]): ResourceDomain[] {
  const domainMap = new Map<string, number>();
  
  resources.forEach(url => {
    try {
      // Extract domain from URL
      const domain = new URL(url).hostname.replace(/^www\./, '');
      domainMap.set(domain, (domainMap.get(domain) || 0) + 1);
    } catch {
      // If URL parsing fails, use the original string
      domainMap.set(url, (domainMap.get(url) || 0) + 1);
    }
  });
  
  return Array.from(domainMap.entries()).map(([domain, count]) => ({
    domain,
    count
  }));
}

/**
 * Formats recording time in MM:SS format
 */
export function formatRecordingTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Determines file type from File object
 */
export function getFileType(file: File): 'image' | 'audio' | 'other' {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('audio/')) return 'audio';
  return 'other';
}

/**
 * Creates a File object from Blob for audio recordings
 */
export function createAudioFile(audioBlob: Blob): File {
  return new File([audioBlob], `recording-${Date.now()}.wav`, {
    type: 'audio/wav',
  });
}

/**
 * Validates message input before sending
 */
export function validateMessageInput(
  content: string, 
  attachments: File[], 
  isLoading: boolean, 
  isRecording: boolean
): boolean {
  return !((!content.trim() && attachments.length === 0) || isLoading || isRecording);
}

/**
 * Scrolls to the bottom of a container element
 */
export function scrollToBottom(element: HTMLElement | null): void {
  element?.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Creates object URL and handles cleanup
 */
export function createManagedObjectURL(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * Revokes object URLs to prevent memory leaks
 */
export function revokeObjectURLs(urls: string[]): void {
  urls.forEach(url => URL.revokeObjectURL(url));
} 