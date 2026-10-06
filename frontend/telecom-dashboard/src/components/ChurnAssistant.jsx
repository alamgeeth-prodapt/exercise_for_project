import { useState, useEffect, useRef } from 'react'
import SignalBars from './SignalBars.jsx'
import {
  sendChatMessage,
  getConversations,
  getConversationMessages,
  deleteConversation,
} from '../api/assistant.js'
import './ChurnAssistant.css'

const SUGGESTED_QUESTIONS = [
  '📊 What is the overall churn rate across telecom partners?',
  '⚠️ Which partner has the highest churn risk and why?',
  '🎯 Predict churn likelihood for Customer #1',
  '👥 What is the customer age breakdown and risk profile?',
  '💡 How can we retain high-risk Airtel subscribers?',
  '⚡ Simulate churn if Customer #1 uses 25 GB data',
]

/**
 * Lightweight, safe Markdown renderer tailored for Claude's formatted outputs
 * Supports headers, bold, bullet points, numbered lists, tables, and inline code.
 */
function MarkdownRenderer({ content }) {
  if (!content) return null

  // Split into lines
  const lines = content.split('\n')
  const elements = []
  let inList = false
  let listItems = []
  let inTable = false
  let tableRows = []

  function flushList() {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="churn-ai-list">
          {listItems.map((item, idx) => (
            <li key={idx}>{formatInline(item)}</li>
          ))}
        </ul>,
      )
      listItems = []
      inList = false
    }
  }

  function flushTable() {
    if (inTable && tableRows.length > 0) {
      const header = tableRows[0]
      const body = tableRows.slice(1).filter((r) => !r.every((c) => c.match(/^[-:| ]+$/)))

      elements.push(
        <div key={`table-wrapper-${elements.length}`} className="churn-ai-table-wrap">
          <table className="churn-ai-table">
            <thead>
              <tr>
                {header.map((cell, idx) => (
                  <th key={idx}>{formatInline(cell.trim())}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx}>{formatInline(cell.trim())}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      )
      tableRows = []
      inTable = false
    }
  }

  function formatInline(text) {
    if (!text) return text
    // Replace **bold** with <strong>
    const parts = []
    let remaining = text

    // Simple regex parser for bold, inline code
    const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g
    let match
    let lastIndex = 0

    while ((match = regex.exec(remaining)) !== null) {
      if (match.index > lastIndex) {
        parts.push(remaining.substring(lastIndex, match.index))
      }
      const token = match[0]
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(<strong key={lastIndex}>{token.slice(2, -2)}</strong>)
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(<code key={lastIndex} className="churn-ai-code">{token.slice(1, -1)}</code>)
      }
      lastIndex = regex.lastIndex
    }

    if (lastIndex < remaining.length) {
      parts.push(remaining.substring(lastIndex))
    }

    return parts.length > 0 ? parts : text
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]
    const trimmed = rawLine.trim()

    // Table row detection (| col | col |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flushList()
      inTable = true
      const cells = trimmed
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim())
      tableRows.push(cells)
      continue
    } else {
      flushTable()
    }

    // Bullet points
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true
      listItems.push(trimmed.slice(2))
      continue
    } else if (trimmed.match(/^\d+\.\s/)) {
      // Numbered items
      inList = true
      listItems.push(trimmed.replace(/^\d+\.\s/, ''))
      continue
    } else {
      flushList()
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={i} className="churn-ai-h4">
          {formatInline(trimmed.slice(4))}
        </h4>,
      )
    } else if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="churn-ai-h3">
          {formatInline(trimmed.slice(3))}
        </h3>,
      )
    } else if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="churn-ai-h2">
          {formatInline(trimmed.slice(2))}
        </h2>,
      )
    } else if (trimmed.length === 0) {
      // Empty line / spacer
      elements.push(<div key={i} className="churn-ai-spacer" />)
    } else {
      // Paragraph
      elements.push(
        <p key={i} className="churn-ai-p">
          {formatInline(rawLine)}
        </p>,
      )
    }
  }

  flushList()
  flushTable()

  return <div className="churn-ai-markdown">{elements}</div>
}

export default function ChurnAssistant() {
  // 'closed', 'normal', 'expanded'
  const [viewState, setViewState] = useState('closed')
  const [conversations, setConversations] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(() => {
    return localStorage.getItem('churn_assistant_session_id') || null
  })
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [error, setError] = useState('')
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false)

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll messages
  useEffect(() => {
    if (viewState !== 'closed') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading, viewState])

  // Load conversation list on open
  useEffect(() => {
    if (viewState !== 'closed') {
      fetchConversations()
    }
  }, [viewState])

  // Load message history when session changes
  useEffect(() => {
    if (currentSessionId && viewState !== 'closed') {
      loadSessionMessages(currentSessionId)
      localStorage.setItem('churn_assistant_session_id', currentSessionId)
    } else if (!currentSessionId) {
      localStorage.removeItem('churn_assistant_session_id')
      setMessages([])
    }
  }, [currentSessionId, viewState])

  async function fetchConversations() {
    try {
      const data = await getConversations()
      setConversations(data)
      // If we don't have a current session but there are conversations, default to newest
      if (!currentSessionId && data.length > 0) {
        setCurrentSessionId(data[0].conversation_id)
      }
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }

  async function loadSessionMessages(sessionId) {
    setLoadingHistory(true)
    setError('')
    try {
      const msgs = await getConversationMessages(sessionId)
      setMessages(msgs)
    } catch (err) {
      setError(err.message || 'Could not load conversation messages.')
    } finally {
      setLoadingHistory(false)
    }
  }

  function handleNewChat() {
    setCurrentSessionId(null)
    setMessages([])
    setError('')
    setInputMessage('')
    setShowHistoryDrawer(false)
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  async function handleDeleteConversation(e, sessionId) {
    e.stopPropagation()
    try {
      await deleteConversation(sessionId)
      setConversations((prev) => prev.filter((c) => c.conversation_id !== sessionId))
      if (currentSessionId === sessionId) {
        handleNewChat()
      }
    } catch (err) {
      alert('Failed to delete conversation: ' + err.message)
    }
  }

  async function handleSend(customText = null) {
    const textToSend = (customText !== null ? customText : inputMessage).trim()
    if (!textToSend || loading) return

    setInputMessage('')
    setError('')

    // Optimistic UI for user message
    const tempUserMsg = {
      message_id: Date.now(),
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])
    setLoading(true)

    try {
      const res = await sendChatMessage(textToSend, currentSessionId)
      if (!currentSessionId) {
        setCurrentSessionId(res.conversation_id)
        localStorage.setItem('churn_assistant_session_id', res.conversation_id)
      }

      const assistantMsg = {
        message_id: Date.now() + 1,
        role: 'assistant',
        content: res.reply,
        tool_calls: res.tool_calls,
        created_at: res.created_at,
      }

      setMessages((prev) => [...prev, assistantMsg])
      // Refresh list to update message count / title
      fetchConversations()
    } catch (err) {
      setError(err.message || 'Failed to get response from Claude.')
    } finally {
      setLoading(false)
      setTimeout(() => textareaRef.current?.focus(), 50)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function toggleExpand() {
    setViewState((prev) => (prev === 'normal' ? 'expanded' : 'normal'))
  }

  function formatToolName(toolName) {
    const names = {
      get_churn_analytics: '📊 Analyzed Churn Rates',
      get_customer_distribution: '🌐 Checked Network Distribution',
      get_demographics_distribution: '👥 Evaluated Demographics',
      get_risk_distribution: '⚠️ Inspected Risk Categories',
      search_customers: '🔍 Queried Customer Records',
      get_customer_profile: '👤 Loaded Customer Profile',
      predict_customer_churn: '⚡ Ran ML Churn Prediction',
      simulate_custom_prediction: '🧪 Simulated What-If Scenario',
    }
    return names[toolName] || `⚡ ${toolName}`
  }

  const activeTitle =
    conversations.find((c) => c.conversation_id === currentSessionId)?.title ||
    (messages.length > 0 ? 'Active Analysis' : 'New Churn Conversation')

  return (
    <div className="churn-assistant-root">
      {/* 1. Floating Launcher Pill / Button */}
      {viewState === 'closed' && (
        <button
          type="button"
          className="churn-assistant__launcher"
          onClick={() => setViewState('normal')}
          aria-label="Open Telecom Churn AI Assistant"
        >
          <div className="launcher__icon-wrap">
            <span className="launcher__sparkle">✦</span>
            <span className="launcher__pulse" />
          </div>
          <span className="launcher__text">Churn AI Assistant</span>
          {conversations.length > 0 && (
            <span className="launcher__badge" title={`${conversations.length} saved chats`}>
              {conversations.length}
            </span>
          )}
        </button>
      )}

      {/* 2. Floating Window (Normal or Expanded) */}
      {viewState !== 'closed' && (
        <div
          className={`churn-assistant__window ${
            viewState === 'expanded' ? 'churn-assistant__window--expanded' : ''
          }`}
        >
          {/* Header Bar */}
          <header className="churn-assistant__header">
            <div className="header__left">
              <div className="header__avatar">
                <span>✦</span>
              </div>
              <div className="header__info">
                <div className="header__title-row">
                  <h3 className="header__title">{activeTitle}</h3>
                  <span className="header__status-dot" title="Claude Intelligence Online" />
                </div>
                <span className="header__subtitle">
                  Powered by Claude & ML Churn Engine
                </span>
              </div>
            </div>

            <div className="header__actions">
              {/* History Toggle */}
              <button
                type="button"
                className={`header__btn ${showHistoryDrawer ? 'header__btn--active' : ''}`}
                onClick={() => setShowHistoryDrawer((p) => !p)}
                title="Conversation History"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>History</span>
              </button>

              {/* New Chat */}
              <button
                type="button"
                className="header__btn"
                onClick={handleNewChat}
                title="Start New Conversation"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
                <span>New</span>
              </button>

              {/* Expand / Minimize Window */}
              <button
                type="button"
                className="header__btn"
                onClick={toggleExpand}
                title={viewState === 'expanded' ? 'Collapse window' : 'Expand window'}
              >
                {viewState === 'expanded' ? (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 14h6m0 0v6m0-6L3 21m17-7h-6m0 0v6m0-6l7 7M4 10h6m0 0V4m0 6L3 3m17 7h-6m0 0V4m0 6l7-7" />
                  </svg>
                ) : (
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h6m0 0v6m0-6l-7 7M9 21H3m0 0v-6m0 6l7-7" />
                  </svg>
                )}
              </button>

              {/* Close / Minimize */}
              <button
                type="button"
                className="header__btn header__btn--close"
                onClick={() => setViewState('closed')}
                title="Close Assistant"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </header>

          {/* Main Body Area: Split into History Drawer (optional or left-side) + Chat View */}
          <div className="churn-assistant__body">
            {/* History Panel (Visible when toggled or expanded) */}
            {(showHistoryDrawer || viewState === 'expanded') && (
              <aside className="churn-assistant__sidebar">
                <div className="sidebar__header">
                  <span>Chat Threads ({conversations.length})</span>
                  <button type="button" className="sidebar__new-btn" onClick={handleNewChat}>
                    + New
                  </button>
                </div>

                <div className="sidebar__list">
                  {conversations.length === 0 && (
                    <div className="sidebar__empty">No past conversations yet.</div>
                  )}

                  {conversations.map((c) => (
                    <div
                      key={c.conversation_id}
                      className={`sidebar__item ${
                        c.conversation_id === currentSessionId ? 'sidebar__item--active' : ''
                      }`}
                      onClick={() => {
                        setCurrentSessionId(c.conversation_id)
                        if (viewState === 'normal') setShowHistoryDrawer(false)
                      }}
                    >
                      <div className="sidebar__item-text">
                        <strong className="sidebar__item-title">{c.title}</strong>
                        <span className="sidebar__item-meta">
                          {c.message_count} messages • {new Date(c.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                      <button
                        type="button"
                        className="sidebar__item-del"
                        onClick={(e) => handleDeleteConversation(e, c.conversation_id)}
                        title="Delete this chat"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </aside>
            )}

            {/* Chat Thread Container */}
            <main className="churn-assistant__chat">
              {/* Message List */}
              <div className="chat__messages">
                {loadingHistory && (
                  <div className="chat__loading-history">
                    <SignalBars variant="loading" label="Loading History" />
                    <span>Retrieving prior analysis…</span>
                  </div>
                )}

                {/* Empty State / Welcome Screen */}
                {!loadingHistory && messages.length === 0 && (
                  <div className="chat__welcome">
                    <div className="welcome__badge">
                      <span>✦</span>
                      <span>Telecom Retention Specialist</span>
                    </div>
                    <h4>How can I assist your churn strategy today?</h4>
                    <p>
                      Ask questions about partner churn rates, inspect subscriber profiles, run
                      real-time ML predictions, or simulate hypothetical retention scenarios.
                    </p>

                    <div className="welcome__suggestions">
                      <span className="suggestions__label">Suggested Prompts:</span>
                      <div className="suggestions__grid">
                        {SUGGESTED_QUESTIONS.map((q, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className="suggestion-chip"
                            onClick={() => handleSend(q)}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Messages stream */}
                {messages.map((msg, index) => {
                  const isUser = msg.role === 'user'
                  return (
                    <div
                      key={msg.message_id || index}
                      className={`chat__message-row ${
                        isUser ? 'chat__message-row--user' : 'chat__message-row--assistant'
                      }`}
                    >
                      {!isUser && (
                        <div className="chat__msg-avatar" title="Claude Assistant">
                          ✦
                        </div>
                      )}

                      <div className="chat__msg-bubble">
                        {/* If tools were executed by this turn */}
                        {!isUser && msg.tool_calls && msg.tool_calls.length > 0 && (
                          <div className="chat__tool-chips">
                            {msg.tool_calls.map((t, tIdx) => (
                              <span key={tIdx} className="tool-chip" title={JSON.stringify(t.input)}>
                                {formatToolName(t.tool || t)}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Render markdown content */}
                        <MarkdownRenderer content={msg.content} />

                        <div className="chat__msg-time">
                          {msg.created_at
                            ? new Date(msg.created_at).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : ''}
                        </div>
                      </div>
                    </div>
                  )
                })}

                {/* Loading / Thinking indicator */}
                {loading && (
                  <div className="chat__message-row chat__message-row--assistant">
                    <div className="chat__msg-avatar">✦</div>
                    <div className="chat__msg-bubble chat__msg-bubble--loading">
                      <SignalBars variant="loading" label="Analyzing" />
                      <span className="loading-text">
                        Querying telecom database & computing ML predictions…
                      </span>
                    </div>
                  </div>
                )}

                {/* Error Banner */}
                {error && (
                  <div className="chat__error-banner">
                    <span>⚠️ {error}</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Suggestions bar when chatting */}
              {messages.length > 0 && !loading && (
                <div className="chat__quick-bar">
                  <button
                    type="button"
                    className="quick-chip"
                    onClick={() => handleSend('What retention strategies do you recommend for this?')}
                  >
                    💡 Recommend Retention Levers
                  </button>
                  <button
                    type="button"
                    className="quick-chip"
                    onClick={() => handleSend('Compare churn rates between Airtel and Jio')}
                  >
                    📊 Airtel vs Jio Comparison
                  </button>
                </div>
              )}

              {/* Input Footer */}
              <footer className="chat__input-bar">
                <textarea
                  ref={textareaRef}
                  className="chat__textarea"
                  placeholder="Ask about churn rates, Customer IDs, ML predictions, or retention plans…"
                  rows="1"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="chat__send-btn"
                  onClick={() => handleSend()}
                  disabled={!inputMessage.trim() || loading}
                  aria-label="Send message"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                  </svg>
                </button>
              </footer>
            </main>
          </div>
        </div>
      )}
    </div>
  )
}
