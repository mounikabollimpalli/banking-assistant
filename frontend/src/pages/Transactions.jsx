import React, { useEffect, useState } from 'react'
import api from '../api'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState('')

  const load = async (cat) => {
    setLoading(true)
    try {
      const params = {}
      if (cat) params.category = cat
      const { data } = await api.get('/transactions/', { params })
      setTransactions(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const categories = Array.from(new Set(transactions.map((t) => t.category)))

  const downloadStatement = async (format) => {
    setDownloading(format)
    try {
      const params = { format }
      if (category) params.category = category
      const response = await api.get('/transactions/export', {
        params,
        responseType: 'blob',
      })
      const extension = format === 'excel' ? 'xlsx' : format
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `transactions.${extension}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      alert('Could not download statement. Please try again.')
    } finally {
      setDownloading('')
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-eyebrow">All activity</div>
          <h1>Transactions</h1>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            className="field"
            style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '8px 12px', color: 'var(--color-text)' }}
            value={category}
            onChange={(e) => { setCategory(e.target.value); load(e.target.value) }}
          >
            <option value="">All categories</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <button className="btn" disabled={downloading === 'csv'} onClick={() => downloadStatement('csv')}>
            {downloading === 'csv' ? 'Preparing…' : 'CSV'}
          </button>
          <button className="btn" disabled={downloading === 'excel'} onClick={() => downloadStatement('excel')}>
            {downloading === 'excel' ? 'Preparing…' : 'Excel'}
          </button>
          <button className="btn" disabled={downloading === 'pdf'} onClick={() => downloadStatement('pdf')}>
            {downloading === 'pdf' ? 'Preparing…' : 'PDF'}
          </button>
        </div>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Date</th><th>Type</th><th>Category</th><th>Description</th><th>Counterparty</th><th>Amount</th></tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id}>
                <td>{new Date(tx.timestamp).toLocaleString('en-IN')}</td>
                <td><span className={`badge ${tx.type}`}>{tx.type.replace('_', ' ')}</span></td>
                <td>{tx.category}</td>
                <td>{tx.description || '—'}</td>
                <td className="mono">{tx.counterparty_account || '—'}</td>
                <td className="mono">₹{tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
              </tr>
            ))}
            {!loading && transactions.length === 0 && (
              <tr><td colSpan={6} style={{ color: 'var(--color-text-muted)' }}>No transactions found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
