import React, { useEffect, useState } from 'react'
import api from '../api'

const CATEGORIES = ['general', 'supplies', 'payroll', 'utilities', 'rent', 'marketing', 'equipment']

export default function Transfer() {
  const [mode, setMode] = useState('deposit') // deposit | withdraw | transfer
  const [accounts, setAccounts] = useState([])
  const [accountId, setAccountId] = useState('')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('general')
  const [description, setDescription] = useState('')
  const [toAccount, setToAccount] = useState('')
  const [message, setMessage] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const loadAccounts = async () => {
    const { data } = await api.get('/accounts/')
    setAccounts(data)
    if (data.length && !accountId) setAccountId(data[0].id)
  }

  useEffect(() => { loadAccounts() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage(null)
    setSubmitting(true)
    try {
      if (mode === 'deposit') {
        await api.post('/accounts/deposit', { account_id: Number(accountId), amount: Number(amount), category, description })
      } else if (mode === 'withdraw') {
        await api.post('/accounts/withdraw', { account_id: Number(accountId), amount: Number(amount), category, description })
      } else {
        await api.post('/accounts/transfer', { from_account_id: Number(accountId), to_account_number: toAccount, amount: Number(amount), description })
      }
      setMessage({ type: 'success', text: 'Transaction completed successfully.' })
      setAmount('')
      setDescription('')
      await loadAccounts()
    } catch (err) {
      setMessage({ type: 'error', text: err?.response?.data?.detail || 'Transaction failed.' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-eyebrow">Move money</div>
          <h1>Deposit, withdraw or transfer</h1>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['deposit', 'withdraw', 'transfer'].map((m) => (
          <button
            key={m}
            className={mode === m ? 'btn' : 'btn btn-secondary'}
            onClick={() => setMode(m)}
            type="button"
          >
            {m[0].toUpperCase() + m.slice(1)}
          </button>
        ))}
      </div>

      <div className="card" style={{ maxWidth: 480 }}>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Account</label>
            <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.account_number} — ₹{a.balance.toLocaleString('en-IN')}</option>
              ))}
            </select>
          </div>

          {mode === 'transfer' && (
            <div className="field">
              <label>Destination account number</label>
              <input value={toAccount} onChange={(e) => setToAccount(e.target.value)} placeholder="SMB12345678" required />
            </div>
          )}

          <div className="field">
            <label>Amount (₹)</label>
            <input type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </div>

          {mode !== 'transfer' && (
            <div className="field">
              <label>Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          )}

          <div className="field">
            <label>Description (optional)</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>

          {message && (
            <p className={message.type === 'error' ? 'error-text' : ''} style={message.type === 'success' ? { color: 'var(--color-accent)', fontSize: 13 } : {}}>
              {message.text}
            </p>
          )}

          <button className="btn" type="submit" style={{ width: '100%' }} disabled={submitting}>
            {submitting ? 'Processing…' : 'Confirm'}
          </button>
        </form>
      </div>
    </div>
  )
}
