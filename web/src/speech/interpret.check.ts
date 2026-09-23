import { interpretVoiceTranscript, type InterpretContext } from './interpret'
import { LISTEN_MS } from './listen'
import type { Player, VoicePreview } from '../types'

const players: Player[] = [
  { id: 'p1', name: '小明' },
  { id: 'p2', name: '小王' },
]

function ctx(
  strokes: number | null,
  par = 4,
  holeIndex = 0,
): InterpretContext {
  return {
    holeCount: 18,
    holeIndex,
    par,
    players,
    focusedPlayerId: 'p1',
    strokesFor: (id) => (id === 'p1' ? strokes : null),
  }
}

function assert(cond: unknown, msg: string): asserts cond {
  if (!cond) throw new Error(msg)
}

function scoreOf(preview: VoicePreview): number {
  assert(preview.ok && preview.kind === 'score', `expected score, got ${JSON.stringify(preview)}`)
  return preview.strokes
}

function expectScore(
  raw: string,
  strokes: number,
  options?: { par?: number; current?: number | null; playerId?: string; summary?: string },
) {
  const preview = interpretVoiceTranscript(
    raw,
    ctx(options?.current ?? null, options?.par ?? 4),
  )
  assert(
    preview.ok && preview.kind === 'score',
    `${raw} → ${JSON.stringify(preview)}`,
  )
  assert(preview.strokes === strokes, `${raw} strokes ${preview.strokes} !== ${strokes}`)
  if (options?.playerId) {
    assert(preview.playerId === options.playerId, `${raw} player ${preview.playerId}`)
  }
  if (options?.summary) {
    assert(
      preview.summary.includes(options.summary),
      `${raw} summary ${preview.summary} missing ${options.summary}`,
    )
  }
  assert(!('message' in preview), `${raw} should not be a failure`)
}

function expectFail(raw: string, snippet: string) {
  const preview = interpretVoiceTranscript(raw, ctx(null))
  assert(!preview.ok, `${raw} should fail, got ${JSON.stringify(preview)}`)
  assert(
    preview.message.includes(snippet),
    `${raw} message ${preview.message} missing ${snippet}`,
  )
  assert(
    preview.message.includes('沒有記入') || preview.message.includes('沒有跳洞'),
    `${raw} should say nothing was written`,
  )
  assert(!('strokes' in preview), `${raw} invented a score payload`)
}

export function runVoiceChecks(): void {
  assert(LISTEN_MS <= 6000, `listen window ${LISTEN_MS} is still too long`)
  assert(LISTEN_MS < 14000, 'listen window was not shortened from 14s')

  expectScore('兩上三推', 5, { par: 4, summary: '5桿' })
  expectScore('兩上三推', 5, { par: 4, summary: '2+3' })
  expectScore('兩上三推', 5, { par: 5, summary: '5桿' })
  expectScore('2上3推', 5, { par: 5, summary: '2+3' })
  expectScore('兩上＋三推', 5, { summary: '2+3' })
  expectScore('兩上+三推', 5)
  expectScore('兩上3推', 5)
  expectScore('2上三推', 5)
  expectScore('两上三推', 5)
  expectScore('兩上三推了', 5)
  expectScore('兩上三推桿', 5)
  expectScore('小明兩上三推', 5, { playerId: 'p1', summary: '2+3' })
  expectScore('小王2上3推', 5, { playerId: 'p2' })
  expectScore('一上兩推', 3, { par: 5 })
  expectScore('三上兩推', 5, { par: 3 })
  const summed = interpretVoiceTranscript('兩上三推', ctx(null, 4))
  assert(summed.ok && summed.kind === 'score' && summed.sumOf?.[0] === 2 && summed.sumOf?.[1] === 3, JSON.stringify(summed))
  assert(summed.ok && summed.strokes === 5, '兩上三推 must be the sum 5, not par')

  expectScore('柏忌', 5, { summary: '柏忌' })
  expectScore('帕', 4, { summary: '帕' })
  expectScore('怕', 4)
  expectScore('小鳥', 3, { summary: '小鳥' })
  expectScore('抓鳥', 3)
  expectScore('抓到鳥', 3)
  expectScore('老鷹', 2, { summary: '老鷹' })
  expectScore('鷹', 2)
  expectScore('雙鷹', 1, { summary: '信天翁' })
  expectScore('三柏忌', 7, { summary: '三柏忌' })
  expectScore('雙柏忌', 6)
  expectScore('bogey', 5)
  expectScore('bogie', 5)
  expectScore('par', 4)
  expectScore('birdie', 3)
  expectScore('eagle', 2)
  expectScore('double bogey', 6)
  expectScore('double-bogey', 6)
  expectScore('triple bogey', 7)
  expectScore('albatross', 1)
  expectScore('double eagle', 1)
  expectScore('even par', 4)
  expectScore('博蒂', 3)
  expectScore('博基', 5)
  expectScore('波忌', 5)
  expectScore('超帕', 5)
  expectScore('四', 4)
  expectScore('四桿', 4)
  expectScore('4', 4)
  expectScore('5 strokes', 5, { summary: '柏忌' })
  expectScore('小明打了五桿', 5, { playerId: 'p1' })
  expectScore('小王柏忌', 5, { playerId: 'p2' })
  expectScore('打了個小鳥', 3, { playerId: 'p1' })
  expectScore('小明打par了', 4, { playerId: 'p1' })
  expectScore('小明打帕', 4, { playerId: 'p1' })
  expectScore('是帕', 4)
  expectScore('請記低柏忌', 5)
  expectScore('one over', 5)
  expectScore('one over par', 5)
  expectScore('two under par', 2)
  expectScore('over par', 5)
  expectScore('under par', 3)
  expectScore('hole in one', 1)
  expectScore('一桿進洞', 1)
  expectScore('加一桿', 5, { summary: '標準桿4加1' })
  expectScore('加一杆', 5)
  expectScore('plus one', 5, { summary: '標準桿4加1' })
  expectScore('plus 1 stroke', 5)
  expectScore('add one', 5)
  expectScore('加一', 5)
  expectScore('多一桿', 5)
  expectScore('one more', 5)
  expectScore('減一', 3, { summary: '標準桿4減1' })
  expectScore('minus one', 3)
  expectScore('加一桿', 7, { current: 6, summary: '6加1' })
  expectScore('plus one', 7, { current: 6, summary: '6加1' })
  expectScore('減一桿', 5, { current: 6, summary: '6減1' })
  expectScore('小明 6', 6, { playerId: 'p1' })
  expectScore('eight', 8)

  const moved = interpretVoiceTranscript('下一洞', ctx(null))
  assert(moved.ok && moved.kind === 'nav' && moved.hole === 2, JSON.stringify(moved))
  const back = interpretVoiceTranscript('上一洞', ctx(null, 4, 0))
  assert(!back.ok, 'prev on first hole should fail')
  const goto = interpretVoiceTranscript('第3洞', ctx(null))
  assert(goto.ok && goto.kind === 'nav' && goto.hole === 3, JSON.stringify(goto))

  expectFail('兩上', '沒聽懂')
  expectFail('三推', '沒聽懂')
  expectFail('兩上三', '沒聽懂')
  expectFail('上三推', '沒聽懂')
  expectFail('今天天氣很好', '沒聽懂')
  expectFail('今天天氣很好', '手動')
  expectFail('', '沒有記入')
  expectFail('   ', '沒有記入')
  expectFail('好多', '沒聽懂')
  expectFail('小', '沒聽懂')
  expectFail('小柏忌', '找不到球員')
  expectFail('20', '1–15')
  expectFail('0', '1–15')

  const par3Albatross = interpretVoiceTranscript('雙鷹', ctx(null, 3))
  assert(!par3Albatross.ok, 'par 3 albatross must not invent 1')
  assert(scoreOf(interpretVoiceTranscript('柏忌', ctx(null, 5))) === 6, 'par 5 bogey')
}
