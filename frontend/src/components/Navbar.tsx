import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Button, buttonBaseClasses } from './Button'

const navLinks = [
  { label: 'Features', to: '/#features' },
  { label: 'How it works', to: '/#how-it-works' },
  { label: 'Learn', to: '/learn' },
  { label: 'Take a quiz', to: '/quiz' },
]

function navLinkClass({ isActive }: { isActive: boolean }) {
  return `text-sm font-semibold transition hover:text-teal ${isActive ? 'text-teal' : 'text-ink/60'}`
}

export function Navbar() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()

  const closeMenu = () => setOpen(false)

  return (
    <header className="relative z-40 border-b border-ink/10 bg-mist/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-8">
        <Link className="flex items-center gap-3" to="/" onClick={closeMenu}>
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-ink text-lg font-black text-white shadow-lg shadow-ink/15" aria-hidden="true">C</span>
          <span className="text-base font-black tracking-[0.12em] text-ink">CYBERSATHI</span>
        </Link>

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Primary navigation">
          {navLinks.map((link) => <NavLink className={navLinkClass} key={link.to} to={link.to}>{link.label}</NavLink>)}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          {user ? (
            <>
              {user.role === 'admin' && <NavLink className={navLinkClass} to="/admin">Admin console</NavLink>}
              <NavLink className={navLinkClass} to="/dashboard">{user.name}</NavLink>
              <Button variant="ghost" type="button" onClick={() => void logout()}>Log out</Button>
            </>
          ) : (
            <>
              <NavLink className={navLinkClass} to="/login">Sign in</NavLink>
              <Link className={`${buttonBaseClasses} bg-teal text-white hover:bg-ink`} to="/register">Get started</Link>
            </>
          )}
        </div>

        <button className="grid h-11 w-11 place-items-center rounded-2xl border border-ink/10 text-xl text-ink lg:hidden" type="button" aria-expanded={open} aria-controls="mobile-navigation" aria-label={open ? 'Close navigation menu' : 'Open navigation menu'} onClick={() => setOpen(!open)}>
          {open ? '×' : '☰'}
        </button>
      </div>

      {open && <nav className="border-t border-ink/10 bg-white px-5 py-5 lg:hidden" id="mobile-navigation" aria-label="Mobile navigation">
        <div className="grid gap-4">
          {navLinks.map((link) => <NavLink className={navLinkClass} key={link.to} to={link.to} onClick={closeMenu}>{link.label}</NavLink>)}
          {user ? (
            <>
              {user.role === 'admin' && <NavLink className={navLinkClass} to="/admin" onClick={closeMenu}>Admin console</NavLink>}
              <NavLink className={navLinkClass} to="/dashboard" onClick={closeMenu}>Dashboard</NavLink>
              <Button variant="ghost" type="button" onClick={() => { closeMenu(); void logout() }}>Log out</Button>
            </>
          ) : (
            <>
              <NavLink className={navLinkClass} to="/login" onClick={closeMenu}>Sign in</NavLink>
              <Link className={`${buttonBaseClasses} w-fit bg-teal text-white`} to="/register" onClick={closeMenu}>Get started</Link>
            </>
          )}
        </div>
      </nav>}
    </header>
  )
}
