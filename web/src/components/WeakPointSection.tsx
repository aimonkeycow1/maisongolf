import { analyzeWeakPoints } from '../stats/weakPoints'
import type { Round } from '../types'

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-elevated px-3 py-3 text-center">
      <p className="tabular text-xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted">{label}</p>
    </div>
  )
}

export function WeakPointSection({
  round,
  playerId,
  playerName,
}: {
  round: Round
  playerId: string
  playerName: string
}) {
  const analysis = analyzeWeakPoints(round, playerId)
  const maxPutt = Math.max(
    1,
    ...analysis.puttBars.map((b) => b.putts ?? 0),
  )

  return (
    <section className="card-shadow mt-3 rounded-2xl border border-line bg-card p-3">
      <h2 className="mb-1 font-semibold">弱項分析 · {playerName}</h2>
      <p className="mb-3 text-sm text-muted">
        單局洞級回顧：推桿、GIR、柏忌洞一目了然
      </p>
      <div className="grid grid-cols-2 gap-2">
        <Tile
          label="總推桿"
          value={
            analysis.totalPutts == null ? '—' : String(analysis.totalPutts)
          }
        />
        <Tile
          label="GIR 上果嶺率"
          value={analysis.girPct == null ? '—' : `${analysis.girPct}%`}
        />
        <Tile
          label="球道命中"
          value={
            analysis.fairwayPct == null ? '—' : `${analysis.fairwayPct}%`
          }
        />
        <Tile label="柏忌及以上洞" value={String(analysis.bogeyPlusHoles)} />
      </div>

      <p className="mt-4 mb-2 text-sm font-medium text-muted">各洞推桿數</p>
      <div className="space-y-1.5">
        {analysis.puttBars.map((bar) => {
          const widthPct =
            bar.putts == null
              ? 0
              : Math.max(8, Math.round((bar.putts / maxPutt) * 100))
          return (
            <div
              key={bar.hole}
              className="grid grid-cols-[1.5rem_1fr_1.75rem] items-center gap-2"
            >
              <span className="tabular text-xs text-muted">{bar.hole}</span>
              <div className="h-5 overflow-hidden rounded-md bg-elevated">
                {bar.putts == null ? (
                  <div className="h-full w-2 bg-line/60" />
                ) : (
                  <div
                    className={
                      bar.putts >= 3
                        ? 'flex h-full items-center justify-end rounded-md bg-over px-1.5 text-[10px] font-semibold text-white'
                        : 'flex h-full items-center justify-end rounded-md bg-accent px-1.5 text-[10px] font-semibold text-accent-ink'
                    }
                    style={{ width: `${widthPct}%` }}
                  >
                    {bar.putts}
                  </div>
                )}
              </div>
              <span className="tabular text-right text-sm font-medium">
                {bar.strokes ?? '—'}
              </span>
            </div>
          )
        })}
      </div>

      {analysis.tips.length > 0 ? (
        <>
          <p className="mt-4 mb-2 text-sm font-medium text-muted">弱項提示</p>
          <ul className="space-y-2">
            {analysis.tips.map((tip) => (
              <li
                key={tip}
                className="rounded-xl bg-warn-bg px-3 py-2 text-sm leading-snug text-warn"
              >
                {tip}
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="mt-4 text-sm text-muted">
          尚未有足夠教練數據可分析。記推桿／GIR／球道後會出現提示。
        </p>
      )}
    </section>
  )
}
