/**
 * MCP (Model Context Protocol) type definitions
 * Used for type safety across the frontend when working with MCP server configurations
 */

export type MCPTransportType = 'stdio' | 'sse';

export interface MCPServerConfig {
  name?: string;
  transport: MCPTransportType;
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  timeout_seconds?: number;
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, any>;
}

export interface MCPServerMetadata {
  transport: string;
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  tools: MCPTool[];
}

export interface MCPCachedConfig {
  name: string;
  transport: string;
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  timeout_seconds?: number;
  tools_count: number;
  discovered_at: string;
  status: 'working' | 'active' | 'inactive' | 'error';
  cache_key: string;
  server_name: string;
}

export interface MCPServerResponse {
  message: string;
  server_name: string;
  tools_discovered: number;
  cached: boolean;
  metadata: MCPServerMetadata;
}

export interface MCPConfigsResponse {
  configs: MCPCachedConfig[];
  count: number;
}

// Form data types for UI components
export interface MCPServerFormData {
  name: string;
  transport: MCPTransportType;
  command: string;
  args: string;
  url: string;
  env: Record<string, string>;
  timeout_seconds: number;
}

// UI state types
export interface MCPServerState {
  isLoading: boolean;
  error: string | null;
  configs: MCPCachedConfig[];
  selectedConfig: MCPCachedConfig | null;
}

// Action result types
export interface MCPActionResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Validation types
export interface MCPValidationResult {
  success: boolean;
  error?: string;
}

// Example MCP server configurations for common use cases
export const MCP_EXAMPLES: Record<string, MCPServerConfig> = {
  filesystem: {
    name: 'Filesystem',
    transport: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/files'],
    timeout_seconds: 30,
  },
  git: {
    name: 'Git',
    transport: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-git', '--repository', 'path/to/git/repo'],
    timeout_seconds: 30,
  },
  postgres: {
    name: 'PostgreSQL',
    transport: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    env: {
      POSTGRES_CONNECTION_STRING: 'postgresql://user:password@localhost:5432/dbname',
    },
    timeout_seconds: 30,
  },
  puppeteer: {
    name: 'Puppeteer',
    transport: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-puppeteer'],
    timeout_seconds: 60,
  },
};

// MCP server status types
export type MCPServerStatus = 'connecting' | 'connected' | 'error' | 'disconnected';

// MCP configuration validation rules
export const MCP_VALIDATION_RULES = {
  MIN_TIMEOUT: 1,
  MAX_TIMEOUT: 300,
  REQUIRED_STDIO_FIELDS: ['command'] as const,
  REQUIRED_SSE_FIELDS: ['url'] as const,
} as const; 