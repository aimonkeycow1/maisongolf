import { useState } from 'react'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { NineTable } from '../components/NineTable'
import { WeakPointSection } from '../components/WeakPointSection'
import {
  buildCoachSummaryText,
  buildRoundExportJson,
  copyText,
  downloadText,
  shareText,
} from '../stats/coach'
import {
  coachStats,
  displayCourseName,
  formatOptional,
  formatRatio,
  formatToPar,
  totalStrokes,
  totalToPar,
} from '../stats/round'
import { navigate, reopenRound } from '../storage/store'
import type { Round } from '../types'

export function ScorecardScreen({ round }: { round: Round }) {
  const [confirmReopen, setConfirmReopen] = useState(false)
  const [copied, setCopied] = useState(false)
  const is18 = round.holeCount === 18
  const canShare =
    typeof navigator !== 'undefined' && typeof navigator.share === 'function'
  const primary = round.players[0]

  async function onCopy() {
    if (await copyText(buildCoachSummaryText(round))) {
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    }
  }

  async function onShare() {
    const text = buildCoachSummaryText(round)
    const ok = await shareText(
      `${displayCourseName(round.courseName)} 計分`,
      text,
    )
    if (!ok) await onCopy()
  }

  function onDownload() {
    downloadText(
      `球場計分-${displayCourseName(round.courseName).replace(/\s+/g, '-')}.json`,
      buildRoundExportJson(round),
    )
  }

  return (
    <div className="flex min-h-dvh flex-col px-3 pb-10 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <header className="mb-3 flex items-center justify-between">
        <button
          type="button"
          className="text-accent"
          onClick={() =>
            navigate(round.status === 'in_progress' ? 'score' : 'home')
          }
        >
          ← 返回
        </button>
        <h1 className="text-lg font-semibold">計分卡</h1>
        <span className="text-sm text-muted">
          {round.status === 'completed' ? '已結束' : '進行中'}
        </span>
      </header>
      <p className="mb-3 text-center text-muted">
        {displayCourseName(round.courseName)}
        {round.isDemo ? (
          <span className="ml-2 rounded-full bg-warn-bg px-2 py-0.5 text-xs text-warn">
            示範
          </span>
        ) : null}
      </p>

      <NineTable
        title="前九"
        round={round}
        from={0}
        to={Math.min(9, round.holeCount)}
      />
      {is18 ? <NineTable title="後九" round={round} from={9} to={18} /> : null}

      <section className="card-shadow rounded-2xl border border-line bg-elevated p-3">
        <h2 className="mb-2 font-semibold">總計</h2>
        <div className="space-y-2">
          {round.players.map((player) => (
            <div
              key={player.id}
              className="flex items-center justify-between rounded-2xl bg-card px-3 py-3"
            >
              <span className="font-medium">{player.name}</span>
              <span className="tabular text-lg">
                {formatOptional(totalStrokes(round, player.id))}
                <span className="ml-2 text-accent">
                  {formatToPar(totalToPar(round, player.id))}
                </span>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="card-shadow mt-3 rounded-2xl border border-line bg-card p-3">
        <h2 className="mb-2 font-semibold">教練數據</h2>
        <div className="space-y-2">
          {round.players.map((player) => {
            const stats = coachStats(round, player.id)
            return (
              <div
                key={player.id}
                className="rounded-2xl bg-elevated px-3 py-3 text-sm"
              >
                <p className="font-medium">{player.name}</p>
                <p className="mt-1 text-muted">
                  三推 {stats.threePutts} · 罰桿 {stats.penalties}
                </p>
                <p className="text-muted">
                  球道 {formatRatio(stats.fairwayHits, stats.fairwayAttempts)}{' '}
                  · GIR {formatRatio(stats.girHits, stats.girAttempts)}
                </p>
                {stats.putts == null ? null : (
                  <p className="text-muted">總推桿 {stats.putts}</p>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {primary ? (
        <WeakPointSection
          round={round}
          playerId={primary.id}
          playerName={primary.name}
        />
      ) : null}

      <div className="mt-4 grid gap-2">
        <Button
          variant={round.status === 'completed' ? 'lime' : 'secondary'}
          className="w-full"
          onClick={() => void onCopy()}
        >
          {copied ? '已複製教練摘要' : '複製教練摘要'}
        </Button>
        {canShare ? (
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => void onShare()}
          >
            分享給教練
          </Button>
        ) : null}
        <Button variant="outline" className="w-full" onClick={onDownload}>
          下載 JSON
        </Button>
        {round.status === 'in_progress' ? (
          <Button
            variant="lime"
            className="w-full"
            onClick={() => navigate('score')}
          >
            繼續記分
          </Button>
        ) : (
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => setConfirmReopen(true)}
          >
            繼續修改
          </Button>
        )}
        <Button
          variant="outline"
          className="w-full"
          onClick={() => navigate('home')}
        >
          回到首頁
        </Button>
      </div>

      {confirmReopen ? (
        <ConfirmDialog
          title="重新打開這輪？"
          body="可以改已經寫下的桿數，改完請再點結束本輪。"
          confirmLabel="去修改"
          onCancel={() => setConfirmReopen(false)}
          onConfirm={() => {
            setConfirmReopen(false)
            reopenRound()
          }}
        />
      ) : null}
    </div>
  )
}
