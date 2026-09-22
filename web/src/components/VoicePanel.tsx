import { useEffect, useRef, useState } from 'react'
import { cn } from '../lib/cn'
import {
  applyVoiceTranscript,
  setVoiceLang,
} from '../storage/store'
import type { VoiceLang, VoiceResult } from '../types'

const LANGS: Array<{ id: VoiceLang; label: string }> = [
  { id: 'zh-HK', label: '粵語' },
  { id: 'zh-TW', label: '國語' },
  { id: 'zh-CN', label: '普通話' },
  { id: 'en-US', label: 'EN' },
]

const LANG_ORDER: VoiceLang[] = ['zh-HK', 'zh-TW', 'zh-CN', 'en-US']
const LISTEN_MS = 14000

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
  results: ArrayLike<{
    isFinal: boolean
    0?: { transcript?: string }
  }>
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

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

function hasFinal(ev: SpeechRecognitionEventLike): boolean {
  for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
    if (ev.results[i]?.isFinal) return true
  }
  return false
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
  const [interim, setInterim] = useState('')
  const [result, setResult] = useState<VoiceResult | null>(null)
  const [micDenied, setMicDenied] = useState(false)
  const [status, setStatus] = useState('')

  const recogRef = useRef<SpeechRecognitionLike | null>(null)
  const timeoutRef = useRef<number | null>(null)
  const intervalRef = useRef<number | null>(null)
  const wantListenRef = useRef(false)
  const heardSomethingRef = useRef(false)
  const deniedRef = useRef(false)
  const pendingRef = useRef('')
  const appliedRef = useRef(false)
  const langRef = useRef(lang)
  langRef.current = lang

  useEffect(
    () => () => {
      clearTimers()
      recogRef.current?.abort()
    },
    [],
  )

  function clearTimers() {
    if (timeoutRef.current != null) {
      window.clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (intervalRef.current != null) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  function applyTranscript(raw: string) {
    const text = raw.trim()
    if (!text || appliedRef.current) return
    appliedRef.current = true
    heardSomethingRef.current = true
    const res = applyVoiceTranscript(text)
    setInterim('')
    setResult(res)
    setStatus(res.message)
  }

  function stopListening(opts?: { applyPending?: boolean }) {
    wantListenRef.current = false
    clearTimers()
    setListening(false)
    setSecondsLeft(0)
    const rec = recogRef.current
    recogRef.current = null
    try {
      rec?.stop()
    } catch {
      rec?.abort()
    }
    if (opts?.applyPending && !appliedRef.current && pendingRef.current) {
      applyTranscript(pendingRef.current)
    }
  }

  function fail(message: string, heard = '') {
    setResult({
      ok: false,
      heard,
      message,
      applied: heard ? '未記入' : undefined,
    })
    setStatus(message)
  }

  function wireRecognition(rec: SpeechRecognitionLike) {
    rec.onresult = (ev) => {
      let interimText = ''
      let finalText = ''
      for (let i = ev.resultIndex; i < ev.results.length; i += 1) {
        const row = ev.results[i]!
        const transcript = row[0]?.transcript ?? ''
        if (row.isFinal) finalText += transcript
        else interimText += transcript
      }
      if (interimText) {
        const t = interimText.trim()
        setInterim(t)
        pendingRef.current = t
        heardSomethingRef.current = true
      }
      const combined = (finalText || interimText).trim()
      if (combined) pendingRef.current = combined
      if (hasFinal(ev) && combined) {
        applyTranscript(combined)
        stopListening()
      }
    }

    rec.onerror = (ev) => {
      if (ev.error === 'aborted') return
      if (ev.error === 'not-allowed') {
        deniedRef.current = true
        setMicDenied(true)
        fail(micDeniedMessage())
        stopListening()
        return
      }
      if (ev.error === 'no-speech') {
        if (pendingRef.current) {
          applyTranscript(pendingRef.current)
          stopListening()
          return
        }
        fail('沒聽到說話。請靠近手機，再說「抓鳥」或「小明打par了」。')
        stopListening()
        return
      }
      if (ev.error === 'language-not-supported') {
        const alt = nextLang(langRef.current)
        if (alt) {
          setVoiceLang(alt)
          fail(
            `這個瀏覽器不支援目前語言，已改用${langLabel(alt)}。請再按「再試一次」。`,
          )
          stopListening()
          return
        }
      }
      if (ev.error === 'network' || ev.error === 'service-not-allowed') {
        fail('語音服務未能連線（要上網）。請再試，或用 − / + 記分。')
        stopListening()
        return
      }
      if (pendingRef.current) {
        applyTranscript(pendingRef.current)
        stopListening()
        return
      }
      fail('語音沒認到。請按「再試一次」，或用 − / + 記分。')
      stopListening()
    }

    rec.onend = () => {
      recogRef.current = null
      if (wantListenRef.current && !deniedRef.current) {
        startEngine()
        return
      }
      setListening(false)
      if (!appliedRef.current && pendingRef.current) {
        applyTranscript(pendingRef.current)
        return
      }
      if (
        !heardSomethingRef.current &&
        !deniedRef.current &&
        !appliedRef.current
      ) {
        setResult(
          (prev) =>
            prev ?? {
              ok: false,
              heard: '',
              message: '沒聽到。請再按「開始聽」說「抓鳥」或「四桿」。',
            },
        )
        setStatus(
          (prev) =>
            prev || '沒聽到。請再按「開始聽」說「抓鳥」或「四桿」。',
        )
      }
    }
  }

  function startEngine() {
    const Ctor = getSpeechCtor()
    if (!Ctor) {
      fail(supportMessage('unsupported'))
      return
    }
    try {
      const rec = new Ctor()
      rec.lang = langRef.current
      rec.continuous = true
      rec.interimResults = true
      rec.maxAlternatives = 5
      wireRecognition(rec)
      rec.start()
      recogRef.current = rec
    } catch (e) {
      const name = e instanceof DOMException ? e.name : ''
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        deniedRef.current = true
        setMicDenied(true)
        fail(micDeniedMessage())
      } else {
        fail('無法開始聆聽。請再試，或用 − / + 記分。')
      }
      wantListenRef.current = false
      setListening(false)
    }
  }

  function startCountdown() {
    clearTimers()
    const endAt = Date.now() + LISTEN_MS
    setSecondsLeft(Math.ceil(LISTEN_MS / 1000))
    intervalRef.current = window.setInterval(() => {
      setSecondsLeft(Math.max(0, Math.ceil((endAt - Date.now()) / 1000)))
    }, 250)
    timeoutRef.current = window.setTimeout(() => {
      stopListening({ applyPending: true })
    }, LISTEN_MS)
  }

  function toggleListen() {
    if (!supported) {
      fail(supportMessage(support))
      return
    }
    if (listening) {
      stopListening({ applyPending: true })
      return
    }
    deniedRef.current = false
    appliedRef.current = false
    pendingRef.current = ''
    setMicDenied(false)
    setResult(null)
    setInterim('')
    heardSomethingRef.current = false
    wantListenRef.current = true
    setListening(true)
    setStatus('正在聆聽… 請說球員＋抓鳥／par／桿數')
    startCountdown()
    startEngine()
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

  const showRetry = !!(result && !result.ok && !listening)

  return (
    <section className="rounded-2xl border border-line bg-elevated/70 p-3">
      <p className="text-sm font-medium text-muted">
        語音記分 <span className="text-xs font-normal">選用</span>
      </p>
      <p className="mt-1 text-xs text-muted">
        第一次可能會問麥克風。多數情況用上面的 − / + 即可。
      </p>
      <p className="mt-2 text-sm">
        而家記：
        <span className="font-semibold text-accent">{currentPlayerName}</span>
        <span className="text-muted">（點球員可改）</span>
      </p>
      <p className="mt-1 text-xs text-muted">
        可說：「{currentPlayerName}打par了」「{currentPlayerName}
        抓鳥」「小鳥」「四」「4桿」「加一」「減一」
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {LANGS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setVoiceLang(item.id)}
            className={cn(
              'min-h-10 rounded-full px-3 text-sm',
              lang === item.id
                ? 'bg-accent text-accent-ink'
                : 'bg-elevated text-muted',
            )}
          >
            {item.label}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={toggleListen}
        className={cn(
          'mt-2 flex min-h-14 w-full select-none flex-col items-center justify-center rounded-2xl border text-base font-medium',
          listening
            ? 'border-accent bg-accent text-accent-ink'
            : 'border-line bg-card text-fg',
        )}
      >
        {listening
          ? `正在聆聽… 還有 ${secondsLeft || 0} 秒`
          : '點一下開始聽'}
        <span
          className={cn(
            'mt-0.5 text-xs font-normal',
            listening ? 'text-accent-ink/80' : 'text-muted',
          )}
        >
          {listening
            ? '聽到會立刻記入；再點一下停止'
            : '聽 14 秒 · 說完會顯示聽到的字與記入結果'}
        </span>
      </button>
      <div
        className={cn(
          'mt-2 min-h-16 rounded-2xl px-3 py-3',
          result?.ok
            ? 'bg-card text-under'
            : micDenied || showRetry
              ? 'bg-warn-bg text-warn'
              : 'bg-card',
        )}
        aria-live="polite"
      >
        {listening ? (
          <p className="text-lg font-semibold leading-snug text-accent">
            {interim || '請現在說話…'}
          </p>
        ) : null}
        {!listening && result?.heard ? (
          <p className="text-lg font-semibold leading-snug text-fg">
            聽到：{result.heard}
          </p>
        ) : null}
        {!listening && result?.applied ? (
          <p className="mt-1 text-lg font-semibold leading-snug text-accent">
            記入：{result.applied}
          </p>
        ) : null}
        <p className="mt-1 text-sm">
          {status || result?.message || '尚未聽到。說完會顯示結果。'}
        </p>
        {showRetry ? (
          <button
            type="button"
            onClick={toggleListen}
            className="mt-3 min-h-12 w-full rounded-2xl bg-accent text-base font-semibold text-accent-ink"
          >
            再試一次
          </button>
        ) : null}
      </div>
    </section>
  )
}
