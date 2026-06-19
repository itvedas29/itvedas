import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const NAV_ITEMS = ['New Chat', 'History', 'Analytics', 'Search Console', 'Tasks', 'Settings']

function TopNav() {
  return (
    <header className="topnav">
      <a className="logo" href="/">
        IT<span>Vedas</span>
      </a>
      <span className="topnav-divider" />
      <span className="topnav-product">Tango</span>
    </header>
  )
}

function Sidebar({ onNewChat }) {
  return (
    <nav className="sidebar">
      <ul className="nav-list">
        {NAV_ITEMS.map((item) => (
          <li key={item}>
            <button
              type="button"
              className="nav-item"
              onClick={item === 'New Chat' ? onNewChat : undefined}
            >
              {item}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  )
}

function ChatPane() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error reaching Tango: ${error.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  return (
    <main className="chat-pane">
      <div className="message-list">
        {messages.length === 0 && (
          <div className="empty-state">
            <p className="empty-state-title">Hi, I&apos;m Tango.</p>
            <p>Ask a business question, or check the dashboard on the right.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`message message-${message.role}`}>
            <span className="message-role">{message.role === 'user' ? 'You' : 'Tango'}</span>
            <p>{message.content}</p>
          </div>
        ))}
        {loading && <div className="message message-assistant">
          <span className="message-role">Tango</span>
          <p>Thinking...</p>
        </div>}
      </div>
      <div className="input-row">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Tango a business question..."
          rows={2}
        />
        <button type="button" onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </main>
  )
}

function CooDashboard() {
  const [context, setContext] = useState('Loading...')
  const [recommendations, setRecommendations] = useState('Loading...')
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const [contextRes, recommendRes] = await Promise.all([
          fetch(`${API_BASE}/api/context`),
          fetch(`${API_BASE}/api/recommend`),
        ])
        const contextData = await contextRes.json()
        const recommendData = await recommendRes.json()
        if (!cancelled) {
          setContext(contextData.context)
          setRecommendations(recommendData.recommendations)
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <aside className="coo-dashboard">
      <h2>Tango Dashboard</h2>
      {error && <p className="error-banner">Could not reach the API: {error}</p>}

      <section>
        <h3>Context</h3>
        <pre>{context}</pre>
      </section>

      <section>
        <h3>Recommendations</h3>
        <pre>{recommendations}</pre>
      </section>
    </aside>
  )
}

function App() {
  const [chatKey, setChatKey] = useState(0)

  return (
    <div className="app-shell">
      <TopNav />
      <div className="app-layout">
        <Sidebar onNewChat={() => setChatKey((key) => key + 1)} />
        <ChatPane key={chatKey} />
        <CooDashboard />
      </div>
    </div>
  )
}

export default App
