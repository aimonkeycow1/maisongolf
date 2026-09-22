import { useMemo, useState } from 'react'
import { Button } from '../components/Button'
import {
  cyclePar,
  defaultParsForHoleCount,
  findCourseByName,
  padParsTo18,
  sumPars,
} from '../courses/memory'
import { cn } from '../lib/cn'
import { useAppState } from '../storage/hooks'
import { navigate, startRound } from '../storage/store'
import type { Course } from '../types'

export function NewRoundScreen() {
  const { courses } = useAppState()
  const [courseName, setCourseName] = useState('')
  const [holeCount, setHoleCount] = useState<9 | 18>(18)
  const [playerNames, setPlayerNames] = useState([''])
  const [pars18, setPars18] = useState(() => defaultParsForHoleCount(18))
  const [error, setError] = useState('')

  const pars = useMemo(() => pars18.slice(0, holeCount), [pars18, holeCount])
  const totalPar = sumPars(pars)
  const selected = findCourseByName(courses, courseName)

  function applyCourse(course: Course) {
    setCourseName(course.name)
    setHoleCount(course.holeCount)
    setPars18(padParsTo18(course.pars))
    setError('')
  }

  function changeHoleCount(n: 9 | 18) {
    setHoleCount(n)
    setPars18((prev) => padParsTo18(prev))
  }

  function addPlayer() {
    if (playerNames.length >= 4) return
    setPlayerNames((prev) => [...prev, ''])
  }

  function submit() {
    const names = playerNames.map((n) => n.trim()).filter(Boolean)
    if (names.length === 0) {
      setError('請至少填寫一名球員')
      return
    }
    try {
      startRound({
        courseName,
        holeCount,
        playerNames: names,
        pars,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : '無法開始')
    }
  }

  return (
    <div className="flex min-h-dvh flex-col px-4 pb-10 pt-[max(1rem,env(safe-area-inset-top))]">
      <button
        type="button"
        className="self-start text-accent"
        onClick={() => navigate('home')}
      >
        ← 返回
      </button>
      <h1 className="mt-3 text-3xl font-bold">新一輪</h1>
      <p className="mt-1 text-muted">最多 4 人，同一支手機記桿。</p>

      {courses.length > 0 ? (
        <section className="mt-6">
          <p className="text-sm text-muted">常用球場</p>
          <p className="mt-1 text-sm leading-relaxed text-muted">
            點一下帶入名稱和每洞標準桿，不用再逐洞填。
          </p>
          <div className="mt-2 space-y-2">
            {courses.map((course) => {
              const isSelected = selected?.id === course.id
              return (
                <button
                  key={course.id}
                  type="button"
                  onClick={() => applyCourse(course)}
                  className={cn(
                    'flex min-h-16 w-full items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-left',
                    isSelected
                      ? 'border-accent bg-elevated'
                      : 'border-line bg-card',
                  )}
                >
                  <span>
                    <span className="block text-lg font-semibold">
                      {course.name}
                    </span>
                    <span className="text-sm text-muted">
                      {course.holeCount}洞 · 標準桿 {sumPars(course.pars)}
                    </span>
                  </span>
                  <span
                    className={cn(
                      'shrink-0 text-sm',
                      isSelected ? 'text-accent' : 'text-muted',
                    )}
                  >
                    {isSelected ? '已選' : '選用'}
                  </span>
                </button>
              )
            })}
          </div>
        </section>
      ) : null}

      <label className="mt-6 text-sm text-muted" htmlFor="course">
        球場名稱（可選）
      </label>
      <input
        id="course"
        value={courseName}
        onChange={(e) => setCourseName(e.target.value)}
        placeholder="例如：滘西洲東場"
        className="mt-1 min-h-14 rounded-2xl border border-line bg-card px-4 text-lg outline-none focus:border-accent"
      />
      <p className="mt-2 text-sm leading-relaxed text-muted">
        填了名稱、設好標準桿後會自動記住，下次可直接選。
      </p>

      <p className="mt-6 text-sm text-muted">洞數</p>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {([9, 18] as const).map((n) => (
          <Button
            key={n}
            variant={holeCount === n ? 'lime' : 'outline'}
            onClick={() => changeHoleCount(n)}
          >
            {n} 洞
          </Button>
        ))}
      </div>

      <p className="mt-6 text-sm text-muted">球員（1–4 人）</p>
      <div className="mt-2 space-y-2">
        {playerNames.map((name, idx) => (
          <div key={idx} className="flex gap-2">
            <input
              value={name}
              onChange={(e) => {
                const next = [...playerNames]
                next[idx] = e.target.value
                setPlayerNames(next)
                setError('')
              }}
              placeholder={`球員${idx + 1} 姓名`}
              className="min-h-14 flex-1 rounded-2xl border border-line bg-card px-4 text-lg outline-none focus:border-accent"
            />
            {playerNames.length > 1 ? (
              <Button
                variant="ghost"
                className="px-3 text-muted"
                onClick={() =>
                  setPlayerNames(playerNames.filter((_, i) => i !== idx))
                }
              >
                去掉
              </Button>
            ) : null}
          </div>
        ))}
      </div>
      {playerNames.length < 4 ? (
        <Button variant="secondary" className="mt-2 w-full" onClick={addPlayer}>
          新增球員
        </Button>
      ) : null}

      <div className="mt-6 flex items-end justify-between">
        <p className="text-sm text-muted">各洞標準桿 · 點一下切換 3/4/5</p>
        <p className="tabular text-accent">合計 {totalPar}</p>
      </div>
      <div className="mt-2 grid grid-cols-6 gap-2">
        {pars.map((par, idx) => (
          <button
            key={idx}
            type="button"
            aria-label={`第${idx + 1}洞標準桿 ${par}`}
            onClick={() => {
              const next = [...pars18]
              next[idx] = cyclePar(par)
              setPars18(next)
            }}
            className={cn(
              'flex min-h-14 flex-col items-center justify-center rounded-2xl border',
              par === 3 && 'border-[#8aa4b4] bg-[#dce8ef]',
              par === 4 && 'border-line bg-elevated',
              par === 5 && 'border-[#c4b07a] bg-[#efe4c8]',
            )}
          >
            <span className="text-[10px] text-muted">{idx + 1}</span>
            <span className="tabular text-xl font-semibold">{par}</span>
          </button>
        ))}
      </div>

      {error ? (
        <p className="mt-4 rounded-2xl bg-warn-bg px-3 py-2 text-warn">
          {error}
        </p>
      ) : null}

      <Button
        variant="lime"
        size="xl"
        className="mt-6 w-full"
        onClick={submit}
      >
        開始計分
      </Button>
    </div>
  )
}
