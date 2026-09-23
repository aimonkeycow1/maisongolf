export type Fairway = 'hit' | 'miss'

export type HoleScore = {
  strokes: number | null
  putts: number | null
  penalties: number
  fairway: Fairway | null
  gir: boolean | null
}

export type Player = {
  id: string
  name: string
}

export type RoundStatus = 'in_progress' | 'completed'

export type Round = {
  id: string
  courseName: string
  holeCount: 9 | 18
  pars: number[]
  players: Player[]
  /** scores[holeIndex][playerId] */
  scores: Record<string, HoleScore>[]
  currentHoleIndex: number
  status: RoundStatus
  createdAt: number
  updatedAt: number
  /** Set when status becomes completed */
  finishedAt?: number
  /** Demo / seeded archive entry */
  isDemo?: boolean
}

export type Course = {
  id: string
  name: string
  holeCount: 9 | 18
  pars: number[]
  updatedAt: number
}

export type Screen = 'home' | 'new' | 'score' | 'scorecard' | 'archive'

export type VoiceLang = 'zh-HK' | 'zh-TW' | 'zh-CN' | 'en-US'

export type AppState = {
  screen: Screen
  activeRoundId: string | null
  focusedPlayerId: string | null
  voiceLang: VoiceLang
  speechUx: number
  /** Default goal for 成績庫 comparison */
  scoreGoal: number
  rounds: Round[]
  courses: Course[]
}

export type CoachStats = {
  playerId: string
  holesPlayed: number
  putts: number | null
  threePutts: number
  penalties: number
  fairwayHits: number
  fairwayAttempts: number
  girHits: number
  girAttempts: number
}

export type RelativeOutcome = {
  id: string
  offset: number
  zh: string
  zhAlt?: string
  en: string
}

export type VoiceCommand =
  | { type: 'unknown' }
  | { type: 'nextHole' }
  | { type: 'prevHole' }
  | { type: 'gotoHole'; hole: number }
  | { type: 'setScore'; strokes: number; playerQuery?: string }
  | { type: 'setRelative'; offset: number; playerQuery?: string }
  | { type: 'adjust'; delta: number; playerQuery?: string }

export type VoiceResult = {
  ok: boolean
  heard: string
  message: string
  applied?: string
}

export type ArchivePayload = {
  version: 1
  kind: 'golf-scorekeeper-archive'
  exportedAt: number
  scoreGoal: number
  courses: Course[]
  rounds: Round[]
}
