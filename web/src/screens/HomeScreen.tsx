import { useState } from 'react'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import {
  deleteRound,
  navigate,
  openRound,
} from '../storage/store'
import {
  displayCourseName,
  formatRoundWhen,
  holesRecorded,
} from '../stats/round'
import type { Round } from '../types'

function RoundCard({
  round,
  action,
  onOpen,
  onDelete,
}: {
  round: Round
  action: string
  onOpen: () => void
  onDelete: () => void
}) {
  const recorded = holesRecorded(round)
  return (
    <article className="card-shadow rounded-2xl border border-line bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">
            {displayCourseName(round.courseName)}
          </h3>
          <p className="mt-1 text-sm text-muted">
            {round.players.length}人 · {round.holeCount}洞 · 已記 {recorded}/
            {round.holeCount} 洞
          </p>
          <p className="text-sm text-muted">{formatRoundWhen(round.updatedAt)}</p>
        </div>
        {round.status === 'in_progress' ? (
          <span className="rounded-full bg-accent/15 px-2 py-1 text-xs text-accent">
            進行中
          </span>
        ) : (
          <span className="rounded-full bg-elevated px-2 py-1 text-xs text-muted">
            已結束
          </span>
        )}
      </div>
      <p className="mt-2 truncate text-sm text-fg/80">
        {round.players.map((p) => p.name).join(' · ')}
      </p>
      <div className="mt-4 grid grid-cols-[1fr_auto] gap-2">
        <Button variant="lime" onClick={onOpen}>
          {action}
        </Button>
        <Button
          variant="ghost"
          className="px-3 text-muted"
          onClick={onDelete}
          aria-label="刪除"
        >
          刪除
        </Button>
      </div>
    </article>
  )
}

export function HomeScreen({ rounds }: { rounds: Round[] }) {
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const inProgress = rounds.filter((r) => r.status === 'in_progress')
  const completed = rounds.filter((r) => r.status === 'completed')

  return (
    <div className="flex min-h-dvh flex-col px-4 pb-8 pt-[max(1rem,env(safe-area-inset-top))]">
      <header className="mb-6">
        <p className="text-sm tracking-[0.18em] text-muted">下場記桿</p>
        <h1 className="mt-1 text-4xl font-semibold leading-tight tracking-tight">
          球場計分
        </h1>
        <p className="mt-2 leading-relaxed text-muted">
          不用鉛筆。桿數記在這支手機上，重新整理也不會丟。
        </p>
      </header>

      <Button
        variant="lime"
        size="xl"
        className="w-full"
        onClick={() => navigate('new')}
      >
        開始新一輪
      </Button>

      <Button
        variant="outline"
        className="mt-3 w-full"
        onClick={() => navigate('archive')}
      >
        成績庫
      </Button>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold tracking-wide text-muted">
          進行中
        </h2>
        {inProgress.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line bg-card px-4 py-8 text-center text-muted">
            還沒有進行中的球局。開一場 9 或 18 洞即可開記。
          </div>
        ) : (
          <div className="space-y-3">
            {inProgress.map((round) => (
              <RoundCard
                key={round.id}
                round={round}
                action="繼續記分"
                onOpen={() => openRound(round.id, 'score')}
                onDelete={() => setPendingDelete(round.id)}
              />
            ))}
          </div>
        )}
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold tracking-wide text-muted">
          已結束
        </h2>
        {completed.length === 0 ? (
          <p className="text-sm text-muted">結束後的計分卡會出現在這裡。</p>
        ) : (
          <div className="space-y-3">
            {completed.slice(0, 5).map((round) => (
              <RoundCard
                key={round.id}
                round={round}
                action="查看計分卡"
                onOpen={() => openRound(round.id, 'scorecard')}
                onDelete={() => setPendingDelete(round.id)}
              />
            ))}
            {completed.length > 5 ? (
              <Button
                variant="secondary"
                className="w-full"
                onClick={() => navigate('archive')}
              >
                查看全部成績庫（{completed.length}）
              </Button>
            ) : null}
          </div>
        )}
      </section>

      {pendingDelete ? (
        <ConfirmDialog
          title="刪除這輪紀錄？"
          body="刪除後無法恢復。若只是想先離開，直接返回即可，分數已自動儲存。"
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
