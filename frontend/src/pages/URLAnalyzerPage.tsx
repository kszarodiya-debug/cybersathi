import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Input } from '../components/Input'
import { LoadingState } from '../components/LoadingState'
import { apiRequest, ApiError } from '../services/api'
import type { URLAnalysisResult, URLRiskLevel } from '../types/url-analysis'

function riskClasses(level: URLRiskLevel) {
  if (level === 'CRITICAL') return { badge: 'bg-red-100 text-red-800', bar: 'bg-red-600', panel: 'border-red-200 bg-red-50' }
  if (level === 'HIGH') return { badge: 'bg-orange-100 text-orange-800', bar: 'bg-orange-500', panel: 'border-orange-200 bg-orange-50' }
  if (level === 'MEDIUM') return { badge: 'bg-signal/25 text-ink', bar: 'bg-signal', panel: 'border-signal/40 bg-signal/10' }
  if (level === 'LOW') return { badge: 'bg-sky-100 text-sky-800', bar: 'bg-sky-500', panel: 'border-sky-200 bg-sky-50' }
  return { badge: 'bg-teal/10 text-teal-900', bar: 'bg-teal', panel: 'border-teal/20 bg-teal/5' }
}

function severityClasses(severity: string) {
  if (severity === 'high') return 'border-red-200 bg-red-50'
  if (severity === 'medium') return 'border-signal/40 bg-signal/10'
  return 'border-teal/20 bg-teal/5'
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

export function URLAnalyzerPage() {
  const { user, authenticatedRequest } = useAuth()
  const [url, setUrl] = useState('')
  const [result, setResult] = useState<URLAnalysisResult | null>(null)
  const [history, setHistory] = useState<URLAnalysisResult[]>([])
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [validationError, setValidationError] = useState('')

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    setHistoryError('')
    if (!user) {
      setHistory([])
      setHistoryLoading(false)
      return
    }
    try {
      setHistory(await authenticatedRequest<URLAnalysisResult[]>('/students/analysis/urls/history'))
    } catch (requestError) {
      setHistoryError(requestError instanceof ApiError ? requestError.message : 'Unable to load your URL history right now.')
    } finally {
      setHistoryLoading(false)
    }
  }, [authenticatedRequest, user])

  useEffect(() => { void loadHistory() }, [loadHistory])

  const analyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) {
      setValidationError('Enter a URL before checking it.')
      return
    }
    setValidationError('')
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const analysis = await (user
        ? authenticatedRequest<URLAnalysisResult>('/students/analysis/urls', {
          method: 'POST',
          body: JSON.stringify({ url: trimmed }),
        })
        : apiRequest<URLAnalysisResult>('/public/analysis/urls', {
        method: 'POST',
        body: JSON.stringify({ url: trimmed }),
        }))
      setResult(analysis)
      setHistory((current) => [analysis, ...current.filter((item) => item.id !== analysis.id)].slice(0, 20))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to check this URL right now.')
    } finally {
      setLoading(false)
    }
  }

  const classes = result ? riskClasses(result.risk_level) : null

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to={user ? '/dashboard' : '/'}>← Back to CyberSathi</Link><p className="mt-8 text-xs font-black uppercase tracking-[0.2em] text-teal">Link safety</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Check a URL before you click.</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-ink/60">CyberSathi checks the URL’s visible structure for defensive indicators. It never opens, scans, exploits, or contacts the destination.</p></div>
    <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start"><Card className="p-7 sm:p-9"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Non-invasive analyzer</p><h2 className="mt-2 text-2xl font-black text-ink">Paste a link to inspect</h2></div><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black uppercase tracking-[0.12em] text-teal-900">{user ? 'History saved privately' : 'No account required'}</span></div><form className="mt-8" onSubmit={(event) => void analyze(event)}><Input id="url-to-check" label="URL" type="url" value={url} maxLength={2048} placeholder="https://example.com/account" hint="Include the complete URL when possible. The analyzer only parses the text you provide." error={validationError} disabled={loading} onChange={(event) => { setUrl(event.target.value); if (validationError) setValidationError('') }} /><div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><p className="max-w-md text-xs leading-5 text-ink/45">A result is not proof that a destination is safe or malicious. Page content and reputation are not checked.</p><Button type="submit" loading={loading} disabled={!url.trim()}>Check URL</Button></div></form>{error && <div className="mt-6"><ErrorState message={error} /></div>}</Card>
      {result && classes ? <Card className={`border ${classes.panel} p-7 sm:p-9`} aria-live="polite"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-ink/55">Risk assessment</p><h2 className="mt-2 text-3xl font-black text-ink">{result.risk_level}</h2></div><div className="text-right"><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/50">Risk score</p><p className="mt-1 text-5xl font-black tracking-[-0.06em] text-ink">{result.risk_score}<span className="text-2xl text-ink/45">/100</span></p></div></div><p className="mt-5 break-all rounded-2xl bg-white/70 px-4 py-3 text-sm font-semibold text-ink/75">{result.url}</p><div className="mt-5 h-3 overflow-hidden rounded-full bg-white/70"><div className={`h-full rounded-full ${classes.bar}`} style={{ width: `${result.risk_score}%` }} /></div><p className="mt-6 text-sm leading-7 text-ink/70">{result.explanation}</p><div className="mt-7"><h3 className="text-sm font-black uppercase tracking-[0.14em] text-ink/60">Detected indicators</h3>{result.detected_indicators.length === 0 ? <p className="mt-3 rounded-2xl bg-white/70 px-4 py-3 text-sm leading-6 text-ink/65">No common structural warning indicators were detected.</p> : <div className="mt-3 grid gap-3">{result.detected_indicators.map((indicator) => <div className={`rounded-2xl border px-4 py-3 ${severityClasses(indicator.severity)}`} key={indicator.code}><div className="flex items-start justify-between gap-3"><p className="text-sm font-black text-ink">{indicator.label}</p><span className="rounded-full bg-white/60 px-2 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-ink/60">{indicator.severity}</span></div><p className="mt-2 text-sm leading-6 text-ink/65">{indicator.description}</p></div>)}</div>}</div><Alert variant="warning"><strong>Recommended action:</strong> {result.recommended_action}</Alert></Card> : <Card><EmptyState title="Your URL result will appear here" description="Paste a link to see its score, observable indicators, and recommended action." /></Card>}</div>
    {user && <section className="mt-10" aria-labelledby="url-history-heading"><div className="flex items-end justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Private history</p><h2 className="mt-2 text-2xl font-black text-ink" id="url-history-heading">Recent URL checks</h2></div><span className="text-sm text-ink/45">Only your records</span></div><Card className="mt-5">{historyLoading ? <LoadingState label="Loading URL history…" /> : historyError ? <ErrorState message={historyError} /> : history.length === 0 ? <EmptyState title="No URL checks yet" description="Your saved URL analysis results will appear here." /> : <div className="divide-y divide-ink/10">{history.map((item) => <div className="flex flex-col justify-between gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center" key={item.id ?? item.created_at}><div className="min-w-0"><p className="truncate text-sm font-bold text-ink">{item.url}</p><p className="mt-1 text-xs text-ink/45">{formatDate(item.created_at)}</p></div><div className="flex shrink-0 items-center gap-3"><span className={`rounded-full px-3 py-1 text-xs font-black ${riskClasses(item.risk_level).badge}`}>{item.risk_level}</span><span className="text-sm font-black text-ink/60">{item.risk_score}/100</span></div></div>)}</div>}</Card></section>}
    <div className="mt-8 grid gap-6 md:grid-cols-2"><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">No active scanning</p><h2 className="mt-3 text-xl font-black">Parse, don’t probe.</h2><p className="mt-4 text-sm leading-6 text-white/60">CyberSathi does not make DNS, HTTP, TLS, or reputation requests. This keeps the check safe and non-invasive.</p></Card><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Before you continue</p><h2 className="mt-3 text-xl font-black text-ink">Use trusted destinations</h2><p className="mt-4 text-sm leading-6 text-ink/65">When in doubt, open the official app or type the organization’s known website yourself instead of following the link.</p></Card></div>
  </div>
}
