import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { useAppState } from '../storage/hooks'
import {
  DEFAULT_SCORE_GOAL,
  IDB_DB_NAME,
  STORAGE_KEY,
  buildArchivePayload,
  deleteRound,
  ensureDemoArchive,
  importArchivePayload,
  navigate,
  openRound,
  setScoreGoal,
} from '../storage/store'
import { downloadText } from '../stats/coach'
import {
  displayCourseName,
  formatDate,
  formatMonthDay,
  formatOptional,
  totalStrokes,
} from '../stats/round'
import { cn } from '../lib/cn'

export function ArchiveScreen() {
  const state = useAppState()
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [flash, setFlash] = useState('')
  const [goalDraft, setGoalDraft] = useState(String(state.scoreGoal))
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    ensureDemoArchive()
  }, [])

  useEffect(() => {
    setGoalDraft(String(state.scoreGoal))
  }, [state.scoreGoal])

  const completed = useMemo(
    () =>
      state.rounds
        .filter((r) => r.status === 'completed')
        .sort(
          (a, b) =>
            (b.finishedAt ?? b.updatedAt) - (a.finishedAt ?? a.updatedAt),
        ),
    [state.rounds],
  )

  const recentVsGoal = useMemo(() => {
    const totals = completed
      .slice(0, 6)
      .map((r) => {
        const primary = r.players[0]
        return primary ? totalStrokes(r, primary.id) : null
      })
      .filter((n): n is number => n != null)
    if (totals.length === 0) return null
    const mean = totals.reduce((a, b) => a + b, 0) / totals.length
    return { count: totals.length, mean }
  }, [completed])

  const hasDemo = completed.some((r) => r.isDemo)

  function exportArchive() {
    const payload = buildArchivePayload()
    downloadText(
      `球場計分-成績庫-${formatDate(Date.now())}.json`,
      JSON.stringify(payload, null, 2),
    )
    setFlash('已匯出完整成績庫')
    window.setTimeout(() => setFlash(''), 2000)
  }

  function onPickFile(file: File | undefined) {
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result))
        const result = importArchivePayload(parsed)
        if (!result.ok) {
          setFlash(result.message)
          return
        }
        setFlash('已匯入成績庫')
        window.setTimeout(() => setFlash(''), 2000)
      } catch {
        setFlash('無法讀取 JSON')
      }
    }
    reader.readAsText(file)
  }

  function applyGoal() {
    const n = Number(goalDraft)
    if (!Number.isFinite(n)) {
      setFlash('目標分數需為數字')
      return
    }
    setScoreGoal(n)
    setFlash(`目標已設為 ${Math.round(n)}`)
    window.setTimeout(() => setFlash(''), 2000)
  }

  return (
    <div className="flex min-h-dvh flex-col px-4 pb-10 pt-[max(1rem,env(safe-area-inset-top))]">
      <button
        type="button"
        className="self-start text-accent"
        onClick={() => navigate('home')}
      >
        ← 返回
      </button>
      <h1 className="mt-3 text-3xl font-bold">成績庫</h1>
      <p className="mt-1 text-muted">
        跨局歷史一覽：對照「目標 {state.scoreGoal}」看進步，而非只留下一張散落的計分卡。
      </p>
      <p className="mt-2 text-xs leading-relaxed text-muted">
        主存放：IndexedDB（{IDB_DB_NAME}）；並鏡像 localStorage（{STORAGE_KEY}
        ）。清站台資料仍會丟——換機請先匯出封存。雲端同步為後續選項，本版不做。
      </p>

      {hasDemo ? (
        <div className="mt-4 rounded-2xl border border-warn/40 bg-warn-bg px-3 py-2 text-sm text-warn">
          示範數據 · 非真實成績（空庫時自動種子，可刪除）
        </div>
      ) : null}

      <section className="card-shadow mt-4 rounded-2xl border border-line bg-card p-4">
        <p className="text-sm font-medium text-muted">
          目標總桿（預設 {DEFAULT_SCORE_GOAL}）
        </p>
        <div className="mt-2 flex gap-2">
          <input
            type="number"
            inputMode="numeric"
            value={goalDraft}
            onChange={(e) => setGoalDraft(e.target.value)}
            className="min-h-12 w-24 rounded-2xl border border-line bg-elevated px-3 text-lg tabular outline-none focus:border-accent"
          />
          <Button variant="secondary" onClick={applyGoal}>
            儲存
          </Button>
        </div>
        <p className="mt-2 text-sm text-muted">
          列表以第一位球員總桿對照此目標（對齊「先穩在 95 內」）。
        </p>
        {recentVsGoal ? (
          <div className="mt-4 border-t border-line pt-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">
                近 {recentVsGoal.count} 局相對目標 {state.scoreGoal}
              </span>
              <span className="tabular font-medium">
                均值 {recentVsGoal.mean.toFixed(1)}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-elevated">
              <div
                className="h-full rounded-full bg-accent"
                style={{
                  width: `${Math.max(
                    8,
                    Math.min(
                      100,
                      (state.scoreGoal / Math.max(recentVsGoal.mean, 1)) * 100,
                    ),
                  )}%`,
                }}
              />
            </div>
          </div>
        ) : null}
      </section>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <Button variant="lime" onClick={exportArchive}>
          匯出封存
        </Button>
        <Button variant="outline" onClick={() => fileRef.current?.click()}>
          匯入封存
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => {
            onPickFile(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>
      {flash ? (
        <p className="mt-3 rounded-2xl bg-elevated px-3 py-2 text-sm text-accent">
          {flash}
        </p>
      ) : null}

      <section className="card-shadow mt-6 overflow-hidden rounded-2xl border border-line bg-card">
        <h2 className="border-b border-line px-4 py-3 text-sm font-semibold tracking-wide text-muted">
          已結束（{completed.length}）
        </h2>
        {completed.length === 0 ? (
          <p className="px-4 py-6 text-sm text-muted">尚無已結束球局。</p>
        ) : (
          <div>
            {completed.map((round) => {
              const primary = round.players[0]
              const total = primary
                ? totalStrokes(round, primary.id)
                : null
              const vs = total == null ? null : total - state.scoreGoal
              const { mon, day } = formatMonthDay(
                round.finishedAt ?? round.updatedAt,
              )
              return (
                <article
                  key={round.id}
                  className="flex items-center gap-3 border-b border-line px-3 py-3 last:border-b-0"
                >
                  <button
                    type="button"
                    className="flex min-w-0 flex-1 items-center gap-3 text-left"
                    onClick={() => openRound(round.id, 'scorecard')}
                  >
                    <div className="flex w-12 shrink-0 flex-col items-center rounded-xl bg-elevated py-1.5">
                      <span className="text-[10px] text-muted">{mon}</span>
                      <span className="tabular text-lg font-semibold leading-none">
                        {day}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold">
                        {displayCourseName(round.courseName)}
                      </p>
                      <p className="mt-0.5 truncate text-sm text-muted">
                        {round.holeCount} 洞
                        {round.isDemo ? ' · 示範' : ''}
                        {primary ? ` · ${primary.name}` : ''}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="tabular text-2xl font-semibold leading-none">
                        {formatOptional(total)}
                      </p>
                      <p
                        className={cn(
                          'mt-1 text-sm font-medium',
                          vs == null && 'text-muted',
                          vs === 0 && 'text-under',
                          vs != null && vs < 0 && 'text-under',
                          vs != null && vs > 0 && 'text-over',
                        )}
                      >
                        {vs == null
                          ? '—'
                          : vs === 0
                            ? '達標'
                            : vs < 0
                              ? `−${-vs}`
                              : `+${vs}`}
                      </p>
                    </div>
                  </button>
                  <Button
                    variant="ghost"
                    className="shrink-0 px-2 text-muted"
                    onClick={() => setPendingDelete(round.id)}
                    aria-label="刪除"
                  >
                    刪除
                  </Button>
                </article>
              )
            })}
          </div>
        )}
      </section>

      {pendingDelete ? (
        <ConfirmDialog
          title="刪除這輪紀錄？"
          body="刪除後無法恢復。完整封存可先匯出備份。"
          confirmLabel="刪除"
          danger
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => {
            deleteRound(pendingDelete)
            setPendingDelete(null)
          }}
        />
      ) : null}
    </div>
  )
}
