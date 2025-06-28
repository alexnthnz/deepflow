'use server';

import { z } from 'zod';
import { API_URL, ENDPOINTS } from '@/lib/api';
import type { 
  MCPServerConfig, 
  MCPServerResponse, 
  MCPConfigsResponse,
  MCPActionResult,
  MCPValidationResult
} from '@/types/mcp';

// Input validation schema for MCP server metadata request
const MCPServerConfigSchema = z.object({
  name: z.string().optional(),
  transport: z.enum(['stdio', 'sse'], {
    required_error: 'Transport type is required',
    invalid_type_error: 'Transport must be either "stdio" or "sse"',
  }),
  command: z.string().optional(),
  args: z.array(z.string()).optional(),
  url: z.string().url().optional(),
  env: z.record(z.string()).optional(),
  timeout_seconds: z.number().int().min(1).max(300).optional(),
}).refine(data => {
  // Validation rules based on transport type
  if (data.transport === 'stdio' && !data.command) {
    return false;
  }
  if (data.transport === 'sse' && !data.url) {
    return false;
  }
  return true;
}, {
  message: 'Command is required for stdio transport, URL is required for sse transport',
});

/**
 * Add a new MCP server configuration and discover its tools
 * @param config The MCP server configuration
 * @returns The API response with discovered tools and metadata
 */
export async function addMCPServerConfig(config: MCPServerConfig): Promise<MCPActionResult<MCPServerResponse>> {
  try {
    // Validate the input
    const validatedData = MCPServerConfigSchema.parse(config);

    // Make the API request
    const response = await fetch(`${API_URL}${ENDPOINTS.MCP_SERVER_METADATA}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(validatedData),
    });

    // Check if the request was successful
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const errorMessage = errorData?.error || `Failed to add MCP server: ${response.status}`;
      throw new Error(errorMessage);
    }

    // Parse the JSON response
    const apiResponse = await response.json();
    
    // Transform the response to match our expected format
    return {
      success: true,
      data: {
        message: apiResponse.message || 'MCP server added successfully',
        server_name: apiResponse.meta?.server_name || 'Unknown',
        tools_discovered: apiResponse.meta?.tools_discovered || 0,
        cached: apiResponse.meta?.cached || false,
        metadata: apiResponse.data,
      },
    };
  } catch (error) {
    // If it's a Zod validation error, return a friendly message
    if (error instanceof z.ZodError) {
      const errorMessage = error.errors.map(err => `${err.path.join('.')}: ${err.message}`).join(', ');
      return { success: false, error: errorMessage };
    }
    
    // For other errors, return the error message
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * Get all cached MCP server configurations
 * @returns The list of cached MCP configurations
 */
export async function getCachedMCPConfigs(): Promise<MCPActionResult<MCPConfigsResponse>> {
  try {
    // Make the API request
    const response = await fetch(`${API_URL}${ENDPOINTS.MCP_CACHED_CONFIGS}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Check if the request was successful
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const errorMessage = errorData?.error || `Failed to get cached configs: ${response.status}`;
      throw new Error(errorMessage);
    }

    // Parse the JSON response
    const apiResponse = await response.json();
    
    // The backend returns configs directly in the data field (as an array)
    const configs = Array.isArray(apiResponse.data) ? apiResponse.data : [];
    
    // Return the data
    return {
      success: true,
      data: {
        configs: configs,
        count: configs.length,
      },
    };
  } catch (error) {
    // For errors, return the error message
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * Delete a cached MCP server configuration
 * @param serverName The name of the MCP server to delete
 * @returns The API response indicating success or failure
 */
export async function deleteMCPConfig(serverName: string): Promise<MCPActionResult<{ deleted_server_name: string; cache_key: string }>> {
  try {
    if (!serverName.trim()) {
      throw new Error('Server name is required');
    }

    // Make the API request
    const response = await fetch(`${API_URL}${ENDPOINTS.MCP_DELETE_CONFIG(serverName)}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Check if the request was successful
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      
      if (response.status === 404) {
        throw new Error(`MCP server '${serverName}' not found`);
      }
      
      const errorMessage = errorData?.error || `Failed to delete MCP server: ${response.status}`;
      throw new Error(errorMessage);
    }

    // Parse the JSON response
    const apiResponse = await response.json();
    
    // Return the data
    return {
      success: true,
      data: apiResponse.data || { deleted_server_name: serverName, cache_key: `mcp_config:${serverName}` },
    };
  } catch (error) {
    // For errors, return the error message
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * Validate MCP server configuration without saving
 * This is a helper function to validate the config format
 * @param config The MCP server configuration to validate
 * @returns Validation result
 */
export async function validateMCPConfig(config: unknown): Promise<MCPValidationResult> {
  try {
    MCPServerConfigSchema.parse(config);
    return { success: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessage = error.errors.map(err => `${err.path.join('.')}: ${err.message}`).join(', ');
      return { success: false, error: errorMessage };
    }
    return { success: false, error: 'Invalid configuration format' };
  }
} 