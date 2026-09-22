import { cn } from '../lib/cn'
import { isThreePutt } from '../stats/round'
import {
  adjustPenalties,
  adjustPutts,
  setPenalties,
  setPutts,
  toggleFairway,
  toggleGir,
} from '../storage/store'
import type { Fairway, HoleScore } from '../types'

function Stepper({
  label,
  value,
  emptyAsZero,
  warn,
  warnLabel,
  missing,
  onMinus,
  onPlus,
  chips,
  onChip,
}: {
  label: string
  value: number | null
  emptyAsZero?: boolean
  warn?: boolean
  warnLabel?: string
  missing?: boolean
  onMinus: () => void
  onPlus: () => void
  chips: number[]
  onChip: (n: number) => void
}) {
  const display = value == null && emptyAsZero ? 0 : value
  return (
    <div className="rounded-2xl border border-line bg-elevated/60 p-2">
      <div className="mb-1 flex items-center justify-between px-1">
        <span className="text-sm font-medium">{label}</span>
        {warn ? (
          <span className="text-xs font-semibold text-over">{warnLabel}</span>
        ) : null}
        {missing ? <span className="text-xs text-warn">請記</span> : null}
      </div>
      <div className="grid grid-cols-3 gap-1">
        <button
          type="button"
          aria-label={`${label}減`}
          onClick={onMinus}
          className="flex min-h-12 items-center justify-center rounded-xl border border-line bg-card text-2xl font-bold active:bg-elevated"
        >
          −
        </button>
        <div
          className={cn(
            'flex min-h-12 items-center justify-center rounded-xl bg-card text-2xl font-bold tabular',
            warn && 'text-over',
            display == null && 'text-muted',
          )}
        >
          {display ?? '—'}
        </div>
        <button
          type="button"
          aria-label={`${label}加`}
          onClick={onPlus}
          className="flex min-h-12 items-center justify-center rounded-xl bg-accent text-xl font-bold text-accent-ink active:brightness-95"
        >
          +
        </button>
      </div>
      <div className="mt-1 grid grid-cols-3 gap-1">
        {chips.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChip(n)}
            className={cn(
              'min-h-9 rounded-lg text-sm font-medium',
              value === n
                ? n >= 3
                  ? 'bg-over text-bg'
                  : 'bg-accent text-accent-ink'
                : n >= 3
                  ? 'bg-danger text-danger-ink'
                  : 'bg-card text-fg',
            )}
          >
            {n}
            {n >= 3 && label === '推桿' ? '推' : ''}
          </button>
        ))}
      </div>
    </div>
  )
}

function TogglePair({
  label,
  left,
  right,
  value,
  onPick,
}: {
  label: string
  left: { id: string; text: string }
  right: { id: string; text: string }
  value: string | null
  onPick: (id: string) => void
}) {
  return (
    <div className="rounded-2xl border border-line bg-elevated/60 p-2">
      <p className="mb-1 px-1 text-sm font-medium">{label}</p>
      <div className="grid grid-cols-2 gap-1">
        <ToggleBtn
          active={value === left.id}
          onClick={() => onPick(left.id)}
        >
          {left.text}
        </ToggleBtn>
        <ToggleBtn
          active={value === right.id}
          tone="miss"
          onClick={() => onPick(right.id)}
        >
          {right.text}
        </ToggleBtn>
      </div>
    </div>
  )
}

function ToggleBtn({
  active,
  tone = 'hit',
  onClick,
  children,
}: {
  active: boolean
  tone?: 'hit' | 'miss'
  onClick: () => void
  children: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'min-h-12 rounded-xl text-base font-semibold active:opacity-90',
        active && tone === 'hit' && 'bg-accent text-accent-ink',
        active && tone === 'miss' && 'bg-fg text-bg',
        !active && 'border border-line bg-card text-fg',
      )}
    >
      {children}
    </button>
  )
}

export function CoachFields({
  playerId,
  par,
  cell,
}: {
  playerId: string
  par: number
  cell: HoleScore
}) {
  const three = isThreePutt(cell.putts)
  const showFairway = par !== 3
  return (
    <div className="mt-3 space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <Stepper
          label="推桿"
          value={cell.putts}
          warn={three}
          warnLabel="三推"
          onMinus={() => adjustPutts(playerId, -1)}
          onPlus={() => adjustPutts(playerId, 1)}
          chips={[1, 2, 3]}
          onChip={(n) => setPutts(playerId, n)}
          missing={cell.strokes != null && cell.putts == null}
        />
        <Stepper
          label="罰桿"
          value={cell.penalties}
          emptyAsZero
          onMinus={() => adjustPenalties(playerId, -1)}
          onPlus={() => adjustPenalties(playerId, 1)}
          chips={[0, 1, 2]}
          onChip={(n) => setPenalties(playerId, n)}
        />
      </div>
      <div
        className={cn('grid gap-2', showFairway ? 'grid-cols-2' : 'grid-cols-1')}
      >
        {showFairway ? (
          <TogglePair
            label="球道"
            left={{ id: 'hit', text: '中' }}
            right={{ id: 'miss', text: '偏' }}
            value={cell.fairway}
            onPick={(id) => toggleFairway(playerId, id as Fairway)}
          />
        ) : null}
        <TogglePair
          label="GIR"
          left={{ id: 'yes', text: '上了' }}
          right={{ id: 'no', text: '沒上' }}
          value={cell.gir === true ? 'yes' : cell.gir === false ? 'no' : null}
          onPick={(id) => toggleGir(playerId, id === 'yes')}
        />
      </div>
    </div>
  )
}
