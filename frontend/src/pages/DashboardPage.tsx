import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { buttonBaseClasses } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { ApiError } from '../services/api'
import type { AwarenessScore, QuizScore, RecentActivity, StudentDashboard } from '../types/dashboard'

const scoreItems: Array<{ key: keyof Omit<AwarenessScore, 'overall_score'>; label: string; icon: string }> = [
  { key: 'phishing_score', label: 'Phishing awareness', icon: '◉' },
  { key: 'password_score', label: 'Password security', icon: '⌁' },
  { key: 'privacy_score', label: 'Data privacy', icon: '◇' },
  { key: 'browsing_score', label: 'Safe browsing', icon: '↗' },
  { key: 'mobile_score', label: 'Mobile security', icon: '⌂' },
]

const quickActions = [
  { label: 'Ask CyberSathi', description: 'Get a clear answer', href: '/ask', icon: '✦' },
  { label: 'Analyze Email', description: 'Pause before replying', href: '/analyze-email', icon: '◎' },
  { label: 'Check URL', description: 'Inspect a suspicious link', href: '/check-url', icon: '↗' },
  { label: 'Report Incident', description: 'Tell your campus team', href: '/report-incident', icon: '!' },
  { label: 'Continue Learning', description: 'Build safer habits', href: '/learn', icon: '◈' },
  { label: 'Take Quiz', description: 'Practice your awareness', href: '/quiz', icon: '✓' },
]

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function riskClass(level: string) {
  if (level.toLowerCase() === 'high' || level.toLowerCase() === 'critical') return 'bg-red-100 text-red-700'
  if (level.toLowerCase() === 'medium') return 'bg-signal/25 text-ink'
  return 'bg-teal/10 text-teal-900'
}

function ScoreBreakdown({ score }: { score: AwarenessScore }) {
  return <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{scoreItems.map((item) => <div className="rounded-2xl bg-mist p-4" key={item.key}><div className="flex items-center justify-between gap-3"><span className="text-lg text-teal" aria-hidden="true">{item.icon}</span><span className="text-xl font-black text-ink">{score[item.key]}%</span></div><p className="mt-5 text-xs font-black uppercase tracking-[0.12em] text-ink/50">{item.label}</p><div className="mt-3 h-2 overflow-hidden rounded-full bg-ink/10"><div className="h-full rounded-full bg-teal" style={{ width: `${Math.min(100, Math.max(0, score[item.key]))}%` }} /></div></div>)}</div>
}

function QuizList({ quizzes }: { quizzes: QuizScore[] }) {
  if (quizzes.length === 0) return <EmptyState title="No quiz attempts yet" description="Take your first quiz to start tracking practice scores." action={<Link className="text-sm font-black text-teal" to="/quiz">Take a quiz →</Link>} />
  return <div className="space-y-3">{quizzes.map((quiz) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={quiz.attempt_id}><div className="min-w-0"><p className="truncate text-sm font-bold text-ink">{quiz.quiz_title}</p><p className="mt-1 text-xs text-ink/50">{formatDate(quiz.completed_at)}</p></div><span className="shrink-0 text-sm font-black text-teal">{quiz.score}/{quiz.total_questions}</span></div>)}</div>
}

function ActivityLists({ activity }: { activity: RecentActivity }) {
  return <div className="grid gap-6 lg:grid-cols-2">
    <Card><h3 className="text-lg font-black text-ink">Recent email analyses</h3><div className="mt-5 space-y-3">{activity.email_analyses.length === 0 ? <EmptyState title="No email analyses" description="Your analyzed messages will appear here." /> : activity.email_analyses.map((item) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={item.id}><div><p className="text-sm font-bold text-ink">Email analysis #{item.id}</p><p className="mt-1 text-xs text-ink/50">{formatDate(item.created_at)}</p></div><span className={`rounded-full px-3 py-1 text-xs font-black capitalize ${riskClass(item.risk_level)}`}>{item.risk_level} · {item.risk_score}%</span></div>)}</div></Card>
    <Card><h3 className="text-lg font-black text-ink">Recent URL analyses</h3><div className="mt-5 space-y-3">{activity.url_analyses.length === 0 ? <EmptyState title="No URL checks" description="Your checked links will appear here." /> : activity.url_analyses.map((item) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={item.id}><div className="min-w-0"><p className="truncate text-sm font-bold text-ink">{item.url}</p><p className="mt-1 text-xs text-ink/50">{formatDate(item.created_at)}</p></div><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-black capitalize ${riskClass(item.risk_level)}`}>{item.risk_level} · {item.risk_score}%</span></div>)}</div></Card>
    <Card><h3 className="text-lg font-black text-ink">Recent quizzes</h3><div className="mt-5"><QuizList quizzes={activity.quizzes} /></div></Card>
    <Card><h3 className="text-lg font-black text-ink">Recent reports</h3><div className="mt-5 space-y-3">{activity.reports.length === 0 ? <EmptyState title="No incident reports" description="Reports you submit will be visible here for follow-up." action={<Link className="text-sm font-black text-teal" to="/report-incident">Report an incident →</Link>} /> : activity.reports.map((item) => <div className="flex items-center justify-between gap-4 rounded-2xl bg-mist px-4 py-3" key={item.id}><div><p className="text-sm font-bold capitalize text-ink">{item.incident_type} report</p><p className="mt-1 text-xs text-ink/50">{formatDate(item.created_at)}</p></div><span className="rounded-full bg-ink/10 px-3 py-1 text-xs font-black capitalize text-ink/70">{item.status}</span></div>)}</div></Card>
  </div>
}

export function DashboardPage() {
  const { authenticatedRequest } = useAuth()
  const [dashboard, setDashboard] = useState<StudentDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setDashboard(await authenticatedRequest<StudentDashboard>('/students/dashboard'))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load your dashboard right now.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest])

  useEffect(() => { void loadDashboard() }, [loadDashboard, reloadKey])

  if (loading) return <div className="mx-auto flex min-h-[60vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading your dashboard…" /></div>
  if (error || !dashboard) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error || 'Dashboard data is unavailable.'} /><button className={`${buttonBaseClasses} mt-6 bg-ink text-white`} onClick={() => setReloadKey((key) => key + 1)} type="button">Try again</button></div>

  const firstName = dashboard.user.name.split(' ')[0]
  const score = dashboard.awareness_score
  const progress = dashboard.learning_progress

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Your campus cockpit</p><h1 className="mt-4 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Welcome, {firstName}.</h1><p className="mt-4 max-w-2xl text-lg leading-8 text-ink/60">A private view of your learning, checks, and everyday cybersecurity habits.</p></div><span className="w-fit rounded-full border border-teal/20 bg-teal/10 px-4 py-2 text-sm font-bold capitalize text-teal-900">{dashboard.user.role} account</span></div>
    <section className="mt-10" aria-labelledby="awareness-heading"><div className="mb-5 flex items-end justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Awareness score</p><h2 className="mt-2 text-2xl font-black text-ink" id="awareness-heading">Your security baseline</h2></div>{score && <span className="text-sm font-bold text-ink/50">Updated from your activity</span>}</div>{score ? <Card tone="dark" className="overflow-hidden p-7 sm:p-9"><div className="flex flex-col gap-8 md:flex-row md:items-center"><div className="shrink-0"><p className="text-xs font-black uppercase tracking-[0.16em] text-white/50">Overall score</p><p className="mt-2 text-7xl font-black tracking-[-0.08em] text-signal">{score.overall_score}<span className="text-3xl text-white/50">%</span></p></div><div className="h-px bg-white/10 md:h-20 md:w-px" /><div className="w-full"><ScoreBreakdown score={score} /></div></div></Card> : <Card><EmptyState title="Your awareness score is waiting" description="Complete lessons and quizzes to build a personalized baseline." action={<Link className="text-sm font-black text-teal" to="/learn">Start learning →</Link>} /></Card>}</section>
    <section className="mt-12" aria-labelledby="quick-actions-heading"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Next best actions</p><h2 className="mt-2 text-2xl font-black text-ink" id="quick-actions-heading">Keep your momentum</h2><div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{quickActions.map((action) => <Link className="group rounded-3xl border border-ink/10 bg-white p-5 shadow-sm shadow-ink/5 transition hover:-translate-y-1 hover:border-teal/30 hover:shadow-lg" key={action.href} to={action.href}><div className="flex items-start justify-between gap-4"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-ink text-xl text-signal" aria-hidden="true">{action.icon}</span><span className="text-xl text-ink/25 transition group-hover:text-teal" aria-hidden="true">↗</span></div><h3 className="mt-6 text-lg font-black text-ink">{action.label}</h3><p className="mt-1 text-sm text-ink/55">{action.description}</p></Link>)}</div></section>
    <section className="mt-12" aria-labelledby="progress-heading"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Learning progress</p><h2 className="mt-2 text-2xl font-black text-ink" id="progress-heading">Small steps, safer habits</h2><div className="mt-5 grid gap-4 md:grid-cols-3"><Card><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/50">Completed lessons</p><p className="mt-4 text-4xl font-black text-ink">{progress.completed_lessons}</p><p className="mt-2 text-sm text-ink/55">lessons completed</p></Card><Card><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/50">Learning streak</p><p className="mt-4 text-4xl font-black text-ink">{progress.current_streak}</p><p className="mt-2 text-sm text-ink/55">{progress.current_streak === 1 ? 'day' : 'days'} in a row</p></Card><Card><p className="text-xs font-black uppercase tracking-[0.12em] text-ink/50">Quiz scores</p><div className="mt-4"><QuizList quizzes={progress.quiz_scores} /></div></Card></div></section>
    <section className="mt-12" aria-labelledby="activity-heading"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Recent activity</p><h2 className="mt-2 text-2xl font-black text-ink" id="activity-heading">Your latest security moments</h2><div className="mt-5"><ActivityLists activity={dashboard.recent_activity} /></div></section>
    <Alert variant="info">Your dashboard only includes records associated with your authenticated account. Sensitive email and report content is not displayed here.</Alert>
  </div>
}
