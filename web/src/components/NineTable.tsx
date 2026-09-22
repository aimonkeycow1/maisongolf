import { cn } from '../lib/cn'
import { sumPars } from '../courses/memory'
import {
  formatOptional,
  getStrokes,
  totalStrokes,
} from '../stats/round'
import type { Round } from '../types'

export function NineTable({
  title,
  round,
  from,
  to,
}: {
  title: string
  round: Round
  from: number
  to: number
}) {
  const holes = Array.from({ length: to - from }, (_, i) => from + i)
  return (
    <section className="card-shadow mb-3 overflow-hidden rounded-2xl border border-line bg-card">
      <div className="flex items-center justify-between border-b border-line px-3 py-2">
        <h2 className="font-semibold">{title}</h2>
        <p className="text-sm text-muted">
          標準桿 {sumPars(round.pars, from, to)}
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full table-fixed border-collapse text-center text-xs">
          <colgroup>
            <col className="w-[3.4rem]" />
            {holes.map((h) => (
              <col key={h} />
            ))}
            <col className="w-8" />
          </colgroup>
          <thead>
            <tr className="bg-elevated">
              <th className="px-1 py-2 text-left font-medium">洞</th>
              {holes.map((h) => (
                <th key={h} className="tabular py-2 text-muted">
                  {h + 1}
                </th>
              ))}
              <th className="tabular py-2">計</th>
            </tr>
            <tr>
              <th className="px-1 py-2 text-left font-normal text-muted">
                標準桿
              </th>
              {holes.map((h) => (
                <td key={h} className="tabular py-2 text-muted">
                  {round.pars[h]}
                </td>
              ))}
              <td className="tabular py-2 text-muted">
                {sumPars(round.pars, from, to)}
              </td>
            </tr>
          </thead>
          <tbody>
            {round.players.map((player) => {
              const sub = totalStrokes(round, player.id, from, to)
              return (
                <tr key={player.id} className="border-t border-line">
                  <th className="truncate px-1 py-2 text-left text-[13px] font-medium">
                    {player.name}
                  </th>
                  {holes.map((h) => {
                    const strokes = getStrokes(round, h, player.id)
                    const diff =
                      strokes == null ? null : strokes - round.pars[h]!
                    return (
                      <td
                        key={h}
                        className={cn(
                          'tabular py-2 text-sm font-semibold',
                          diff != null && diff < 0 && 'text-under',
                          diff != null && diff > 0 && 'text-over',
                          strokes == null && 'text-muted',
                        )}
                      >
                        {strokes ?? '·'}
                      </td>
                    )
                  })}
                  <td className="tabular py-2 font-bold">
                    {formatOptional(sub)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
