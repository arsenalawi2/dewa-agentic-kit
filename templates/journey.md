# Journey Page — journey-data.json

Every DAK project ships a `/journey` page (`frontend/src/views/Journey.vue`) that
renders `public/journey-data.json` — the narrative story of the project. You
(Claude Code) keep that JSON current after significant work; the page renders
whatever's there. You don't build the page — it ships in the template; you only
keep the data honest. Validate with `npm run validate:journey` before calling
journey work done.

## Schema (unified, `schema_version` 1)

`phases` is the **required spine** — always at least one, one per meaningful
milestone. The rich blocks (`hero_stats`, `challenge`, `features`, `tech_stats`)
are optional headline polish — add them only when you have real, verifiable
numbers.

```json
{
  "schema_version": 1,
  "project_name": "My Project",
  "tagline": "One-line description of what this project does and why it matters.",
  "updated_at": "2026-06-14T00:00:00Z",
  "hero_stats": [
    { "value": "113K+", "label": "items tracked" },
    { "value": "8", "label": "AI domains" }
  ],
  "phases": [
    { "number": 1, "title": "Project scaffolded", "body": "What happened in this phase, in 1-3 sentences." }
  ],
  "challenge": {
    "title": "The problem",
    "description": "2-3 sentences about the pain point this solves.",
    "stats": [ { "value": "100+", "label": "daily updates to track" } ]
  },
  "features": [
    { "title": "Feature name", "description": "What it does in 1-2 sentences." }
  ],
  "tech_stats": { "api_endpoints": 34, "database_tables": 12 }
}
```

| Field | Required | Shape | Renders as |
|---|---|---|---|
| `schema_version` | yes | int (`1`) | — |
| `project_name` | yes | string | page title |
| `tagline` | yes | string | sub-title |
| `updated_at` | yes | ISO 8601 | "Last updated" footer |
| `phases` | yes | `[{number, title, body}]` | the timeline (the spine) |
| `hero_stats` | no | `[{value, label}]` | headline stat row |
| `challenge` | no | `{title, description, stats?}` | "the problem" block |
| `features` | no | `[{title, description}]` | feature grid |
| `tech_stats` | no | `{label: number}` | "by the numbers" |

Keys outside this contract (e.g. a legacy `how_it_works` or `stack`) are ignored
by the renderer — don't add them. Tech-stack detail lives in `/architecture`.

## Rules for keeping journey-data.json current
- **`phases` is the spine** — tell the chronological story; append a phase after
  significant work (don't overwrite earlier ones).
- **Bump `updated_at`** (ISO 8601) every time you edit the file.
- **Every stat must be real and verifiable** from the code — no vanity numbers.
- Write in active voice, present tense; lead with impact, not implementation.
- Generate from PROJECT.md, the code, and what was built this session.
- Run `npm run validate:journey` — part of the finish-line checklist for journey
  work.

The page uses the EZ design system (Inter / `var(--font-display)`, warm
neutrals, borders over shadows) — consistent with the other three auto-pages.
