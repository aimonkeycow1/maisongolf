import type { Round } from '../types'
import {
  coachStats,
  displayCourseName,
  fairwayLabel,
  formatOptional,
  formatRatio,
  formatToPar,
  getHoleScore,
  girLabel,
  totalStrokes,
  totalToPar,
} from './round'

export function buildCoachSummaryText(round: Round): string {
  const lines: string[] = []
  lines.push(
    `球場計分 · ${displayCourseName(round.courseName)} · ${round.holeCount}洞`,
  )
  lines.push('')
  for (const player of round.players) {
    const gross = totalStrokes(round, player.id)
    const toPar = totalToPar(round, player.id)
    const stats = coachStats(round, player.id)
    lines.push(
      `${player.name}  總桿 ${formatOptional(gross)}（${formatToPar(toPar)}）`,
    )
    lines.push(
      `推桿 ${stats.putts ?? '—'} · 三推 ${stats.threePutts} · 罰桿 ${stats.penalties}`,
    )
    lines.push(
      `球道 ${formatRatio(stats.fairwayHits, stats.fairwayAttempts)} · GIR ${formatRatio(stats.girHits, stats.girAttempts)}`,
    )
    lines.push('洞  標準  桿  推  罰  球道  GIR')
    for (let i = 0; i < round.holeCount; i += 1) {
      const cell = getHoleScore(round, i, player.id)
      const par = round.pars[i] ?? 4
      const strokes =
        cell.strokes == null ? '—' : String(cell.strokes)
      const putts = cell.putts == null ? '—' : String(cell.putts)
      lines.push(
        `${String(i + 1).padStart(2, ' ')}   ${par}    ${strokes.padStart(2, ' ')}  ${putts.padStart(2, ' ')}  ${String(cell.penalties).padStart(2, ' ')}   ${fairwayLabel(cell.fairway, par)}    ${girLabel(cell.gir)}`,
      )
    }
    lines.push('')
  }
  return `${lines.join('\n').trim()}\n`
}

export function buildRoundExportJson(round: Round): string {
  const payload = {
    courseName: displayCourseName(round.courseName),
    holeCount: round.holeCount,
    pars: round.pars.slice(0, round.holeCount),
    status: round.status,
    finishedAt: round.finishedAt ?? null,
    isDemo: round.isDemo ?? false,
    players: round.players.map((player) => {
      const stats = coachStats(round, player.id)
      return {
        name: player.name,
        gross: totalStrokes(round, player.id),
        toPar: totalToPar(round, player.id),
        putts: stats.putts,
        threePutts: stats.threePutts,
        penalties: stats.penalties,
        fairway: { hits: stats.fairwayHits, attempts: stats.fairwayAttempts },
        gir: { hits: stats.girHits, attempts: stats.girAttempts },
        holes: Array.from({ length: round.holeCount }, (_, i) => {
          const cell = getHoleScore(round, i, player.id)
          return {
            hole: i + 1,
            par: round.pars[i],
            strokes: cell.strokes,
            putts: cell.putts,
            penalties: cell.penalties,
            fairway: round.pars[i] === 3 ? 'na' : cell.fairway,
            gir: cell.gir,
          }
        }),
      }
    }),
  }
  return JSON.stringify(payload, null, 2)
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

export async function shareText(
  title: string,
  text: string,
): Promise<boolean> {
  try {
    if (!navigator.share) return false
    await navigator.share({ title, text })
    return true
  } catch {
    return false
  }
}

export function downloadText(
  filename: string,
  content: string,
  mime = 'application/json',
): void {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
