import React, { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { t } from '../i18n'

const COLORS = ['#2BB794', '#E8B559', '#5B8DEF', '#E8615C', '#9B7EDE', '#4FC3D9']

export default function Dashboard() {
  const { user } = useAuth()
  const lang = user?.preferred_language || 'en'
  const [accounts, setAccounts] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [accRes, txnRes] = await Promise.all([
          api.get('/accounts/'),
          api.get('/transactions/'),
        ])
        setAccounts(accRes.data)
        setTransactions(txnRes.data)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0)
  const spend = transactions.filter((t) => ['withdrawal', 'transfer_out'].includes(t.type))
  const byCategory = {}
  spend.forEach((t) => { byCategory[t.category] = (byCategory[t.category] || 0) + t.amount })
  const chartData = Object.entries(byCategory).map(([name, value]) => ({ name, value }))

  const deposits = transactions.filter((t) => ['deposit', 'transfer_in'].includes(t.type))
    .reduce((s, t) => s + t.amount, 0)
  const withdrawals = spend.reduce((s, t) => s + t.amount, 0)

  if (loading) return <p style={{ color: 'var(--color-text-muted)' }}>Loading dashboard…</p>

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-eyebrow">Welcome back</div>
          <h1>{user?.business_name}</h1>
        </div>
      </div>

      <div className="card-grid">
        <div className="card">
          <div className="stat-label">{t(lang, 'balance')}</div>
          <div className="stat-value mono">₹{totalBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
        <div className="card">
          <div className="stat-label">Money in (all time)</div>
          <div className="stat-value mono">₹{deposits.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            <span className="tick up">▲ in</span>
          </div>
        </div>
        <div className="card">
          <div className="stat-label">Money out (all time)</div>
          <div className="stat-value mono">₹{withdrawals.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            <span className="tick down">▼ out</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>{t(lang, 'recent')}</h3>
          <table>
            <thead>
              <tr><th>Date</th><th>Type</th><th>Category</th><th>Amount</th></tr>
            </thead>
            <tbody>
              {transactions.slice(0, 8).map((tx) => (
                <tr key={tx.id}>
                  <td>{new Date(tx.timestamp).toLocaleDateString('en-IN')}</td>
                  <td><span className={`badge ${tx.type}`}>{tx.type.replace('_', ' ')}</span></td>
                  <td>{tx.category}</td>
                  <td className="mono">₹{tx.amount.toLocaleString('en-IN')}</td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr><td colSpan={4} style={{ color: 'var(--color-text-muted)' }}>No transactions yet — try a deposit from "Move Money".</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Spending by category</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>
                  {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v) => `₹${v.toLocaleString('en-IN')}`} contentStyle={{ background: '#1C2E48', border: '1px solid #263954', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: 'var(--color-text-muted)', fontSize: 14 }}>No spending recorded yet.</p>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 8 }}>
            {chartData.map((d, i) => (
              <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS[i % COLORS.length], display: 'inline-block' }} />
                {d.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
