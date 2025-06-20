'use server'

import { Node, Edge } from '@xyflow/react';
import { API_URL, ENDPOINTS } from '@/lib/api';

// Types for API responses
interface ApiResponse<T = any> {
  message: string;
  status_code: number;
  data: T;
  error: string | null;
}

interface WorkflowExecutionResponse {
  execution_id: string;
  messages: any[];
  node_executions: any[];
  status: 'completed' | 'failed';
  error?: string;
}

interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Save workflow to backend
 */
export async function saveWorkflow(nodes: Node[], edges: Edge[]) {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.WORKFLOW_SAVE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        nodes,
        edges,
      }),
    });

    const result: ApiResponse = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || 'Failed to save workflow',
      };
    }

    return {
      success: true,
      data: result.data,
      message: result.message,
    };
  } catch (error) {
    console.error('Error saving workflow:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Load workflow from backend
 */
export async function loadWorkflow() {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.WORKFLOW_LOAD}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store', // Always fetch fresh data
    });

    const result: ApiResponse<{ nodes: Node[]; edges: Edge[] }> = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || 'Failed to load workflow',
      };
    }

    return {
      success: true,
      data: result.data,
      message: result.message,
    };
  } catch (error) {
    console.error('Error loading workflow:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Clear workflow (delete all nodes and edges)
 */
export async function clearWorkflow() {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.WORKFLOW_CLEAR}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const result: ApiResponse = await response.json();
      return {
        success: false,
        error: result.error || 'Failed to clear workflow',
      };
    }

    return {
      success: true,
      message: 'Workflow cleared successfully',
    };
  } catch (error) {
    console.error('Error clearing workflow:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Validate workflow structure
 */
export async function validateWorkflow(nodes: Node[], edges: Edge[]) {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.WORKFLOW_VALIDATE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        nodes,
        edges,
      }),
    });

    const result: ApiResponse<ValidationResult> = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || 'Failed to validate workflow',
      };
    }

    return {
      success: true,
      data: result.data,
      message: result.message,
    };
  } catch (error) {
    console.error('Error validating workflow:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Execute workflow with input message
 */
export async function executeWorkflow(
  message: string,
  sessionId?: string,
  chatId?: string
) {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.WORKFLOW_EXECUTE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId || `workflow-${Date.now()}`,
        chat_id: chatId,
        graph_name: 'default',
      }),
    });

    const result: ApiResponse<WorkflowExecutionResponse> = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || 'Failed to execute workflow',
      };
    }

    return {
      success: true,
      data: result.data,
      message: result.message,
    };
  } catch (error) {
    console.error('Error executing workflow:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Get graph overview (complete structure)
 */
export async function getGraphOverview() {
  try {
    const response = await fetch(`${API_URL}${ENDPOINTS.GRAPHS}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    const result: ApiResponse = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || 'Failed to get graph overview',
      };
    }

    return {
      success: true,
      data: result.data,
      message: result.message,
    };
  } catch (error) {
    console.error('Error getting graph overview:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Auto-save workflow (debounced save)
 */
let autoSaveTimeout: NodeJS.Timeout | null = null;

export async function autoSaveWorkflow(nodes: Node[], edges: Edge[], delay = 2000) {
  return new Promise((resolve) => {
    // Clear existing timeout
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
    }

    // Set new timeout
    autoSaveTimeout = setTimeout(async () => {
      const result = await saveWorkflow(nodes, edges);
      resolve(result);
    }, delay);
  });
} 