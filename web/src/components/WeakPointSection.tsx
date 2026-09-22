import { analyzeWeakPoints } from '../stats/weakPoints'
import type { Round } from '../types'

function Tile({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-2xl bg-elevated px-3 py-3 text-center">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 tabular text-xl font-semibold">{value}</p>
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
      <p className="mb-3 text-sm text-muted">依推桿、GIR、球道與柏忌洞推導</p>
      <div className="grid grid-cols-2 gap-2">
        <Tile
          label="總推桿"
          value={
            analysis.totalPutts == null ? '—' : String(analysis.totalPutts)
          }
        />
        <Tile
          label="GIR%"
          value={analysis.girPct == null ? '—' : `${analysis.girPct}%`}
        />
        <Tile
          label="球道%"
          value={
            analysis.fairwayPct == null ? '—' : `${analysis.fairwayPct}%`
          }
        />
        <Tile label="柏忌+洞" value={String(analysis.bogeyPlusHoles)} />
      </div>

      <p className="mt-4 mb-2 text-sm font-medium text-muted">各洞推桿</p>
      <div className="flex items-end gap-1 overflow-x-auto pb-1">
        {analysis.puttBars.map((bar) => {
          const h =
            bar.putts == null
              ? 4
              : Math.max(8, Math.round((bar.putts / maxPutt) * 48))
          return (
            <div
              key={bar.hole}
              className="flex w-5 shrink-0 flex-col items-center gap-1"
            >
              <div
                className={
                  bar.putts == null
                    ? 'w-full rounded-t bg-line/50'
                    : bar.putts >= 3
                      ? 'w-full rounded-t bg-over'
                      : 'w-full rounded-t bg-accent'
                }
                style={{ height: h }}
                title={
                  bar.putts == null
                    ? `第${bar.hole}洞未記`
                    : `第${bar.hole}洞 ${bar.putts}推`
                }
              />
              <span className="text-[10px] text-muted">{bar.hole}</span>
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
