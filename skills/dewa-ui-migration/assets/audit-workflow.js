// DEWA UI migration — AUDIT workflow (Phase 1).
// Fans out one gap-finder per unit, then adversarially verifies each gap, then a
// completeness critic. Reusable across any migration — everything comes from `args`.
//
// Invoke:  Workflow({ scriptPath: '<skill>/assets/audit-workflow.js', args })
// args = {
//   OLD: '/abs/path/old-app/src',            // the UI migrated FROM (reference)
//   NEW: '/abs/path/new-app/src',            // the React/Astryx app (served files)
//   pages: [ { name, oldFile, newFile, hint? }, ... ],   // one per served route
//   crosscuts: [ { name, oldFile, newFile, hint } ]      // optional: routes/nav, data-layer, charts
// }
export const meta = {
  name: 'dewa-ui-migration-audit',
  description: 'Audit an old UI vs its React/Astryx migration for dropped/broken features',
  phases: [
    { title: 'Audit', detail: 'per-unit gap analysis: old vs served new' },
    { title: 'Verify', detail: 'adversarially confirm each gap against the whole new codebase' },
    { title: 'Critic', detail: 'completeness pass — whole classes the per-unit audit missed' },
  ],
}

const { OLD, NEW, pages = [], crosscuts = [] } = args || {}
if (!OLD || !NEW || !pages.length) throw new Error('args must include OLD, NEW, and pages[]')
const units = [...pages.map((p) => ({ ...p, kind: 'page' })), ...crosscuts.map((c) => ({ ...c, kind: 'crosscut' }))]

const GAP_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['unit', 'parity', 'gaps'],
  properties: {
    unit: { type: 'string' },
    parity: { type: 'string', description: '1-2 sentence overall parity verdict' },
    gaps: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      required: ['title', 'category', 'severity', 'status', 'oldEvidence', 'newEvidence'],
      properties: {
        title: { type: 'string' },
        category: { type: 'string', enum: ['filter/control', 'data/metric', 'visualization/chart', 'table/column', 'interaction', 'navigation/route', 'content', 'auth/visibility', 'empty/loading-state', 'other'] },
        severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        status: { type: 'string', enum: ['missing', 'dead-stub', 'changed', 'moved-elsewhere'] },
        oldEvidence: { type: 'string' }, newEvidence: { type: 'string' },
      },
    } },
  },
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['title', 'verdict', 'severity', 'evidence', 'fixHint'],
  properties: {
    title: { type: 'string' },
    verdict: { type: 'string', enum: ['confirmed_gap', 'dead_stub_confirmed', 'false_positive', 'present_elsewhere', 'intentional_by_design', 'uncertain'] },
    severity: { type: 'string', enum: ['high', 'medium', 'low'] },
    evidence: { type: 'string' }, fixHint: { type: 'string' },
  },
}

phase('Audit')
const results = await pipeline(
  units,
  (u) => agent(
    `You are auditing a UI migration for DROPPED / BROKEN / degraded features. Find what the OLD app did that the NEW served file does NOT (or does non-functionally).\n\n` +
    `UNIT: ${u.name} (${u.kind})\nOLD: ${u.oldFile}\nNEW (served): ${u.newFile}\n` + (u.hint ? `HINT: ${u.hint}\n` : '') +
    `\nHOW: (1) Read the OLD file(s); follow its imports under ${OLD} — enumerate every filter, toggle, period/month picker, search, sort, CSV/export, tab, per-row action, drawer/modal, tooltip, KPI, table column, chart, empty/loading/error state, auto-refresh, and WHO can see it. (2) Read the NEW served file; follow its imports under ${NEW}. (3) GREP THE WHOLE NEW src (${NEW}) — a feature may have moved to a shared component/hook; only call it a gap if truly absent OR present-but-non-functional. DEAD-STUB = a control whose state is set but never read, or a button with no handler. Report ONLY real regressions with file:line evidence on BOTH sides. Empty gaps array if parity is complete.`,
    { label: `audit:${u.name}`.slice(0, 48), phase: 'Audit', schema: GAP_SCHEMA },
  ),
  async (gapResult, u) => {
    if (!gapResult) return null
    const toVerify = (gapResult.gaps || []).filter((g) => g.severity !== 'low').slice(0, 12)
    const verdicts = await parallel(toVerify.map((g) => () =>
      agent(
        `Adversarially verify a claimed migration gap. Try to REFUTE it.\nCLAIM (unit "${gapResult.unit}"): "${g.title}" — ${g.status}. Old: ${g.oldEvidence}. New: ${g.newEvidence}.\n` +
        `Search the ENTIRE new app at ${NEW} (all variant folders + components/hooks/lib/utils). Is it present+functional somewhere → present_elsewhere/false_positive. Present but non-functional → dead_stub_confirmed. Genuinely absent → confirmed_gap. Clearly intentional (admin-only page correctly hidden, dev-only tool) → intentional_by_design. Default confirmed_gap ONLY after searching. Give exact paths checked + a one-line fix hint.`,
        { label: `verify:${g.title}`.slice(0, 48), phase: 'Verify', schema: VERDICT_SCHEMA },
      ).then((v) => (v ? { ...v, unit: gapResult.unit, category: g.category } : null)),
    ))
    const lows = (gapResult.gaps || []).filter((g) => g.severity === 'low')
      .map((g) => ({ title: g.title, unit: gapResult.unit, verdict: 'unverified_low', severity: 'low', evidence: g.newEvidence, fixHint: '' }))
    return { unit: gapResult.unit, parity: gapResult.parity, verdicts: [...verdicts.filter(Boolean), ...lows] }
  },
)

const clean = results.filter(Boolean)
const allVerdicts = clean.flatMap((r) => (r.verdicts || []).map((v) => ({ ...v, unit: v.unit || r.unit })))
const confirmed = allVerdicts.filter((v) => v.verdict === 'confirmed_gap' || v.verdict === 'dead_stub_confirmed')
log(`Audit: ${units.length} units, ${allVerdicts.length} candidate gaps, ${confirmed.length} confirmed`)

phase('Critic')
const critic = await agent(
  `Completeness critic for a UI migration audit. Units covered: ${units.map((u) => u.name).join(', ')}.\n` +
  `Confirmed gaps: ${confirmed.map((v) => v.title + ' @ ' + v.unit).join(' | ') || '(none)'}.\nOLD: ${OLD}  NEW: ${NEW}.\n` +
  `Find whole CLASSES the per-unit pass missed: old routes with no new equivalent; global/cross-page controls (theme toggle, search, analytics, admin unlock, print/export) that vanished; app-shell/footer/nav features; auth-guard behavior changes; any new page that is a near-empty placeholder. Grep/Read as needed. Return a concise list with evidence + overall completeness note.`,
  { label: 'completeness-critic', phase: 'Critic' },
)

return {
  unitsAudited: units.length,
  perUnit: clean.map((r) => ({ unit: r.unit, parity: r.parity, gapCount: (r.verdicts || []).length })),
  confirmed,
  presentElsewhere: allVerdicts.filter((v) => v.verdict === 'present_elsewhere' || v.verdict === 'false_positive'),
  intentional: allVerdicts.filter((v) => v.verdict === 'intentional_by_design'),
  criticNotes: critic,
}
