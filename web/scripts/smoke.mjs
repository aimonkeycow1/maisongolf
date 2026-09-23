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
const page = await context.newPage()

async function assertNoVoice(page) {
  const voiceCopy = page.getByText(/語音|麥克風|開始聽/)
  if (await voiceCopy.count()) {
    throw new Error(
      'voice UI still visible: ' + (await voiceCopy.first().textContent()),
    )
  }
  const voiceButton = page.getByRole('button', { name: /語音|麥克風|開始聽|聽緊/ })
  if (await voiceButton.count()) {
    throw new Error('voice button still visible')
  }
}

async function shot(name) {
  await page.screenshot({
    path: `${outDir}/${name}.png`,
    fullPage: true,
  })
  console.log('shot', name)
}

try {
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.clear())
  // Clear IndexedDB so demo seed is deterministic
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
  await assertNoVoice(page)
  await shot('01-home')

  await page.getByRole('button', { name: '成績庫' }).click()
  await page.getByRole('heading', { name: '成績庫' }).waitFor()
  await page.getByText('滘西洲東場').first().waitFor({ timeout: 5000 })
  await page.getByText('示範').first().waitFor()
  await page.getByText('89').first().waitFor()
  await page.getByText('目標總桿（預設 95）').waitFor()
  await shot('02-archive-demo')

  await page.getByText('滘西洲東場').first().click()
  await page.getByRole('heading', { name: '計分卡' }).waitFor()
  await page.getByText('弱項分析').waitFor()
  await page.getByText('GIR 上果嶺率').waitFor()
  await page.getByText('各洞推桿數').waitFor()
  await page.getByText('弱項提示').waitFor()
  await shot('03-scorecard-weak')

  await page.getByRole('button', { name: '回到首頁' }).click()
  await page.getByRole('heading', { name: '球場計分' }).waitFor()

  await page.getByRole('button', { name: '開始新一輪' }).click()
  await page.getByRole('heading', { name: '新一輪' }).waitFor()
  const selectCourse = page.getByRole('button', { name: '選用' }).first()
  await selectCourse.click()
  await page.getByRole('button', { name: '9 洞' }).click()
  await page.getByPlaceholder('球員1 姓名').fill('測試員')
  await shot('04-new-round')
  await page.getByRole('button', { name: '開始計分' }).click()

  await page.getByText('HOLE').waitFor()
  await assertNoVoice(page)
  // Par chip on score row
  await page.getByRole('button', { name: 'Par' }).first().click()
  // Coach: bump putts once
  const puttPlus = page.getByLabel('推桿加')
  if (await puttPlus.count()) await puttPlus.click()
  await shot('05-scoring')

  await page.getByRole('button', { name: '結束本輪' }).click()
  await page.getByRole('button', { name: '結束', exact: true }).click()
  await page.getByRole('heading', { name: '計分卡' }).waitFor({ timeout: 5000 })
  await shot('06-completed-scorecard')

  const before = await page.evaluate(() =>
    localStorage.getItem('golf-scorekeeper-v1'),
  )
  if (!before || !before.includes('"status":"completed"')) {
    throw new Error('completed round not in localStorage')
  }

  await page.goto(`${BASE}/#/archive`, { waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: '成績庫' }).waitFor()
  await page.getByText('測試員').first().waitFor({ timeout: 5000 })
  await page.getByRole('button', { name: '匯出封存' }).waitFor()
  await shot('07-archive-after-reload')

  console.log('SMOKE_OK')
} catch (err) {
  console.error('SMOKE_FAIL', err)
  await shot('99-failure')
  process.exitCode = 1
} finally {
  await browser.close()
}
