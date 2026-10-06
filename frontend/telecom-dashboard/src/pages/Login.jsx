import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import SignalBars from '../components/SignalBars.jsx'
import './Login.css'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const redirectTo = location.state?.from?.pathname || '/'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate(redirectTo, { replace: true })
    } catch {
      setError('Could not sign in. Check your username and password and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login">
      <div className="login__panel">
        <div className="login__mark">
          <SignalBars variant="meter" strength={4} label="Signal" />
          <span>PRODAPT</span>
        </div>
        <p className="login__tagline">Churn analytics for our telecom partners.</p>

        <form className="login__form" onSubmit={handleSubmit}>
          <h1>Sign in</h1>

          <label className="login__field">
            <span>Username</span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>

          <label className="login__field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className="login__error">{error}</p>}

          <button type="submit" className="login__submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>

      <div className="login__side" aria-hidden="true">
        <div className="login__bars">
          {[10, 18, 28, 40, 55, 34, 22, 46, 60, 15, 26, 38].map((h, i) => (
            <span key={i} style={{ height: h }} />
          ))}
        </div>
        <p className="login__side-caption">Live partner coverage, at a glance.</p>
      </div>
    </div>
  )
}
