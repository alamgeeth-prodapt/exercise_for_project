import { apiClient } from './client'

// POST /assistant/chat -> { conversation_id, title, reply, tool_calls, created_at }
export async function sendChatMessage(message, conversationId = null) {
  try {
    const { data } = await apiClient.post('/assistant/chat', {
      message,
      conversation_id: conversationId || undefined,
    })
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Failed to communicate with Churn Assistant.')
  }
}

// GET /assistant/conversations -> [{ conversation_id, title, created_at, updated_at, message_count }]
export async function getConversations() {
  try {
    const { data } = await apiClient.get('/assistant/conversations')
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Failed to fetch conversation history.')
  }
}

// GET /assistant/conversations/{conversation_id} -> [{ message_id, role, content, tool_calls, created_at }]
export async function getConversationMessages(conversationId) {
  try {
    const { data } = await apiClient.get(`/assistant/conversations/${conversationId}`)
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Failed to fetch messages for this conversation.')
  }
}

// DELETE /assistant/conversations/{conversation_id}
export async function deleteConversation(conversationId) {
  try {
    const { data } = await apiClient.delete(`/assistant/conversations/${conversationId}`)
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Failed to delete conversation.')
  }
}

// POST /assistant/conversations
export async function createConversation() {
  try {
    const { data } = await apiClient.post('/assistant/conversations')
    return data
  } catch (err) {
    const detail = err.response?.data?.detail
    throw new Error(detail || 'Failed to initialize new conversation.')
  }
}
