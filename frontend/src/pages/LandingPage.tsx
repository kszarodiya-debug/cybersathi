import { useState } from 'react'
import { Link } from 'react-router-dom'

import { buttonBaseClasses } from '../components/Button'
import { Card } from '../components/Card'
import { Modal } from '../components/Modal'

const featureCards = [
  { icon: '✦', eyebrow: 'Ask', title: 'Ask CyberSathi', text: 'Get clear, practical guidance for the security questions that show up in real campus life.', to: '/ask', cta: 'Ask a question' },
  { icon: '◎', eyebrow: 'Check', title: 'Analyze Email', text: 'Prepare suspicious messages for a safer review flow before you reply, click, or forward.', to: '/analyze-email', cta: 'Analyze Email' },
  { icon: '↗', eyebrow: 'Verify', title: 'Check URL', text: 'Use a focused URL-checking workspace to make the pause-and-verify habit easier.', to: '/check-url', cta: 'Check URL' },
  { icon: '◈', eyebrow: 'Build', title: 'Learn Cybersecurity', text: 'Build stronger digital habits with short, approachable learning journeys for your campus.', to: '/learn', cta: 'Learn Cybersecurity' },
  { icon: '✓', eyebrow: 'Practice', title: 'Take Quiz', text: 'Turn awareness into confidence with quiz-ready practice tied to the lessons you complete.', to: '/quiz', cta: 'Take Quiz' },
]

const categories = [
  { label: 'Phishing & scams', detail: 'Spot urgency, impersonation, and suspicious requests.', tone: 'bg-signal/20 text-ink' },
  { label: 'Passwords & access', detail: 'Protect accounts with better secrets and safer sign-ins.', tone: 'bg-teal/10 text-teal-950' },
  { label: 'Privacy on campus', detail: 'Make thoughtful choices with personal and academic data.', tone: 'bg-sky-100 text-sky-950' },
  { label: 'Safe browsing', detail: 'Navigate links, downloads, and public networks with confidence.', tone: 'bg-violet-100 text-violet-950' },
]

export function LandingPage() {
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <>
      <section className="relative overflow-hidden bg-mist">
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-50" aria-hidden="true" />
        <div className="pointer-events-none absolute -right-32 top-16 h-80 w-80 rounded-full bg-signal/25 blur-3xl" aria-hidden="true" />
        <div className="pointer-events-none absolute -left-32 bottom-0 h-80 w-80 rounded-full bg-teal/15 blur-3xl" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-7xl gap-16 px-5 pb-20 pt-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8 lg:pb-28 lg:pt-24">
          <div>
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-teal/20 bg-teal/5 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-teal"><span className="h-2 w-2 rounded-full bg-teal" aria-hidden="true" /> Built for safer campuses</div>
            <h1 className="max-w-3xl text-5xl font-black leading-[0.98] tracking-[-0.06em] text-ink sm:text-6xl lg:text-8xl">Your digital safety <span className="text-teal">companion.</span></h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-ink/65 sm:text-xl">CyberSathi helps students and staff pause, verify, learn, and respond with more confidence in a connected campus.</p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link className={`${buttonBaseClasses} bg-ink text-white shadow-xl shadow-ink/15 hover:bg-teal`} to="/ask">Ask CyberSathi <span aria-hidden="true">↗</span></Link>
              <Link className={`${buttonBaseClasses} border border-ink/15 bg-white text-ink hover:border-teal hover:text-teal`} to="/learn">Learn Cybersecurity</Link>
            </div>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 text-xs font-bold uppercase tracking-[0.16em] text-ink/45"><span>Student-friendly</span><span className="h-1 w-1 rounded-full bg-signal" aria-hidden="true" /><span>Privacy-aware</span><span className="h-1 w-1 rounded-full bg-signal" aria-hidden="true" /><span>Campus-ready</span></div>
          </div>

          <div className="relative mx-auto w-full max-w-lg">
            <div className="absolute -right-5 -top-8 h-28 w-28 rounded-[2rem] border border-teal/20 bg-white/40" aria-hidden="true" />
            <div className="relative rounded-[2.5rem] bg-ink p-3 shadow-2xl shadow-ink/25 sm:p-5">
              <div className="rounded-[2rem] border border-white/10 bg-[#183453] p-6 sm:p-8">
                <div className="flex items-start justify-between gap-5">
                  <div><p className="text-xs font-bold uppercase tracking-[0.2em] text-white/45">CyberSathi protocol</p><p className="mt-3 text-3xl font-black tracking-tight text-white">Pause. Verify. Protect.</p></div>
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-signal text-xl font-black text-ink" aria-hidden="true">✓</span>
                </div>
                <div className="mt-10 grid gap-3">
                  {[['01', 'Learn', 'Understand the pattern'], ['02', 'Check', 'Slow down the click'], ['03', 'Respond', 'Choose the safer next step']].map(([number, title, detail]) => <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4" key={number}><span className="text-sm font-black text-signal">{number}</span><span className="grid gap-1"><strong className="text-sm text-white">{title}</strong><span className="text-xs text-white/45">{detail}</span></span><span className="ml-auto text-white/35" aria-hidden="true">→</span></div>)}
                </div>
                <div className="mt-6 flex items-center justify-between rounded-2xl bg-teal p-4"><span className="text-sm font-bold text-white">A safer campus starts with one good pause.</span><span className="text-xl text-white/70" aria-hidden="true">✦</span></div>
              </div>
            </div>
            <div className="absolute -bottom-7 -left-7 rounded-2xl border border-ink/10 bg-white px-4 py-3 shadow-xl shadow-ink/10"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-ink/40">Designed for</p><p className="mt-1 text-sm font-bold text-ink">Every campus citizen</p></div>
          </div>
        </div>
      </section>

      <section className="border-y border-ink/10 bg-white" id="features">
        <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
          <div className="max-w-2xl"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">One place for everyday security</p><h2 className="mt-4 text-4xl font-black tracking-[-0.04em] text-ink sm:text-5xl">Small actions. Stronger habits.</h2><p className="mt-5 text-lg leading-8 text-ink/60">CyberSathi turns security awareness into approachable moments students and staff can actually use.</p></div>
          <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">{featureCards.map((feature, index) => <Card className={`${index === 0 ? 'lg:col-span-2 lg:flex lg:items-end lg:justify-between lg:gap-10' : ''} group transition hover:-translate-y-1 hover:border-teal/30 hover:shadow-xl hover:shadow-teal/5`} key={feature.to}><div><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-ink text-xl text-signal" aria-hidden="true">{feature.icon}</span><span className="text-xs font-black uppercase tracking-[0.18em] text-teal">{feature.eyebrow}</span></div><h3 className="mt-8 text-2xl font-black tracking-tight text-ink">{feature.title}</h3><p className="mt-3 max-w-md text-sm leading-6 text-ink/60">{feature.text}</p></div><Link className="mt-7 inline-flex items-center gap-2 text-sm font-black text-teal transition group-hover:gap-3 lg:shrink-0" to={feature.to}>{feature.cta} <span aria-hidden="true">↗</span></Link></Card>)}</div>
        </div>
      </section>

      <section className="bg-ink text-white" id="how-it-works">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[0.7fr_1.3fr] lg:px-8 lg:py-28"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-signal">How it works</p><h2 className="mt-4 text-4xl font-black tracking-[-0.04em] sm:text-5xl">Security guidance that meets you where you are.</h2><button className="mt-8 rounded-2xl border border-white/15 px-5 py-3 text-sm font-bold text-white/75 transition hover:border-signal hover:text-signal" type="button" onClick={() => setModalOpen(true)}>See the safety loop <span aria-hidden="true">↗</span></button></div><div className="grid gap-4 sm:grid-cols-3">{[['01', 'Bring the question', 'A strange email, an unfamiliar link, or a “what should I do?” moment.'], ['02', 'Build the context', 'Use learning, guided checks, and clear explanations to make sense of the signal.'], ['03', 'Make the move', 'Choose a safer next step and strengthen the habit for the next time.']].map(([number, title, text]) => <div className="border-t border-white/15 pt-5" key={number}><span className="text-sm font-black text-signal">{number}</span><h3 className="mt-12 text-xl font-black">{title}</h3><p className="mt-3 text-sm leading-6 text-white/55">{text}</p></div>)}</div></div>
      </section>

      <section className="bg-mist" id="categories">
        <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Explore the everyday</p><h2 className="mt-4 text-4xl font-black tracking-[-0.04em] text-ink sm:text-5xl">Your awareness toolkit.</h2></div><Link className="text-sm font-black text-teal" to="/learn">View learning paths <span aria-hidden="true">↗</span></Link></div><div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{categories.map((category) => <Card className="group transition hover:-translate-y-1 hover:shadow-xl" key={category.label}><span className={`inline-flex rounded-full px-3 py-1 text-xs font-black ${category.tone}`}>Topic</span><h3 className="mt-12 text-xl font-black tracking-tight text-ink">{category.label}</h3><p className="mt-3 text-sm leading-6 text-ink/60">{category.detail}</p><Link className="mt-6 inline-flex text-sm font-black text-teal" to="/learn" aria-label={`Learn about ${category.label}`}>Learn more <span className="ml-2" aria-hidden="true">↗</span></Link></Card>)}</div></div>
      </section>

      <section className="border-t border-ink/10 bg-white"><div className="mx-auto max-w-7xl px-5 py-20 text-center lg:px-8 lg:py-28"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">Ready when you are</p><h2 className="mx-auto mt-4 max-w-3xl text-4xl font-black tracking-[-0.05em] text-ink sm:text-6xl">Make your next digital decision a little safer.</h2><p className="mx-auto mt-5 max-w-xl text-lg leading-8 text-ink/60">Start with a question, a lesson, or a quick check. CyberSathi is here to help you take the next right step.</p><div className="mt-9 flex flex-wrap justify-center gap-3"><Link className={`${buttonBaseClasses} bg-teal text-white hover:bg-ink`} to="/register">Get started <span aria-hidden="true">↗</span></Link><Link className={`${buttonBaseClasses} border border-ink/15 bg-white text-ink hover:border-teal hover:text-teal`} to="/quiz">Take Quiz</Link></div></div></section>

      <Modal open={modalOpen} title="The CyberSathi safety loop" onClose={() => setModalOpen(false)}><p>Good security decisions rarely begin with panic. They begin with a pause: notice the signal, check the context, then choose a response you can explain.</p><ol className="mt-4 grid gap-3 text-ink"><li><strong>Pause:</strong> urgency is a signal, not an instruction.</li><li><strong>Verify:</strong> use a trusted channel and inspect the context.</li><li><strong>Protect:</strong> report, reset, or ask for help when needed.</li></ol></Modal>
    </>
  )
}
