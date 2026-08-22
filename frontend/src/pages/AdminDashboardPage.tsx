import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import type { AdminActivity, AdminAnalytics, AdminLesson, AdminQuiz, AdminStats, AdminUser, AdminUserPage } from '../types/admin'

const label = (value: string) => value.replace(/[_-]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
const dateLabel = (value?: string | null) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : 'Not recorded'

function MetricCard({ title, value, accent = false }: { title: string; value: string | number; accent?: boolean }) {
  return <Card className={accent ? 'border-teal/20 bg-teal/5' : ''}><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/45">{title}</p><p className="mt-4 text-3xl font-black tracking-[-0.04em] text-ink">{value}</p></Card>
}

function ChartCard({ eyebrow, title, children }: { eyebrow: string; title: string; children: ReactNode }) {
  return <Card className="min-w-0"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">{eyebrow}</p><h2 className="mt-2 text-xl font-black text-ink">{title}</h2><div className="mt-6">{children}</div></Card>
}

function Bars({ items, valueKey, suffix = '' }: { items: { label: string; count?: number; score?: number; average_score?: number }[]; valueKey: 'count' | 'score' | 'average_score'; suffix?: string }) {
  if (!items.length) return <EmptyState title="No data yet" description="This view will populate as the campus uses CyberSathi." />
  const max = Math.max(...items.map((item) => Number(item[valueKey] ?? 0)), 1)
  return <div className="grid gap-4">{items.map((item) => { const value = Number(item[valueKey] ?? 0); return <div key={item.label}><div className="flex items-center justify-between gap-3 text-sm"><span className="truncate font-bold text-ink/70">{label(item.label)}</span><span className="shrink-0 font-black text-ink">{value}{suffix}</span></div><div className="mt-2 h-3 overflow-hidden rounded-full bg-ink/10"><div className="h-full rounded-full bg-teal" style={{ width: `${Math.max((value / max) * 100, value ? 4 : 0)}%` }} /></div></div> })}</div>
}

function Trend({ items, emptyTitle }: { items: { label: string; count: number }[]; emptyTitle: string }) {
  if (!items.length || items.every((item) => item.count === 0)) return <EmptyState title={emptyTitle} description="This chart will populate as the platform receives activity." />
  const max = Math.max(...items.map((item) => item.count), 1)
  const points = items.map((item, index) => `${(index / Math.max(items.length - 1, 1)) * 100},${100 - (item.count / max) * 82 - 8}`).join(' ')
  return <div><svg className="h-44 w-full" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Activity trend chart"><path d="M 0 92 H 100" stroke="currentColor" strokeOpacity=".1" vectorEffect="non-scaling-stroke" /><polyline fill="none" points={points} stroke="#0f9f95" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg><div className="mt-3 flex justify-between text-[10px] font-bold text-ink/40"><span>{items[0].label}</span><span>{items[Math.floor(items.length / 2)].label}</span><span>{items[items.length - 1].label}</span></div></div>
}

export function AdminDashboardPage() {
  const { authenticatedRequest } = useAuth()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null)
  const [activity, setActivity] = useState<AdminActivity | null>(null)
  const [users, setUsers] = useState<AdminUserPage | null>(null)
  const [lessons, setLessons] = useState<AdminLesson[]>([])
  const [quizzes, setQuizzes] = useState<AdminQuiz[]>([])
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const [department, setDepartment] = useState('')
  const [sort, setSort] = useState<'created_at_asc' | 'created_at_desc'>('created_at_desc')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError('')
    const params = new URLSearchParams({ page: String(page), page_size: '12', sort })
    if (search.trim()) params.set('search', search.trim())
    if (role) params.set('role', role)
    if (department.trim()) params.set('department', department.trim())
    try {
      const [nextStats, nextAnalytics, nextActivity, nextUsers, nextLessons, nextQuizzes] = await Promise.all([
        authenticatedRequest<AdminStats>('/admin/stats'), authenticatedRequest<AdminAnalytics>('/admin/analytics'), authenticatedRequest<AdminActivity>('/admin/activity'), authenticatedRequest<AdminUserPage>(`/admin/users?${params.toString()}`), authenticatedRequest<AdminLesson[]>('/admin/lessons'), authenticatedRequest<AdminQuiz[]>('/admin/quizzes'),
      ])
      setStats(nextStats); setAnalytics(nextAnalytics); setActivity(nextActivity); setUsers(nextUsers); setLessons(nextLessons); setQuizzes(nextQuizzes)
    } catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Unable to load the admin dashboard.') } finally { setLoading(false) }
  }, [authenticatedRequest, department, page, role, search, sort])

  useEffect(() => { void load() }, [load])
  const filter = (setter: (value: string) => void, value: string) => { setPage(1); setter(value) }

  async function changeRole(user: AdminUser, nextRole: AdminUser['role']) {
    setUpdatingUserId(user.id); setActionError('')
    try { await authenticatedRequest<AdminUser>(`/admin/users/${user.id}`, { method: 'PATCH', body: JSON.stringify({ role: nextRole }) }); await load() } catch (requestError) { setActionError(requestError instanceof ApiError ? requestError.message : 'Unable to update this user.') } finally { setUpdatingUserId(null) }
  }

  if (loading && !stats) return <div className="mx-auto flex min-h-[70vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading CyberSathi administration…" /></div>
  if (error && !stats) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error} /><Button className="mt-6" type="button" onClick={() => void load()}>Try again</Button></div>
  if (!stats || !analytics || !activity || !users) return null

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
    <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end"><div className="max-w-3xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Platform Security &amp; Activity Overview</p><h1 className="mt-3 text-4xl font-black tracking-[-0.05em] text-ink sm:text-6xl">CyberSathi Admin Dashboard</h1><p className="mt-5 text-lg leading-8 text-ink/60">A privacy-conscious view of learning, security signals, and campus activity using live database aggregates.</p></div><Link className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white hover:bg-teal" to="/admin/incidents">Review incident queue →</Link></div>
    <div className="mt-8"><Alert variant="info"><strong>Admin privacy notice:</strong> this console excludes passwords, password hashes, tokens, message contents, submitted URLs, and evidence metadata.</Alert></div>
    {actionError && <div className="mt-6"><ErrorState message={actionError} /></div>}{error && <div className="mt-6"><Alert variant="warning">Some dashboard data could not be refreshed. Showing the last available results.</Alert></div>}
    <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Admin summary metrics"><MetricCard title="Registered users" value={stats.registered_users.toLocaleString()} /><MetricCard title="Active users · 30 days" value={stats.active_users.toLocaleString()} accent /><MetricCard title="Students" value={stats.students.toLocaleString()} /><MetricCard title="Faculty" value={stats.faculty.toLocaleString()} /><MetricCard title="Total quiz attempts" value={stats.total_quiz_attempts.toLocaleString()} /><MetricCard title="Total incidents" value={stats.total_incident_reports.toLocaleString()} /><MetricCard title="Email analyses" value={stats.total_email_analyses.toLocaleString()} /><MetricCard title="URL analyses" value={stats.total_url_analyses.toLocaleString()} /></section>
    <section className="mt-8 grid gap-6 lg:grid-cols-2" aria-label="Security analytics"><ChartCard eyebrow="User activity" title="Registrations over the last 30 days"><Trend items={activity.registrations} emptyTitle="No registrations in this window" /></ChartCard><ChartCard eyebrow="Incident activity" title="Incident trends"><Trend items={analytics.incident_trends} emptyTitle="No incidents in the trend window" /></ChartCard><ChartCard eyebrow="Threat landscape" title="Reported categories"><Bars items={analytics.threat_categories} valueKey="count" /></ChartCard><ChartCard eyebrow="Awareness" title="Average category scores"><Bars items={analytics.awareness_scores} valueKey="score" suffix="%" /></ChartCard><ChartCard eyebrow="Learning outcomes" title="Quiz performance"><Bars items={analytics.quiz_performance} valueKey="average_score" suffix="%" /></ChartCard><ChartCard eyebrow="Message analysis" title="Email risk levels"><Bars items={analytics.email_risk_levels} valueKey="count" /></ChartCard><ChartCard eyebrow="Link analysis" title="URL risk levels"><Bars items={analytics.url_risk_levels} valueKey="count" /></ChartCard><ChartCard eyebrow="Awareness distribution" title="Score distribution"><Bars items={analytics.awareness_distribution} valueKey="count" /></ChartCard></section>
    <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5" aria-label="Security analytics summary"><MetricCard title="Phishing reports" value={analytics.phishing_reports.toLocaleString()} /><MetricCard title="Suspicious URLs" value={analytics.suspicious_url_analyses.toLocaleString()} /><MetricCard title="High-risk URLs" value={analytics.high_risk_url_analyses.toLocaleString()} /><MetricCard title="High-risk emails" value={analytics.high_risk_email_analyses.toLocaleString()} /><MetricCard title="Awareness average" value={`${analytics.summary.awareness_average}%`} accent /></section>
    <section className="mt-12" aria-labelledby="management-heading"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Administration</p><h2 className="mt-2 text-3xl font-black tracking-[-0.03em] text-ink" id="management-heading">Manage the platform.</h2></div><Link className="text-sm font-black text-teal" to="/admin/incidents">Open incident queue →</Link></div>
      <Card className="mt-6"><div className="flex flex-col gap-4 lg:flex-row lg:items-end"><label className="grid flex-1 gap-2 text-sm font-bold text-ink" htmlFor="user-search">Search users<input className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" id="user-search" maxLength={100} placeholder="Name or email" value={search} onChange={(event) => filter(setSearch, event.target.value)} /></label><label className="grid gap-2 text-sm font-bold text-ink" htmlFor="user-role">Role<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" id="user-role" value={role} onChange={(event) => filter(setRole, event.target.value)}><option value="">All roles</option><option value="student">Student</option><option value="faculty">Faculty</option><option value="admin">Admin</option></select></label><label className="grid gap-2 text-sm font-bold text-ink" htmlFor="user-department">Department<input className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" id="user-department" maxLength={120} placeholder="Exact department" value={department} onChange={(event) => filter(setDepartment, event.target.value)} /></label><label className="grid gap-2 text-sm font-bold text-ink" htmlFor="user-sort">Sort<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium" id="user-sort" value={sort} onChange={(event) => { setPage(1); setSort(event.target.value as typeof sort) }}><option value="created_at_desc">Newest first</option><option value="created_at_asc">Oldest first</option></select></label></div><div className="mt-6 flex items-center justify-between gap-4"><p className="text-sm text-ink/55">Showing {users.users.length} of {users.total} users. Progress is aggregated per account.</p>{loading && <LoadingState label="Refreshing…" />}</div>{users.users.length ? <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[980px] text-left text-sm"><thead className="border-b border-ink/10 text-xs uppercase tracking-[0.1em] text-ink/40"><tr><th className="pb-3 pr-4">User</th><th className="pb-3 pr-4">Role</th><th className="pb-3 pr-4">Joined</th><th className="pb-3 pr-4">Last activity</th><th className="pb-3 pr-4">Learning</th><th className="pb-3 pr-4">Quiz average</th><th className="pb-3">Awareness</th></tr></thead><tbody>{users.users.map((user) => <tr className="border-b border-ink/5 last:border-0" key={user.id}><td className="py-4 pr-4"><p className="font-black text-ink">{user.name}</p><p className="mt-1 text-xs text-ink/50">{user.email}</p><p className="mt-1 text-xs text-ink/45">{user.department || 'No department'}{user.year ? ` · Year ${user.year}` : ''}</p></td><td className="py-4 pr-4"><select className="min-h-10 rounded-xl border border-ink/15 bg-white px-3 text-xs font-bold text-ink" aria-label={`Role for ${user.name}`} disabled={updatingUserId === user.id} value={user.role} onChange={(event) => void changeRole(user, event.target.value as AdminUser['role'])}><option value="student">Student</option><option value="faculty">Faculty</option><option value="admin">Admin</option></select></td><td className="py-4 pr-4 text-ink/60">{dateLabel(user.created_at)}</td><td className="py-4 pr-4 text-ink/60">{dateLabel(user.last_login_at)}</td><td className="py-4 pr-4 text-ink/60">{user.lessons_completed ?? 0} lessons · {user.quiz_attempts ?? 0} quizzes</td><td className="py-4 pr-4 font-bold text-ink/70">{user.average_quiz_score ?? 0}%</td><td className="py-4 font-bold text-teal">{user.awareness_score == null ? 'Not started' : `${user.awareness_score}%`}</td></tr>)}</tbody></table></div> : <div className="mt-5"><EmptyState title="No users found" description="Try a different filter or wait for registered accounts." /></div>}<div className="mt-6 flex items-center justify-between gap-4 border-t border-ink/10 pt-5"><Button type="button" variant="secondary" disabled={users.page <= 1 || loading} onClick={() => setPage((current) => Math.max(1, current - 1))}>← Previous</Button><span className="text-sm font-bold text-ink/55">Page {users.page} of {Math.max(users.total_pages, 1)}</span><Button type="button" variant="secondary" disabled={users.page >= users.total_pages || loading} onClick={() => setPage((current) => current + 1)}>Next →</Button></div></Card>
      <div className="mt-6 grid gap-6 xl:grid-cols-2"><Card><div className="flex items-center justify-between gap-3"><div><h3 className="text-xl font-black text-ink">Learning content</h3><p className="mt-1 text-sm text-ink/50">Lessons and quizzes are sourced from the database.</p></div><Link className="text-sm font-black text-teal" to="/learn">Open hub →</Link></div><div className="mt-5 grid gap-3">{lessons.length ? lessons.slice(0, 5).map((lesson) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={lesson.id}><div className="min-w-0"><p className="truncate text-sm font-black text-ink">{lesson.title}</p><p className="mt-1 text-xs text-ink/50">{label(lesson.category)} · {lesson.quiz_count} quiz{lesson.quiz_count === 1 ? '' : 'zes'}</p></div><span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-black capitalize text-ink/60">{lesson.difficulty}</span></div>) : <EmptyState title="No lessons found" description="Seed or create lessons to manage learning content." />}</div></Card><Card><p className="text-xs font-black uppercase tracking-[0.12em] text-teal">Quiz activity</p><h3 className="mt-2 text-xl font-black text-ink">Participation by quiz</h3>{quizzes.length ? <div className="mt-5 grid gap-3">{quizzes.slice(0, 6).map((quiz) => <div className="flex justify-between gap-3 rounded-2xl bg-mist px-4 py-3 text-sm" key={quiz.id}><span className="truncate font-bold text-ink/70">{quiz.title}</span><span className="shrink-0 text-xs font-black text-ink/45">{quiz.attempt_count} attempts</span></div>)}</div> : <EmptyState title="No quiz activity" description="Quiz participation will appear here after submission." />}</Card></div>
    </section><p className="mt-8 text-xs text-ink/40">Analytics generated {dateLabel(analytics.generated_at)}. Active users are accounts with a successful login in the last 30 days. Administrative updates are audit logged.</p>
  </div>
}
