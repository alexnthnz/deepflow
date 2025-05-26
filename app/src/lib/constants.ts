// Model configurations
export const AVAILABLE_MODELS = [
  { id: 'claude-3.5-sonnet-v2', name: 'Claude 3.5 Sonnet v2' },
  { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
  { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet' },
  { id: 'claude-3-haiku', name: 'Claude 3 Haiku' },
] as const;

export type ModelId = typeof AVAILABLE_MODELS[number]['id'];

// File upload constraints
export const MAX_ATTACHMENTS = 5;
export const ACCEPTED_FILE_TYPES = 'image/*,audio/*';

// Default messages and placeholders
export const DEFAULT_PLACEHOLDER = "How can Deepflow help?";
export const WELCOME_MESSAGE = "👋 Hello, there!";
export const WELCOME_DESCRIPTION = "Welcome to DeepFlow, a deep research assistant built on cutting-edge language models, helps you search on web, browse information, and handle complex tasks.";

// Sample questions for the home page
export const SAMPLE_QUESTIONS = [
  "How many times taller is the Eiffel Tower than the tallest building in the world?",
  "How many years does an average Tesla battery last compared to a gasoline engine?",
  "How many liters of water are required to produce 1 kg of beef?",
  "How many times faster is the speed of light compared to the speed of sound?",
];

// Animation delays and durations
export const ANIMATION_DELAYS = {
  CARD_STAGGER: 0.1,
  INITIAL_DELAY: 0.5,
  DURATION: 0.2,
} as const;

// UI constraints
export const UI_CONSTRAINTS = {
  MAX_TEXTAREA_HEIGHT: 'max-h-32',
  MIN_TEXTAREA_HEIGHT: 'min-h-[40px]',
  ATTACHMENT_PREVIEW_SIZE: 'h-12 w-12',
} as const; 