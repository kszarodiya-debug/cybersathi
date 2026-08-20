export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm font-semibold text-ink/60" role="status" aria-live="polite">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-teal border-t-transparent" aria-hidden="true" />
      {label}
    </div>
  )
}
