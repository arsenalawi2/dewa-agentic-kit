#!/usr/bin/env node
// Validate public/journey-data.json against the unified journey schema.
// Run: npm run validate:journey   (part of the finish-line checklist for
// journey work). Dependency-free.
//
// ERRORS (exit 1) catch things the page would render WRONG — malformed JSON or
// a present field with the wrong shape. WARNINGS (exit 0) flag missing
// recommended fields, matching the renderer's tolerance (it falls back on /
// hides absent sections rather than breaking). So an old {phases}-only file
// passes with suggestions, exactly as Journey.vue renders it.
import { readFileSync } from "node:fs"

const PATH = new URL("../public/journey-data.json", import.meta.url)
const errs = []
const warns = []
const isStr = (v) => typeof v === "string" && v.trim().length > 0
const isObj = (v) => v && typeof v === "object" && !Array.isArray(v)
const isStat = (s) => isObj(s) && s.value != null && isStr(s.label)

let data
try {
  data = JSON.parse(readFileSync(PATH, "utf8"))
} catch (e) {
  console.error(`journey-data.json: not valid JSON — ${e.message}`)
  process.exit(1)
}
if (!isObj(data)) {
  console.error("journey-data.json: top level must be an object")
  process.exit(1)
}

// Recommended fields — warn if absent (the renderer tolerates them), error only
// if present-but-malformed.
if (data.schema_version === undefined) warns.push("schema_version missing (recommend 1)")
else if (!Number.isInteger(data.schema_version)) errs.push("schema_version must be an integer")
if (!isStr(data.project_name)) warns.push("project_name missing — page falls back to a generic title")
if (!isStr(data.tagline)) warns.push("tagline missing")
if (data.updated_at === undefined) warns.push("updated_at missing — bump it whenever you edit the journey")
else if (Number.isNaN(new Date(data.updated_at).getTime())) errs.push("updated_at must be a valid ISO 8601 date")

// phases — the spine. Warn if absent/empty; error if present-but-malformed.
if (data.phases === undefined || (Array.isArray(data.phases) && data.phases.length === 0)) {
  warns.push("phases is empty — add the timeline (the journey's spine)")
} else if (!Array.isArray(data.phases)) {
  errs.push("phases must be an array")
} else {
  data.phases.forEach((p, i) => {
    if (!isObj(p)) return errs.push(`phases[${i}] must be an object`)
    if (!Number.isInteger(p.number)) errs.push(`phases[${i}].number must be an integer`)
    if (!isStr(p.title)) errs.push(`phases[${i}].title must be a non-empty string`)
    if (!isStr(p.body)) errs.push(`phases[${i}].body must be a non-empty string`)
  })
}

// Optional rich blocks — shape-checked ONLY when present (every key the renderer reads).
if (data.hero_stats !== undefined) {
  if (!Array.isArray(data.hero_stats)) errs.push("hero_stats must be an array")
  else data.hero_stats.forEach((s, i) => { if (!isStat(s)) errs.push(`hero_stats[${i}] needs {value, label}`) })
}
if (data.features !== undefined) {
  if (!Array.isArray(data.features)) errs.push("features must be an array")
  else data.features.forEach((f, i) => {
    if (!isObj(f) || !isStr(f.title) || !isStr(f.description)) errs.push(`features[${i}] needs {title, description}`)
  })
}
if (data.challenge !== undefined && data.challenge !== null) {
  if (!isObj(data.challenge)) {
    errs.push("challenge must be an object")
  } else {
    if (!isStr(data.challenge.description)) errs.push("challenge.description must be a non-empty string")
    if (data.challenge.stats !== undefined) {
      if (!Array.isArray(data.challenge.stats)) errs.push("challenge.stats must be an array")
      else data.challenge.stats.forEach((s, i) => { if (!isStat(s)) errs.push(`challenge.stats[${i}] needs {value, label}`) })
    }
  }
}
if (data.tech_stats !== undefined && !isObj(data.tech_stats)) {
  errs.push("tech_stats must be a {label: number} object")
}

if (errs.length) {
  console.error("journey-data.json is invalid:")
  for (const e of errs) console.error(`  ✗ ${e}`)
  process.exit(1)
}
if (warns.length) {
  console.warn("journey-data.json is valid, with suggestions:")
  for (const w of warns) console.warn(`  • ${w}`)
} else {
  console.log("journey-data.json ✓ valid")
}
process.exit(0)
