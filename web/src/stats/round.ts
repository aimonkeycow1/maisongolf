import type { Fairway, HoleScore, Round } from '../types'
import type { CoachStats } from '../types'

export const EMPTY_HOLE: HoleScore = {
  strokes: null,
  putts: null,
  penalties: 0,
  fairway: null,
  gir: null,
}

export function normalizeHoleScore(raw: unknown): HoleScore {
  if (raw == null) return { ...EMPTY_HOLE }
  if (typeof raw === 'number') return { ...EMPTY_HOLE, strokes: raw }
  const e = raw as Record<string, unknown>
  return {
    strokes: typeof e.strokes === 'number' ? e.strokes : null,
    putts: typeof e.putts === 'number' ? e.putts : null,
    penalties:
      typeof e.penalties === 'number' && e.penalties > 0 ? e.penalties : 0,
    fairway: e.fairway === 'hit' || e.fairway === 'miss' ? e.fairway : null,
    gir: typeof e.gir === 'boolean' ? e.gir : null,
  }
}

export function clampPutts(putts: number, strokes: number | null): number {
  const max = strokes == null ? 8 : Math.max(0, Math.min(8, strokes))
  if (putts < 0) return 0
  if (putts > max) return max
  return putts
}

export function clampPenalties(n: number): number {
  if (n < 0) return 0
  if (n > 5) return 5
  return n
}

export function isThreePutt(putts: number | null | undefined): boolean {
  return putts != null && putts >= 3
}

export function fairwayLabel(fairway: Fairway | null, par: number): string {
  if (par === 3) return '—'
  if (fairway === 'hit') return '中'
  if (fairway === 'miss') return '偏'
  return '—'
}

export function girLabel(gir: boolean | null): string {
  if (gir === true) return '上'
  if (gir === false) return '沒上'
  return '—'
}

export function getHoleScore(
  round: Round,
  holeIndex: number,
  playerId: string,
): HoleScore {
  return normalizeHoleScore(round.scores[holeIndex]?.[playerId])
}

export function getStrokes(
  round: Round,
  holeIndex: number,
  playerId: string,
): number | null {
  return getHoleScore(round, holeIndex, playerId).strokes
}

export function getToPar(
  round: Round,
  holeIndex: number,
  playerId: string,
): number | null {
  const strokes = getStrokes(round, holeIndex, playerId)
  return strokes == null ? null : strokes - round.pars[holeIndex]!
}

export function totalStrokes(
  round: Round,
  playerId: string,
  from = 0,
  to: number = round.holeCount,
): number | null {
  let sum = 0
  let any = false
  for (let i = from; i < to; i += 1) {
    const s = getStrokes(round, i, playerId)
    if (s != null) {
      sum += s
      any = true
    }
  }
  return any ? sum : null
}

export function totalToPar(
  round: Round,
  playerId: string,
  from = 0,
  to: number = round.holeCount,
): number | null {
  let sum = 0
  let any = false
  for (let i = from; i < to; i += 1) {
    const d = getToPar(round, i, playerId)
    if (d != null) {
      sum += d
      any = true
    }
  }
  return any ? sum : null
}

export function holesRecorded(round: Round, playerId?: string): number {
  let n = 0
  for (let i = 0; i < round.holeCount; i += 1) {
    if (playerId) {
      if (getStrokes(round, i, playerId) != null) n += 1
    } else if (round.players.some((p) => getStrokes(round, i, p.id) != null)) {
      n += 1
    }
  }
  return n
}

export function formatToPar(n: number | null): string {
  if (n == null) return '—'
  if (n === 0) return 'E'
  if (n > 0) return `+${n}`
  return String(n)
}

export function formatOptional(n: number | null): string {
  return n == null ? '—' : String(n)
}

export function clampStrokes(n: number): number {
  if (n < 1) return 1
  if (n > 15) return 15
  return n
}

export function coachStats(round: Round, playerId: string): CoachStats {
  let holesPlayed = 0
  let puttSum = 0
  let puttHoles = 0
  let threePutts = 0
  let penalties = 0
  let fairwayHits = 0
  let fairwayAttempts = 0
  let girHits = 0
  let girAttempts = 0

  for (let i = 0; i < round.holeCount; i += 1) {
    const cell = getHoleScore(round, i, playerId)
    if (cell.strokes == null) continue
    holesPlayed += 1
    penalties += cell.penalties
    if (cell.putts != null) {
      puttSum += cell.putts
      puttHoles += 1
      if (isThreePutt(cell.putts)) threePutts += 1
    }
    const par = round.pars[i] ?? 4
    if (par !== 3 && cell.fairway) {
      fairwayAttempts += 1
      if (cell.fairway === 'hit') fairwayHits += 1
    }
    if (cell.gir != null) {
      girAttempts += 1
      if (cell.gir) girHits += 1
    }
  }

  return {
    playerId,
    holesPlayed,
    putts: puttHoles ? puttSum : null,
    threePutts,
    penalties,
    fairwayHits,
    fairwayAttempts,
    girHits,
    girAttempts,
  }
}

export function formatRatio(hits: number, attempts: number): string {
  if (attempts === 0) return '—'
  return `${hits}/${attempts}（${Math.round((hits / attempts) * 100)}%）`
}

export function displayCourseName(name: string): string {
  return name.trim() || '未命名球場'
}

export function formatRoundWhen(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  if (sameDay) return `今天 ${hh}:${mm}`
  return `${d.getMonth() + 1}月${d.getDate()}日 ${hh}:${mm}`
}

export function formatDate(ts: number): string {
  const d = new Date(ts)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function strokesFromParOffset(par: number, offset: number): number {
  return clampStrokes(Math.max(1, par + offset))
}

export function bogeyPlusCount(round: Round, playerId: string): number {
  let n = 0
  for (let i = 0; i < round.holeCount; i += 1) {
    const toPar = getToPar(round, i, playerId)
    if (toPar != null && toPar >= 1) n += 1
  }
  return n
}

export function puttPerHole(
  round: Round,
  playerId: string,
): Array<number | null> {
  return Array.from({ length: round.holeCount }, (_, i) => {
    const cell = getHoleScore(round, i, playerId)
    return cell.strokes == null ? null : cell.putts
  })
}
