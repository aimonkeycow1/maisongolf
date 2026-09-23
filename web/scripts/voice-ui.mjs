import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const BASE = process.env.SMOKE_URL || 'http://127.0.0.1:4173'
const outDir = '/opt/cursor/artifacts/screenshots'
mkdirSync(outDir, { recursive: true })

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  locale: 'zh-HK',
})

await context.addInitScript(() => {
  class FakeSpeechRecognition {
    constructor() {
      this.lang = 'zh-HK'
      this.continuous = false
      this.interimResults = true
      this.maxAlternatives = 1
      this.onresult = null
      this.onerror = null
      this.onend = null
      this._timers = []
    }

    start() {
      const mode = window.__speechMode || 'hold'
      const rec = this
      const fire = (isFinal, alts) => {
        const row = { isFinal, length: alts.length }
        alts.forEach((alt, index) => {
          row[index] = alt
        })
        rec.onresult?.({ resultIndex: 0, results: [row] })
      }
      const later = (ms, fn) => {
        this._timers.push(setTimeout(fn, ms))
      }
      if (mode === 'hold') {
        later(120, () => {
          fire(false, [{ transcript: '柏忌', confidence: 0.4 }])
        })
        return
      }
      if (mode === 'alts') {
        later(100, () => {
          fire(true, [
            { transcript: '八季', confidence: 0.96 },
            { transcript: '柏忌', confidence: 0.41 },
          ])
          rec.onend?.()
        })
        return
      }
      if (mode === 'bogey') {
        later(100, () => {
          fire(true, [{ transcript: '柏忌', confidence: 0.9 }])
          rec.onend?.()
        })
        return
      }
      if (mode === 'garbage') {
        later(80, () => {
          fire(true, [{ transcript: '今天天氣很好', confidence: 0.9 }])
          rec.onend?.()
        })
        return
      }
      if (mode === 'four') {
        later(80, () => {
          fire(true, [{ transcript: '四桿', confidence: 0.92 }])
          rec.onend?.()
        })
      }
    }

    stop() {
      this.onend?.()
    }

    abort() {
      this._timers.forEach((id) => clearTimeout(id))
      this.onend?.()
    }
  }

  window.SpeechRecognition = FakeSpeechRecognition
  window.webkitSpeechRecognition = FakeSpeechRecognition
})

const page = await context.newPage()

function check(cond, message) {
  if (!cond) throw new Error(message)
}

async function shot(name) {
  const region = page.getByRole('region', { name: '語音記分' })
  await region.scrollIntoViewIfNeeded()
  await region.screenshot({ path: `${outDir}/${name}.png` })
  console.log('shot', name)
}

async function readStrokes() {
  const text = await page.getByRole('button', { name: /點此/ }).innerText()
  const line = text
    .split('\n')
    .map((s) => s.trim())
    .find(Boolean)
  if (!line || line === '—' || line === '-') return null
  const n = Number(line)
  if (!Number.isFinite(n)) throw new Error(`unreadable strokes: ${text}`)
  return n
}

async function setMode(mode) {
  await page.evaluate((next) => {
    window.__speechMode = next
  }, mode)
}

try {
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.clear())
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      const req = indexedDB.deleteDatabase('golf-scorekeeper')
      req.onsuccess = () => resolve(null)
      req.onerror = () => resolve(null)
      req.onblocked = () => resolve(null)
    })
  })
  await page.reload({ waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: '球場計分' }).waitFor({ timeout: 10000 })
  await page.getByRole('button', { name: '開始新一輪' }).click()
  await page.getByRole('heading', { name: '新一輪' }).waitFor()
  await page.getByRole('button', { name: '選用' }).first().click()
  await page.getByRole('button', { name: '9 洞' }).click()
  await page.getByPlaceholder('球員1 姓名').fill('測試員')
  await page.getByRole('button', { name: '開始計分' }).click()
  await page.getByText('HOLE').waitFor()
  await page.getByRole('region', { name: '語音記分' }).waitFor()
  await page.getByText('最長 6 秒').waitFor()
  check((await page.getByText('14 秒').count()) === 0, 'UI still says 14 seconds')

  const parLine = await page.locator('p', { hasText: '標準桿' }).first().innerText()
  const parMatch = parLine.match(/標準桿\s*(\d+)/)
  check(parMatch, `missing par: ${parLine}`)
  const par = Number(parMatch[1])
  const bogey = par + 1
  console.log('par', par, 'bogey', bogey)
  check((await readStrokes()) == null, 'score should start empty')

  await setMode('hold')
  const stopStarted = Date.now()
  await page.getByRole('button', { name: '點一下開始聽' }).click()
  await page.getByRole('status').getByText('正在聽').waitFor()
  await page.getByRole('button', { name: '結束聆聽' }).waitFor()
  await page.getByRole('button', { name: '取消聆聽' }).waitFor()
  await page.getByRole('status').getByText('柏忌', { exact: true }).waitFor()
  const appeared = Date.now() - stopStarted
  check(appeared < 3000, `listening UI slow to appear: ${appeared}ms`)
  await shot('voice-listening')
  await page.getByRole('button', { name: '取消聆聽' }).click()
  const cancelledAt = Date.now() - stopStarted
  check(cancelledAt < 4000, `cancel still waiting: ${cancelledAt}ms`)
  await page.getByText('已取消，沒有記入分數。').waitFor()
  check((await readStrokes()) == null, 'cancel wrote a score')
  console.log('cancel_ms', cancelledAt)

  await setMode('alts')
  const altStarted = Date.now()
  await page.getByRole('button', { name: '點一下開始聽' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.waitFor()
  const altMs = Date.now() - altStarted
  check(altMs < 2500, `confirm waited too long: ${altMs}ms`)
  const chip = await dialog.innerText()
  check(chip.includes('即將記入：'), chip)
  check(chip.includes('柏忌'), chip)
  check(chip.includes(`${bogey}桿`), chip)
  check(!chip.includes('八季'), `used the unparsed alternative: ${chip}`)
  check((await readStrokes()) == null, 'confirm chip wrote before tap')
  await shot('voice-confirm')
  await page.getByRole('button', { name: '取消記入' }).click()
  await page.getByText('已取消，沒有記入分數。').waitFor()
  check((await readStrokes()) == null, 'dismiss wrote a score')
  console.log('confirm_ms', altMs)

  await setMode('bogey')
  await page.getByRole('button', { name: '點一下開始聽' }).click()
  await dialog.waitFor()
  await page.getByRole('button', { name: '確認' }).click()
  await page.getByText(`已記入：`).waitFor()
  check((await readStrokes()) === bogey, `confirmed score ${await readStrokes()} !== ${bogey}`)

  await setMode('garbage')
  const beforeGarbage = await readStrokes()
  await page.getByRole('button', { name: '點一下開始聽' }).click()
  await page.getByText('沒聽懂').waitFor()
  await page.getByText('手動記').waitFor()
  const failure = await page.getByRole('region', { name: '語音記分' }).innerText()
  check(failure.includes('沒有記入分數'), failure)
  check((await readStrokes()) === beforeGarbage, 'garbage changed the score')
  await shot('voice-failure')

  await setMode('four')
  await page.getByRole('button', { name: '點一下開始聽' }).click()
  await dialog.waitFor()
  check((await readStrokes()) === beforeGarbage, 'four wrote before confirm')
  await page.getByRole('button', { name: '修改' }).click()
  await page.getByRole('button', { name: '增加桿數' }).click()
  await page.getByRole('button', { name: '確認' }).click()
  check((await readStrokes()) === 5, `edited score ${await readStrokes()} !== 5`)

  console.log('VOICE_UI_OK')
} catch (err) {
  console.error('VOICE_UI_FAIL', err)
  await page.screenshot({
    path: `${outDir}/voice-ui-failure.png`,
    fullPage: true,
  }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}
