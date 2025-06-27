# Dynamic Graph Execute API Documentation

## Overview
The Dynamic Graph Execute API (`/api/v1/graphs/execute`) now supports both new chat sessions and continuing existing conversations, similar to the static graph chat API.

## Endpoint
```
POST /api/v1/graphs/execute
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | ✅ Yes | - | The user's input message (min 1 character) |
| `is_new_chat` | boolean | ❌ No | `false` | Whether to start a new chat session |
| `session_id` | string | ❌ Conditional | - | Required when `is_new_chat=false`. Must be UUID format |
| `chat_id` | string | ❌ No | `null` | Optional chat ID for database linking |
| `graph_name` | string | ❌ No | `"default"` | Graph configuration name (max 100 chars) |

## Validation Rules

1. **New Chat**: When `is_new_chat=true`
   - `session_id` is optional (will be auto-generated)
   - A new UUID session ID is created automatically

2. **Existing Chat**: When `is_new_chat=false` (default)
   - `session_id` is **required**
   - Must be a valid UUID format
   - Conversation history is loaded from database

3. **Boolean Handling**: `is_new_chat` accepts multiple formats:
   - `true`, `"true"`, `"True"`, `1`, `"1"`
   - `false`, `"false"`, `"False"`, `0`, `"0"`, `null`

## Response Format

```json
{
  "message": "Graph executed successfully",
  "status_code": 200,
  "data": {
    "execution_id": "uuid",
    "session_id": "uuid",
    "messages": [
      {
        "type": "system|human|ai",
        "content": "message content",
        "additional_kwargs": {},
        "response_metadata": {},
        "name": null,
        "id": "uuid",
        "example": false
      }
    ],
    "node_executions": [],
    "status": "completed|failed",
    "attempts": 1,
    "error": null
  },
  "error": null,
  "meta": null
}
```

## Usage Examples

### 1. Start a New Conversation

```bash
curl -X POST http://localhost:8000/api/v1/graphs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! I am starting a new conversation.",
    "is_new_chat": true
  }'
```

**Response:**
```json
{
  "message": "Graph executed successfully",
  "status_code": 200,
  "data": {
    "execution_id": "abc123...",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
      {
        "type": "human",
        "content": "Hello! I am starting a new conversation."
      },
      {
        "type": "ai", 
        "content": "Hello! How can I help you today?"
      }
    ],
    "status": "completed"
  }
}
```

### 2. Continue an Existing Conversation

```bash
curl -X POST http://localhost:8000/api/v1/graphs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did I say in my first message?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_new_chat": false
  }'
```

**Response:**
```json
{
  "message": "Graph executed successfully", 
  "status_code": 200,
  "data": {
    "execution_id": "def456...",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
      {
        "type": "human",
        "content": "What did I say in my first message?"
      },
      {
        "type": "ai",
        "content": "In your first message, you said 'Hello! I am starting a new conversation.'"
      }
    ],
    "status": "completed"
  }
}
```

### 3. Continue Conversation (Simplified)

Since `is_new_chat` defaults to `false`, you can omit it:

```bash
curl -X POST http://localhost:8000/api/v1/graphs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about AI",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## Error Handling

### Missing session_id for existing chat
```bash
curl -X POST http://localhost:8000/api/v1/graphs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "This will fail",
    "is_new_chat": false
  }'
```

**Error Response:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, session_id is required when is_new_chat is False",
      "input": {"message": "This will fail", "is_new_chat": false}
    }
  ]
}
```

### Invalid session_id format
```bash
curl -X POST http://localhost:8000/api/v1/graphs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "session_id": "invalid-format"
  }'
```

**Error Response:**
```json
{
  "message": "Graph executed successfully",
  "status_code": 200,
  "data": {
    "status": "failed",
    "error": "Invalid session id. Session id must be a valid UUID. Got invalid-format"
  }
}
```

## Conversation Features

### ✅ **Conversation Persistence**
- All conversations are stored in PostgreSQL using `PostgresChatMessageHistory`
- Each `session_id` maintains a separate conversation thread
- Messages are automatically saved after each execution

### ✅ **Context Window**
- Last 10 messages are used for conversation context
- Automatic system prompt injection for AI guidance
- Context is filtered when saving to avoid duplication

### ✅ **Session Management**
- New sessions: Auto-generated UUID session IDs
- Existing sessions: Load conversation history from database
- Session isolation: Each session_id is completely independent

### ✅ **Backward Compatibility**
- Default `is_new_chat=false` maintains existing behavior
- Existing API calls continue to work without changes
- Optional parameters don't break existing integrations

## Comparison with Static Graph

| Feature | Static Graph (`/api/v1/chats/messages`) | Dynamic Graph (`/api/v1/graphs/execute`) |
|---------|----------------------------------------|------------------------------------------|
| New Chat | `is_new_chat=true` | `is_new_chat=true` ✅ |
| Continue Chat | `session_id` required | `session_id` required ✅ |
| Session ID Generation | Auto-generated UUID | Auto-generated UUID ✅ |
| Conversation History | PostgresChatMessageHistory | PostgresChatMessageHistory ✅ |
| Validation | Pydantic validation | Pydantic validation ✅ |
| Response Format | Custom JSON | CommonResponse wrapper |

The dynamic graph now has **feature parity** with the static graph for conversation management! 🚀 