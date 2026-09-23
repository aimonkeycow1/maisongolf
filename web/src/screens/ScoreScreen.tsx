import { useState } from 'react'
import { Button } from '../components/Button'
import { CoachFields } from '../components/CoachFields'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { StrokePad } from '../components/StrokePad'
import { cn } from '../lib/cn'
import { RELATIVE_OUTCOMES, relativeChipCaption } from '../lib/outcomes'
import {
  adjustStrokes,
  completeRound,
  navigate,
  nextHole,
  prevHole,
  setFocusedPlayer,
  setRelativeScore,
  setStrokes,
} from '../storage/store'
import {
  displayCourseName,
  formatOptional,
  formatToPar,
  getHoleScore,
  getStrokes,
  holesRecorded,
  totalStrokes,
  totalToPar,
} from '../stats/round'
import type { AppState, Round } from '../types'

export function ScoreScreen({
  state,
  round,
}: {
  state: AppState
  round: Round
}) {
  const [padPlayerId, setPadPlayerId] = useState<string | null>(null)
  const [confirmEnd, setConfirmEnd] = useState(false)
  const holeIndex = round.currentHoleIndex
  const holeNo = holeIndex + 1
  const par = round.pars[holeIndex]!
  const padPlayer = round.players.find((p) => p.id === padPlayerId)

  return (
    <div className="flex min-h-dvh flex-col px-3 pb-8 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <header className="mb-2 flex items-center justify-between gap-2">
        <button
          type="button"
          className="text-accent"
          onClick={() => navigate('home')}
        >
          ← 首頁
        </button>
        <p className="truncate text-sm text-muted">
          {displayCourseName(round.courseName)}
        </p>
        <button
          type="button"
          className="text-accent"
          onClick={() => navigate('scorecard')}
        >
          計分卡
        </button>
      </header>

      <section className="card-shadow rounded-2xl border border-line bg-card px-4 py-5 text-center">
        <p className="text-sm tracking-[0.22em] text-muted">HOLE</p>
        <p className="tabular text-7xl font-semibold leading-none text-accent">
          {holeNo}
        </p>
        <p className="mt-2 text-lg text-fg">
          標準桿 <span className="tabular font-semibold">{par}</span>
          <span className="text-muted"> · {round.holeCount} 洞</span>
        </p>
        <p className="mt-3 text-sm leading-snug text-muted">
          抓鳥＝標準桿−1。點 − / + 加減，或點中間數字輸入。
        </p>
      </section>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <Button
          variant="secondary"
          onClick={prevHole}
          disabled={holeIndex === 0}
        >
          上一洞
        </Button>
        <Button
          variant="secondary"
          onClick={nextHole}
          disabled={holeIndex === round.holeCount - 1}
        >
          下一洞
        </Button>
      </div>

      <div className="mt-3 space-y-2">
        {round.players.map((player) => {
          const cell = getHoleScore(round, holeIndex, player.id)
          const strokes = cell.strokes
          const toPar = strokes == null ? null : strokes - par
          const isFocused = state.focusedPlayerId === player.id
          return (
            <article
              key={player.id}
              className={cn(
                'card-shadow rounded-2xl border bg-card p-3',
                isFocused ? 'border-accent' : 'border-line',
              )}
            >
              <div className="mb-2 flex items-center justify-between px-1">
                <button
                  type="button"
                  className="text-left text-lg font-semibold"
                  onClick={() => setFocusedPlayer(player.id)}
                >
                  {player.name}
                </button>
                <span className="text-sm text-muted">
                  總桿 {formatOptional(totalStrokes(round, player.id))} ·{' '}
                  {formatToPar(totalToPar(round, player.id))}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  aria-label="減一桿"
                  onClick={() => adjustStrokes(player.id, -1)}
                  className="flex min-h-[5.5rem] w-full flex-col items-center justify-center rounded-2xl border-2 border-fg bg-fg text-bg active:opacity-90"
                >
                  <span className="text-5xl font-bold leading-none">−</span>
                  <span className="mt-1 text-base font-semibold">減</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setFocusedPlayer(player.id)
                    setPadPlayerId(player.id)
                  }}
                  className="flex min-h-[5.5rem] w-full flex-col items-center justify-center rounded-2xl border border-line bg-card"
                >
                  <span
                    className={cn(
                      'tabular text-5xl font-bold leading-none',
                      toPar == null && 'text-muted',
                      toPar != null && toPar < 0 && 'text-under',
                      toPar != null && toPar > 0 && 'text-over',
                    )}
                  >
                    {strokes ?? '—'}
                  </span>
                  <span className="mt-1 text-xs text-muted">
                    點此：抓鳥／數字
                  </span>
                </button>
                <button
                  type="button"
                  aria-label="加一桿"
                  onClick={() => adjustStrokes(player.id, 1)}
                  className="flex min-h-[5.5rem] w-full flex-col items-center justify-center rounded-2xl bg-accent text-accent-ink active:brightness-95"
                >
                  <span className="text-5xl font-bold leading-none">+</span>
                  <span className="mt-1 text-base font-semibold">加</span>
                </button>
              </div>
              <div className="-mx-1 mt-2 flex gap-1 overflow-x-auto px-1 pb-0.5">
                {RELATIVE_OUTCOMES.map((outcome) => (
                  <button
                    key={outcome.id}
                    type="button"
                    onClick={() => {
                      setFocusedPlayer(player.id)
                      setRelativeScore(player.id, outcome.offset)
                    }}
                    className="flex min-h-11 shrink-0 flex-col items-center justify-center rounded-full border border-line bg-card px-3 text-sm active:bg-elevated"
                  >
                    <span className="font-medium">{outcome.zh}</span>
                    <span className="text-[10px] text-muted">
                      {relativeChipCaption(outcome, par)}
                    </span>
                  </button>
                ))}
              </div>
              <CoachFields playerId={player.id} par={par} cell={cell} />
            </article>
          )
        })}
      </div>

      <p className="mt-3 text-center text-sm text-muted">
        已記 {holesRecorded(round)} / {round.holeCount} 洞 · 分數已自動儲存
      </p>

      <Button
        variant="danger"
        className="mt-3 w-full"
        onClick={() => setConfirmEnd(true)}
      >
        結束本輪
      </Button>

      {padPlayer ? (
        <StrokePad
          playerName={padPlayer.name}
          holeNo={holeNo}
          par={par}
          value={getStrokes(round, holeIndex, padPlayer.id)}
          onCancel={() => setPadPlayerId(null)}
          onClear={() => {
            setStrokes(padPlayer.id, null)
            setPadPlayerId(null)
          }}
          onPick={(n) => {
            setStrokes(padPlayer.id, n)
            setPadPlayerId(null)
          }}
        />
      ) : null}

      {confirmEnd ? (
        <ConfirmDialog
          title="結束本輪？"
          body="結束後仍可打開計分卡查看，也可以再改分數。資料已儲存在本機。"
          confirmLabel="結束"
          onCancel={() => setConfirmEnd(false)}
          onConfirm={() => {
            setConfirmEnd(false)
            completeRound()
          }}
        />
      ) : null}
    </div>
  )
}
