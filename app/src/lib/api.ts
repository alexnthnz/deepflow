/**
 * API configuration and utility functions
 */

// API URL configuration - can be overridden with environment variables
export const API_URL = process.env.API_URL || 'https://u2m4hpxzi9.execute-api.ap-southeast-2.amazonaws.com';
export const API_VERSION = process.env.API_VERSION || 'v1';

// API endpoints
export const ENDPOINTS = {
  CHATS: `/api/${API_VERSION}/chats`,
  MESSAGES: `/api/${API_VERSION}/chats/messages`,
  
  // Workflow/Graph endpoints
  GRAPHS: `/api/${API_VERSION}/graphs`,
  GRAPH_NODES: `/api/${API_VERSION}/graphs/nodes`,
  GRAPH_EDGES: `/api/${API_VERSION}/graphs/edges`,
  WORKFLOW_SAVE: `/api/${API_VERSION}/graphs/bulk/save`,
  WORKFLOW_CLEAR: `/api/${API_VERSION}/graphs/bulk/clear`,
  WORKFLOW_LOAD: `/api/${API_VERSION}/graphs/workflow/reactflow`,
  WORKFLOW_VALIDATE: `/api/${API_VERSION}/graphs/validate`,
  WORKFLOW_EXECUTE: `/api/${API_VERSION}/graphs/execute`,
  WORKFLOW_TEMPLATES: `/api/${API_VERSION}/graphs/templates`,
  WORKFLOW_APPLY_TEMPLATE: (templateId: string) => `/api/${API_VERSION}/graphs/templates/${templateId}/apply`,
}; 