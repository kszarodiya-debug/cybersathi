import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Textarea } from '../components/Textarea'
import { ApiError } from '../services/api'
import type { MessageAnalysisResult, MessageContentType } from '../types/analysis'

const contentTypes: Array<{ value: MessageContentType; label: string; description: string }> = [
  { value: 'email', label: 'Email', description: 'Formal or campus email' },
  { value: 'sms', label: 'SMS', description: 'Text message' },
  { value: 'whatsapp', label: 'WhatsApp', description: 'Chat message' },
  { value: 'social_media', label: 'Social media', description: 'DM or social post' },
]

function riskClasses(level: MessageAnalysisResult['risk_level']) {
  if (level === 'CRITICAL') return { badge: 'bg-red-100 text-red-800', bar: 'bg-red-600', panel: 'border-red-200 bg-red-50' }
  if (level === 'HIGH') return { badge: 'bg-orange-100 text-orange-800', bar: 'bg-orange-500', panel: 'border-orange-200 bg-orange-50' }
  if (level === 'MEDIUM') return { badge: 'bg-signal/25 text-ink', bar: 'bg-signal', panel: 'border-signal/40 bg-signal/10' }
  return { badge: 'bg-teal/10 text-teal-900', bar: 'bg-teal', panel: 'border-teal/20 bg-teal/5' }
}

function severityClasses(severity: string) {
  if (severity === 'high') return 'border-red-200 bg-red-50'
  if (severity === 'medium') return 'border-signal/40 bg-signal/10'
  return 'border-teal/20 bg-teal/5'
}

export function AnalyzerPage() {
  const { authenticatedRequest } = useAuth()
  const [contentType, setContentType] = useState<MessageContentType>('email')
  const [message, setMessage] = useState('')
  const [result, setResult] = useState<MessageAnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')

  const analyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = message.trim()
    if (!trimmed) {
      setValidationError('Paste a message before analyzing it.')
      return
    }
    setValidationError('')
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const analysis = await authenticatedRequest<MessageAnalysisResult>('/students/analysis/messages', {
        method: 'POST',
        body: JSON.stringify({ content_type: contentType, message: trimmed }),
      })
      setResult(analysis)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to analyze this message right now.')
    } finally {
      setLoading(false)
    }
  }

  const classes = result ? riskClasses(result.risk_level) : null

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to="/dashboard">← Back to dashboard</Link><p className="mt-8 text-xs font-black uppercase tracking-[0.2em] text-teal">Message safety</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Analyze before you act.</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-ink/60">Paste an email, SMS, WhatsApp-style message, or social media DM. CyberSathi will highlight observable warning signs and suggest safer next steps.</p></div>
    <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start"><Card className="p-7 sm:p-9"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Defensive analyzer</p><h2 className="mt-2 text-2xl font-black text-ink">What would you like to check?</h2></div><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black uppercase tracking-[0.12em] text-teal-900">Private to you</span></div><div className="mt-7 grid grid-cols-2 gap-2 sm:grid-cols-4" role="tablist" aria-label="Message type">{contentTypes.map((type) => <button className={`rounded-2xl border px-3 py-3 text-left transition focus:outline-none focus:ring-4 focus:ring-teal/20 ${contentType === type.value ? 'border-teal bg-teal/10 text-teal-900' : 'border-ink/10 bg-mist text-ink/60 hover:border-teal/40'}`} key={type.value} type="button" role="tab" aria-selected={contentType === type.value} onClick={() => setContentType(type.value)}><span className="block text-sm font-black">{type.label}</span><span className="mt-1 block text-xs leading-5 opacity-70">{type.description}</span></button>)}</div><form className="mt-7" onSubmit={(event) => void analyze(event)}><Textarea id="message-to-analyze" label={`${contentTypes.find((type) => type.value === contentType)?.label ?? 'Message'} content`} value={message} maxLength={50_000} placeholder="Paste the complete message here, including sender details, links, and attachment names when available…" hint={`${message.length.toLocaleString()}/50,000 characters · Include the original wording for better context.`} error={validationError} disabled={loading} onChange={(event) => { setMessage(event.target.value); if (validationError) setValidationError('') }} /><div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><p className="max-w-md text-xs leading-5 text-ink/45">The analyzer uses explainable defensive rules. A result is not proof that a message is safe or malicious.</p><Button type="submit" loading={loading} disabled={!message.trim()}>Analyze message</Button></div></form>{error && <div className="mt-6"><ErrorState message={error} /></div>}</Card>
      <div className="grid gap-6">{result && classes ? <Card className={`border ${classes.panel} p-7 sm:p-9`} aria-live="polite"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-ink/55">Risk assessment</p><h2 className="mt-2 text-3xl font-black text-ink">{result.risk_level}</h2></div><div className="text-right"><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/50">Risk score</p><p className="mt-1 text-5xl font-black tracking-[-0.06em] text-ink">{result.risk_score}<span className="text-2xl text-ink/45">/100</span></p></div></div><div className="mt-6 h-3 overflow-hidden rounded-full bg-white/70"><div className={`h-full rounded-full ${classes.bar}`} style={{ width: `${result.risk_score}%` }} /></div><p className="mt-6 text-sm leading-7 text-ink/70">{result.explanation}</p><div className="mt-7"><h3 className="text-sm font-black uppercase tracking-[0.14em] text-ink/60">Detected indicators</h3>{result.detected_indicators.length === 0 ? <p className="mt-3 rounded-2xl bg-white/70 px-4 py-3 text-sm leading-6 text-ink/65">No common warning indicators were detected by the current rules.</p> : <div className="mt-3 grid gap-3">{result.detected_indicators.map((indicator) => <div className={`rounded-2xl border px-4 py-3 ${severityClasses(indicator.severity)}`} key={indicator.code}><div className="flex items-start justify-between gap-3"><p className="text-sm font-black text-ink">{indicator.label}</p><span className="rounded-full bg-white/60 px-2 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-ink/60">{indicator.severity}</span></div><p className="mt-2 text-sm leading-6 text-ink/65">{indicator.description}</p></div>)}</div>}</div></Card> : <Card><EmptyState title="Your result will appear here" description="Paste a message and run the analyzer to see its risk score, observable indicators, and recommended actions." /></Card>}
        {result && <><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Recommended actions</p><h2 className="mt-2 text-2xl font-black text-ink">Safer next steps</h2><ul className="mt-5 grid gap-3">{result.recommended_actions.map((action) => <li className="flex gap-3 rounded-2xl bg-mist px-4 py-3 text-sm leading-6 text-ink/70" key={action}><span className="mt-0.5 text-teal" aria-hidden="true">✓</span><span>{action}</span></li>)}</ul></Card><Alert variant="warning"><strong>Safe handling advice:</strong> {result.safe_handling_advice}</Alert></>}</div></div>
    <div className="mt-8 grid gap-6 md:grid-cols-2"><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Remember</p><h2 className="mt-3 text-xl font-black">Pause. Verify. Protect.</h2><p className="mt-4 text-sm leading-6 text-white/60">Do not share passwords, OTPs, recovery codes, or payment information in response to an unexpected message.</p></Card><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">If you already interacted</p><h2 className="mt-3 text-xl font-black text-ink">Get help quickly</h2><p className="mt-4 text-sm leading-6 text-ink/65">Contact campus IT/security through a trusted channel, change exposed credentials from an official site, and preserve the original message for reporting.</p></Card></div>
  </div>
}
