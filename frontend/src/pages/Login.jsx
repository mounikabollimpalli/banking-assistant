import React, { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, error, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('owner@srisai.com')
  const [password, setPassword] = useState('password123')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    const ok = await login(email, password)
    setSubmitting(false)
    if (ok) navigate('/')
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand"><div className="dot" /><span>Vantage</span></div>
        <p className="auth-subtitle">Personalized banking assistant for SMBs</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn" type="submit" style={{ width: '100%' }} disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p style={{ marginTop: 20, fontSize: 13, color: 'var(--color-text-muted)' }}>
          New business? <Link to="/register" style={{ color: 'var(--color-accent)' }}>Create an account</Link>
        </p>
        <p style={{ marginTop: 16, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Demo logins — SMB: owner@srisai.com / password123 · Admin: admin@bank.com / admin123
        </p>
      </div>
    </div>
  )
}
