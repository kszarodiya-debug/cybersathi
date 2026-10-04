import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { Modal } from '../components/Modal'
import { Textarea } from '../components/Textarea'
import { apiRequest, ApiError } from '../services/api'
import type { ChatHistoryResponse, ChatMessage } from '../types/chat'

const suggestedQuestions = [
  'What is phishing?',
  'How do I secure my account?',
  'What is 2FA?',
  'Someone sent me a suspicious message. What should I do?',
]

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' }).format(new Date(value))
}

function ChatTurn({ turn }: { turn: ChatMessage }) {
  return <article className="grid gap-4" aria-label={`Conversation from ${formatTime(turn.created_at)}`}><div className="ml-auto max-w-3xl rounded-3xl rounded-br-md bg-ink px-5 py-4 text-sm leading-7 text-white shadow-lg shadow-ink/10"><p className="mb-2 text-[11px] font-black uppercase tracking-[0.16em] text-signal">You</p><p className="whitespace-pre-wrap">{turn.message}</p></div><div className="max-w-3xl rounded-3xl rounded-bl-md border border-teal/15 bg-white px-5 py-4 text-sm leading-7 text-ink shadow-sm"><p className="mb-2 flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.16em] text-teal"><span className="grid h-5 w-5 place-items-center rounded-md bg-ink text-[10px] text-signal" aria-hidden="true">C</span>CyberSathi</p><p className="whitespace-pre-wrap">{turn.response}</p><p className="mt-3 text-xs text-ink/40">{formatTime(turn.created_at)}</p></div></article>
}

export function ChatPage() {
  const { user, authenticatedRequest } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')
  const [clearOpen, setClearOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadHistory = useCallback(async () => {
    setLoading(true)
    setError('')
    if (!user) {
      setMessages([])
      setLoading(false)
      return
    }
    try {
      const result = await authenticatedRequest<ChatHistoryResponse>('/chat/history')
      setMessages(result.messages)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load your conversation right now.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, user])

  useEffect(() => { void loadHistory() }, [loadHistory])
  useEffect(() => { messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' }) }, [messages, sending])

  const submitMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const message = draft.trim()
    if (!message) {
      setValidationError('Write a question before sending.')
      return
    }
    if (message.length > 2000) {
      setValidationError('Keep your question under 2,000 characters.')
      return
    }
    setValidationError('')
    setError('')
    setSending(true)
    try {
      const result = await (user
        ? authenticatedRequest<ChatMessage>('/chat', { method: 'POST', body: JSON.stringify({ message }) })
        : apiRequest<ChatMessage>('/chat', { method: 'POST', body: JSON.stringify({ message }) }))
      setMessages((current) => [...current, result])
      setDraft('')
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to reach CyberSathi right now.')
    } finally {
      setSending(false)
    }
  }

  const handleComposerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  const clearConversation = async () => {
    setError('')
    if (!user) {
      setMessages([])
      setClearOpen(false)
      return
    }
    try {
      await authenticatedRequest('/chat/history', { method: 'DELETE' })
      setMessages([])
      setClearOpen(false)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to clear this conversation right now.')
    }
  }

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
    <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to={user ? '/dashboard' : '/'}>← Back to CyberSathi</Link><p className="mt-8 text-xs font-black uppercase tracking-[0.2em] text-teal">AI cybersecurity awareness</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Ask CyberSathi.</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-ink/60">Get calm, educational guidance for everyday cybersecurity questions and safer next steps.</p></div><Button variant="secondary" type="button" disabled={messages.length === 0 || sending} onClick={() => setClearOpen(true)}>Clear conversation</Button></div>
    <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start"><Card className="overflow-hidden p-0"><div className="border-b border-ink/10 bg-ink px-6 py-5 text-white sm:px-8"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-signal text-lg font-black text-ink" aria-hidden="true">C</span><div><p className="font-black">CyberSathi assistant</p><p className="mt-1 text-xs text-white/55">Defensive guidance for your campus life</p></div></div></div><div className="min-h-[360px] space-y-6 bg-mist/70 p-5 sm:p-8">{loading ? <div className="flex min-h-[280px] items-center justify-center"><LoadingState label="Loading your conversation…" /></div> : error && messages.length === 0 ? <div className="grid min-h-[280px] place-items-center"><ErrorState message={error} /></div> : messages.length === 0 ? <EmptyState title="Start with a cybersecurity question" description="CyberSathi explains defensive concepts and practical next steps. It will never ask for passwords, codes, or API keys." /> : <>{messages.map((turn, index) => <ChatTurn key={`${turn.created_at}-${index}`} turn={turn} />)}{sending && <div className="max-w-xs rounded-3xl rounded-bl-md border border-teal/15 bg-white px-5 py-4 text-sm text-ink/60" role="status" aria-live="polite"><span className="mr-2 inline-flex gap-1 align-middle"><span className="h-2 w-2 animate-bounce rounded-full bg-teal [animation-delay:-0.2s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-teal [animation-delay:-0.1s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-teal" /></span>CyberSathi is thinking…</div>}</>}<div ref={messagesEndRef} /></div><form className="border-t border-ink/10 bg-white p-5 sm:p-8" onSubmit={(event) => void submitMessage(event)}><Textarea id="chat-message" label="Your question" value={draft} maxLength={2000} placeholder="Ask about phishing, ransomware, 2FA, suspicious messages, or account safety…" hint={`${draft.length}/2,000 characters · Enter to send, Shift+Enter for a new line`} error={validationError} disabled={sending} onChange={(event) => { setDraft(event.target.value); if (validationError) setValidationError('') }} onKeyDown={handleComposerKeyDown} /><div className="mt-4 flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><p className="text-xs text-ink/45">{user ? 'Your conversation is stored privately with your authenticated account.' : 'This public conversation is ephemeral. Sign in if you want to save your history.'}</p><Button type="submit" loading={sending} disabled={loading || !draft.trim()}>Send question</Button></div></form></Card>
      <aside className="grid gap-6"><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Try asking</p><h2 className="mt-3 text-xl font-black text-ink">Start with a prompt</h2><div className="mt-5 grid gap-2">{suggestedQuestions.map((question) => <button className="rounded-2xl border border-ink/10 bg-white px-4 py-3 text-left text-sm font-semibold leading-6 text-ink/70 transition hover:border-teal hover:text-teal" key={question} type="button" onClick={() => { setDraft(question); setValidationError('') }}>{question}</button>)}</div></Card><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Safety boundary</p><h2 className="mt-3 text-xl font-black">Learn. Pause. Protect.</h2><p className="mt-4 text-sm leading-6 text-white/60">CyberSathi is for defensive awareness. It does not make deterministic URL or email verdicts, and it will redirect requests for harmful or unauthorized activity.</p></Card>{error && messages.length > 0 && <Alert variant="error">{error}</Alert>}</aside></div>
    <Alert variant="info">Never share passwords, one-time codes, recovery codes, API keys, or other secrets in chat.</Alert><Modal open={clearOpen} title="Clear conversation?" onClose={() => setClearOpen(false)}><p>{user ? 'This removes your saved CyberSathi conversation from the database. This cannot be undone.' : 'This clears the current public conversation from this page.'}</p><div className="mt-6 flex justify-end gap-3"><Button variant="secondary" type="button" onClick={() => setClearOpen(false)}>Cancel</Button><Button variant="danger" type="button" onClick={() => void clearConversation()}>Clear conversation</Button></div></Modal>
  </div>
}
