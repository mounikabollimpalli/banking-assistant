import React, { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register, error, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ business_name: '', email: '', password: '', preferred_language: 'en' })
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    const ok = await register(form)
    setSubmitting(false)
    if (ok) navigate('/')
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand"><div className="dot" /><span>Vantage</span></div>
        <p className="auth-subtitle">Set up your business banking account</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Business name</label>
            <input value={form.business_name} onChange={update('business_name')} required />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={update('email')} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={update('password')} required />
          </div>
          <div className="field">
            <label>Preferred language</label>
            <select value={form.preferred_language} onChange={update('preferred_language')}>
              <option value="en">English</option>
              <option value="hi">हिंदी</option>
              <option value="te">తెలుగు</option>
            </select>
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn" type="submit" style={{ width: '100%' }} disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p style={{ marginTop: 20, fontSize: 13, color: 'var(--color-text-muted)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--color-accent)' }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
