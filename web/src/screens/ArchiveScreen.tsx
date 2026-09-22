import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { useAppState } from '../storage/hooks'
import {
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
  formatOptional,
  totalStrokes,
} from '../stats/round'

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
        已結束的球局、對目標比較，以及完整封存匯出／匯入。資料存於本機
        localStorage（鍵{' '}
        <code className="text-xs">golf-scorekeeper-v1</code>
        ）；清快取或換機會遺失，請先匯出封存再搬移。
      </p>

      <section className="card-shadow mt-5 rounded-2xl border border-line bg-card p-4">
        <p className="text-sm font-medium text-muted">目標總桿（預設 95）</p>
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
          列表會以第一位球員總桿對照此目標。
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

      <section className="mt-6">
        <h2 className="mb-3 text-sm font-semibold tracking-wide text-muted">
          已結束（{completed.length}）
        </h2>
        {completed.length === 0 ? (
          <p className="text-sm text-muted">尚無已結束球局。</p>
        ) : (
          <div className="space-y-3">
            {completed.map((round) => {
              const primary = round.players[0]
              const total = primary
                ? totalStrokes(round, primary.id)
                : null
              const vs =
                total == null ? null : total - state.scoreGoal
              const when = formatDate(
                round.finishedAt ?? round.updatedAt,
              )
              return (
                <article
                  key={round.id}
                  className="card-shadow rounded-2xl border border-line bg-card p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-lg font-semibold">
                        {displayCourseName(round.courseName)}
                        {round.isDemo ? (
                          <span className="ml-2 rounded-full bg-warn-bg px-2 py-0.5 text-xs font-normal text-warn">
                            示範
                          </span>
                        ) : null}
                      </h3>
                      <p className="mt-1 text-sm text-muted">
                        {when} · {round.holeCount}洞
                        {primary ? ` · ${primary.name}` : ''}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="tabular text-2xl font-semibold">
                        {formatOptional(total)}
                      </p>
                      <p
                        className={
                          vs == null
                            ? 'text-sm text-muted'
                            : vs === 0
                              ? 'text-sm font-medium text-under'
                              : vs < 0
                                ? 'text-sm font-medium text-under'
                                : 'text-sm font-medium text-over'
                        }
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
                  </div>
                  <p className="mt-2 truncate text-sm text-fg/80">
                    {round.players.map((p) => p.name).join(' · ')}
                  </p>
                  <div className="mt-3 grid grid-cols-[1fr_auto] gap-2">
                    <Button
                      variant="lime"
                      onClick={() => openRound(round.id, 'scorecard')}
                    >
                      查看計分卡
                    </Button>
                    <Button
                      variant="ghost"
                      className="px-3 text-muted"
                      onClick={() => setPendingDelete(round.id)}
                    >
                      刪除
                    </Button>
                  </div>
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
