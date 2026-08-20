import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import type { AdminAnalytics, AdminLesson, AdminQuiz, AdminUser } from '../types/admin'

function titleCase(value: string) {
  return value.replace(/[_-]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function numberLabel(value: number) {
  return new Intl.NumberFormat().format(value)
}

function MetricCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return <Card className={accent ? 'border-teal/20 bg-teal/5' : ''}><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/45">{label}</p><p className="mt-4 text-3xl font-black tracking-[-0.04em] text-ink">{value}</p></Card>
}

function ChartCard({ title, eyebrow, children }: { title: string; eyebrow: string; children: ReactNode }) {
  return <Card className="min-w-0"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">{eyebrow}</p><h2 className="mt-2 text-xl font-black text-ink">{title}</h2><div className="mt-6">{children}</div></Card>
}

function Bars({ items, valueKey, suffix = '' }: { items: { label: string; count?: number; score?: number; average_score?: number }[]; valueKey: 'count' | 'score' | 'average_score'; suffix?: string }) {
  if (!items.length) return <EmptyState title="No data yet" description="This chart will populate as the campus uses CyberSathi." />
  const max = Math.max(...items.map((item) => Number(item[valueKey] ?? 0)), 1)
  return <div className="grid gap-4">{items.map((item) => { const value = Number(item[valueKey] ?? 0); return <div key={item.label}><div className="flex items-center justify-between gap-3 text-sm"><span className="truncate font-bold text-ink/70">{titleCase(item.label)}</span><span className="shrink-0 font-black text-ink">{value}{suffix}</span></div><div className="mt-2 h-3 overflow-hidden rounded-full bg-ink/10"><div className="h-full rounded-full bg-teal transition-all" style={{ width: `${Math.max((value / max) * 100, value ? 4 : 0)}%` }} /></div></div> })}</div>
}

function TrendChart({ items }: { items: { label: string; count: number }[] }) {
  if (!items.length || items.every((item) => item.count === 0)) return <EmptyState title="No incidents in the trend window" description="Incident activity will appear here once reports are submitted." />
  const max = Math.max(...items.map((item) => item.count), 1)
  const points = items.map((item, index) => `${(index / Math.max(items.length - 1, 1)) * 100},${100 - (item.count / max) * 82 - 8}`).join(' ')
  return <div><svg className="h-48 w-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Incident trend line chart"><path d="M 0 92 H 100" stroke="currentColor" strokeOpacity=".1" vectorEffect="non-scaling-stroke" /><polyline fill="none" points={points} stroke="#0f9f95" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg><div className="mt-3 flex justify-between text-[10px] font-bold text-ink/40"><span>{items[0].label}</span><span>{items[Math.floor(items.length / 2)].label}</span><span>{items[items.length - 1].label}</span></div></div>
}

function ManagementSection({ users, lessons, quizzes, onRoleChange, updatingUserId }: { users: AdminUser[]; lessons: AdminLesson[]; quizzes: AdminQuiz[]; onRoleChange: (user: AdminUser, role: AdminUser['role']) => void; updatingUserId: number | null }) {
  return <section className="mt-12" aria-labelledby="management-heading"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Administration</p><h2 className="mt-2 text-3xl font-black tracking-[-0.03em] text-ink" id="management-heading">Manage the platform.</h2></div><Link className="text-sm font-black text-teal" to="/admin/incidents">Open incident queue →</Link></div><div className="mt-6 grid gap-6 xl:grid-cols-2"><Card><div className="flex items-center justify-between gap-3"><div><h3 className="text-xl font-black text-ink">Users</h3><p className="mt-1 text-sm text-ink/50">Role and academic profile controls. Passwords are never returned.</p></div><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black text-teal-900">{users.length}</span></div>{users.length ? <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm"><thead className="border-b border-ink/10 text-xs uppercase tracking-[0.1em] text-ink/40"><tr><th className="pb-3 pr-4">User</th><th className="pb-3 pr-4">Department</th><th className="pb-3">Role</th></tr></thead><tbody>{users.map((user) => <tr className="border-b border-ink/5 last:border-0" key={user.id}><td className="py-4 pr-4"><p className="font-black text-ink">{user.name}</p><p className="mt-1 text-xs text-ink/50">{user.email}</p></td><td className="py-4 pr-4 text-ink/60">{user.department || '—'}{user.year ? ` · Year ${user.year}` : ''}</td><td className="py-4"><select className="min-h-10 rounded-xl border border-ink/15 bg-white px-3 text-xs font-bold text-ink" aria-label={`Role for ${user.name}`} disabled={updatingUserId === user.id} value={user.role} onChange={(event) => onRoleChange(user, event.target.value as AdminUser['role'])}><option value="student">Student</option><option value="faculty">Faculty</option><option value="admin">Admin</option></select></td></tr>)}</tbody></table></div> : <div className="mt-5"><EmptyState title="No users found" description="Registered accounts will appear here." /></div>}</Card><Card><div className="flex items-center justify-between gap-3"><div><h3 className="text-xl font-black text-ink">Learning content</h3><p className="mt-1 text-sm text-ink/50">Review lessons and quiz participation at a glance.</p></div><Link className="text-sm font-black text-teal" to="/learn">Open hub →</Link></div><div className="mt-5 grid gap-3">{lessons.length ? lessons.slice(0, 5).map((lesson) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={lesson.id}><div className="min-w-0"><p className="truncate text-sm font-black text-ink">{lesson.title}</p><p className="mt-1 text-xs text-ink/50">{titleCase(lesson.category)} · {lesson.quiz_count} quiz{lesson.quiz_count === 1 ? '' : 'zes'}</p></div><span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-black capitalize text-ink/60">{lesson.difficulty}</span></div>) : <EmptyState title="No lessons found" description="Seed or create lessons to manage learning content." />}</div><div className="mt-6 border-t border-ink/10 pt-5"><p className="text-xs font-black uppercase tracking-[0.12em] text-teal">Quizzes</p>{quizzes.length ? <div className="mt-3 grid gap-2">{quizzes.slice(0, 4).map((quiz) => <div className="flex justify-between gap-3 text-sm" key={quiz.id}><span className="truncate font-bold text-ink/70">{quiz.title}</span><span className="shrink-0 text-xs font-black text-ink/45">{quiz.attempt_count} attempts</span></div>)}</div> : <p className="mt-3 text-sm text-ink/50">No quizzes found.</p>}</div></Card></div></section>
}

export function AdminDashboardPage() {
  const { authenticatedRequest } = useAuth()
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [lessons, setLessons] = useState<AdminLesson[]>([])
  const [quizzes, setQuizzes] = useState<AdminQuiz[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [nextAnalytics, nextUsers, nextLessons, nextQuizzes] = await Promise.all([
        authenticatedRequest<AdminAnalytics>('/admin/analytics'),
        authenticatedRequest<AdminUser[]>('/admin/users'),
        authenticatedRequest<AdminLesson[]>('/admin/lessons'),
        authenticatedRequest<AdminQuiz[]>('/admin/quizzes'),
      ])
      setAnalytics(nextAnalytics)
      setUsers(nextUsers)
      setLessons(nextLessons)
      setQuizzes(nextQuizzes)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load the admin dashboard.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest])

  useEffect(() => { void load() }, [load])

  async function changeRole(user: AdminUser, role: AdminUser['role']) {
    setUpdatingUserId(user.id)
    setActionError('')
    try {
      const updated = await authenticatedRequest<AdminUser>(`/admin/users/${user.id}`, { method: 'PATCH', body: JSON.stringify({ role }) })
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (requestError) {
      setActionError(requestError instanceof ApiError ? requestError.message : 'Unable to update this user.')
    } finally {
      setUpdatingUserId(null)
    }
  }

  const metrics = useMemo(() => analytics ? [
    ['Total students', numberLabel(analytics.summary.total_students)],
    ['Total faculty', numberLabel(analytics.summary.total_faculty)],
    ['Total users', numberLabel(analytics.summary.total_users)],
    ['Awareness average', `${analytics.summary.awareness_average}%`],
    ['Total incidents', numberLabel(analytics.summary.total_incidents)],
    ['Open incidents', numberLabel(analytics.summary.open_incidents)],
    ['High / critical', numberLabel(analytics.summary.high_critical_incidents)],
    ['Email analyses', numberLabel(analytics.summary.total_email_analyses)],
    ['URL analyses', numberLabel(analytics.summary.total_url_analyses)],
    ['Quiz participation', numberLabel(analytics.summary.quiz_participation)],
  ] : [], [analytics])

  if (loading && !analytics) return <div className="mx-auto flex min-h-[70vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading admin intelligence…" /></div>
  if (error && !analytics) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error} /><Button className="mt-6" type="button" onClick={() => void load()}>Try again</Button></div>
  if (!analytics) return null

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end"><div className="max-w-3xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Admin console</p><h1 className="mt-3 text-4xl font-black tracking-[-0.05em] text-ink sm:text-6xl">See the campus security picture.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Aggregate awareness, learning, analysis, and incident signals in one privacy-conscious workspace.</p></div><Link className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white hover:bg-teal" to="/admin/incidents">Review incident queue →</Link></div>{actionError && <div className="mt-8"><ErrorState message={actionError} /></div>}{error && <div className="mt-8"><Alert variant="info">Some dashboard data could not be refreshed. Showing the last available results.</Alert></div>}<section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5" aria-label="Admin summary metrics">{metrics.map(([label, value], index) => <MetricCard accent={index === 3} key={label} label={label} value={value} />)}</section><section className="mt-8 grid gap-6 lg:grid-cols-2" aria-label="Security analytics"><ChartCard eyebrow="Incident activity" title="Incident trends"><TrendChart items={analytics.incident_trends} /></ChartCard><ChartCard eyebrow="Threat landscape" title="Reported categories"><Bars items={analytics.threat_categories} valueKey="count" /></ChartCard><ChartCard eyebrow="Awareness" title="Average category scores"><Bars items={analytics.awareness_scores} valueKey="score" suffix="%" /></ChartCard><ChartCard eyebrow="Learning outcomes" title="Quiz performance"><Bars items={analytics.quiz_performance} valueKey="average_score" suffix="%" /></ChartCard><ChartCard eyebrow="Message analysis" title="Email risk levels"><Bars items={analytics.email_risk_levels} valueKey="count" /></ChartCard><ChartCard eyebrow="Link analysis" title="URL risk levels"><Bars items={analytics.url_risk_levels} valueKey="count" /></ChartCard></section><ManagementSection users={users} lessons={lessons} quizzes={quizzes} onRoleChange={(user, role) => void changeRole(user, role)} updatingUserId={updatingUserId} /><p className="mt-8 text-xs text-ink/40">Analytics generated {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(analytics.generated_at))}. Metrics are aggregated and do not include message contents, URLs, or incident descriptions.</p></div>
}
