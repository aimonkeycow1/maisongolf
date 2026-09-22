import type { Round } from '../types'
import {
  bogeyPlusCount,
  coachStats,
  getHoleScore,
  getToPar,
} from './round'

export type WeakPointAnalysis = {
  totalPutts: number | null
  girPct: number | null
  fairwayPct: number | null
  bogeyPlusHoles: number
  puttBars: Array<{ hole: number; putts: number | null; strokes: number | null }>
  tips: string[]
}

function pct(hits: number, attempts: number): number | null {
  if (attempts === 0) return null
  return Math.round((hits / attempts) * 100)
}

/** Derive up to 3 coaching tips from recorded coach fields. */
export function analyzeWeakPoints(
  round: Round,
  playerId: string,
): WeakPointAnalysis {
  const stats = coachStats(round, playerId)
  const tips: string[] = []

  const girPct = pct(stats.girHits, stats.girAttempts)
  const fairwayPct = pct(stats.fairwayHits, stats.fairwayAttempts)
  const bogeyPlusHoles = bogeyPlusCount(round, playerId)

  const puttBars = Array.from({ length: round.holeCount }, (_, i) => {
    const cell = getHoleScore(round, i, playerId)
    return {
      hole: i + 1,
      putts: cell.strokes == null ? null : cell.putts,
      strokes: cell.strokes,
    }
  })

  if (stats.threePutts >= 3) {
    tips.push(
      `三推 ${stats.threePutts} 洞偏多——優先練短推（1.5 公尺內）與 lag 控距。`,
    )
  } else if (stats.putts != null && stats.holesPlayed > 0) {
    const avg = stats.putts / stats.holesPlayed
    if (avg >= 2.2) {
      tips.push(
        `平均每洞 ${avg.toFixed(1)} 推偏高——下场前練 lag putt，減少三推。`,
      )
    }
  }

  if (girPct != null && girPct < 40 && stats.girAttempts >= 6) {
    tips.push(
      `GIR ${girPct}% 偏低——接近果嶺時保守進攻，先保上果嶺再搏鳥。`,
    )
  }

  if (fairwayPct != null && fairwayPct < 50 && stats.fairwayAttempts >= 6) {
    tips.push(
      `球道命中 ${fairwayPct}%——開球可改用較穩球桿，先求落點再求距離。`,
    )
  }

  if (stats.penalties >= 3) {
    tips.push(
      `罰桿 ${stats.penalties}——避開麻煩區，大數字洞以柏忌封頂即可。`,
    )
  }

  if (tips.length < 3) {
    let worstHole: { hole: number; toPar: number } | null = null
    for (let i = 0; i < round.holeCount; i += 1) {
      const toPar = getToPar(round, i, playerId)
      if (toPar == null) continue
      if (!worstHole || toPar > worstHole.toPar) {
        worstHole = { hole: i + 1, toPar }
      }
    }
    if (worstHole && worstHole.toPar >= 2) {
      tips.push(
        `第 ${worstHole.hole} 洞 ${worstHole.toPar > 0 ? `+${worstHole.toPar}` : worstHole.toPar} 最大失分——複盤該洞策略與開球選擇。`,
      )
    }
  }

  if (tips.length === 0 && stats.holesPlayed > 0) {
    tips.push('教練欄位已有紀錄，整體穩定——維持現有節奏即可。')
  }

  return {
    totalPutts: stats.putts,
    girPct,
    fairwayPct,
    bogeyPlusHoles,
    puttBars,
    tips: tips.slice(0, 3),
  }
}
