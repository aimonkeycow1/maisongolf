export const RELATIVE_OUTCOMES = [
  { id: 'eagle', offset: -2, zh: '老鷹', en: 'eagle' },
  { id: 'birdie', offset: -1, zh: '抓鳥', zhAlt: '小鳥', en: 'birdie' },
  { id: 'par', offset: 0, zh: 'Par', en: 'par' },
  { id: 'bogey', offset: 1, zh: '柏忌', en: 'bogey' },
  { id: 'doubleBogey', offset: 2, zh: '雙柏忌', en: 'double bogey' },
] as const

export function relativeChipCaption(
  outcome: (typeof RELATIVE_OUTCOMES)[number],
  par: number,
): string {
  const strokes = Math.max(1, Math.min(15, par + outcome.offset))
  const offsetLabel =
    outcome.offset === 0
      ? '±0'
      : outcome.offset > 0
        ? `+${outcome.offset}`
        : String(outcome.offset)
  return `${strokes}桿 ${offsetLabel}`
}
