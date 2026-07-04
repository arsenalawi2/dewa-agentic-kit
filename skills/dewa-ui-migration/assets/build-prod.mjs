// DEWA UI migration — PII-safe production build (Phase 5).
//
// Real dev-fixtures (sample per-user data) are never LOADED in prod (the resource
// layer should gate the fallback on `import.meta.env.DEV || VITE_USE_FIXTURES`),
// but Rolldown/Vite still BUNDLES the dynamic-import chunks — so the real data
// would sit in downloadable JS. This blanks the fixtures on disk for the build,
// then restores them (local dev keeps real fixtures).
//
// GENERIC: run this FROM YOUR APP ROOT (`cd <app> && node scripts/build-prod.mjs`),
// or copy it to <app>/scripts/. It resolves the app root from process.cwd().
// Point FIXTURES_DIR at wherever your app stores its bundled sample data.
import { readdirSync, readFileSync, writeFileSync, copyFileSync, mkdirSync, rmSync, existsSync } from 'fs'
import { execSync } from 'child_process'
import { join } from 'path'

const root = process.cwd()
const FX = join(root, process.env.FIXTURES_DIR || 'src/dev-fixtures') + '/'
const BUILD_CMD = process.env.BUILD_CMD || 'npx vite build'
const BAK = '/tmp/astryx-fixtures-real-bak/'

if (!existsSync(FX)) {
  console.warn(`[build-prod] fixtures dir not found: ${FX}\n` +
    `  Set FIXTURES_DIR to your app's bundled-sample-data folder, or verify your\n` +
    `  prod bundle carries no real data another way. Building without blanking.`)
  execSync(BUILD_CMD, { stdio: 'inherit', cwd: root })
  process.exit(0)
}

const files = readdirSync(FX).filter((f) => f.endsWith('.json'))
mkdirSync(BAK, { recursive: true })
console.log(`[build-prod] blanking ${files.length} fixtures in ${FX} for the build…`)
for (const f of files) {
  copyFileSync(FX + f, BAK + f)
  let blank = '{}'
  try { blank = Array.isArray(JSON.parse(readFileSync(FX + f, 'utf8'))) ? '[]' : '{}' } catch { /* keep {} */ }
  writeFileSync(FX + f, blank)
}
try {
  execSync(BUILD_CMD, { stdio: 'inherit', cwd: root })
} finally {
  for (const f of files) copyFileSync(BAK + f, FX + f) // restore real fixtures for dev
  rmSync(BAK, { recursive: true, force: true })
  console.log('[build-prod] fixtures restored to real for local dev')
}
