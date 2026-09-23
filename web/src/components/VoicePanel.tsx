import { useEffect, useRef, useState } from 'react'
import { cn } from '../lib/cn'
import { LISTEN_MS } from '../speech/listen'
import { formatScoreSummary } from '../speech/interpret'
import {
  commitVoicePreview,
  previewVoiceTranscript,
  setVoiceLang,
} from '../storage/store'
import type { VoiceLang, VoicePreview, VoiceResult } from '../types'
import { Button } from './Button'

const LANGS: Array<{ id: VoiceLang; label: string }> = [
  { id: 'zh-HK', label: '粵語' },
  { id: 'zh-TW', label: '國語' },
  { id: 'zh-CN', label: '普通話' },
  { id: 'en-US', label: 'EN' },
]

const LANG_ORDER: VoiceLang[] = ['zh-HK', 'zh-TW', 'zh-CN', 'en-US']

type SpeechAlt = { transcript?: string; confidence?: number }

type SpeechResultRow = {
  isFinal: boolean
  length?: number
  [index: number]: SpeechAlt | boolean | number | undefined
}

type SpeechRecognitionLike = {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  start: () => void
  stop: () => void
  abort: () => void
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null
  onerror: ((ev: { error: string }) => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionEventLike = {
  resultIndex: number
  results: ArrayLike<SpeechResultRow>
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

type ScorePreview = Extract<VoicePreview, { kind: 'score' }>
type NavPreview = Extract<VoicePreview, { kind: 'nav' }>
type ReadyPreview = ScorePreview | NavPreview

function getSpeechCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

type Support = 'ok' | 'unsupported' | 'insecure'

function getSupport(): Support {
  if (typeof window === 'undefined') return 'unsupported'
  if (!window.isSecureContext) return 'insecure'
  return getSpeechCtor() ? 'ok' : 'unsupported'
}

function supportMessage(s: Support): string {
  return s === 'insecure'
    ? '語音只在安全連線（https）下可用。請用按鈕 +/− 記分。'
    : '此瀏覽器不支援語音，請用按鈕記分。iPhone 可用 Safari（設定允許麥克風）；Android 請用 Chrome。'
}

function micDeniedMessage(): string {
  return '瀏覽器拒絕了麥克風。請到設定允許這個網站的麥克風（iPhone：設定 → Safari → 麥克風；Android：網址列左邊網站設定），然後返回按「再試一次」。+ / − 隨時可用。'
}

function nextLang(lang: VoiceLang): VoiceLang | null {
  const i = LANG_ORDER.indexOf(lang)
  if (i < 0) return LANG_ORDER[0] ?? null
  return LANG_ORDER[i + 1] ?? null
}

function langLabel(lang: VoiceLang): string {
  return LANGS.find((l) => l.id === lang)?.label ?? lang
}

function altAt(row: SpeechResultRow, index: number): SpeechAlt | null {
  const value = row[index]
  if (!value || typeof value !== 'object') return null
  return value
}

function rowAlternatives(row: SpeechResultRow): SpeechAlt[] {
  const count =
    typeof row.length === 'number' && row.length > 0 ? row.length : 1
  const alts: SpeechAlt[] = []
  for (let i = 0; i < count; i += 1) {
    const alt = altAt(row, i)
    if (!alt?.transcript?.trim()) continue
    alts.push(alt)
  }
  return alts
}

function pickTranscript(alts: SpeechAlt[]): string | null {
  if (alts.length === 0) return null
  let best = alts[0]!
  let bestParsed = previewVoiceTranscript(best.transcript ?? '').ok
  for (let i = 1; i < alts.length; i += 1) {
    const alt = alts[i]!
    const parsed = previewVoiceTranscript(alt.transcript ?? '').ok
    const confidence = alt.confidence ?? 0
    const bestConfidence = best.confidence ?? 0
    if (
      (parsed && !bestParsed) ||
      (parsed === bestParsed && confidence > bestConfidence)
    ) {
      best = alt
      bestParsed = parsed
    }
  }
  return best.transcript?.trim() || null
}

function chooseUtterance(
  ev: SpeechRecognitionEventLike,
): { text: string; isFinal: boolean } | null {
  let interim = ''
  let finalRow: SpeechResultRow | null = null
  for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
    const row = ev.results[i]
    if (!row) continue
    if (row.isFinal) {
      finalRow = row
      continue
    }
    const alt = rowAlternatives(row)[0]
    if (alt?.transcript?.trim()) interim = alt.transcript.trim()
  }
  if (finalRow) {
    const text = pickTranscript(rowAlternatives(finalRow))
    if (text) return { text, isFinal: true }
  }
  if (interim) return { text: interim, isFinal: false }
  return null
}

const NO_SPEECH =
  '沒聽到說話。沒有記入分數。請再按「開始聽」，或用上方 + / −、點擊桿數手動記。'

function openListenClock(
  onTick: (leftMs: number) => void,
  onDone: () => void,
): () => void {
  const endAt = Date.now() + LISTEN_MS
  const tick = () => {
    onTick(Math.max(0, endAt - Date.now()))
  }
  tick()
  const interval = window.setInterval(tick, 100)
  const timeout = window.setTimeout(onDone, LISTEN_MS)
  return () => {
    window.clearInterval(interval)
    window.clearTimeout(timeout)
  }
}

export function VoicePanel({
  lang,
  currentPlayerName,
}: {
  lang: VoiceLang
  currentPlayerName: string
}) {
  const support = getSupport()
  const supported = support === 'ok'
  const [listening, setListening] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [progress, setProgress] = useState(1)
  const [interim, setInterim] = useState('')
  const [draft, setDraft] = useState<ReadyPreview | null>(null)
  const [editing, setEditing] = useState(false)
  const [editStrokes, setEditStrokes] = useState(4)
  const [result, setResult] = useState<VoiceResult | null>(null)

  const recogRef = useRef<SpeechRecognitionLike | null>(null)
  const flushRef = useRef<number | null>(null)
  const settledRef = useRef(false)
  const mountedRef = useRef(true)
  const pendingRef = useRef('')
  const confirmLockRef = useRef(false)
  const clockStopRef = useRef<(() => void) | null>(null)

  function clearTimers() {
    clockStopRef.current?.()
    clockStopRef.current = null
    if (flushRef.current != null) {
      window.clearTimeout(flushRef.current)
      flushRef.current = null
    }
  }

  function releaseEngine() {
    clearTimers()
    const rec = recogRef.current
    recogRef.current = null
    try {
      rec?.abort()
    } catch {
      /* already stopped */
    }
  }

  function finishWithTranscript(raw: string) {
    if (settledRef.current) return
    settledRef.current = true
    releaseEngine()
    if (!mountedRef.current) return
    setListening(false)
    setSecondsLeft(0)
    setInterim('')
    const text = raw.trim()
    if (!text) {
      setDraft(null)
      setResult({ ok: false, heard: '', message: NO_SPEECH })
      return
    }
    const preview = previewVoiceTranscript(text)
    if (!preview.ok) {
      setDraft(null)
      setResult({ ok: false, heard: preview.heard, message: preview.message })
      return
    }
    setResult(null)
    setDraft(preview)
    setEditing(false)
    if (preview.kind === 'score') setEditStrokes(preview.strokes)
  }

  function requestFinish() {
    if (settledRef.current) return
    if (pendingRef.current.trim()) {
      finishWithTranscript(pendingRef.current)
      return
    }
    try {
      recogRef.current?.stop()
    } catch {
      finishWithTranscript('')
      return
    }
    if (flushRef.current != null) window.clearTimeout(flushRef.current)
    flushRef.current = window.setTimeout(() => {
      flushRef.current = null
      if (!settledRef.current) finishWithTranscript(pendingRef.current)
    }, 400)
  }

  function failHard(message: string) {
    if (settledRef.current) return
    settledRef.current = true
    releaseEngine()
    if (!mountedRef.current) return
    setListening(false)
    setSecondsLeft(0)
    setInterim('')
    setDraft(null)
    setResult({ ok: false, heard: '', message })
  }

  useEffect(
    () => () => {
      mountedRef.current = false
      settledRef.current = true
      clearTimers()
      try {
        recogRef.current?.abort()
      } catch {
        /* ignore */
      }
    },
    [],
  )

  function cancelListen() {
    if (settledRef.current) return
    settledRef.current = true
    pendingRef.current = ''
    releaseEngine()
    setListening(false)
    setSecondsLeft(0)
    setInterim('')
    setDraft(null)
    setResult({
      ok: false,
      heard: '',
      message: '已取消，沒有記入分數。',
    })
  }

  function wireRecognition(rec: SpeechRecognitionLike) {
    rec.onresult = (ev) => {
      if (settledRef.current) return
      const chosen = chooseUtterance(ev)
      if (!chosen) return
      pendingRef.current = chosen.text
      setInterim(chosen.text)
      if (chosen.isFinal) finishWithTranscript(chosen.text)
    }

    rec.onerror = (ev) => {
      if (ev.error === 'aborted' || settledRef.current) return
      if (ev.error === 'not-allowed') {
        failHard(micDeniedMessage())
        return
      }
      if (ev.error === 'no-speech') {
        finishWithTranscript(pendingRef.current)
        return
      }
      if (ev.error === 'language-not-supported') {
        const alt = nextLang(lang)
        if (alt) {
          setVoiceLang(alt)
          failHard(
            `這個瀏覽器不支援目前語言，已改用${langLabel(alt)}。請再按「再試一次」。沒有記入分數。`,
          )
          return
        }
      }
      if (ev.error === 'network' || ev.error === 'service-not-allowed') {
        if (pendingRef.current.trim()) {
          finishWithTranscript(pendingRef.current)
          return
        }
        failHard('語音服務未能連線（要上網）。沒有記入分數。請再用 + / − 手動記。')
        return
      }
      if (pendingRef.current.trim()) {
        finishWithTranscript(pendingRef.current)
        return
      }
      failHard('語音沒認到。沒有記入分數。請按「再試一次」，或用 + / −、點擊桿數手動記。')
    }

    rec.onend = () => {
      if (recogRef.current !== rec) return
      recogRef.current = null
      if (settledRef.current) return
      finishWithTranscript(pendingRef.current)
    }
  }

  function startEngine() {
    const Ctor = getSpeechCtor()
    if (!Ctor) {
      failHard(supportMessage('unsupported'))
      return
    }
    try {
      const rec = new Ctor()
      rec.lang = lang
      rec.continuous = false
      rec.interimResults = true
      rec.maxAlternatives = 5
      wireRecognition(rec)
      recogRef.current = rec
      rec.start()
    } catch (e) {
      const name = e instanceof DOMException ? e.name : ''
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        failHard(micDeniedMessage())
      } else {
        failHard('無法開始聆聽。沒有記入分數。請再試，或用 + / − 手動記。')
      }
    }
  }

  function startCountdown() {
    clearTimers()
    clockStopRef.current = openListenClock(
      (left) => {
        setSecondsLeft(Math.ceil(left / 1000))
        setProgress(left / LISTEN_MS)
      },
      () => requestFinish(),
    )
  }

  function startListen() {
    if (!supported) {
      setResult({ ok: false, heard: '', message: supportMessage(support) })
      return
    }
    settledRef.current = false
    pendingRef.current = ''
    setResult(null)
    setDraft(null)
    setEditing(false)
    setInterim('')
    setListening(true)
    setProgress(1)
    setSecondsLeft(Math.ceil(LISTEN_MS / 1000))
    startCountdown()
    startEngine()
  }

  function dismissDraft() {
    setDraft(null)
    setEditing(false)
    setResult({ ok: false, heard: '', message: '已取消，沒有記入分數。' })
  }

  function confirmDraft() {
    if (!draft || confirmLockRef.current) return
    confirmLockRef.current = true
    const res = commitVoicePreview(
      draft,
      draft.kind === 'score' ? editStrokes : undefined,
    )
    confirmLockRef.current = false
    setDraft(null)
    setEditing(false)
    setResult(res)
  }

  if (!supported) {
    return (
      <section className="rounded-2xl border border-warn/40 bg-warn-bg p-3">
        <p className="text-sm font-semibold text-warn">
          此瀏覽器不支援語音，請用按鈕記分
        </p>
        <p className="mt-1 text-sm text-muted">{supportMessage(support)}</p>
      </section>
    )
  }

  const showRetry = !!(
    result &&
    !result.ok &&
    !listening &&
    !draft &&
    !result.message.startsWith('已取消')
  )
  const cancelled = !!result?.message.startsWith('已取消')
  const scoreSummary =
    draft?.kind === 'score'
      ? formatScoreSummary(
          draft.playerName,
          draft.holeNo,
          draft.par,
          editStrokes,
        )
      : ''

  return (
    <section
      aria-label="語音記分"
      className="rounded-2xl border border-line bg-elevated/70 p-3"
    >
      <p className="text-sm font-medium text-muted">
        語音記分 <span className="text-xs font-normal">選用</span>
      </p>
      <p className="mt-1 text-xs text-muted">
        說完會先顯示「即將記入」，確認後才寫入。+ / − 隨時可用。
      </p>
      <p className="mt-2 text-sm">
        而家記：
        <span className="font-semibold text-accent">{currentPlayerName}</span>
        <span className="text-muted">（點球員可改）</span>
      </p>
      <p className="mt-1 text-xs text-muted">
        可說：「柏忌」「帕」「小鳥」「老鷹」「四桿」「加一桿」「bogey」「par」「plus
        one」
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {LANGS.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled={listening}
            onClick={() => setVoiceLang(item.id)}
            className={cn(
              'min-h-10 rounded-full px-3 text-sm disabled:opacity-40',
              lang === item.id
                ? 'bg-accent text-accent-ink'
                : 'bg-elevated text-muted',
            )}
          >
            {item.label}
          </button>
        ))}
      </div>

      {listening ? (
        <div
          role="status"
          aria-live="polite"
          className="mt-3 rounded-2xl border-2 border-accent bg-card p-3"
        >
          <p className="flex items-center justify-center gap-2 text-xl font-semibold text-accent">
            <span
              className="inline-block size-3 animate-pulse rounded-full bg-accent"
              aria-hidden
            />
            正在聽
          </p>
          <p className="mt-1 text-center text-sm text-muted">
            剩餘 {secondsLeft} 秒 · 說完一句就停
          </p>
          <div
            className="mt-2 h-2 overflow-hidden rounded-full bg-line"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(progress * 100)}
            aria-label="聆聽剩餘時間"
          >
            <div
              className="h-full bg-accent"
              style={{ width: `${Math.max(0, Math.min(100, progress * 100))}%` }}
            />
          </div>
          <p className="mt-3 min-h-8 text-center text-lg font-medium break-words">
            {interim || '請說桿數或柏忌、帕、小鳥…'}
          </p>
          <Button
            variant="lime"
            size="xl"
            className="mt-3 w-full"
            aria-label="結束聆聽"
            onClick={requestFinish}
          >
            結束
          </Button>
          <Button
            variant="danger"
            size="xl"
            className="mt-2 w-full"
            aria-label="取消聆聽"
            onClick={cancelListen}
          >
            取消
          </Button>
        </div>
      ) : null}

      {!listening && !draft ? (
        <button
          type="button"
          onClick={startListen}
          className="mt-2 flex min-h-14 w-full select-none flex-col items-center justify-center rounded-2xl border border-line bg-card text-base font-medium text-fg"
        >
          點一下開始聽
          <span className="mt-0.5 text-xs font-normal text-muted">
            最長 {Math.round(LISTEN_MS / 1000)} 秒 · 辨識到就停 · 確認後才記入
          </span>
        </button>
      ) : null}

      {draft ? (
        <div
          role="dialog"
          aria-modal="false"
          aria-labelledby="voice-confirm-title"
          className="mt-3 rounded-2xl border-2 border-accent bg-card p-3"
        >
          <p
            id="voice-confirm-title"
            className="text-lg font-semibold leading-snug break-words"
          >
            {draft.kind === 'score'
              ? `即將記入：${scoreSummary}`
              : `即將前往：${draft.summary}`}
          </p>
          <p className="mt-1 text-sm text-muted break-words">
            聽到：「{draft.heard}」
          </p>
          {draft.kind === 'score' && editing ? (
            <div className="mt-3 flex items-center justify-center gap-3">
              <button
                type="button"
                aria-label="減少桿數"
                onClick={() => setEditStrokes((n) => Math.max(1, n - 1))}
                className="flex size-14 items-center justify-center rounded-2xl border border-line bg-elevated text-2xl font-semibold"
              >
                −
              </button>
              <p className="tabular min-w-12 text-center text-4xl font-bold">
                {editStrokes}
              </p>
              <button
                type="button"
                aria-label="增加桿數"
                onClick={() => setEditStrokes((n) => Math.min(15, n + 1))}
                className="flex size-14 items-center justify-center rounded-2xl border border-line bg-elevated text-2xl font-semibold"
              >
                +
              </button>
            </div>
          ) : null}
          <div
            className={cn(
              'mt-3 grid gap-2',
              draft.kind === 'score' ? 'grid-cols-3' : 'grid-cols-2',
            )}
          >
            <button
              type="button"
              onClick={confirmDraft}
              className="min-h-14 rounded-2xl bg-accent text-base font-semibold text-accent-ink"
            >
              確認
            </button>
            {draft.kind === 'score' ? (
              <button
                type="button"
                aria-expanded={editing}
                onClick={() => setEditing(true)}
                className="min-h-14 rounded-2xl border border-line bg-elevated text-base font-semibold"
              >
                修改
              </button>
            ) : null}
            <button
              type="button"
              aria-label="取消記入"
              onClick={dismissDraft}
              className="min-h-14 rounded-2xl bg-danger text-base font-semibold text-danger-ink"
            >
              取消
            </button>
          </div>
        </div>
      ) : null}

      {!listening && !draft && result ? (
        <div
          className={cn(
            'mt-2 min-h-16 rounded-2xl px-3 py-3',
            result.ok
              ? 'bg-card text-under'
              : cancelled
                ? 'bg-card text-muted'
                : 'bg-warn-bg text-warn',
          )}
          aria-live="assertive"
        >
          {result.heard ? (
            <p className="text-base font-semibold leading-snug break-words text-fg">
              聽到：「{result.heard}」
            </p>
          ) : null}
          {result.ok && result.applied ? (
            <p className="text-lg font-semibold leading-snug text-accent">
              已記入：{result.applied}
            </p>
          ) : (
            <p className={cn('text-sm leading-relaxed', result.heard && 'mt-1')}>
              {result.message}
            </p>
          )}
          {showRetry ? (
            <button
              type="button"
              onClick={startListen}
              className="mt-3 min-h-12 w-full rounded-2xl bg-accent text-base font-semibold text-accent-ink"
            >
              再試一次
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
