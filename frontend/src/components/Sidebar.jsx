import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { t } from '../i18n'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const lang = user?.preferred_language || 'en'

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="dot" />
        <span>Vantage</span>
      </div>

      <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
        {t(lang, 'dashboard')}
      </NavLink>
      <NavLink to="/transactions" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
        {t(lang, 'transactions')}
      </NavLink>
      <NavLink to="/transfer" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
        {t(lang, 'transfer')}
      </NavLink>
      {user?.role === 'bank_admin' && (
        <NavLink to="/admin" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
          {t(lang, 'admin')}
        </NavLink>
      )}

      <div style={{ flex: 1 }} />
      <button className="nav-link" style={{ border: 'none', background: 'none', textAlign: 'left' }} onClick={logout}>
        {t(lang, 'logout')}
      </button>
    </aside>
  )
}
