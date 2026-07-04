// DEWA UI migration — headless route SMOKE TEST (Phase 4).
// Visits every route, admin-unlocks, collects console errors + uncaught pageerrors
// + blank-page detection, and screenshots the hero pages. A green `npm run build`
// does NOT catch React runtime crashes — this does.
//
// Setup:  the app must have Playwright installed (npm i -D playwright) and a dev
//         server running in fixtures mode:  VITE_USE_FIXTURES=1 npm run dev -- --port 3899
//         Run this FROM INSIDE the app dir so `import 'playwright'` resolves:
//           cp <skill>/assets/smoke.mjs ./_smoke.mjs && node _smoke.mjs && rm _smoke.mjs
//
// Configure BASE, ROUTES, ADMIN_PW, and HERO (screenshot targets) below.
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'

const BASE = process.env.SMOKE_BASE || 'http://localhost:3899'
const ADMIN_PW = process.env.SMOKE_ADMIN_PW || 'admin' // fixtures demo password
const SHOTS = process.env.SMOKE_SHOTS || '/tmp/dewa-migration-smoke'
// Every hash route in the app (no leading '#/'):
const ROUTES = (process.env.SMOKE_ROUTES || 'ranking,leaderboard,executive,productivity,architecture,progress,vibe-code,journey,profile,settings').split(',')
const HERO = new Set((process.env.SMOKE_HERO || 'ranking').split(',')) // which routes to screenshot
// Admin-unlock flow — override for your app's auth (defaults = the leaderboard's Welcome gate).
const UNLOCK_ROUTE = process.env.SMOKE_UNLOCK_ROUTE || 'welcome'       // hash route of the unlock UI
const UNLOCK_TRIGGER = process.env.SMOKE_UNLOCK_TRIGGER || 'admin access' // text that opens the password field
const UNLOCK_BUTTON = process.env.SMOKE_UNLOCK_BUTTON || 'Unlock'      // submit button label
mkdirSync(SHOTS, { recursive: true })

const browser = await chromium.launch()
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage()
const errorsByRoute = {}
let current = 'boot'
const push = (m) => { (errorsByRoute[current] ??= []).push(m) }
page.on('console', (m) => { if (m.type() === 'error') push('console: ' + m.text().slice(0, 300)) })
page.on('pageerror', (e) => push('PAGEERROR: ' + (e.message || String(e)).split('\n')[0].slice(0, 300)))

// Admin unlock so admin-only routes actually render (else they redirect and go
// untested). Override the selectors via SMOKE_UNLOCK_* for your app's auth.
let unlocked = false
current = UNLOCK_ROUTE
await page.goto(`${BASE}/#/${UNLOCK_ROUTE}`, { waitUntil: 'networkidle' }).catch(() => {})
await page.waitForTimeout(600)
try {
  await page.getByText(new RegExp(UNLOCK_TRIGGER, 'i')).first().click({ timeout: 4000 })
  await page.waitForTimeout(300)
  await page.locator('input[type=password]').first().fill(ADMIN_PW)
  const btn = page.getByRole('button', { name: new RegExp(`^\\s*${UNLOCK_BUTTON}\\s*$`) }).first()
  if (await btn.count()) await btn.click().catch(() => {})
  else await page.locator('input[type=password]').first().press('Enter')
  await page.waitForTimeout(900)
  unlocked = true
  console.log('admin unlock: done')
} catch (e) { console.log('admin unlock: FAILED —', e.message.split('\n')[0].slice(0, 100)) }
if (!unlocked) console.log('⚠️  WARNING: admin NOT unlocked — admin-only routes below likely redirected and were NOT tested. Fix SMOKE_UNLOCK_* or the auth flow before trusting this run.')

for (const r of ROUTES) {
  current = r
  try {
    await page.goto(`${BASE}/#/${r}`, { waitUntil: 'networkidle', timeout: 15000 })
    await page.waitForTimeout(700)
    const txt = (await page.locator('body').innerText().catch(() => '')).trim()
    if (txt.length < 20) push('BLANK/near-empty page (len ' + txt.length + ')')
    if (HERO.has(r)) await page.screenshot({ path: `${SHOTS}/${r.replace(/\//g, '_')}.png` })
  } catch (e) { push('NAV FAIL: ' + e.message.split('\n')[0].slice(0, 160)) }
}
await browser.close()

const withIssues = Object.entries(errorsByRoute).filter(([, v]) => v.length)
console.log('\n===== SMOKE RESULT =====')
console.log(`routes tested: ${ROUTES.length}, routes with issues: ${withIssues.length}, shots: ${SHOTS}`)
for (const [r, errs] of withIssues) {
  console.log(`\n[${r}]`)
  for (const e of [...new Set(errs)].slice(0, 6)) console.log('  - ' + e)
}
if (!withIssues.length) console.log('\nNo console/runtime errors on any route ✓')
// NOTE: 401s on admin API endpoints are EXPECTED in fixtures/dev (no backend) — not crashes.
// PAGEERROR / "styleq: … typeof undefined" / BLANK = real bugs to fix.
