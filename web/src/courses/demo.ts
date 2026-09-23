import { makeId } from '../lib/ids'
import { SEED_COURSE_NAME, SEED_COURSE_PARS } from '../courses/memory'
import type { Fairway, HoleScore, Round } from '../types'

type DemoHole = {
  strokes: number
  putts: number | null
  penalties: number
  fairway: Fairway | null
  gir: boolean | null
}

function cell(
  strokes: number,
  putts: number | null,
  penalties = 0,
  fairway: Fairway | null = null,
  gir: boolean | null = null,
): DemoHole {
  return { strokes, putts, penalties, fairway, gir }
}

/** DP full coach fields from 2026-09-16 Kau Sai Chau East scorecard. */
const DP_HOLES: DemoHole[] = [
  cell(5, 3, 0, 'hit', false),
  cell(5, 2, 0, 'hit', false),
  cell(5, 2, 1, null, null),
  cell(4, 2, 0, 'hit', true),
  cell(4, 2, 0, null, null),
  cell(8, 3, 0, null, null),
  cell(5, 2, 1, null, null),
  cell(6, 3, 1, null, null),
  cell(4, 1, 0, 'hit', true),
  cell(8, 3, 1, 'hit', false),
  cell(4, 1, 0, 'miss', false),
  cell(4, 2, 0, 'hit', true),
  cell(4, 3, 0, null, true),
  cell(5, 3, 0, null, null),
  cell(3, 2, 0, null, null),
  cell(5, 2, 0, null, null),
  cell(5, 1, 0, 'hit', false),
  cell(5, 2, 0, null, null),
]

/** LCK strokes; putts sparse as in source markdown. */
const LCK_HOLES: DemoHole[] = [
  cell(5, null, 0),
  cell(5, 2, 0),
  cell(3, 1, 0),
  cell(5, 3, 0),
  cell(4, 3, 0),
  cell(6, null, 0),
  cell(5, 2, 0),
  cell(3, 1, 0),
  cell(6, 2, 1),
  cell(7, 2, 0),
  cell(5, null, 0),
  cell(6, null, 0),
  cell(4, null, 0),
  cell(4, null, 0),
  cell(4, null, 0),
  cell(5, null, 0),
  cell(5, null, 0),
  cell(5, null, 0),
]

function toHoleScore(h: DemoHole): HoleScore {
  return {
    strokes: h.strokes,
    putts: h.putts,
    penalties: h.penalties,
    fairway: h.fairway,
    gir: h.gir,
  }
}

/** Seed one completed demo round when 成績庫 is empty. */
export function createDemoRound(): Round {
  const dpId = makeId('p')
  const lckId = makeId('p')
  const finishedAt = new Date('2026-09-16T16:00:00+08:00').getTime()
  const scores = Array.from({ length: 18 }, (_, i) => ({
    [dpId]: toHoleScore(DP_HOLES[i]!),
    [lckId]: toHoleScore(LCK_HOLES[i]!),
  }))

  return {
    id: makeId('r'),
    courseName: SEED_COURSE_NAME,
    holeCount: 18,
    pars: [...SEED_COURSE_PARS],
    players: [
      { id: dpId, name: 'DP' },
      { id: lckId, name: 'LCK' },
    ],
    scores,
    currentHoleIndex: 17,
    status: 'completed',
    createdAt: finishedAt,
    updatedAt: finishedAt,
    finishedAt,
    isDemo: true,
  }
}
