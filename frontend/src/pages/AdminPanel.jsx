import React, { useEffect, useState } from 'react'
import api from '../api'

export default function AdminPanel() {
  const [alerts, setAlerts] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [alertsRes, usersRes] = await Promise.all([
        api.get('/compliance/alerts'),
        api.get('/compliance/users'),
      ])
      setAlerts(alertsRes.data)
      setUsers(usersRes.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const resolve = async (id) => {
    await api.post(`/compliance/alerts/${id}/resolve`)
    load()
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-eyebrow">Bank admin</div>
          <h1>Compliance & Oversight</h1>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 16 }}>KYC / AML Alerts</h3>
        <table>
          <thead>
            <tr><th>Transaction</th><th>Reason</th><th>Severity</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td className="mono">#{a.transaction_id}</td>
                <td>{a.reason}</td>
                <td><span className={`badge ${a.severity}`}>{a.severity}</span></td>
                <td>{a.resolved ? '✅ Resolved' : '⏳ Pending'}</td>
                <td>
                  {!a.resolved && (
                    <button className="btn btn-secondary" onClick={() => resolve(a.id)}>Mark resolved</button>
                  )}
                </td>
              </tr>
            ))}
            {!loading && alerts.length === 0 && (
              <tr><td colSpan={5} style={{ color: 'var(--color-text-muted)' }}>No compliance alerts — all clear.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Registered SMB clients</h3>
        <table>
          <thead>
            <tr><th>Business</th><th>Email</th><th>Role</th><th>Language</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.business_name}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.preferred_language}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
