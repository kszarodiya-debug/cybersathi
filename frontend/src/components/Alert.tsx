import type { ReactNode } from 'react'

type AlertVariant = 'info' | 'success' | 'warning' | 'error'

const alertClasses: Record<AlertVariant, string> = {
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  success: 'border-teal/20 bg-teal/10 text-teal-950',
  warning: 'border-signal/40 bg-signal/15 text-ink',
  error: 'border-red-200 bg-red-50 text-red-800',
}

export function Alert({ children, variant = 'info' }: { children: ReactNode; variant?: AlertVariant }) {
  return <div className={`rounded-2xl border px-4 py-3 text-sm leading-6 ${alertClasses[variant]}`} role={variant === 'error' ? 'alert' : 'status'}>{children}</div>
}
