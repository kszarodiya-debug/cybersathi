import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { ApiError } from '../services/api'
import type { LessonCompletionResponse, LessonDetail } from '../types/lesson'

function categoryLabel(category: string) {
  return category.split('-').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

function ContentList({ items, icon = '✓' }: { items: string[]; icon?: string }) {
  return <ul className="grid gap-3">{items.map((item) => <li className="flex gap-3 rounded-2xl bg-mist px-4 py-3 text-sm leading-6 text-ink/70" key={item}><span className="mt-0.5 font-black text-teal" aria-hidden="true">{icon}</span><span>{item}</span></li>)}</ul>
}

export function LessonDetailPage() {
  const { lessonId } = useParams<{ lessonId: string }>()
  const { authenticatedRequest } = useAuth()
  const [lesson, setLesson] = useState<LessonDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState('')

  const loadLesson = useCallback(async () => {
    if (!lessonId) return
    setLoading(true)
    setError('')
    try {
      setLesson(await authenticatedRequest<LessonDetail>(`/students/lessons/${lessonId}`))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to load this lesson right now.')
    } finally {
      setLoading(false)
    }
  }, [authenticatedRequest, lessonId])

  useEffect(() => { void loadLesson() }, [loadLesson])

  const complete = async () => {
    if (!lessonId || !lesson || lesson.completed) return
    setCompleting(true)
    setError('')
    try {
      const completion = await authenticatedRequest<LessonCompletionResponse>(`/students/lessons/${lessonId}/complete`, { method: 'POST' })
      setLesson((current) => current ? { ...current, completed: completion.completed, completed_at: completion.completed_at } : current)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to save your progress right now.')
    } finally {
      setCompleting(false)
    }
  }

  if (loading) return <div className="mx-auto flex min-h-[60vh] max-w-4xl items-center justify-center px-5"><LoadingState label="Loading lesson…" /></div>
  if (error && !lesson) return <div className="mx-auto max-w-2xl px-5 py-24"><ErrorState message={error} /><button className="mt-6 rounded-2xl bg-ink px-5 py-3 text-sm font-bold text-white" type="button" onClick={() => void loadLesson()}>Try again</button></div>
  if (!lesson) return null

  return <div className="mx-auto max-w-5xl px-5 py-12 lg:px-8 lg:py-16"><Link className="text-sm font-bold text-teal" to="/learn">← Back to Learning Hub</Link><div className="mt-8 max-w-3xl"><div className="flex flex-wrap items-center gap-3"><span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-black capitalize text-teal-900">{categoryLabel(lesson.category)}</span><span className="rounded-full bg-ink/10 px-3 py-1 text-xs font-black capitalize text-ink/65">{lesson.difficulty}</span>{lesson.completed && <span className="rounded-full bg-signal/20 px-3 py-1 text-xs font-black text-ink">Completed</span>}</div><h1 className="mt-5 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">{lesson.title}</h1><p className="mt-5 text-lg leading-8 text-ink/65">{lesson.introduction}</p></div>{error && <div className="mt-6"><ErrorState message={error} /></div>}<div className="mt-10 grid gap-6"><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.16em] text-signal">What you will learn</p><div className="mt-5"><ContentList items={lesson.learning_objectives} icon="→" /></div></Card><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Explanation</p><p className="mt-4 text-base leading-8 text-ink/70">{lesson.explanation}</p></Card><Card tone="accent"><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Real-world example</p><p className="mt-4 text-base leading-8 text-ink/70">{lesson.real_world_example}</p></Card><div className="grid gap-6 md:grid-cols-2"><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Safety tips</p><div className="mt-5"><ContentList items={lesson.safety_tips} /></div></Card><Card><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Key takeaways</p><div className="mt-5"><ContentList items={lesson.key_takeaways} icon="◆" /></div></Card></div><Card className="flex flex-col justify-between gap-6 border-teal/20 bg-teal/5 sm:flex-row sm:items-center"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-teal">Your progress</p><h2 className="mt-2 text-xl font-black text-ink">{lesson.completed ? 'Lesson completed' : 'Finished reading?'}</h2><p className="mt-2 text-sm text-ink/60">{lesson.completed ? 'This lesson is included in your Learning Hub progress.' : 'Mark this lesson complete when you are ready.'}</p></div><Button type="button" loading={completing} disabled={lesson.completed} onClick={() => void complete()}>{lesson.completed ? 'Completed' : 'Mark complete'}</Button></Card><Alert variant="info">CyberSathi lessons build awareness. For an active incident, contact your campus IT or security team through an official channel.</Alert></div></div>
}
