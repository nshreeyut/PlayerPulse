/**
 * ChatPanel Component
 * ====================
 * The AI analyst chatbot interface. Lives in the right column of the home page.
 * Pre-loaded with the current player's context so the LLM knows who you're asking about.
 *
 * PROPS:
 *   playerContext — the full player data object (or null if no player is selected)
 *                  passed to useChat() → sent to the API → given to the LangChain agent
 *
 * WHAT TO RENDER:
 *
 * 1. CHAT HEADER
 *    Title: "AI Analyst"
 *    If playerContext is set, show: "Analyzing: {player_id} on {platform}"
 *
 * 2. MESSAGE LIST (scrollable)
 *    Map over messages from useChat():
 *      - User messages:     right-aligned, different background
 *      - Assistant messages: left-aligned, with a small AI icon or label
 *    Show streamingMessage as a live "typing" bubble at the bottom when loading=true
 *    Auto-scroll to bottom when new messages arrive (useEffect + useRef on the list div)
 *
 * 3. SUGGESTED QUESTIONS (show when chat is empty)
 *    To help users get started, show clickable example questions:
 *      - "Why is this player predicted to churn?"
 *      - "What does engagement score mean?"
 *      - "How can we retain this player?"
 *      - "What's the overall churn rate in the dataset?"
 *    Clicking one fills the input and sends it.
 *
 * 4. INPUT BAR
 *    - A text <input> for typing a message
 *    - A Send button (disabled while loading=true)
 *    - Submit on Enter key OR button click
 *
 * AUTO-SCROLL TRICK:
 * ------------------
 * To scroll to the bottom when messages update:
 *   const bottomRef = useRef(null)
 *   useEffect(() => {
 *     bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
 *   }, [messages, streamingMessage])
 *   // At the bottom of your message list: <div ref={bottomRef} />
 *
 * TODO: Implement this component.
 * The useChat hook gives you everything you need:
 *   const { messages, streamingMessage, loading, sendMessage } = useChat(playerContext)
 */

import { useState, useEffect, useRef } from 'react'
import { useChat } from '../../hooks/useChat'
import './ChatPanel.css'

const DEFAULT_SUGGESTED_QUESTIONS = [
  "Why is this player predicted to churn?",
  "What does the engagement score mean?",
  "How can we retain this player?",
  "What's the overall churn rate in the dataset?",
]

/**
 * @param {object}   playerContext        — current player data (passed to the chat hook for LLM context)
 * @param {Function} [streamFn]           — optional custom stream function (used by demo mode)
 * @param {string[]} [suggestedQuestions] — override default suggested questions
 */
function ChatPanel({ playerContext, streamFn, suggestedQuestions = DEFAULT_SUGGESTED_QUESTIONS }) {
  const { messages, streamingMessage, loading, sendMessage } = useChat(playerContext, streamFn)
  const [inputText, setInputText] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  function handleSubmit(e) {
    e.preventDefault()
    if (!inputText.trim() || loading) return
    sendMessage(inputText.trim())
    setInputText('')
  }

  function handleSuggestion(q) {
    sendMessage(q)
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>AI Analyst</h2>
        {playerContext && (
          <span className="chat-context-label">
            {playerContext.player_id} · {playerContext.platform}
          </span>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message message-${msg.role}`}>
            {msg.content}
          </div>
        ))}

        {streamingMessage && (
          <div className="message message-assistant message-streaming">
            {streamingMessage}
            <span className="typing-cursor" />
          </div>
        )}

        {loading && !streamingMessage && (
          <div className="message message-assistant message-streaming">
            <span className="typing-cursor" />
          </div>
        )}

        {messages.length === 0 && !loading && (
          <div className="suggested-questions">
            <p className="suggested-label">Try asking:</p>
            {suggestedQuestions.map((q) => (
              <button key={q} className="suggestion-btn" onClick={() => handleSuggestion(q)}>
                {q}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={playerContext ? `Ask me about ${playerContext.player_id}…` : 'Ask about this player or the dataset…'}
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading || !inputText.trim()} className="chat-send-btn">
          {loading ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default ChatPanel
