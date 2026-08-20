import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-ink text-white shadow-lg shadow-ink/15 hover:bg-teal',
  secondary: 'border border-ink/15 bg-white text-ink hover:border-teal hover:text-teal',
  ghost: 'text-ink/70 hover:bg-ink/5 hover:text-ink',
  danger: 'border border-red-200 bg-red-50 text-red-700 hover:bg-red-100',
}

export const buttonBaseClasses = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl px-5 py-3 text-sm font-bold transition focus:outline-none focus:ring-4 focus:ring-teal/20 disabled:cursor-not-allowed disabled:opacity-50'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
  loading?: boolean
}

export function Button({ children, variant = 'primary', loading = false, disabled, ...props }: ButtonProps) {
  return (
    <button className={`${buttonBaseClasses} ${variantClasses[variant]}`} disabled={disabled || loading} {...props}>
      {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />}
      {loading ? 'Working…' : children}
    </button>
  )
}
