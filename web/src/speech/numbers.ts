const ZH_DIGITS: Record<string, number> = {
  零: 0,
  一: 1,
  壹: 1,
  二: 2,
  两: 2,
  兩: 2,
  三: 3,
  四: 4,
  五: 5,
  六: 6,
  七: 7,
  八: 8,
  九: 9,
}

const EN_DIGITS: Record<string, number> = {
  zero: 0,
  one: 1,
  two: 2,
  three: 3,
  four: 4,
  five: 5,
  six: 6,
  seven: 7,
  eight: 8,
  nine: 9,
  ten: 10,
  eleven: 11,
  twelve: 12,
  thirteen: 13,
  fourteen: 14,
  fifteen: 15,
}

const FILLER = /[呀啊啦喎喔哦呢嘿咯囉噶嘅嗯咁吧嘛咧喲唷哇耶]/g

export const NUM_TOKEN =
  '([0-9]{1,2}|十[一二三四五六七八九]?|[一二三四五六七八九]十[一二三四五六七八九]?|[一二两三兩四五六七八九十壹])'

export function normalizeSpeech(input: string): string {
  return input
    .replace(/[，。,.!！?？、]/g, ' ')
    .replace(/[０-９]/g, (ch) =>
      String.fromCharCode(ch.charCodeAt(0) - 65296 + 48),
    )
    .replace(FILLER, '')
    .replace(/^(係|是|为|為)\s*/u, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function parseNumberToken(raw: string): number | null {
  const t = raw.trim().toLowerCase()
  if (!t) return null
  if (/^\d{1,2}$/.test(t)) return Number(t)
  if (t in EN_DIGITS) return EN_DIGITS[t]!
  if (t === '十') return 10
  if (t.startsWith('十') && t.length === 2 && t[1]! in ZH_DIGITS) {
    return 10 + ZH_DIGITS[t[1]!]!
  }
  if (t.length === 2 && t.endsWith('十') && t[0]! in ZH_DIGITS) {
    return ZH_DIGITS[t[0]!]! * 10
  }
  if (
    t.length === 3 &&
    t[1] === '十' &&
    t[0]! in ZH_DIGITS &&
    t[2]! in ZH_DIGITS
  ) {
    return ZH_DIGITS[t[0]!]! * 10 + ZH_DIGITS[t[2]!]!
  }
  if (t.length === 1 && t in ZH_DIGITS) return ZH_DIGITS[t]!
  return null
}

export function takeLeadingNumber(
  text: string,
): { value: number; rest: string } | null {
  const t = text.trim()
  const en = t.match(
    /^(ten|eleven|twelve|thirteen|fourteen|fifteen|one|two|three|four|five|six|seven|eight|nine|zero)\b/i,
  )
  if (en) {
    const value = parseNumberToken(en[1]!)
    if (value != null) return { value, rest: t.slice(en[0].length).trim() }
  }
  const zh = t.match(RegExp(`^${NUM_TOKEN}`))
  if (zh) {
    const value = parseNumberToken(zh[1]!)
    if (value != null) return { value, rest: t.slice(zh[0].length).trim() }
  }
  return null
}

export function stripStrokeSuffix(text: string): string {
  return text.replace(/^(杆|桿|分|strokes?|stroke)\s*/i, '').trim()
}
