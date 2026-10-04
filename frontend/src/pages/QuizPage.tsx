import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { apiRequest, ApiError } from '../services/api'
import type {
  QuizAttemptHistory,
  QuizAttemptHistoryResponse,
  QuizAttemptStart,
  QuizListResponse,
  QuizResult,
} from '../types/quiz'

function categoryLabel(category: string) {
  return category.split('-').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function scoreClass(score: number | null) {
  if (score === null) return 'text-ink/35'
  if (score >= 80) return 'text-teal-900'
  if (score >= 50) return 'text-ink'
  return 'text-red-700'
}

function AwarenessSnapshot({ result }: { result: QuizResult }) {
  const items = [
    ['Overall', result.awareness_score.overall_score],
    ['Phishing', result.awareness_score.phishing_score],
    ['Passwords', result.awareness_score.password_score],
    ['Privacy', result.awareness_score.privacy_score],
    ['Browsing', result.awareness_score.browsing_score],
    ['Mobile', result.awareness_score.mobile_score],
  ] as const
  return <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">{items.map(([label, score]) => <div className="rounded-2xl bg-mist p-4" key={label}><p className="text-xs font-black uppercase tracking-[0.1em] text-ink/50">{label}</p><p className="mt-2 text-2xl font-black text-ink">{score}%</p></div>)}</div>
}

function HistoryList({ attempts }: { attempts: QuizAttemptHistory[] }) {
  if (attempts.length === 0) return <EmptyState title="No attempts yet" description="Complete a quiz to start building your awareness score." />
  return <div className="space-y-3">{attempts.map((attempt) => <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-mist px-4 py-3" key={attempt.attempt_id}><div className="min-w-0"><p className="truncate text-sm font-bold text-ink">{attempt.quiz_title}</p><p className="mt-1 text-xs text-ink/50">{categoryLabel(attempt.category)} · {formatDate(attempt.completed_at)}</p></div><span className={`text-sm font-black ${scoreClass((attempt.score / 100) * 100)}`}>{attempt.score}%</span></div>)}</div>
}

export function QuizPage() {
  const { user, authenticatedRequest } = useAuth()
  const [catalog, setCatalog] = useState<QuizListResponse | null>(null)
  const [history, setHistory] = useState<QuizAttemptHistoryResponse | null>(null)
  const [category, setCategory] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [activeAttempt, setActiveAttempt] = useState<QuizAttemptStart | null>(null)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const query = new URLSearchParams()
      if (category) query.set('category', category)
      if (difficulty) query.set('difficulty', difficulty)
      const suffix = query.toString() ? `?${query.toString()}` : ''
      const [quizData, attemptData] = await Promise.all([
        user
          ? authenticatedRequest<QuizListResponse>(`/students/quizzes${suffix}`)
          : apiRequest<QuizListResponse>(`/public/quizzes${suffix}`),
        user
          ? authenticatedRequest<QuizAttemptHistoryResponse>('/students/quiz-attempts')
          : Promise.resolve<QuizAttemptHistoryResponse>({ attempts: [], total: 0 }),
      ])
      setCatalog(quizData)
      setHistory(attemptData)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load quizzes right now.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, category, difficulty, user])

  useEffect(() => { void loadData() }, [loadData])

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers])

  async function startQuiz(quizId: number) {
    if (!user) {
      setActionError('Sign in to take this quiz and save your awareness score.')
      return
    }
    setStarting(true)
    setActionError('')
    setResult(null)
    try {
      const attempt = await authenticatedRequest<QuizAttemptStart>(`/students/quizzes/${quizId}/attempts`, { method: 'POST' })
      setActiveAttempt(attempt)
      setAnswers({})
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (requestError) {
      setActionError(requestError instanceof ApiError ? requestError.message : 'Unable to start this quiz.')
    } finally {
      setStarting(false)
    }
  }

  async function submitQuiz() {
    if (!activeAttempt || answeredCount !== activeAttempt.questions.length) return
    setSubmitting(true)
    setActionError('')
    try {
      const quizResult = await authenticatedRequest<QuizResult>(`/students/quizzes/${activeAttempt.quiz_id}/attempts/${activeAttempt.attempt_id}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers: activeAttempt.questions.map((question) => ({ question_id: question.id, answer: answers[question.id] })) }),
      })
      setResult(quizResult)
      setActiveAttempt(null)
      await loadData()
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (requestError) {
      setActionError(requestError instanceof ApiError ? requestError.message : 'Unable to submit this quiz.')
    } finally {
      setSubmitting(false)
    }
  }

  function resetQuiz() {
    setActiveAttempt(null)
    setResult(null)
    setAnswers({})
    setActionError('')
  }

  if (loading) return <div className="mx-auto flex min-h-[60vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading quizzes…" /></div>
  if (error || !catalog || !history) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error || 'Quiz data is unavailable.'} /><button className="mt-6 rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white" type="button" onClick={() => void loadData()}>Try again</button></div>

  if (result) return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><Link className="text-sm font-bold text-teal" to="/dashboard">← Back to dashboard</Link><div className="mt-8 max-w-3xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Quiz complete</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Nice work. Keep building the habit.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Your answers were graded by CyberSathi and your awareness score was recalculated from your submitted attempts.</p></div><Card tone="dark" className="mt-10 overflow-hidden p-7 sm:p-9"><div className="flex flex-col gap-8 md:flex-row md:items-center md:justify-between"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-white/50">Your result</p><p className="mt-2 text-7xl font-black tracking-[-0.08em] text-signal">{result.score}<span className="text-3xl text-white/50">%</span></p></div><div className="rounded-2xl bg-white/10 px-5 py-4 text-sm text-white/70"><span className="font-black text-white">{result.correct_answers}</span> correct out of <span className="font-black text-white">{result.total_questions}</span></div></div></Card><section className="mt-8"><div className="mb-4"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Awareness score</p><h2 className="mt-2 text-2xl font-black text-ink">Your updated security baseline</h2></div><AwarenessSnapshot result={result} /></section><section className="mt-10"><div className="mb-4"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Review answers</p><h2 className="mt-2 text-2xl font-black text-ink">Understand every choice</h2></div><div className="grid gap-4">{result.results.map((row, index) => <Card className={row.is_correct ? 'border-teal/20' : 'border-red-200'} key={row.question_id}><div className="flex items-start gap-4"><span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-black ${row.is_correct ? 'bg-teal/10 text-teal-900' : 'bg-red-50 text-red-700'}`}>{row.is_correct ? '✓' : '!'}</span><div className="min-w-0"><p className="text-xs font-black uppercase tracking-[0.1em] text-ink/45">Question {index + 1}</p><p className="mt-2 text-sm font-bold text-ink">Your answer: <span className="font-normal text-ink/65">{row.selected_answer}</span></p><p className="mt-1 text-sm font-bold text-ink">Correct answer: <span className="font-normal text-ink/65">{row.correct_answer}</span></p><p className="mt-3 text-sm leading-6 text-ink/60">{row.explanation}</p></div></div></Card>)}</div></section><div className="mt-8 flex flex-wrap gap-3"><Button type="button" onClick={resetQuiz}>Back to quiz catalog</Button><Button variant="secondary" type="button" onClick={() => void startQuiz(result.quiz_id)}>Try again</Button></div></div>

  if (activeAttempt) return <div className="mx-auto max-w-4xl px-5 py-12 lg:px-8 lg:py-16"><button className="text-sm font-bold text-teal" type="button" onClick={resetQuiz}>← Leave quiz</button><div className="mt-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">{categoryLabel(activeAttempt.category)} · {activeAttempt.difficulty}</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink">{activeAttempt.title}</h1><p className="mt-3 text-sm text-ink/55">Answer every question. Your score is calculated securely after submission.</p></div><span className="rounded-full bg-teal/10 px-4 py-2 text-sm font-black text-teal-900">{answeredCount}/{activeAttempt.questions.length} answered</span></div>{actionError && <div className="mt-6"><ErrorState message={actionError} /></div>}<div className="mt-8 grid gap-5">{activeAttempt.questions.map((question, index) => <Card key={question.id}><p className="text-xs font-black uppercase tracking-[0.12em] text-teal">Question {index + 1}</p><h2 className="mt-3 text-xl font-black leading-8 text-ink">{question.question}</h2><div className="mt-6 grid gap-3">{question.options.map((option) => <label className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-4 text-sm font-semibold transition ${answers[question.id] === option ? 'border-teal bg-teal/5 text-teal-950' : 'border-ink/10 bg-white text-ink/70 hover:border-teal/40'}`} key={option}><input className="mt-1 accent-teal" type="radio" name={`question-${question.id}`} value={option} checked={answers[question.id] === option} onChange={() => setAnswers((current) => ({ ...current, [question.id]: option }))} />{option}</label>)}</div></Card>)}</div><div className="sticky bottom-4 mt-8 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-ink/10 bg-white/95 p-4 shadow-xl backdrop-blur"><p className="text-sm font-semibold text-ink/60">{answeredCount === activeAttempt.questions.length ? 'Ready to submit.' : 'Choose an answer for every question.'}</p><Button type="button" loading={submitting} disabled={answeredCount !== activeAttempt.questions.length} onClick={() => void submitQuiz()}>Submit quiz</Button></div></div>

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to="/dashboard">← Back to dashboard</Link><p className="mt-8 text-xs font-black uppercase tracking-[0.2em] text-teal">Practice zone</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Practice safer decisions.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Take short, practical quizzes connected to your Learning Hub progress. Correct answers and explanations are kept on the backend until you submit.</p></div><div className="rounded-3xl bg-ink px-6 py-5 text-white"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Your attempts</p><p className="mt-2 text-3xl font-black">{history.total}</p><p className="mt-1 text-sm text-white/55">completed quizzes</p></div></div>{actionError && <div className="mt-8"><ErrorState message={actionError} /></div>}<Card className="mt-10 p-5 sm:p-6"><div className="flex flex-col gap-4 sm:flex-row"><label className="grid flex-1 gap-2 text-sm font-bold text-ink" htmlFor="quiz-category">Category<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium outline-none focus:border-teal focus:ring-4 focus:ring-teal/10" id="quiz-category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{catalog.categories.map((item) => <option key={item} value={item}>{categoryLabel(item)}</option>)}</select></label><label className="grid flex-1 gap-2 text-sm font-bold text-ink" htmlFor="quiz-difficulty">Difficulty<select className="min-h-11 rounded-2xl border border-ink/15 bg-white px-4 text-sm font-medium outline-none focus:border-teal focus:ring-4 focus:ring-teal/10" id="quiz-difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="">All levels</option>{catalog.difficulties.map((item) => <option key={item} value={item}>{categoryLabel(item)}</option>)}</select></label></div></Card><section className="mt-10" aria-labelledby="quiz-catalog-heading"><div className="flex items-end justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Quiz catalog</p><h2 className="mt-2 text-2xl font-black text-ink" id="quiz-catalog-heading">Choose a topic to practice</h2></div><span className="text-sm text-ink/45">{catalog.total} available</span></div>{catalog.quizzes.length === 0 ? <div className="mt-5"><EmptyState title="No quizzes match these filters" description="Try another category or difficulty level." action={<button className="text-sm font-black text-teal" type="button" onClick={() => { setCategory(''); setDifficulty('') }}>Clear filters →</button>} /></div> : <div className="mt-5 grid gap-5 md:grid-cols-2 lg:grid-cols-3">{catalog.quizzes.map((quiz) => <Card className="flex flex-col" key={quiz.id}><div className="flex items-start justify-between gap-3"><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black text-teal-900">{categoryLabel(quiz.category)}</span><span className="text-xs font-black capitalize text-ink/45">{quiz.difficulty}</span></div><h3 className="mt-6 text-xl font-black leading-tight text-ink">{quiz.title}</h3><p className="mt-3 flex-1 text-sm leading-6 text-ink/60">{quiz.description}</p><div className="mt-6 flex items-center justify-between text-xs font-bold text-ink/45"><span>{quiz.question_count} questions</span><span className={scoreClass(quiz.best_score)}>{quiz.best_score === null ? 'Not attempted' : `Best ${quiz.best_score}%`}</span></div><Button className="mt-6 w-full" type="button" loading={starting} disabled={starting} onClick={() => void startQuiz(quiz.id)}>Start quiz</Button></Card>)}</div>}</section><section className="mt-12" aria-labelledby="history-heading"><div className="mb-5"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Attempt history</p><h2 className="mt-2 text-2xl font-black text-ink" id="history-heading">Your recent practice</h2></div><HistoryList attempts={history.attempts} /></section><Alert variant="info" >Scores are calculated from the answer choices validated against the database. The frontend never sends or sets a score.</Alert></div>
}
