import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { ErrorState } from '../components/ErrorState'
import { Input } from '../components/Input'
import { LoadingState } from '../components/LoadingState'
import { ApiError } from '../services/api'

function AuthShell({ title, eyebrow, children, alternate }: { title: string; eyebrow: string; children: ReactNode; alternate: ReactNode }) {
  return <div className="mx-auto grid min-h-[calc(100vh-10rem)] max-w-7xl items-center gap-12 px-5 py-16 lg:grid-cols-[0.9fr_1.1fr] lg:px-8"><div className="hidden lg:block"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">{eyebrow}</p><h1 className="mt-4 max-w-xl text-6xl font-black leading-[0.98] tracking-[-0.06em] text-ink">A safer sign-in for a <span className="text-teal">safer campus.</span></h1><p className="mt-6 max-w-md text-lg leading-8 text-ink/60">Your CyberSathi session opens the door to learning, checks, and future campus security tools.</p><div className="mt-8 grid gap-3 text-sm font-semibold text-ink/60"><span>✓ Short-lived access tokens</span><span>✓ No password hashes in responses</span><span>✓ Student-first security guidance</span></div></div><div className="mx-auto w-full max-w-lg"><Card className="p-7 sm:p-9"><p className="text-xs font-black uppercase tracking-[0.2em] text-teal">{eyebrow}</p><h2 className="mt-3 text-3xl font-black tracking-tight text-ink">{title}</h2>{children}<div className="mt-7 border-t border-ink/10 pt-5 text-center text-sm text-ink/55">{alternate}</div></Card></div></div>
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  useEffect(() => { if (user) navigate('/dashboard', { replace: true }) }, [navigate, user])
  if (user) return null

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setLoading(true)
    try { await login(email, password); navigate(redirectTo, { replace: true }) } catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Unable to sign in right now.') } finally { setLoading(false) }
  }

  return <AuthShell eyebrow="Welcome back" title="Sign in to CyberSathi" alternate={<span>New here? <Link className="font-bold text-teal" to="/register">Create a student account</Link></span>}><form className="mt-8 grid gap-5" onSubmit={handleSubmit}><Input id="login-email" label="College email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /><Input id="login-password" label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /><Alert>Use your campus account details. Sessions are held securely in memory.</Alert>{error && <ErrorState message={error} />}<Button type="submit" loading={loading}>Sign in securely</Button>{loading && <LoadingState label="Checking your secure session…" />}</form></AuthShell>
}

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [department, setDepartment] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => { if (user) navigate('/dashboard', { replace: true }) }, [navigate, user])
  if (user) return null

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setLoading(true)
    try { await register(name, email, password, department); navigate('/dashboard', { replace: true }) } catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Unable to create your account right now.') } finally { setLoading(false) }
  }

  return <AuthShell eyebrow="Start here" title="Create your student account" alternate={<span>Already have an account? <Link className="font-bold text-teal" to="/login">Sign in</Link></span>}><form className="mt-8 grid gap-5" onSubmit={handleSubmit}><Input id="register-name" label="Full name" value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" minLength={2} maxLength={150} required /><Input id="register-email" label="College email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /><Input id="register-department" label="Department" hint="Optional — you can add this later." value={department} onChange={(event) => setDepartment(event.target.value)} maxLength={120} /><Input id="register-password" label="Password" hint="Use at least 12 characters. Never reuse an important password." type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={12} maxLength={128} required />{error && <ErrorState message={error} />}<Button type="submit" loading={loading}>Create account</Button>{loading && <LoadingState label="Creating your secure session…" />}</form></AuthShell>
}

export function AuthPages({ mode }: { mode: 'login' | 'register' }) {
  return mode === 'login' ? <LoginPage /> : <RegisterPage />
}
