import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-ink/10 bg-ink text-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 sm:grid-cols-2 lg:grid-cols-[1.4fr_0.8fr_0.8fr_0.8fr_0.9fr] lg:px-8">
        <div>
          <Link className="flex items-center gap-3" to="/" aria-label="CyberSathi home">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-signal font-black text-ink" aria-hidden="true">C</span>
            <span className="font-black tracking-[0.12em]">YBERSATHI</span>
          </Link>
          <p className="mt-5 max-w-xs text-sm leading-6 text-white/55">A friendly security companion for safer study, work, and digital campus life.</p>
        </div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Explore</p><div className="mt-4 grid gap-3 text-sm text-white/60"><Link className="hover:text-white" to="/learn">Learn cybersecurity</Link><Link className="hover:text-white" to="/quiz">Take a quiz</Link><Link className="hover:text-white" to="/ask">Ask CyberSathi</Link></div></div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Check</p><div className="mt-4 grid gap-3 text-sm text-white/60"><Link className="hover:text-white" to="/analyze-email">Analyze email</Link><Link className="hover:text-white" to="/check-url">Check a URL</Link><Link className="hover:text-white" to="/register">Join CyberSathi</Link></div></div>
        <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Built for</p><p className="mt-4 text-sm leading-6 text-white/60">Students, faculty, and campus teams building better digital habits.</p></div>
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-signal">Project owner</p>
          <p className="mt-3 text-lg font-black tracking-tight text-white drop-shadow-[0_0_14px_rgba(246,183,60,0.2)]">Kunal S. Zarodiya</p>
          <a
            className="group relative mt-5 flex min-h-24 w-full min-w-0 items-center gap-4 overflow-hidden rounded-2xl border border-fuchsia-300/30 bg-gradient-to-br from-fuchsia-500/20 via-rose-500/10 to-amber-300/10 p-4 text-left transition duration-300 hover:-translate-y-1 hover:scale-[1.02] hover:border-fuchsia-200/75 hover:shadow-[0_0_32px_rgba(236,72,153,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
            href="https://www.instagram.com/kunal.sysx"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Follow Kunal S. Zarodiya on Instagram"
          >
            <span className="instagram-pulse relative grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-tr from-amber-300 via-rose-500 to-fuchsia-600 text-white shadow-[0_0_22px_rgba(236,72,153,0.42)]" aria-hidden="true">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                <rect x="3.25" y="3.25" width="17.5" height="17.5" rx="5" />
                <circle cx="12" cy="12" r="4.1" />
                <circle cx="17.65" cy="6.45" r="0.8" fill="currentColor" stroke="none" />
              </svg>
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-black text-white">Follow Me on Instagram</span>
              <span className="mt-1 block truncate text-xs font-semibold text-white/70">@kunal.sysx</span>
              <span className="mt-2 block text-xs font-bold text-signal transition group-hover:text-white">Connect with me <span aria-hidden="true">↗</span></span>
            </span>
          </a>
        </div>
      </div>
      <div className="border-t border-white/10"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-white/40 sm:flex-row sm:items-center sm:justify-between lg:px-8"><p>© 2026 CyberSathi. Safer clicks, stronger campus.</p><p>Initial platform foundation · v0.1.0</p></div></div>
    </footer>
  )
}
