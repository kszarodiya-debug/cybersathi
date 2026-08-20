import type { ReactNode } from 'react'

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-ink/15 bg-mist/60 px-5 py-6 text-center">
      <p className="text-sm font-black text-ink">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink/55">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
