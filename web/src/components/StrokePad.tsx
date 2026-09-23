import { Button } from './Button'
import { RELATIVE_OUTCOMES, relativeChipCaption } from '../lib/outcomes'

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '清除', '10', '確定']

type Props = {
  playerName: string
  holeNo: number
  par: number
  value: number | null
  onCancel: () => void
  onClear: () => void
  onPick: (strokes: number) => void
}

export function StrokePad({
  playerName,
  holeNo,
  par,
  value,
  onCancel,
  onClear,
  onPick,
}: Props) {
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-fg/35 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <div className="card-shadow w-full max-w-md rounded-2xl border border-line bg-card p-4">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <p className="text-sm text-muted">
              第{holeNo}洞 · 標準桿 {par}
            </p>
            <h2 className="text-xl font-semibold">{playerName}</h2>
          </div>
          <p className="tabular text-3xl font-bold text-accent">{value ?? '—'}</p>
        </div>
        <p className="mb-2 text-sm text-muted">相對標準桿（點一下即記入）</p>
        <div className="mb-3 grid grid-cols-3 gap-2">
          {RELATIVE_OUTCOMES.map((outcome) => (
            <button
              key={outcome.id}
              type="button"
              onClick={() =>
                onPick(Math.max(1, Math.min(15, par + outcome.offset)))
              }
              className="flex min-h-16 flex-col items-center justify-center rounded-2xl border border-line bg-elevated px-1 py-2 active:bg-line"
            >
              <span className="text-base font-semibold leading-tight">
                {outcome.zh}
                {'zhAlt' in outcome && outcome.zhAlt
                  ? `／${outcome.zhAlt}`
                  : ''}
              </span>
              <span className="mt-0.5 text-xs text-muted">
                {relativeChipCaption(outcome, par)}
              </span>
            </button>
          ))}
        </div>
        <p className="mb-2 text-sm text-muted">或直接輸入桿數</p>
        <div className="grid grid-cols-3 gap-2">
          {KEYS.map((key) => {
            if (key === '清除') {
              return (
                <Button
                  key={key}
                  variant="danger"
                  className="h-16 text-lg"
                  onClick={onClear}
                >
                  清除
                </Button>
              )
            }
            if (key === '確定') {
              return (
                <Button
                  key={key}
                  variant="secondary"
                  className="h-16 text-lg"
                  onClick={onCancel}
                >
                  關閉
                </Button>
              )
            }
            const n = Number(key)
            return (
              <Button
                key={key}
                variant="lime"
                className="h-16 text-2xl tabular"
                onClick={() => onPick(n)}
              >
                {key}
              </Button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
