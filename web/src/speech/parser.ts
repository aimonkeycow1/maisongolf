import type { Player, VoiceCommand } from '../types'
import {
  NUM_SRC,
  NUM_TOKEN,
  normalizeSpeech,
  parseNumberToken,
  stripStrokeSuffix,
  takeLeadingNumber,
} from './numbers'

const EN_NUM =
  'zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen'

const ADJUST_NUM = `${NUM_SRC}|${EN_NUM}`

const RELATIVE_RULES: Array<{ offset: number; pattern: RegExp }> = [
  {
    offset: 3,
    pattern: /三柏忌|三柏基|三波忌|triple[\s-]*bog(?:ey|ie)s?/i,
  },
  {
    offset: 2,
    pattern:
      /雙柏忌|双柏忌|雙柏基|双柏基|雙波忌|双波忌|double[\s-]*bog(?:ey|ie)s?/i,
  },
  {
    offset: -3,
    pattern: /信天翁|雙鷹|双鹰|albatross|double[\s-]*eagles?/i,
  },
  {
    offset: -2,
    pattern: /老鷹|老鹰|(?<![雙双老])鷹|(?<![雙双])鹰|\beagles?\b/i,
  },
  {
    offset: -1,
    pattern:
      /抓到?鳥|抓到?鸟|捉到?鳥|捉到?鸟|小鳥|小鸟|博蒂|搏蒂|\bbirdies?\b/i,
  },
  {
    offset: 1,
    pattern:
      /柏忌|柏基|波忌|波基|博忌|博基|八忌|百忌|白忌|\bbog(?:ey|ie)s?\b/i,
  },
  {
    offset: 1,
    pattern: /超帕|超標準桿|超标准杆|高於帕|高于帕|高於標準|高于标准/i,
  },
  {
    offset: -1,
    pattern: /低帕|低標準桿|低标准杆|低於帕|低于帕|低於標準|低于标准/i,
  },
  {
    offset: 0,
    pattern:
      /平帕|平標準桿|平标准杆|標準桿|标准杆|標桿|标杆|\b(?:even\s+)?pars?\b|(?:帕|怕)/i,
  },
]

const OVER_UNDER_NUM = `(${EN_NUM}|[1-6]|[一二兩三两四五六])`

function cleanPlayerQuery(raw: string): string | undefined {
  const text = raw
    .replace(/[了啦]/g, ' ')
    .replace(/打了?/g, ' ')
    .replace(/[個个]/g, ' ')
    .replace(/的/g, ' ')
    .replace(
      /\b(please|set|score|got|made|hit|scored|is|was|a|an|the|for|player|and)\b/gi,
      ' ',
    )
    .replace(/\s+/g, ' ')
    .trim()
  return text || undefined
}

function relativeTailOk(rest: string): boolean {
  const text = rest.replace(/[了啦呀啊]/g, '').replace(/\s+/g, '').trim()
  return text === '' || /^(?:杆|桿|分|球|下|strokes?)$/i.test(text)
}

function withPlayer(
  before: string,
  command: VoiceCommand,
): VoiceCommand {
  const playerQuery = cleanPlayerQuery(before)
  if (!playerQuery || !('type' in command) || command.type === 'unknown') {
    return command
  }
  if (
    command.type === 'setScore' ||
    command.type === 'setRelative' ||
    command.type === 'adjust'
  ) {
    return { ...command, playerQuery }
  }
  return command
}

function parseOverUnder(text: string): VoiceCommand | null {
  const numbered = text.match(
    new RegExp(
      `^(.*?)${OVER_UNDER_NUM}\\s+(over|under)(?:\\s+par)?$`,
      'i',
    ),
  )
  if (numbered) {
    const n = parseNumberToken(numbered[2]!)
    if (n == null || n === 0) return null
    const offset = numbered[3]!.toLowerCase() === 'over' ? n : -n
    return withPlayer(numbered[1] ?? '', { type: 'setRelative', offset })
  }
  const bare = text.match(/^(.*?)\s*(over|under)\s+par$/i)
  if (!bare) return null
  const offset = bare[2]!.toLowerCase() === 'over' ? 1 : -1
  return withPlayer(bare[1] ?? '', { type: 'setRelative', offset })
}

function parseRelative(text: string): VoiceCommand | null {
  let best: { offset: number; index: number; len: number } | null = null
  for (const item of RELATIVE_RULES) {
    const matched = text.match(item.pattern)
    if (!matched || matched.index == null) continue
    const index = matched.index
    const len = matched[0].length
    if (!relativeTailOk(text.slice(index + len))) continue
    if (
      !best ||
      len > best.len ||
      (len === best.len && index < best.index)
    ) {
      best = { offset: item.offset, index, len }
    }
  }
  if (!best) return null
  return withPlayer(text.slice(0, best.index), {
    type: 'setRelative',
    offset: best.offset,
  })
}

function parseHoleInOne(text: string): VoiceCommand | null {
  const matched = text.match(
    /^(.*?)(?:一[杆桿]進洞|一[杆桿]进洞|hole[\s-]*in[\s-]*one)$/i,
  )
  if (!matched) return null
  return withPlayer(matched[1] ?? '', { type: 'setScore', strokes: 1 })
}

const PLUS_WORD = 'plus|add|\\+|加上|加多|再加|增加|多打|加|多'
const MINUS_WORD = 'minus|subtract|−|-|减去|減去|减掉|減掉|少打|减|減|少'

function shortKeywordNeedsAmount(keyword: string, amount: string | undefined, stroke: string | undefined): boolean {
  return keyword.length === 1 && !amount && !stroke
}

function parseAdjust(text: string): VoiceCommand | null {
  const more = text.match(
    new RegExp(
      `^(.*?)${OVER_UNDER_NUM}\\s+(more|less)(?:\\s+strokes?)?$`,
      'i',
    ),
  )
  if (more) {
    const n = parseNumberToken(more[2]!)
    if (n == null || n === 0) return null
    const delta = more[3]!.toLowerCase() === 'more' ? n : -n
    return withPlayer(more[1] ?? '', { type: 'adjust', delta })
  }

  const plus = text.match(
    new RegExp(
      `^(.*?)(${PLUS_WORD})\\s*(${ADJUST_NUM})?\\s*(杆|桿|分|下|strokes?)?$`,
      'i',
    ),
  )
  if (plus && !shortKeywordNeedsAmount(plus[2]!, plus[3], plus[4])) {
    const delta = plus[3] ? parseNumberToken(plus[3]) : 1
    if (delta != null && delta !== 0) {
      return withPlayer(plus[1] ?? '', { type: 'adjust', delta })
    }
  }

  const minus = text.match(
    new RegExp(
      `^(.*?)(${MINUS_WORD})\\s*(${ADJUST_NUM})?\\s*(杆|桿|分|下|strokes?)?$`,
      'i',
    ),
  )
  if (minus && !shortKeywordNeedsAmount(minus[2]!, minus[3], minus[4])) {
    const delta = minus[3] ? parseNumberToken(minus[3]) : 1
    if (delta != null && delta !== 0) {
      return withPlayer(minus[1] ?? '', { type: 'adjust', delta: -delta })
    }
  }
  return null
}

function parseSetScore(text: string): VoiceCommand | null {
  const zhStroke = text.match(
    RegExp(`^(.*?)${NUM_TOKEN}\\s*[杆桿下]$`),
  )
  if (zhStroke) {
    const strokes = parseNumberToken(zhStroke[2]!)
    if (strokes == null) return null
    return withPlayer(zhStroke[1] ?? '', { type: 'setScore', strokes })
  }

  const en = text.match(
    new RegExp(
      `^(.*?)(?:score|set)?\\s*(${EN_NUM}|\\d{1,2})\\s*(?:strokes?)?$`,
      'i',
    ),
  )
  if (en) {
    const strokes = parseNumberToken(en[2]!)
    const prefix = (en[1] ?? '').trim()
    const hasCue = /stroke|score|set|\d/i.test(text)
    if (strokes != null && (hasCue || prefix.length > 0)) {
      return withPlayer(prefix.replace(/\b(score|set)\b/gi, ''), {
        type: 'setScore',
        strokes,
      })
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
    /^(下一洞|下个洞|下個洞|下洞|下一个|下一個|next(?:\s+hole)?)$/i.test(
      lower,
    )
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
      new RegExp(
        `^hole\\s+([0-9]+|${EN_NUM})$`,
        'i',
      ),
    )
  if (goto) {
    const hole = parseNumberToken(goto[1]!)
    if (hole != null) return { type: 'gotoHole', hole }
  }

  return (
    parseOverUnder(text) ||
    parseRelative(text) ||
    parseHoleInOne(text) ||
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
