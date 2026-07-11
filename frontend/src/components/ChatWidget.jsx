import React, { useEffect, useRef, useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { LANGUAGES, t } from '../i18n'

export default function ChatWidget() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [lang, setLang] = useState(user?.preferred_language || 'en')
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! Ask me about your balance, spending, or recent transactions.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages, open])

  const send = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', content: input }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const { data } = await api.post('/assistant/chat', { message: userMsg.content, language: lang })
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: "Sorry, I couldn't reach the assistant service." }])
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button className="chat-toggle" onClick={() => setOpen(true)} aria-label="Open banking assistant">
        💬
      </button>
    )
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span>🤖 {t(lang, 'assistant')}</span>
        <select className="lang-select" style={{ marginLeft: 'auto' }} value={lang} onChange={(e) => setLang(e.target.value)}>
          {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
        </select>
        <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', color: 'inherit', marginLeft: 8, fontSize: 16 }}>✕</button>
      </div>
      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>{m.content}</div>
        ))}
        {loading && <div className="chat-bubble assistant">Thinking…</div>}
      </div>
      <div className="chat-input-row">
        <input
          value={input}
          placeholder={t(lang, 'askPlaceholder')}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
        />
        <button className="btn" onClick={send}>Send</button>
      </div>
    </div>
  )
}
