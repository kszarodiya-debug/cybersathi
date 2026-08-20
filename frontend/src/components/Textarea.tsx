import type { TextareaHTMLAttributes } from 'react'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
  hint?: string
}

export function Textarea({ label, error, hint, id, className = '', ...props }: TextareaProps) {
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  return (
    <div className="grid gap-2">
      <label className="text-sm font-bold text-ink" htmlFor={id}>{label}</label>
      <textarea
        className={`min-h-36 resize-y rounded-2xl border bg-white px-4 py-3 text-sm leading-6 text-ink outline-none transition placeholder:text-ink/35 focus:border-teal focus:ring-4 focus:ring-teal/10 ${error ? 'border-red-400' : 'border-ink/15'} ${className}`}
        id={id}
        aria-describedby={describedBy}
        aria-invalid={Boolean(error)}
        {...props}
      />
      {hint && <p className="text-xs leading-5 text-ink/50" id={`${id}-hint`}>{hint}</p>}
      {error && <p className="text-xs font-semibold text-red-700" id={`${id}-error`}>{error}</p>}
    </div>
  )
}
