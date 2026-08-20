import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  tone?: 'light' | 'dark' | 'accent'
}

const toneClasses = {
  light: 'border-ink/10 bg-white shadow-sm shadow-ink/5',
  dark: 'border-white/10 bg-ink text-white shadow-2xl shadow-ink/20',
  accent: 'border-teal/15 bg-teal/5',
}

export function Card({ children, tone = 'light', className = '', ...props }: CardProps) {
  return <div className={`rounded-3xl border p-6 ${toneClasses[tone]} ${className}`} {...props}>{children}</div>
}
