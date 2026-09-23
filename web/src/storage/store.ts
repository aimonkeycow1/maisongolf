import { createDemoRound } from '../courses/demo'
import { ensureCourses, rememberCourse } from '../courses/memory'
import { makeId } from '../lib/ids'
import {
  clampPenalties,
  clampPutts,
  clampStrokes,
  getHoleScore,
  getStrokes,
  normalizeHoleScore,
  strokesFromParOffset,
} from '../stats/round'
import type {
  AppState,
  ArchivePayload,
  Fairway,
  HoleScore,
  Round,
  Screen,
  VoiceLang,
} from '../types'
import { idbGetState, idbSetState } from './idb'

/** Legacy localStorage key — still used as write-through mirror + migration source. */
export const STORAGE_KEY = 'golf-scorekeeper-v1'
export const DEFAULT_SCORE_GOAL = 95
/** Durable primary store: IndexedDB database `golf-scorekeeper`. */
export const IDB_DB_NAME = 'golf-scorekeeper'

const DEFAULT_STATE_BASE: Omit<AppState, 'courses'> = {
  screen: 'home',
  activeRoundId: null,
  focusedPlayerId: null,
  voiceLang: 'zh-HK',
  speechUx: 2,
  scoreGoal: DEFAULT_SCORE_GOAL,
  rounds: [],
}

function isScreen(v: unknown): v is Screen {
  return (
    v === 'home' ||
    v === 'new' ||
    v === 'score' ||
    v === 'scorecard' ||
    v === 'archive'
  )
}

function isVoiceLang(v: unknown): v is VoiceLang {
  return v === 'zh-CN' || v === 'zh-HK' || v === 'zh-TW' || v === 'en-US'
}

function createDefaultState(): AppState {
  return {
    ...DEFAULT_STATE_BASE,
    courses: ensureCourses([], []).courses,
  }
}

function resolveVoiceLang(raw: Record<string, unknown>): VoiceLang {
  const speechUx = typeof raw.speechUx === 'number' ? raw.speechUx : 1
  if (speechUx >= 2 && isVoiceLang(raw.voiceLang)) return raw.voiceLang
  return 'zh-HK'
}

function hydrateFromRaw(parsed: Record<string, unknown>): AppState | null {
  if (!parsed || !Array.isArray(parsed.rounds)) return null

  const { courses, changed } = ensureCourses(
    Array.isArray(parsed.courses) ? parsed.courses : [],
    parsed.rounds as Round[],
  )

  const next: AppState = {
    screen: isScreen(parsed.screen) ? parsed.screen : 'home',
    activeRoundId:
      typeof parsed.activeRoundId === 'string' ? parsed.activeRoundId : null,
    focusedPlayerId:
      typeof parsed.focusedPlayerId === 'string'
        ? parsed.focusedPlayerId
        : null,
    speechUx: typeof parsed.speechUx === 'number' ? parsed.speechUx : 1,
    voiceLang: resolveVoiceLang(parsed),
    scoreGoal:
      typeof parsed.scoreGoal === 'number' && parsed.scoreGoal > 0
        ? Math.round(parsed.scoreGoal)
        : DEFAULT_SCORE_GOAL,
    rounds: parsed.rounds as Round[],
    courses,
  }
  return changed ? { ...next, courses } : next
}

function readLocalStorageRaw(): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Record<string, unknown>
    if (!parsed || !Array.isArray(parsed.rounds)) return null
    return parsed
  } catch {
    return null
  }
}

/** Write-through: IndexedDB (primary) + localStorage mirror (fast resume / fallback). */
export function saveState(next: AppState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    /* ignore quota */
  }
  void idbSetState(next)
}

export function loadStateFromLocalStorage(): AppState {
  const raw = readLocalStorageRaw()
  if (!raw) {
    const fresh = createDefaultState()
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh))
    } catch {
      /* ignore */
    }
    return fresh
  }
  return hydrateFromRaw(raw) ?? createDefaultState()
}

let state: AppState = loadStateFromLocalStorage()
let booted = false
let bootPromise: Promise<void> | null = null
const listeners = new Set<() => void>()

function emit(): void {
  saveState(state)
  listeners.forEach((fn) => fn())
}

/**
 * Prefer IndexedDB as durable source of truth; migrate localStorage once if needed.
 * Safe to call multiple times — subsequent calls await the same promise.
 */
export function bootStore(): Promise<void> {
  if (booted) return Promise.resolve()
  if (bootPromise) return bootPromise

  bootPromise = (async () => {
    const fromIdb = await idbGetState()
    if (fromIdb && typeof fromIdb === 'object') {
      const hydrated = hydrateFromRaw(fromIdb as Record<string, unknown>)
      if (hydrated) {
        state = hydrated
        // Keep localStorage mirror in sync with IDB authority.
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
        } catch {
          /* ignore */
        }
        listeners.forEach((fn) => fn())
        booted = true
        return
      }
    }

    // Migrate legacy localStorage → IndexedDB.
    const fromLs = readLocalStorageRaw()
    if (fromLs) {
      const hydrated = hydrateFromRaw(fromLs)
      if (hydrated) {
        state = hydrated
        await idbSetState(state)
        listeners.forEach((fn) => fn())
        booted = true
        return
      }
    }

    await idbSetState(state)
    booted = true
  })().catch(() => {
    booted = true
  })

  return bootPromise
}

export function isStoreBooted(): boolean {
  return booted
}

function patch(partial: Partial<AppState>): void {
  state = { ...state, ...partial }
  emit()
}

function updateRound(id: string, updater: (r: Round) => Round): void {
  patch({
    rounds: state.rounds.map((r) => (r.id === id ? updater(r) : r)),
  })
}

export function getState(): AppState {
  return state
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function getActiveRound(): Round | undefined {
  return state.rounds.find((r) => r.id === state.activeRoundId)
}

function hashForScreen(screen: Screen): string {
  if (screen === 'home') return '#/'
  if (screen === 'new') return '#/new'
  if (screen === 'scorecard') return '#/card'
  if (screen === 'archive') return '#/archive'
  return '#/play'
}

export function navigate(screen: Screen): void {
  patch({ screen })
  const hash = hashForScreen(screen)
  if (location.hash !== hash) location.hash = hash
}

export function syncHashRoute(): void {
  const path = location.hash.replace('#', '')
  if (!path || path === '/') {
    if (state.screen !== 'home') navigate(state.screen)
    return
  }
  const screen: Screen = path.startsWith('/new')
    ? 'new'
    : path.startsWith('/card')
      ? 'scorecard'
      : path.startsWith('/play')
        ? 'score'
        : path.startsWith('/archive')
          ? 'archive'
          : 'home'
  if (screen !== state.screen) patch({ screen })
}

export function setFocusedPlayer(playerId: string): void {
  patch({ focusedPlayerId: playerId })
}

export function setScoreGoal(goal: number): void {
  const n = Math.round(goal)
  if (n < 50 || n > 150) return
  patch({ scoreGoal: n })
}

function rememberFromRound(round: Round, at = Date.now()) {
  return rememberCourse(
    state.courses,
    {
      name: round.courseName,
      holeCount: round.holeCount,
      pars: round.pars,
    },
    at,
  )
}

export function startRound(input: {
  courseName: string
  holeCount: 9 | 18
  playerNames: string[]
  pars: number[]
}): void {
  const players = input.playerNames
    .map((n) => n.trim())
    .filter(Boolean)
    .slice(0, 4)
    .map((name) => ({ id: makeId('p'), name }))
  if (players.length === 0) throw new Error('請至少填寫一名球員')

  const pars = input.pars
    .slice(0, input.holeCount)
    .map((p) => (p === 3 || p === 4 || p === 5 ? p : 4))
  while (pars.length < input.holeCount) pars.push(4)

  const now = Date.now()
  const round: Round = {
    id: makeId('r'),
    courseName: input.courseName.trim(),
    holeCount: input.holeCount,
    pars,
    players,
    scores: Array.from({ length: input.holeCount }, () => ({})),
    currentHoleIndex: 0,
    status: 'in_progress',
    createdAt: now,
    updatedAt: now,
  }

  patch({
    rounds: [round, ...state.rounds],
    activeRoundId: round.id,
    focusedPlayerId: players[0]?.id ?? null,
    screen: 'score',
    courses: rememberFromRound(round, now),
  })
  location.hash = '#/play'
}

export function openRound(id: string, screen: Screen = 'score'): void {
  const round = state.rounds.find((r) => r.id === id)
  if (!round) return
  patch({
    activeRoundId: id,
    focusedPlayerId: round.players[0]?.id ?? null,
    screen,
  })
  navigate(screen)
}

export function setCurrentHole(index: number): void {
  const round = getActiveRound()
  if (!round) return
  const next = Math.max(0, Math.min(round.holeCount - 1, index))
  updateRound(round.id, (r) => ({
    ...r,
    currentHoleIndex: next,
    updatedAt: Date.now(),
  }))
}

export function nextHole(): void {
  const round = getActiveRound()
  if (!round) return
  setCurrentHole(round.currentHoleIndex + 1)
}

export function prevHole(): void {
  const round = getActiveRound()
  if (!round) return
  setCurrentHole(round.currentHoleIndex - 1)
}

function mutateHole(
  playerId: string,
  updater: (cell: HoleScore) => HoleScore | null,
  holeIndex?: number,
): void {
  const round = getActiveRound()
  if (!round) return
  const hi = holeIndex ?? round.currentHoleIndex
  updateRound(round.id, (r) => {
    const scores = r.scores.map((row, idx) => {
      if (idx !== hi) return row
      const next = updater(normalizeHoleScore(row[playerId]))
      if (next == null) {
        const rest = { ...row }
        delete rest[playerId]
        return rest
      }
      return { ...row, [playerId]: next }
    })
    return { ...r, scores, updatedAt: Date.now() }
  })
  patch({ focusedPlayerId: playerId })
}

export function setStrokes(
  playerId: string,
  strokes: number | null,
  holeIndex?: number,
): void {
  if (strokes == null) {
    mutateHole(playerId, () => null, holeIndex)
    return
  }
  mutateHole(
    playerId,
    (cell) => {
      const s = clampStrokes(strokes)
      const putts =
        cell.putts == null ? cell.putts : clampPutts(cell.putts, s)
      return { ...cell, strokes: s, putts }
    },
    holeIndex,
  )
}

export function setPutts(playerId: string, putts: number): void {
  mutateHole(playerId, (cell) => ({
    ...cell,
    putts: clampPutts(putts, cell.strokes),
  }))
}

export function adjustPutts(playerId: string, delta: number): void {
  const round = getActiveRound()
  if (!round) return
  const current = getHoleScore(round, round.currentHoleIndex, playerId).putts
  if (current == null) {
    if (delta > 0) setPutts(playerId, 1)
    return
  }
  setPutts(playerId, current + delta)
}

export function setPenalties(playerId: string, penalties: number): void {
  mutateHole(playerId, (cell) => ({
    ...cell,
    penalties: clampPenalties(penalties),
  }))
}

export function adjustPenalties(playerId: string, delta: number): void {
  const round = getActiveRound()
  if (!round) return
  const current = getHoleScore(
    round,
    round.currentHoleIndex,
    playerId,
  ).penalties
  setPenalties(playerId, current + delta)
}

export function toggleFairway(playerId: string, value: Fairway): void {
  const round = getActiveRound()
  if (!round) return
  if ((round.pars[round.currentHoleIndex] ?? 4) === 3) return
  mutateHole(playerId, (cell) => ({
    ...cell,
    fairway: cell.fairway === value ? null : value,
  }))
}

export function toggleGir(playerId: string, value: boolean): void {
  mutateHole(playerId, (cell) => ({
    ...cell,
    gir: cell.gir === value ? null : value,
  }))
}

export function adjustStrokes(playerId: string, delta: number): void {
  const round = getActiveRound()
  if (!round) return
  const current = getStrokes(round, round.currentHoleIndex, playerId)
  if (current == null) {
    if (delta > 0) setStrokes(playerId, 1)
    return
  }
  setStrokes(playerId, Math.max(1, current + delta))
}

export function setRelativeScore(playerId: string, offset: number): void {
  const round = getActiveRound()
  if (!round) return
  const par = round.pars[round.currentHoleIndex] ?? 4
  setStrokes(playerId, strokesFromParOffset(par, offset))
}

export function completeRound(): void {
  const round = getActiveRound()
  if (!round) return
  const now = Date.now()
  const completed: Round = {
    ...round,
    status: 'completed',
    updatedAt: now,
    finishedAt: now,
  }
  patch({
    rounds: state.rounds.map((r) => (r.id === round.id ? completed : r)),
    courses: rememberFromRound(completed, now),
  })
  navigate('scorecard')
}

export function reopenRound(): void {
  const round = getActiveRound()
  if (!round) return
  updateRound(round.id, (r) => ({
    ...r,
    status: 'in_progress',
    updatedAt: Date.now(),
  }))
  navigate('score')
}

export function deleteRound(id: string): void {
  const rounds = state.rounds.filter((r) => r.id !== id)
  const activeRoundId =
    state.activeRoundId === id
      ? (rounds[0]?.id ?? null)
      : state.activeRoundId
  const stillActive =
    activeRoundId && rounds.some((r) => r.id === activeRoundId)
      ? activeRoundId
      : null
  patch({ rounds, activeRoundId: stillActive })
  if (!stillActive) navigate('home')
}

export function buildArchivePayload(): ArchivePayload {
  return {
    version: 1,
    kind: 'golf-scorekeeper-archive',
    exportedAt: Date.now(),
    scoreGoal: state.scoreGoal,
    courses: state.courses,
    rounds: state.rounds,
  }
}

export function importArchivePayload(raw: unknown): { ok: true } | { ok: false; message: string } {
  if (!raw || typeof raw !== 'object') {
    return { ok: false, message: '檔案格式不正確' }
  }
  const data = raw as Record<string, unknown>
  if (data.kind !== 'golf-scorekeeper-archive' && !Array.isArray(data.rounds)) {
    return { ok: false, message: '不是成績庫封存檔' }
  }
  if (!Array.isArray(data.rounds)) {
    return { ok: false, message: '缺少 rounds' }
  }
  const rounds = data.rounds as Round[]
  const { courses } = ensureCourses(
    Array.isArray(data.courses) ? (data.courses as AppState['courses']) : [],
    rounds,
  )
  const scoreGoal =
    typeof data.scoreGoal === 'number' && data.scoreGoal > 0
      ? Math.round(data.scoreGoal)
      : state.scoreGoal

  patch({
    rounds,
    courses,
    scoreGoal,
    activeRoundId: null,
    focusedPlayerId: null,
    screen: 'archive',
  })
  return { ok: true }
}

/** Ensure 成績庫 has at least one completed round (demo seed). */
export function ensureDemoArchive(): void {
  const hasCompleted = state.rounds.some((r) => r.status === 'completed')
  if (hasCompleted) return
  const demo = createDemoRound()
  const now = Date.now()
  patch({
    rounds: [demo, ...state.rounds],
    courses: rememberFromRound(demo, now),
  })
}
