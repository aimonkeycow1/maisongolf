import { makeId } from '../lib/ids'
import type { Course, Round } from '../types'

export const SEED_COURSE_ID = 'course_seed_kau-sai-chau-east'
export const SEED_COURSE_NAME = '滘西洲東場'
export const SEED_COURSE_PARS = [
  5, 4, 3, 4, 3, 5, 4, 3, 4, 5, 4, 4, 3, 4, 3, 5, 4, 5,
]

const DEFAULT_PARS_18 = [4, 4, 3, 5, 4, 4, 3, 5, 4, 4, 4, 3, 5, 4, 4, 3, 5, 4]

export function normalizeName(name: string): string {
  return name.trim().replace(/\s+/g, ' ')
}

export function isHoleCount(n: unknown): n is 9 | 18 {
  return n === 9 || n === 18
}

export function normalizePars(pars: unknown, holeCount: number): number[] {
  const src = Array.isArray(pars) ? pars : []
  const out: number[] = []
  for (let i = 0; i < holeCount; i += 1) {
    const p = src[i]
    out.push(p === 3 || p === 4 || p === 5 ? p : 4)
  }
  return out
}

export function padParsTo18(pars: number[]): number[] {
  return normalizePars(pars, 18)
}

export function createSeedCourse(updatedAt = Date.now()): Course {
  return {
    id: SEED_COURSE_ID,
    name: SEED_COURSE_NAME,
    holeCount: 18,
    pars: [...SEED_COURSE_PARS],
    updatedAt,
  }
}

export function parseCourse(raw: unknown): Course | null {
  if (!raw || typeof raw !== 'object') return null
  const t = raw as Record<string, unknown>
  const name = typeof t.name === 'string' ? normalizeName(t.name) : ''
  if (!name) return null
  const holeCount = isHoleCount(t.holeCount) ? t.holeCount : 18
  const id =
    typeof t.id === 'string' && t.id.trim() ? t.id : makeId('c')
  const updatedAt = typeof t.updatedAt === 'number' ? t.updatedAt : 0
  return {
    id,
    name,
    holeCount,
    pars: normalizePars(t.pars, holeCount),
    updatedAt,
  }
}

export function dedupeCourses(list: unknown): Course[] {
  if (!Array.isArray(list)) return []
  const map = new Map<string, Course>()
  for (const item of list) {
    const course = parseCourse(item)
    if (!course) continue
    const prev = map.get(course.name)
    if (!prev || course.updatedAt >= prev.updatedAt) {
      map.set(course.name, course)
    }
  }
  return [...map.values()]
}

export function findCourseByName(
  courses: Course[],
  name: string,
): Course | undefined {
  const n = normalizeName(name)
  if (!n) return undefined
  return courses.find((c) => c.name === n)
}

export function sortCourses(courses: Course[]): Course[] {
  return [...courses].sort((a, b) => {
    if (a.name === SEED_COURSE_NAME && b.name !== SEED_COURSE_NAME) return -1
    if (b.name === SEED_COURSE_NAME && a.name !== SEED_COURSE_NAME) return 1
    if (b.updatedAt === a.updatedAt) {
      return a.name.localeCompare(b.name, 'zh-Hant')
    }
    return b.updatedAt - a.updatedAt
  })
}

function upsertCourse(
  courses: Course[],
  draft: { name: string; holeCount: 9 | 18; pars: number[] },
  updatedAt = Date.now(),
): Course[] {
  const name = normalizeName(draft.name)
  if (!name) return courses
  const holeCount = draft.holeCount
  const pars = normalizePars(draft.pars, holeCount)
  if (courses.find((c) => c.name === name)) {
    return courses.map((c) =>
      c.name === name ? { ...c, holeCount, pars, updatedAt } : c,
    )
  }
  return [
    {
      id: makeId('c'),
      name,
      holeCount,
      pars,
      updatedAt,
    },
    ...courses,
  ]
}

export function rememberCourse(
  courses: Course[],
  draft: { name: string; holeCount: 9 | 18; pars: number[] },
  updatedAt = Date.now(),
): Course[] {
  if (!normalizeName(draft.name)) return courses
  return sortCourses(upsertCourse(courses, draft, updatedAt))
}

function courseFromRound(round: Round): Course | null {
  const name = normalizeName(round.courseName)
  if (!name) return null
  const holeCount = isHoleCount(round.holeCount) ? round.holeCount : 18
  return {
    id: makeId('c'),
    name,
    holeCount,
    pars: normalizePars(round.pars, holeCount),
    updatedAt: typeof round.updatedAt === 'number' ? round.updatedAt : 0,
  }
}

/** Ensure seed course exists; backfill from rounds when missing. */
export function ensureCourses(
  courses: Course[],
  rounds: Round[],
  now = Date.now(),
): { courses: Course[]; changed: boolean } {
  const map = new Map<string, Course>()
  for (const c of courses) map.set(c.name, c)
  let changed = false
  if (!map.has(SEED_COURSE_NAME)) {
    map.set(SEED_COURSE_NAME, createSeedCourse(now))
    changed = true
  }
  for (const round of rounds) {
    const fromRound = courseFromRound(round)
    if (fromRound && !map.has(fromRound.name)) {
      map.set(fromRound.name, fromRound)
      changed = true
    }
  }
  return { courses: sortCourses([...map.values()]), changed }
}

export function defaultParsForHoleCount(holeCount: 9 | 18): number[] {
  return DEFAULT_PARS_18.slice(0, holeCount)
}

export function cyclePar(par: number): number {
  return par === 3 ? 4 : par === 4 ? 5 : 3
}

export function sumPars(pars: number[], from = 0, to = pars.length): number {
  return pars.slice(from, to).reduce((a, b) => a + b, 0)
}
