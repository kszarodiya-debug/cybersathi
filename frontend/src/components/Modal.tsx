import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
}

export function Modal({ open, title, children, onClose }: ModalProps) {
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose, open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink/60 p-5 backdrop-blur-sm" role="presentation" onMouseDown={onClose}>
      <div className="w-full max-w-lg rounded-3xl bg-white p-7 shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-5">
          <h2 className="text-2xl font-bold tracking-tight text-ink" id="modal-title">{title}</h2>
          <button className="grid h-9 w-9 place-items-center rounded-full text-xl text-ink/50 hover:bg-ink/5 hover:text-ink" type="button" aria-label="Close dialog" onClick={onClose}>×</button>
        </div>
        <div className="mt-5 text-sm leading-7 text-ink/65">{children}</div>
      </div>
    </div>
  )
}
