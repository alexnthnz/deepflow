import { useState, useCallback, useEffect } from 'react';
import { Node, Edge } from '@xyflow/react';
import { 
  saveWorkflow, 
  loadWorkflow, 
  clearWorkflow, 
  validateWorkflow, 
  executeWorkflow, 
  autoSaveWorkflow 
} from '@/actions/workflow';
import { toast } from 'sonner';

interface WorkflowState {
  isSaving: boolean;
  isLoading: boolean;
  isExecuting: boolean;
  isValidating: boolean;
  hasUnsavedChanges: boolean;
  lastSaved: Date | null;
  validationResult: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  } | null;
}

interface UseWorkflowReturn extends WorkflowState {
  // Actions
  save: (nodes: Node[], edges: Edge[]) => Promise<boolean>;
  load: () => Promise<{ nodes: Node[]; edges: Edge[] } | null>;
  clear: () => Promise<boolean>;
  validate: (nodes: Node[], edges: Edge[]) => Promise<boolean>;
  execute: (message: string, sessionId?: string) => Promise<any>;
  
  // Auto-save
  enableAutoSave: (nodes: Node[], edges: Edge[]) => void;
  disableAutoSave: () => void;
  
  // State helpers
  markAsChanged: () => void;
  markAsSaved: () => void;
}

export function useWorkflow(): UseWorkflowReturn {
  const [state, setState] = useState<WorkflowState>({
    isSaving: false,
    isLoading: false,
    isExecuting: false,
    isValidating: false,
    hasUnsavedChanges: false,
    lastSaved: null,
    validationResult: null,
  });

  // Save workflow
  const save = useCallback(async (nodes: Node[], edges: Edge[]): Promise<boolean> => {
    setState(prev => ({ ...prev, isSaving: true }));
    
    try {
      const result = await saveWorkflow(nodes, edges);
      
      if (result.success) {
        setState(prev => ({ 
          ...prev, 
          isSaving: false, 
          hasUnsavedChanges: false,
          lastSaved: new Date()
        }));
        toast.success('Workflow saved successfully');
        return true;
      } else {
        setState(prev => ({ ...prev, isSaving: false }));
        toast.error(result.error || 'Failed to save workflow');
        return false;
      }
    } catch (error) {
      setState(prev => ({ ...prev, isSaving: false }));
      toast.error('Unexpected error while saving');
      return false;
    }
  }, []);

  // Load workflow
  const load = useCallback(async (): Promise<{ nodes: Node[]; edges: Edge[] } | null> => {
    setState(prev => ({ ...prev, isLoading: true }));
    
    try {
      const result = await loadWorkflow();
      
      if (result.success && result.data) {
        setState(prev => ({ 
          ...prev, 
          isLoading: false,
          hasUnsavedChanges: false,
          lastSaved: new Date()
        }));
        toast.success('Workflow loaded successfully');
        return result.data;
      } else {
        setState(prev => ({ ...prev, isLoading: false }));
        toast.error(result.error || 'Failed to load workflow');
        return null;
      }
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      toast.error('Unexpected error while loading');
      return null;
    }
  }, []);

  // Clear workflow
  const clear = useCallback(async (): Promise<boolean> => {
    setState(prev => ({ ...prev, isSaving: true }));
    
    try {
      const result = await clearWorkflow();
      
      if (result.success) {
        setState(prev => ({ 
          ...prev, 
          isSaving: false,
          hasUnsavedChanges: false,
          lastSaved: new Date()
        }));
        toast.success('Workflow cleared successfully');
        return true;
      } else {
        setState(prev => ({ ...prev, isSaving: false }));
        toast.error(result.error || 'Failed to clear workflow');
        return false;
      }
    } catch (error) {
      setState(prev => ({ ...prev, isSaving: false }));
      toast.error('Unexpected error while clearing');
      return false;
    }
  }, []);

  // Validate workflow
  const validate = useCallback(async (nodes: Node[], edges: Edge[]): Promise<boolean> => {
    setState(prev => ({ ...prev, isValidating: true }));
    
    try {
      const result = await validateWorkflow(nodes, edges);
      
      if (result.success && result.data) {
        setState(prev => ({ 
          ...prev, 
          isValidating: false,
          validationResult: result.data
        }));
        
        if (result.data.is_valid) {
          toast.success('Workflow is valid');
        } else {
          toast.error(`Workflow has ${result.data.errors.length} error(s)`);
        }
        
        return result.data.is_valid;
      } else {
        setState(prev => ({ ...prev, isValidating: false }));
        toast.error(result.error || 'Failed to validate workflow');
        return false;
      }
    } catch (error) {
      setState(prev => ({ ...prev, isValidating: false }));
      toast.error('Unexpected error while validating');
      return false;
    }
  }, []);

  // Execute workflow
  const execute = useCallback(async (message: string, sessionId?: string) => {
    setState(prev => ({ ...prev, isExecuting: true }));
    
    try {
      const result = await executeWorkflow(message, sessionId);
      
      if (result.success) {
        setState(prev => ({ ...prev, isExecuting: false }));
        toast.success('Workflow executed successfully');
        return result.data;
      } else {
        setState(prev => ({ ...prev, isExecuting: false }));
        toast.error(result.error || 'Failed to execute workflow');
        return null;
      }
    } catch (error) {
      setState(prev => ({ ...prev, isExecuting: false }));
      toast.error('Unexpected error while executing');
      return null;
    }
  }, []);

  // Auto-save functionality
  const enableAutoSave = useCallback((nodes: Node[], edges: Edge[]) => {
    if (state.hasUnsavedChanges) {
      autoSaveWorkflow(nodes, edges, 3000); // 3 second delay
    }
  }, [state.hasUnsavedChanges]);

  const disableAutoSave = useCallback(() => {
    // Auto-save timeout is handled within the action itself
  }, []);

  // Mark as changed
  const markAsChanged = useCallback(() => {
    setState(prev => ({ ...prev, hasUnsavedChanges: true }));
  }, []);

  // Mark as saved
  const markAsSaved = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      hasUnsavedChanges: false,
      lastSaved: new Date()
    }));
  }, []);

  // Auto-save on changes (when enabled)
  useEffect(() => {
    if (state.hasUnsavedChanges) {
      // Could trigger auto-save here if needed
    }
  }, [state.hasUnsavedChanges]);

  return {
    ...state,
    save,
    load,
    clear,
    validate,
    execute,
    enableAutoSave,
    disableAutoSave,
    markAsChanged,
    markAsSaved,
  };
} 