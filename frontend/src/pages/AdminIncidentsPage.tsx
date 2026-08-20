import { useCallback, useEffect, useState } from 'react'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { ApiError } from '../services/api'
import type { AdminIncidentReport, AdminIncidentReportListResponse, IncidentSeverity, IncidentStatus } from '../types/incident'

const statuses: IncidentStatus[] = ['OPEN', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED']
const severities: IncidentSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

function label(value: string) {
  return value.split('_').join(' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function dateLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function Pill({ value }: { value: string }) {
  const className = value === 'CRITICAL' || value === 'REJECTED' ? 'bg-red-50 text-red-700' : value === 'HIGH' || value === 'UNDER_REVIEW' ? 'bg-signal/25 text-ink' : value === 'RESOLVED' ? 'bg-teal/10 text-teal-900' : 'bg-sky-50 text-sky-900'
  return <span className={`rounded-full px-3 py-1 text-xs font-black ${className}`}>{label(value)}</span>
}

export function AdminIncidentsPage() {
  const { authenticatedRequest } = useAuth()
  const [data, setData] = useState<AdminIncidentReportListResponse | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const query = new URLSearchParams()
      if (statusFilter) query.set('status', statusFilter)
      if (severityFilter) query.set('severity', severityFilter)
      const suffix = query.toString() ? `?${query.toString()}` : ''
      setData(await authenticatedRequest<AdminIncidentReportListResponse>(`/admin/incidents${suffix}`))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load incident reports.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, severityFilter, statusFilter])

  useEffect(() => { void load() }, [load])

  async function update(report: AdminIncidentReport, field: 'status' | 'severity', value: string) {
    setUpdatingId(report.id)
    setActionError('')
    try {
      await authenticatedRequest<AdminIncidentReport>(`/admin/incidents/${report.id}`, { method: 'PATCH', body: JSON.stringify({ [field]: value }) })
      await load()
    } catch (requestError) {
      setActionError(requestError instanceof ApiError ? requestError.message : 'Unable to update this report.')
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading && !data) return <div className="mx-auto flex min-h-[60vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading incident queue…" /></div>
  if (error && !data) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error} /><button className="mt-6 rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white" type="button" onClick={() => void load()}>Try again</button></div>

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="max-w-3xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Admin console</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Incident response queue.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Review submitted reports and record status or severity changes. Every administrative update creates an audit log.</p></div>{actionError && <div className="mt-8"><ErrorState message={actionError} /></div>}<Card className="mt-10 p-5 sm:p-6"><div className="flex flex-col gap-4 sm:flex-row"><label className="grid flex-1 gap-2 text-sm font-bold text-ink" htmlFor="admin-status">Status<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium outline-none focus:border-teal focus:ring-4 focus:ring-teal/10" id="admin-status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option>{statuses.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></label><label className="grid flex-1 gap-2 text-sm font-bold text-ink" htmlFor="admin-severity">Severity<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium outline-none focus:border-teal focus:ring-4 focus:ring-teal/10" id="admin-severity" value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}><option value="">All severities</option>{severities.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></label></div></Card>{data?.reports.length ? <div className="mt-8 grid gap-5">{data.reports.map((report) => <Card key={report.id}><div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start"><div><div className="flex flex-wrap items-center gap-2"><span className="text-xs font-black uppercase tracking-[0.12em] text-teal">Report #{report.id}</span><Pill value={report.status} /><Pill value={report.severity} /></div><h2 className="mt-3 text-xl font-black text-ink">{label(report.incident_type)}</h2><p className="mt-2 text-sm text-ink/55">{report.reporter_name} · {report.reporter_email}{report.reporter_department ? ` · ${report.reporter_department}` : ''}</p></div><p className="text-xs text-ink/45">Submitted {dateLabel(report.created_at)}</p></div><p className="mt-5 whitespace-pre-wrap text-sm leading-7 text-ink/70">{report.description}</p>{report.suspicious_url && <p className="mt-4 break-all rounded-2xl bg-mist px-4 py-3 text-sm font-semibold text-ink/65">{report.suspicious_url}</p>}<div className="mt-6 grid gap-4 border-t border-ink/10 pt-5 sm:grid-cols-2"><label className="grid gap-2 text-sm font-bold text-ink" htmlFor={`status-${report.id}`}>Update status<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" disabled={updatingId === report.id} id={`status-${report.id}`} value={report.status} onChange={(event) => void update(report, 'status', event.target.value)}>{statuses.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></label><label className="grid gap-2 text-sm font-bold text-ink" htmlFor={`severity-${report.id}`}>Update severity<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" disabled={updatingId === report.id} id={`severity-${report.id}`} value={report.severity} onChange={(event) => void update(report, 'severity', event.target.value)}>{severities.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></label></div></Card>)}</div> : <div className="mt-8"><EmptyState title="No reports match the queue filters" description="New student reports will appear here when submitted." /></div>}<div className="mt-8"><Alert variant="info">Administrative audit entries record the actor, report, action, and before/after status or severity. Report descriptions and evidence metadata are not copied into the audit log.</Alert></div></div>
}
