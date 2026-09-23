import { Button } from './Button'

type Props = {
  title: string
  body: string
  confirmLabel: string
  danger?: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmDialog({
  title,
  body,
  confirmLabel,
  danger,
  onCancel,
  onConfirm,
}: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-fg/35 p-5">
      <div className="card-shadow w-full max-w-sm rounded-2xl border border-line bg-card p-5">
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="mt-2 text-muted">{body}</p>
        <div className="mt-5 grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={onCancel}>
            取消
          </Button>
          <Button variant={danger ? 'danger' : 'lime'} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
