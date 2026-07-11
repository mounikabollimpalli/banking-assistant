import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Transfer from './pages/Transfer'
import AdminPanel from './pages/AdminPanel'
import Layout from './components/Layout'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<Layout><Dashboard /></Layout>} />
      <Route path="/transactions" element={<Layout><Transactions /></Layout>} />
      <Route path="/transfer" element={<Layout><Transfer /></Layout>} />
      <Route path="/admin" element={<Layout adminOnly><AdminPanel /></Layout>} />
    </Routes>
  )
}
