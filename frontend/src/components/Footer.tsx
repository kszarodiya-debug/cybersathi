import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-ink/10 bg-ink text-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 sm:grid-cols-2 lg:grid-cols-[1.4fr_0.8fr_0.8fr_0.8fr] lg:px-8">
        <div>
          <Link className="flex items-center gap-3" to="/">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-signal font-black text-ink" aria-hidden="true">C</span>
            <span className="font-black tracking-[0.12em]">CYBERSATHI</span>
          </Link>
          <p className="mt-5 max-w-xs text-sm leading-6 text-white/55">A friendly security companion for safer study, work, and digital campus life.</p>
        </div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Explore</p><div className="mt-4 grid gap-3 text-sm text-white/60"><Link className="hover:text-white" to="/learn">Learn cybersecurity</Link><Link className="hover:text-white" to="/quiz">Take a quiz</Link><Link className="hover:text-white" to="/ask">Ask CyberSathi</Link></div></div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Check</p><div className="mt-4 grid gap-3 text-sm text-white/60"><Link className="hover:text-white" to="/analyze-email">Analyze email</Link><Link className="hover:text-white" to="/check-url">Check a URL</Link><Link className="hover:text-white" to="/register">Join CyberSathi</Link></div></div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Built for</p><p className="mt-4 text-sm leading-6 text-white/60">Students, faculty, and campus teams building better digital habits.</p></div>
      </div>
      <div className="border-t border-white/10"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-white/40 sm:flex-row sm:items-center sm:justify-between lg:px-8"><p>© 2026 CyberSathi. Safer clicks, stronger campus.</p><p>Initial platform foundation · v0.1.0</p></div></div>
    </footer>
  )
}
