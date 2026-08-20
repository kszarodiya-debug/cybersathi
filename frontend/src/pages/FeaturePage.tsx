import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { ErrorState } from '../components/ErrorState'
import { Input } from '../components/Input'
import { Textarea } from '../components/Textarea'

type FeatureKind = 'assistant' | 'email' | 'url' | 'learn' | 'quiz' | 'incident'

const featureConfig: Record<FeatureKind, { eyebrow: string; title: string; description: string; icon: string }> = {
  assistant: { eyebrow: 'AI assistant', title: 'Ask CyberSathi', description: 'Bring a cybersecurity question. The connected assistant will help you understand the risk and choose your next step.', icon: '✦' },
  email: { eyebrow: 'Message safety', title: 'Analyze Email', description: 'Review a suspicious message with a calm, structured workflow before you interact with it.', icon: '◎' },
  url: { eyebrow: 'Link safety', title: 'Check URL', description: 'Inspect a link in a focused workspace designed to make “pause before you click” a habit.', icon: '↗' },
  learn: { eyebrow: 'Learning paths', title: 'Learn Cybersecurity', description: 'Build practical security awareness through short topics made for students, faculty, and staff.', icon: '◈' },
  quiz: { eyebrow: 'Practice zone', title: 'Take Quiz', description: 'Turn lessons into confidence with quiz experiences connected to your awareness journey.', icon: '✓' },
  incident: { eyebrow: 'Campus response', title: 'Report Incident', description: 'Share a suspicious or harmful cybersecurity event with your campus response team.', icon: '!' },
}

export function FeaturePage({ kind }: { kind: FeatureKind }) {
  const config = featureConfig[kind]
  const { user } = useAuth()
  const [value, setValue] = useState('')

  const isInputFeature = kind === 'assistant' || kind === 'email' || kind === 'url' || kind === 'incident'
  const inputLabel = kind === 'assistant' ? 'Your question' : kind === 'email' ? 'Email content' : kind === 'url' ? 'URL to check' : 'Incident details'
  const placeholder = kind === 'assistant' ? 'Example: How can I tell if a message from a professor is genuine?' : kind === 'email' ? 'Paste the message here when the analyzer is connected.' : kind === 'url' ? 'https://example.com' : 'Describe what happened, when it happened, and any safe-to-share context.'

  return <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8 lg:py-20"><div className="max-w-3xl"><Link className="text-sm font-bold text-teal" to="/">← Back to CyberSathi</Link><div className="mt-8 flex items-start gap-5"><span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-ink text-2xl text-signal" aria-hidden="true">{config.icon}</span><div><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">{config.eyebrow}</p><h1 className="mt-3 text-4xl font-black tracking-[-0.04em] text-ink sm:text-6xl">{config.title}</h1></div></div><p className="mt-6 max-w-2xl text-lg leading-8 text-ink/60">{config.description}</p></div><div className="mt-12 grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">{isInputFeature ? <Card className="p-7 sm:p-9"><div className="flex items-center justify-between gap-4"><div><h2 className="text-2xl font-black text-ink">Secure workspace</h2><p className="mt-2 text-sm text-ink/55">No request is sent until the backend integration is available.</p></div><span className="rounded-full bg-signal/20 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-ink">Ready soon</span></div><div className="mt-8 grid gap-5">{kind === 'url' ? <Input id="feature-url" label={inputLabel} type="url" placeholder={placeholder} value={value} onChange={(event) => setValue(event.target.value)} /> : <Textarea id={`feature-${kind}`} label={inputLabel} placeholder={placeholder} value={value} onChange={(event) => setValue(event.target.value)} />}{user ? <Button type="button" disabled>Connect backend to continue</Button> : <Alert variant="warning"><Link className="font-bold underline underline-offset-4" to="/login">Sign in</Link> to prepare this workspace for your campus account.</Alert>}</div></Card> : <Card className="p-7 sm:p-9"><h2 className="text-2xl font-black text-ink">A clear path is coming</h2><p className="mt-3 text-sm leading-6 text-ink/60">This page is the accessible, responsive surface for the next backend-connected learning experience.</p><div className="mt-8 grid gap-3">{(kind === 'learn' ? ['Short learning paths', 'Campus-relevant examples', 'Progress connected to awareness'] : ['Questions tied to lessons', 'Immediate explanations', 'Awareness progress over time']).map((item) => <div className="flex items-center gap-3 rounded-2xl bg-mist px-4 py-3 text-sm font-semibold text-ink/70" key={item}><span className="text-teal" aria-hidden="true">✓</span>{item}</div>)}</div><div className="mt-8"><Button type="button" disabled>{kind === 'learn' ? 'Lesson catalog coming soon' : 'Quiz engine coming soon'}</Button></div></Card>}<div className="grid gap-6"><Card tone="dark"><p className="text-xs font-black uppercase tracking-[0.18em] text-signal">Security first</p><h2 className="mt-4 text-2xl font-black">Clarity before action.</h2><p className="mt-4 text-sm leading-6 text-white/55">CyberSathi will connect this experience to validated APIs without storing sensitive content in the browser.</p></Card><ErrorState message="This feature is not connected to a backend service yet. Your draft stays on this page and is not submitted." /></div></div></div>
}
