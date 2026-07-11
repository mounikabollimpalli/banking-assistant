import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from './Sidebar'
import ChatWidget from './ChatWidget'

export default function Layout({ children, adminOnly = false }) {
  const { user } = useAuth()

  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'bank_admin') return <Navigate to="/" replace />

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
      <ChatWidget />
    </div>
  )
}
