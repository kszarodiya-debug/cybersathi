import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Card } from '../components/Card'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { ApiError } from '../services/api'
import type { LessonListResponse } from '../types/lesson'

function categoryLabel(category: string) {
  return category.split('-').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

export function LearningHubPage() {
  const { authenticatedRequest } = useAuth()
  const [data, setData] = useState<LessonListResponse | null>(null)
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadLessons = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const query = category ? `?category=${encodeURIComponent(category)}` : ''
      setData(await authenticatedRequest<LessonListResponse>(`/students/lessons${query}`))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load the Learning Hub right now.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, category])

  useEffect(() => { void loadLessons() }, [loadLessons])

  if (loading) return <div className="mx-auto flex min-h-[60vh] max-w-7xl items-center justify-center px-5"><LoadingState label="Loading learning paths…" /></div>
  if (error || !data) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error || 'Learning content is unavailable.'} /><button className="mt-6 rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white" type="button" onClick={() => void loadLessons()}>Try again</button></div>

  return <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16"><div className="max-w-3xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Learning Hub</p><h1 className="mt-4 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">Build safer digital habits.</h1><p className="mt-5 text-lg leading-8 text-ink/60">Short, practical lessons for the security decisions you make every day on campus and beyond.</p></div><Card tone="dark" className="mt-10 overflow-hidden p-7 sm:p-9"><div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Your progress</p><p className="mt-3 text-4xl font-black text-white">{data.completed_count}<span className="text-xl text-white/45">/{data.total}</span></p><p className="mt-2 text-sm text-white/55">lessons completed</p></div><div className="w-full max-w-md"><div className="flex justify-between text-xs font-bold text-white/55"><span>Keep going</span><span>{data.total ? Math.round((data.completed_count / data.total) * 100) : 0}%</span></div><div className="mt-3 h-3 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-signal transition-all" style={{ width: `${data.total ? (data.completed_count / data.total) * 100 : 0}%` }} /></div></div></div></Card><section className="mt-12" aria-labelledby="category-heading"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Explore topics</p><h2 className="mt-2 text-2xl font-black text-ink" id="category-heading">Choose a learning path</h2></div><span className="text-sm text-ink/45">{data.total} lessons available</span></div><div className="mt-5 flex gap-2 overflow-x-auto pb-2" role="tablist" aria-label="Lesson categories"><button className={`shrink-0 rounded-full px-4 py-2 text-sm font-bold transition ${category === '' ? 'bg-ink text-white' : 'border border-ink/10 bg-white text-ink/60 hover:border-teal hover:text-teal'}`} type="button" role="tab" aria-selected={category === ''} onClick={() => setCategory('')}>All topics</button>{data.categories.map((item) => <button className={`shrink-0 rounded-full px-4 py-2 text-sm font-bold transition ${category === item ? 'bg-teal text-white' : 'border border-ink/10 bg-white text-ink/60 hover:border-teal hover:text-teal'}`} key={item} type="button" role="tab" aria-selected={category === item} onClick={() => setCategory(item)}>{categoryLabel(item)}</button>)}</div>{data.lessons.length === 0 ? <div className="mt-6"><EmptyState title="No lessons in this category" description="Try another category or return to all topics." action={<button className="text-sm font-black text-teal" type="button" onClick={() => setCategory('')}>Show all topics →</button>} /></div> : <div className="mt-6 grid gap-5 md:grid-cols-2 lg:grid-cols-3">{data.lessons.map((lesson) => <Card className="flex flex-col" key={lesson.id}><div className="flex items-start justify-between gap-3"><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black capitalize text-teal-900">{lesson.difficulty}</span>{lesson.completed && <span className="rounded-full bg-signal/20 px-3 py-1 text-xs font-black text-ink">Completed</span>}</div><p className="mt-6 text-xs font-black uppercase tracking-[0.12em] text-teal">{categoryLabel(lesson.category)}</p><h3 className="mt-2 text-xl font-black leading-tight text-ink">{lesson.title}</h3><p className="mt-3 flex-1 text-sm leading-6 text-ink/60">{lesson.description}</p><Link className="mt-7 inline-flex text-sm font-black text-teal" to={`/learn/${lesson.id}`}>{lesson.completed ? 'Review lesson →' : 'Start lesson →'}</Link></Card>)}</div>}</section><div className="mt-12 grid gap-6 md:grid-cols-2"><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Learn at your pace</p><h2 className="mt-3 text-xl font-black text-ink">Progress belongs to you.</h2><p className="mt-4 text-sm leading-6 text-ink/65">Your completion status is stored with your authenticated account and is not shared with other students.</p></Card><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">Need a quick answer?</p><h2 className="mt-3 text-xl font-black">Ask CyberSathi.</h2><p className="mt-4 text-sm leading-6 text-white/60">Use the assistant when you want a concept explained in a little more detail.</p><Link className="mt-5 inline-flex text-sm font-black text-signal" to="/ask">Open assistant →</Link></Card></div></div>
}
