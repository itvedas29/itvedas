import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const TOKEN_KEY = 'itvedas_token'

function authHeader(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function LoginPage({ onLogin }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        setError('Incorrect password')
        return
      }
      const { token } = await res.json()
      localStorage.setItem(TOKEN_KEY, token)
      onLogin(token)
    } catch (err) {
      setError(`Could not reach API: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <a className="logo" href="/">IT<span>Vedas</span></a>
        <p className="login-subtitle">Tango COO Dashboard</p>
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="password"
            placeholder="Dashboard password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {error && <p className="login-error">{error}</p>}
          <button type="submit" disabled={loading || !password}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}

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

function ChatPane({ token }) {
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
        headers: { 'Content-Type': 'application/json', ...authHeader(token) },
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

function CooDashboard({ token }) {
  const [context, setContext] = useState('Loading...')
  const [recommendations, setRecommendations] = useState('Loading...')
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const [contextRes, recommendRes] = await Promise.all([
          fetch(`${API_BASE}/api/context`, { headers: authHeader(token) }),
          fetch(`${API_BASE}/api/recommend`, { headers: authHeader(token) }),
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
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))

  if (!token) {
    return <LoginPage onLogin={setToken} />
  }

  return (
    <div className="app-shell">
      <TopNav />
      <div className="app-layout">
        <Sidebar onNewChat={() => setChatKey((key) => key + 1)} />
        <ChatPane key={chatKey} token={token} />
        <CooDashboard token={token} />
      </div>
    </div>
  )
}

export default App
