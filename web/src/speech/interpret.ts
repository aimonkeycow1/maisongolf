import type { Player, VoicePreview } from '../types'
import { parseVoiceCommand, resolvePlayer } from './parser'

const MANUAL = '沒有記入分數。請用上方 + / −，或點擊桿數手動記。'

const SCORE_LABEL: Record<number, string> = {
  [-3]: '信天翁',
  [-2]: '老鷹',
  [-1]: '小鳥',
  [0]: '帕',
  [1]: '柏忌',
  [2]: '雙柏忌',
  [3]: '三柏忌',
}

export type InterpretContext = {
  holeCount: number
  holeIndex: number
  par: number
  players: Player[]
  focusedPlayerId: string | null
  strokesFor: (playerId: string) => number | null
}

export function scoreWords(par: number, strokes: number): string {
  const offset = strokes - par
  if (Object.prototype.hasOwnProperty.call(SCORE_LABEL, offset)) {
    return SCORE_LABEL[offset]!
  }
  if (offset > 0) return `+${offset}`
  return String(offset)
}

export function formatScoreSummary(
  playerName: string,
  holeNo: number,
  par: number,
  strokes: number,
): string {
  return `${playerName} 第${holeNo}洞 ${strokes}桿（${scoreWords(par, strokes)}）`
}

function fail(heard: string, message: string): VoicePreview {
  return { ok: false, heard, message }
}

function didntUnderstand(heard: string): VoicePreview {
  const lead = heard ? `沒聽懂「${heard}」。` : '沒聽到清楚的話。'
  return fail(heard, `${lead}${MANUAL}`)
}

export function interpretVoiceTranscript(
  raw: string,
  ctx: InterpretContext,
): VoicePreview {
  const heard = raw.trim()
  if (!heard) {
    return fail(
      '',
      `沒聽到清楚的話。${MANUAL}`,
    )
  }

  const cmd = parseVoiceCommand(heard)
  const holeNo = ctx.holeIndex + 1

  if (cmd.type === 'unknown') return didntUnderstand(heard)

  if (cmd.type === 'nextHole') {
    if (ctx.holeIndex >= ctx.holeCount - 1) {
      return fail(heard, '已經是最後一洞。沒有跳洞，也沒有記入分數。')
    }
    const hole = holeNo + 1
    return {
      ok: true,
      kind: 'nav',
      heard,
      fromHoleIndex: ctx.holeIndex,
      hole,
      summary: `第${hole}洞`,
    }
  }

  if (cmd.type === 'prevHole') {
    if (ctx.holeIndex <= 0) {
      return fail(heard, '已經是第1洞。沒有跳洞，也沒有記入分數。')
    }
    const hole = holeNo - 1
    return {
      ok: true,
      kind: 'nav',
      heard,
      fromHoleIndex: ctx.holeIndex,
      hole,
      summary: `第${hole}洞`,
    }
  }

  if (cmd.type === 'gotoHole') {
    if (cmd.hole < 1 || cmd.hole > ctx.holeCount) {
      return fail(
        heard,
        `本場只有${ctx.holeCount}洞。沒有跳洞，也沒有記入分數。`,
      )
    }
    return {
      ok: true,
      kind: 'nav',
      heard,
      fromHoleIndex: ctx.holeIndex,
      hole: cmd.hole,
      summary: `第${cmd.hole}洞`,
    }
  }

  const player = resolvePlayer(
    'playerQuery' in cmd ? cmd.playerQuery : undefined,
    ctx.players,
    ctx.focusedPlayerId,
  )
  if (!player) {
    const named = 'playerQuery' in cmd ? cmd.playerQuery : undefined
    return fail(
      heard,
      named
        ? `找不到球員「${named}」。${MANUAL}`
        : `請先點選一名球員。${MANUAL}`,
    )
  }

  if (cmd.type === 'setScore') {
    if (cmd.strokes < 1 || cmd.strokes > 15) {
      return fail(heard, `桿數需在 1–15 之間。${MANUAL}`)
    }
    return {
      ok: true,
      kind: 'score',
      heard,
      playerId: player.id,
      playerName: player.name,
      holeIndex: ctx.holeIndex,
      holeNo,
      par: ctx.par,
      strokes: cmd.strokes,
      summary: formatScoreSummary(player.name, holeNo, ctx.par, cmd.strokes),
    }
  }

  if (cmd.type === 'setRelative') {
    const strokes = ctx.par + cmd.offset
    if (strokes < 1 || strokes > 15) {
      return fail(heard, `這樣會變成 ${strokes} 桿，超出 1–15。${MANUAL}`)
    }
    return {
      ok: true,
      kind: 'score',
      heard,
      playerId: player.id,
      playerName: player.name,
      holeIndex: ctx.holeIndex,
      holeNo,
      par: ctx.par,
      strokes,
      summary: formatScoreSummary(player.name, holeNo, ctx.par, strokes),
    }
  }

  const current = ctx.strokesFor(player.id)
  const base = current ?? ctx.par
  const strokes = base + cmd.delta
  if (strokes < 1 || strokes > 15) {
    return fail(heard, `這樣會變成 ${strokes} 桿，超出 1–15。${MANUAL}`)
  }
  const how =
    current == null
      ? `標準桿${ctx.par}${cmd.delta > 0 ? '加' : '減'}${Math.abs(cmd.delta)}`
      : `${current}${cmd.delta > 0 ? '加' : '減'}${Math.abs(cmd.delta)}`
  const summary = `${player.name} 第${holeNo}洞 ${strokes}桿（${scoreWords(ctx.par, strokes)}，${how}）`
  return {
    ok: true,
    kind: 'score',
    heard,
    playerId: player.id,
    playerName: player.name,
    holeIndex: ctx.holeIndex,
    holeNo,
    par: ctx.par,
    strokes,
    summary,
  }
}
