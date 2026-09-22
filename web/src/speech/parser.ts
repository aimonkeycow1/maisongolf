import type { Player, VoiceCommand } from '../types'
import {
  NUM_TOKEN,
  normalizeSpeech,
  parseNumberToken,
  stripStrokeSuffix,
  takeLeadingNumber,
} from './numbers'

const RELATIVE_PATTERNS: Array<{ offset: number; pattern: RegExp }> = [
  { offset: 2, pattern: /雙柏忌|双柏忌|double\s*bogeys?/i },
  { offset: -2, pattern: /老鷹|老鹰|雙鷹|双鹰|\beagles?\b/i },
  { offset: -1, pattern: /抓鳥|抓鸟|小鳥|小鸟|\bbirdies?\b/i },
  { offset: 1, pattern: /柏忌|\bbogeys?\b/i },
  { offset: 0, pattern: /\bpars?\b|標準桿|标准杆/i },
]

function cleanPlayerQuery(raw: string): string | undefined {
  return (
    raw
      .replace(/的/g, ' ')
      .replace(/\b(please|set|score)\b/gi, ' ')
      .trim() || undefined
  )
}

function relativeTailOk(rest: string): boolean {
  const t = rest.replace(/了/g, '').replace(/\s+/g, '').trim()
  return t === '' || /^(杆|桿|分)$/.test(t)
}

function extractPlayerBeforeRelative(before: string): string | undefined {
  return cleanPlayerQuery(
    before
      .replace(/了/g, ' ')
      .replace(/打了?/g, ' ')
      .replace(/\b(got|made|hit|scored|is|was|a|an|the|for)\b/gi, ' ')
      .trim(),
  )
}

function parseRelative(text: string): VoiceCommand | null {
  for (const item of RELATIVE_PATTERNS) {
    const m = text.match(item.pattern)
    if (!m || m.index == null) continue
    if (!relativeTailOk(text.slice(m.index + m[0].length))) continue
    const playerQuery = extractPlayerBeforeRelative(text.slice(0, m.index))
    return {
      type: 'setRelative',
      offset: item.offset,
      ...(playerQuery ? { playerQuery } : {}),
    }
  }
  return null
}

function parseAdjust(text: string): VoiceCommand | null {
  const plus = text.match(
    /^(.*?)(?:plus|\+|加|增加|多)\s*(one|two|[0-9一二两三兩四五六七八九十]+)?\s*(杆|桿|分|stroke)?$/i,
  )
  if (plus && /plus|\+|加|增加|多/i.test(plus[0])) {
    const delta = plus[2] ? parseNumberToken(plus[2]) : 1
    if (delta == null || delta === 0) return null
    const playerQuery = cleanPlayerQuery(plus[1]!)
    return {
      type: 'adjust',
      delta,
      ...(playerQuery ? { playerQuery } : {}),
    }
  }
  const minus = text.match(
    /^(.*?)(?:minus|−|-|减|減|减去|減去|少)\s*(one|two|[0-9一二两三兩四五六七八九十]+)?\s*(杆|桿|分|stroke)?$/i,
  )
  if (minus && /minus|−|-|减|減|少/i.test(minus[0])) {
    const delta = minus[2] ? parseNumberToken(minus[2]) : 1
    if (delta == null || delta === 0) return null
    const playerQuery = cleanPlayerQuery(minus[1]!)
    return {
      type: 'adjust',
      delta: -delta,
      ...(playerQuery ? { playerQuery } : {}),
    }
  }
  return null
}

function parseSetScore(text: string): VoiceCommand | null {
  const zhStroke = text.match(RegExp(`^(.*?)${NUM_TOKEN}\\s*[杆桿]$`))
  if (zhStroke) {
    const strokes = parseNumberToken(zhStroke[2]!)
    if (strokes == null) return null
    const playerQuery = cleanPlayerQuery(zhStroke[1]!)
    return {
      type: 'setScore',
      strokes,
      ...(playerQuery ? { playerQuery } : {}),
    }
  }

  const en = text.match(
    /^(.*?)(?:score|set)?\s*(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|\d{1,2})\s*(?:strokes?)?$/i,
  )
  if (en && /stroke|score|set|\d/.test(text.toLowerCase())) {
    const strokes = parseNumberToken(en[2]!)
    if (strokes == null) return null
    const playerQuery = cleanPlayerQuery(
      en[1]!.replace(/\b(score|set)\b/gi, ''),
    )
    return {
      type: 'setScore',
      strokes,
      ...(playerQuery ? { playerQuery } : {}),
    }
  }

  const leading = takeLeadingNumber(text)
  if (leading && stripStrokeSuffix(leading.rest) === '') {
    return { type: 'setScore', strokes: leading.value }
  }

  const spaced = text.match(RegExp(`^(.+?)\\s+${NUM_TOKEN}$`))
  if (spaced) {
    const strokes = parseNumberToken(spaced[2]!)
    const playerQuery = cleanPlayerQuery(spaced[1]!)
    if (strokes != null && playerQuery) {
      return { type: 'setScore', strokes, playerQuery }
    }
  }

  const glued = text.match(RegExp(`^(.+?)${NUM_TOKEN}$`))
  if (glued) {
    const strokes = parseNumberToken(glued[2]!)
    const playerQuery = cleanPlayerQuery(glued[1]!)
    if (strokes != null && playerQuery && !/^(第|下|上)$/.test(playerQuery)) {
      return { type: 'setScore', strokes, playerQuery }
    }
  }

  return null
}

export function parseVoiceCommand(raw: string): VoiceCommand {
  const text = normalizeSpeech(raw)
  if (!text) return { type: 'unknown' }
  const lower = text.toLowerCase()

  if (
    /^(下一洞|下个洞|下個洞|下洞|下一个|下一個|next(?:\s+hole)?)$/i.test(lower)
  ) {
    return { type: 'nextHole' }
  }
  if (
    /^(上一洞|上个洞|上個洞|上洞|上一个|上一個|prev(?:ious)?(?:\s+hole)?|last hole|back)$/i.test(
      lower,
    )
  ) {
    return { type: 'prevHole' }
  }

  const goto =
    text.match(/^(?:去|到|跳到)?第\s*([0-9一二三四五六七八九十]+)\s*洞$/) ??
    lower.match(
      /^hole\s+([0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen)$/,
    )
  if (goto) {
    const hole = parseNumberToken(goto[1]!)
    if (hole != null) return { type: 'gotoHole', hole }
  }

  return (
    parseRelative(text) ||
    parseAdjust(text) ||
    parseSetScore(text) || { type: 'unknown' }
  )
}

export function resolvePlayer(
  query: string | undefined,
  players: Player[],
  focusedPlayerId: string | null,
): Player | null {
  if (query) {
    const q = query.trim().toLowerCase()
    if (!q) return null
    const exact = players.find((p) => p.name.trim().toLowerCase() === q)
    if (exact) return exact
    const indexed = q.match(/^(?:球员|球員|player)\s*([1-4一二三四])$/)
    if (indexed) {
      const n = parseNumberToken(indexed[1]!)
      if (n != null && players[n - 1]) return players[n - 1]!
    }
    const partial = players.filter((p) => {
      const name = p.name.trim().toLowerCase()
      return name.includes(q) || q.includes(name)
    })
    if (partial.length === 1) return partial[0]!
    return null
  }
  if (focusedPlayerId) {
    const focused = players.find((p) => p.id === focusedPlayerId)
    if (focused) return focused
  }
  return players[0] ?? null
}
