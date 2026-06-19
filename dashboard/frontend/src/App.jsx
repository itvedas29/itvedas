import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const TOKEN_KEY = 'tango_session_token'

const NAV_ITEMS = ['New Chat']

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

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

function LoginScreen({ onLogin }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Login failed')
      }
      const data = await res.json()
      onLogin(data.token)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <a className="logo" href="/">
          IT<span>Vedas</span>
        </a>
        <h1>Tango</h1>
        <p className="login-sub">Enter the dashboard password to continue.</p>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          autoFocus
        />
        {error && <p className="error-banner">{error}</p>}
        <button type="submit" disabled={loading || !password}>
          {loading ? 'Checking...' : 'Sign in'}
        </button>
      </form>
    </div>
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

function ChatPane({ token, onUnauthorized }) {
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
        headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
        body: JSON.stringify({ message: text }),
      })
      if (res.status === 401) return onUnauthorized()
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
            <div className="markdown-body">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
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

function CooDashboard({ token, onUnauthorized }) {
  const [context, setContext] = useState('Loading...')
  const [recommendations, setRecommendations] = useState('Loading...')
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const [contextRes, recommendRes] = await Promise.all([
          fetch(`${API_BASE}/api/context`, { headers: authHeaders(token) }),
          fetch(`${API_BASE}/api/recommend`, { headers: authHeaders(token) }),
        ])
        if (contextRes.status === 401 || recommendRes.status === 401) {
          return onUnauthorized()
        }
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
  }, [token, onUnauthorized])

  return (
    <aside className="coo-dashboard">
      <h2>Tango Dashboard</h2>
      {error && <p className="error-banner">Could not reach the API: {error}</p>}

      <section>
        <h3>Context</h3>
        <div className="markdown-body markdown-panel">
          <ReactMarkdown>{context}</ReactMarkdown>
        </div>
      </section>

      <section>
        <h3>Recommendations</h3>
        <div className="markdown-body markdown-panel">
          <ReactMarkdown>{recommendations}</ReactMarkdown>
        </div>
      </section>
    </aside>
  )
}

function App() {
  const [chatKey, setChatKey] = useState(0)
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY))

  const handleLogin = (newToken) => {
    sessionStorage.setItem(TOKEN_KEY, newToken)
    setToken(newToken)
  }

  const handleUnauthorized = () => {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken(null)
  }

  if (!token) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <div className="app-shell">
      <TopNav />
      <div className="app-layout">
        <Sidebar onNewChat={() => setChatKey((key) => key + 1)} />
        <ChatPane key={chatKey} token={token} onUnauthorized={handleUnauthorized} />
        <CooDashboard token={token} onUnauthorized={handleUnauthorized} />
      </div>
    </div>
  )
}

export default App
