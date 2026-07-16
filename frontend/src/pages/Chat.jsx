import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, FileText, Sparkles, AlertCircle, Plus } from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { PageWrap } from '../components/ui'

const GREETING = {
  role: 'assistant',
  text: "Hi! I'm CivilAI. Ask me about forest clearance, DPRs, milestones, drainage, land acquisition, and other project documents.",
}

export default function Chat() {
  const storageKey = 'civilai-chat-history'
  const [messages, setMessages] = useState(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(storageKey) || 'null')
      return Array.isArray(saved) && saved.length ? saved : [GREETING]
    } catch {
      return [GREETING]
    }
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    window.localStorage.setItem(storageKey, JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  const send = async (e) => {
    e?.preventDefault()
    const query = input.trim()
    if (!query || loading) return

    setMessages((m) => [...m, { role: 'user', text: query }])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post('/api/v1/chat/generate', { query })
      const data = unwrap(res) || {}
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: data.answer || data.combined_context || 'No answer available.',
          sources: data.sources,
          meta: { cache_hit: data.cache_hit, llm: data.llm },
        },
      ])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: errMessage(err), error: true },
      ])
    } finally {
      setLoading(false)
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }

  return (
    <PageWrap>
      <div className="flex h-[calc(100vh-6rem)] flex-col md:h-[calc(100vh-8rem)]">
        <div className="mb-5 flex items-center gap-3">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-[#F97316] text-white">
            <Bot size={22} />
          </div>
          <div className="flex-1">
            <h1 className="font-display text-3xl font-bold leading-none text-[#111827]">CivilAI</h1>
            <p className="mt-1.5 text-sm text-[#6B7280]">Ask about your construction documents</p>
          </div>
          <button
            type="button"
            title="Start a new chat"
            aria-label="Start a new chat"
            onClick={() => setMessages([GREETING])}
            className="btn btn-ghost shrink-0 text-xs"
          >
            <Plus size={16} /> New chat
          </button>
        </div>

        <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <Bubble key={i} msg={msg} />
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="glass flex items-center gap-2 rounded-[24px] rounded-tl-md px-4 py-3">
                <Bot size={16} className="text-[#F97316]" />
                <TypingDots />
              </div>
            </motion.div>
          )}
        </div>

        <form onSubmit={send} className="glass mt-4 flex items-center gap-2 rounded-[28px] p-2">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            autoFocus
            placeholder="Ask CivilAI about your documents..."
            className="flex-1 bg-transparent px-3 py-2 text-sm text-[#111827] placeholder:text-slate-400 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn btn-primary shrink-0 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </PageWrap>
  )
}

function Bubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[80%] ${isUser ? 'order-2' : ''}`}>
        <div
          className={
            isUser
              ? 'rounded-[24px] rounded-tr-md bg-[#F97316] px-4 py-3 text-white shadow-[0_12px_24px_rgba(249,115,22,0.18)]'
              : msg.error
                ? 'rounded-[24px] rounded-tl-md border border-red-100 bg-red-50 px-4 py-3 text-red-700'
                : 'glass rounded-[24px] rounded-tl-md px-4 py-3 text-[#111827]'
          }
        >
          {!isUser && (
            <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#F97316]">
              {msg.error ? <AlertCircle size={13} /> : <Sparkles size={13} />}
              {msg.error ? 'Error' : 'CivilAI'}
              {msg.meta?.cache_hit && (
                <span className="ml-1 inline-flex items-center gap-0.5 rounded-full bg-orange-50 px-1.5 py-0.5 text-[9px] normal-case tracking-normal text-[#EA580C]">
                  cached
                </span>
              )}
              {msg.meta?.llm && (
                <span className="ml-1 inline-flex items-center rounded-full bg-slate-50 px-1.5 py-0.5 text-[9px] normal-case tracking-normal text-[#6B7280]">
                  {msg.meta.llm}
                </span>
              )}
            </div>
          )}
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>

          {!isUser && Array.isArray(msg.sources) && msg.sources.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {msg.sources.map((s, i) => (
                <span
                  key={i}
                  className="chip bg-slate-50 text-[11px] text-[#6B7280]"
                  title={typeof s.score === 'number' ? `relevance ${s.score.toFixed(3)}` : undefined}
                >
                  <FileText size={12} />
                  {s.source}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function TypingDots() {
  return (
    <span className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[#F97316]"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
          transition={{ repeat: Infinity, duration: 0.9, delay: i * 0.15 }}
        />
      ))}
    </span>
  )
}
