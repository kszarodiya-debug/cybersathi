import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Input } from '../components/Input'
import { LoadingState } from '../components/LoadingState'
import { Textarea } from '../components/Textarea'
import { ApiError } from '../services/api'
import type { IncidentReport, IncidentReportListResponse, IncidentType } from '../types/incident'

const incidentTypes: Array<{ value: IncidentType; label: string }> = [
  { value: 'phishing', label: 'Phishing' },
  { value: 'suspicious_link', label: 'Suspicious link' },
  { value: 'account_compromise', label: 'Account compromise' },
  { value: 'cyberbullying', label: 'Cyberbullying' },
  { value: 'malware', label: 'Malware' },
  { value: 'data_leakage', label: 'Data leakage' },
  { value: 'online_scam', label: 'Online scam' },
  { value: 'fake_website', label: 'Fake website' },
  { value: 'other', label: 'Other' },
]

function label(value: string) {
  return value.split('_').join(' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function localDateTime() {
  const date = new Date()
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

function dateLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function StatusPill({ value }: { value: string }) {
  const className = value === 'RESOLVED' ? 'bg-teal/10 text-teal-900' : value === 'REJECTED' ? 'bg-red-50 text-red-700' : value === 'UNDER_REVIEW' ? 'bg-signal/25 text-ink' : 'bg-sky-50 text-sky-900'
  return <span className={`rounded-full px-3 py-1 text-xs font-black ${className}`}>{label(value)}</span>
}

function IncidentDetail({ reportId }: { reportId: number }) {
  const { authenticatedRequest } = useAuth()
  const [report, setReport] = useState<IncidentReport | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setReport(await authenticatedRequest<IncidentReport>(`/students/incidents/${reportId}`))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load this incident report.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, reportId])

  useEffect(() => { void load() }, [load])

  if (loading) return <div className="mx-auto flex min-h-[55vh] max-w-4xl items-center justify-center px-5"><LoadingState label="Loading report…" /></div>
  if (error || !report) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error || 'Report unavailable.'} /><button className="mt-6 rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white" type="button" onClick={() => void load()}>Try again</button></div>

  return <div className="mx-auto max-w-4xl px-5 py-12 lg:px-8 lg:py-16"><Link className="text-sm font-bold text-teal" to="/report-incident">← Back to my reports</Link><div className="mt-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Incident report #{report.id}</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink">{label(report.incident_type)}</h1><p className="mt-3 text-sm text-ink/55">Submitted {dateLabel(report.created_at)} · Incident time {dateLabel(report.occurred_at)}</p></div><div className="flex gap-2"><StatusPill value={report.status} /><StatusPill value={report.severity} /></div></div><div className="mt-8 grid gap-6"><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Description</p><p className="mt-4 whitespace-pre-wrap text-base leading-8 text-ink/70">{report.description}</p>{report.suspicious_url && <div className="mt-6"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Suspicious URL</p><p className="mt-3 break-all rounded-2xl bg-mist px-4 py-3 text-sm font-semibold text-ink/70">{report.suspicious_url}</p></div>}</Card><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Optional evidence metadata</p>{Object.keys(report.evidence_metadata).length === 0 ? <p className="mt-4 text-sm leading-6 text-ink/60">No metadata was attached. This is okay; do not send passwords, OTPs, private keys, or unnecessary personal information.</p> : <dl className="mt-4 grid gap-3 sm:grid-cols-2">{Object.entries(report.evidence_metadata).map(([key, value]) => <div key={key}><dt className="text-xs font-black uppercase tracking-[0.1em] text-ink/50">{label(key)}</dt><dd className="mt-1 text-sm text-ink/70">{value}</dd></div>)}</dl>}</Card><Alert variant="info">Status updates are handled by the campus security team. If there is immediate danger or active account misuse, contact your official campus IT/security channel directly.</Alert></div></div>
}

function IncidentFormPage() {
  const { authenticatedRequest } = useAuth()
  const [data, setData] = useState<IncidentReportListResponse | null>(null)
  const [incidentType, setIncidentType] = useState<IncidentType>('phishing')
  const [description, setDescription] = useState('')
  const [suspiciousUrl, setSuspiciousUrl] = useState('')
  const [occurredAt, setOccurredAt] = useState(localDateTime)
  const [channel, setChannel] = useState('')
  const [sender, setSender] = useState('')
  const [attachmentName, setAttachmentName] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await authenticatedRequest<IncidentReportListResponse>('/students/incidents'))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load your incident reports.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest])

  useEffect(() => { void load() }, [load])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')
    const evidence_metadata = Object.fromEntries(Object.entries({ channel, sender, attachment_name: attachmentName }).filter(([, value]) => value.trim()))
    try {
      await authenticatedRequest<IncidentReport>('/students/incidents', { method: 'POST', body: JSON.stringify({ incident_type: incidentType, description, suspicious_url: suspiciousUrl || null, occurred_at: new Date(occurredAt).toISOString(), evidence_metadata }) })
      setDescription('')
      setSuspiciousUrl('')
      setChannel('')
      setSender('')
      setAttachmentName('')
      setOccurredAt(localDateTime())
      setSuccess('Your report was submitted securely. The campus security team can now review it.')
      await load()
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to submit your report.')
    } finally {
      setSubmitting(false)
    }
  }

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to="/dashboard">← Back to dashboard</Link><p className="mt-8 text-xs font-black uppercase tracking-[0.2em] text-teal">Campus response</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Report a cyber incident.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Share enough context for your security team to help. Do not include passwords, OTPs, recovery codes, private keys, or unrelated personal information.</p></div>{error && <div className="mt-8"><ErrorState message={error} /></div>}{success && <div className="mt-8"><Alert variant="success">{success}</Alert></div>}<div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"><Card><form className="grid gap-5" onSubmit={submit}><div><label className="grid gap-2 text-sm font-bold text-ink" htmlFor="incident-type">Incident type<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium outline-none focus:border-teal focus:ring-4 focus:ring-teal/10" id="incident-type" value={incidentType} onChange={(event) => setIncidentType(event.target.value as IncidentType)}>{incidentTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label></div><Textarea id="incident-description" label="What happened?" placeholder="Describe what you noticed, what you interacted with, and any safe-to-share context." value={description} onChange={(event) => setDescription(event.target.value)} required /><Input id="incident-url" label="Suspicious URL (optional)" type="url" placeholder="https://example.com" value={suspiciousUrl} onChange={(event) => setSuspiciousUrl(event.target.value)} /><Input id="incident-time" label="Date/time of incident" type="datetime-local" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} required /><div className="border-t border-ink/10 pt-5"><p className="text-sm font-black text-ink">Optional evidence metadata</p><p className="mt-1 text-xs leading-5 text-ink/50">Context only—not the original sensitive content.</p><div className="mt-4 grid gap-4 sm:grid-cols-2"><Input id="incident-channel" label="Channel" placeholder="Email, SMS, WhatsApp" value={channel} onChange={(event) => setChannel(event.target.value)} /><Input id="incident-sender" label="Sender label (optional)" placeholder="Displayed sender name" value={sender} onChange={(event) => setSender(event.target.value)} /><Input id="incident-attachment" label="Attachment name (optional)" placeholder="invoice.pdf" value={attachmentName} onChange={(event) => setAttachmentName(event.target.value)} /></div></div><Button type="submit" loading={submitting}>Submit report securely</Button></form></Card><div className="grid gap-6"><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Safety first</p><h2 className="mt-3 text-2xl font-black">Preserve context. Remove secrets.</h2><p className="mt-4 text-sm leading-6 text-white/60">Keep the original message or link available through approved campus processes, but never paste passwords, OTPs, payment details, or private keys into a report.</p></Card><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">What happens next?</p><div className="mt-5 grid gap-3 text-sm leading-6 text-ink/65"><p><strong className="text-ink">1. Open:</strong> your report is recorded for the security team.</p><p><strong className="text-ink">2. Under review:</strong> an authorized reviewer assesses the context.</p><p><strong className="text-ink">3. Resolved or rejected:</strong> the team records the outcome.</p></div></Card></div></div><section className="mt-12" aria-labelledby="report-history"><div className="flex items-end justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">My reports</p><h2 className="mt-2 text-2xl font-black text-ink" id="report-history">Report history</h2></div>{data && <span className="text-sm text-ink/45">{data.total} total</span>}</div>{loading ? <div className="mt-6"><LoadingState label="Loading report history…" /></div> : data?.reports.length ? <div className="mt-5 grid gap-4 md:grid-cols-2">{data.reports.map((report) => <Card key={report.id}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-[0.1em] text-teal">Report #{report.id}</p><h3 className="mt-2 text-lg font-black text-ink">{label(report.incident_type)}</h3></div><StatusPill value={report.status} /></div><p className="mt-4 line-clamp-2 text-sm leading-6 text-ink/60">{report.description}</p><div className="mt-5 flex items-center justify-between gap-3"><span className="text-xs text-ink/45">{dateLabel(report.created_at)}</span><Link className="text-sm font-black text-teal" to={`/report-incident/${report.id}`}>View details →</Link></div></Card>)}</div> : <div className="mt-5"><EmptyState title="No reports yet" description="If something suspicious happens, report it here so your campus team can help." /></div>}</section></div>
}

export function IncidentReportingPage() {
  const { reportId } = useParams()
  return reportId ? <IncidentDetail reportId={Number(reportId)} /> : <IncidentFormPage />
}
