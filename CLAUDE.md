# DAK

You are configured with the DAK — an opinionated set of defaults for building production-grade applications with Claude Code.

DAK is designed so any engineer can start any project and get a working, observable, well-organized app in 10 seconds via `dak init <name>`. The kit is the default; deviation requires an explicit reason.

## Tech Stack (read ~/.claude/stack.md for details)

- **Frontend:** Vue 3 + Vite + Vue Router (NOT static HTML, NOT React unless asked)
- **Backend:** FastAPI + SQLAlchemy 2 async + Pydantic (NOT Flask, NOT Express unless asked)
- **Database:** PostgreSQL via Docker for shared apps. SQLite only for local-only tools.
- **Styling:** EZ Design System — `~/design-system/index.css` (NOT Tailwind, NOT Bootstrap unless asked)
- **Currency:** AED via UAESymbol font + `<Aed>` component — `~/design-system/components/Aed.vue`. Dirham is the DAK default currency everywhere.
- **Docker:** Required for every project with a database. Read ~/.claude/deploy.md for patterns.
- **Ports:** Check `lsof -iTCP -sTCP:LISTEN` before assigning. Frontend 3xxx, Backend 8xxx, DB 54xx.

## Dependency floor (DAK 1.0)

Every new DAK project requires:
- Python **3.12+**
- Node **20+**
- Postgres **16+** (Docker image `postgres:16-alpine`)
- Docker Compose v2

If the host machine can't meet these, fix the host — don't downgrade the stack.

## When to deviate from the stack

The stack covers ~90% of internal tools. For the 10% that genuinely needs more:

1. **Say so in the first message of the conversation.** State what the requirement is, what the kit doesn't cover, and what you propose instead.
2. **Get approval before starting.** Don't silently pick Next.js because it feels right.
3. **Document the decision in PROJECT.md under a "Stack Deviation" heading** — the why, and the alternative considered.

Before deviating, check `~/.claude/stack-decisions.md` — common "need more" cases (realtime, ML serving, static site, mobile) have kit-compatible answers already. You'll likely find one.

## Design System (read ~/design-system/DESIGN_SYSTEM.md when building UI)

Warm neutrals (#faf9f7 bg, #23221f text), Inter for all UI text (display + body), real monospace stack for data/metrics. Green primary #0f4024 + violet secondary #6d28d9 (the parallel track — use sparingly). Sidebar-first layout — new apps use the hover-expand rail (`.app-shell.app-shell--rail`: 64px icon rail, expands on hover, no collapse button). Borders over shadows. Dark mode via `html[data-theme="dark"]` or `html.dark` — the app owns its theme, no OS auto-switch. Surfaces stay warm-tinted; pure white only as contrast text on filled color.

**Currency:** Use `<Aed>` for all money in Vue. In raw HTML, wrap the glyph in `class="currency-aed"`. Never hardcode `$` or `AED` strings where the UAESymbol glyph could render instead.

## Code organization — tiered file size caps

The goal is single responsibility per file; line caps are the smoke alarm that keeps you honest.

| File type | Soft cap | Why |
|---|---|---|
| **Function** | 50 lines | If it doesn't fit on a screen, it's doing too much |
| **Vue SFC component** | 250 lines | Template + script + style combined |
| **Composable / util module** | 200 lines | Should do one thing |
| **Backend service / route module** | 400 lines | Realistic for a non-trivial module |
| **Aggregator (`app.py`, `main.py`, `index.ts`)** | 200 lines | Force routers out; aggregators should be thin |
| **Test file** | 500 lines | Tests are allowed to be verbose |

**The real rule:** If you can't explain the file's single responsibility in one sentence, split it. If you can't name the function in one word, split it.

**Escape hatch:** a file can exceed its cap if (a) it has one clear responsibility and (b) splitting would genuinely hurt readability. Document why in a header comment.

**Pre-append check:** before appending to an existing file, read its current length. If you'd push it past its cap, extract the new code into a new module instead.

## Convention before creation

Before writing any new helper, util, or component — **grep for existing ones**. If something similar exists, extend it; don't duplicate. Search patterns:

- Helpers → `grep -rn "def helperName" backend/` or `rg "export function" frontend/`
- Components → `rg "defineComponent\|<template>" components/`
- Routes → `rg "@app.get\|@app.post" backend/`

Duplicated logic is the #1 source of rot in AI-assisted codebases.

## Finish-line checklist

Before declaring any task "done":

- [ ] Type checker passes (`mypy`, `tsc --noEmit`)
- [ ] Lint clean (`ruff check`, `eslint .`)
- [ ] Tests pass (`pytest`, `vitest`)
- [ ] New code has corresponding tests (golden path + one edge case minimum)
- [ ] No secrets / tokens in the diff
- [ ] `PROJECT.md` updated if this changes current state
- [ ] If UI: opened it in a browser, hit the golden path, checked one edge case

Skip any of these at your own peril. "It compiles" isn't "it works."

## Guides (read when relevant — NOT every conversation)

| Guide | When to read | Location |
|-------|-------------|----------|
| Tech stack rationale | Starting a new project | `~/.claude/stack.md` |
| Stack deviation tree | Project feels non-standard | `~/.claude/stack-decisions.md` |
| Git workflow | Any git operation | `~/.claude/git-workflow.md` |
| API patterns | Building REST endpoints | `~/.claude/api-patterns.md` |
| Deployment | Shipping to production | `~/.claude/deploy.md` |
| Design system | Building any UI | `~/design-system/DESIGN_SYSTEM.md` |
| Security (OWASP) | Invoke `/owasp-security` | `~/.claude/skills/owasp-security/` |
| Project conventions | Starting work on a project | `CONVENTIONS.md` in repo root |

## Project Management

**Every project lives in its own named folder — always.** This is how the fleet tracks work cleanly: building in your home directory, Desktop, Documents, a cloud-sync folder (OneDrive/Dropbox/iCloud), or a bare `projects`/`code` folder collapses everything into junk buckets. Before writing any code for something new, you MUST be inside a dedicated, descriptively-named project folder.

When starting a new project:
1. **Default — run `dak init <name>`:** scaffolds the full kit in one command (named folder + `.dak/project.json` identity + the DAK stack), then `dak doctor` to confirm it's ready and `dak add-model <Name>` to add a data resource. The `dak` command lives in `~/.claude/bin`, which push_stats.py puts on your PATH automatically.
2. **A different stack/architecture is fine** — that's the player's call. But still start in a dedicated, kebab-case-named folder with its own `.dak/project.json` (run `dak init <name>` first, then adjust the stack). Never build in an un-named or catch-all directory.
3. **Manual fallback:** copy `~/.claude/project-management-template.md` into the project root as `PROJECT.md`, copy `~/.claude/conventions-template.md` as `CONVENTIONS.md`, set up the rest.
4. Update PROJECT.md after each significant phase (what was done, issues, lessons).
5. Keep the "Current State" section always up to date — and keep the PROJECT.md **front-matter** intent (`goal`, `domain`, `audience`) filled and `status` current (`building`/`live`/`paused`/`archived`). The fleet leaderboard reads these. `.dak/project.json` (the UUID identity card) is written once by `dak init` — don't edit it.
6. Read `CONVENTIONS.md` on every session — it describes the naming, layout, and patterns specific to this project.

This is NOT optional. Every project gets its own named folder, a PROJECT.md, and a CONVENTIONS.md.

## Auto-Updating Pages

Every project gets four pages that auto-update:

| Page | Data file | Updated by |
|------|-----------|------------|
| `/vibe-code` | `public/vibe-stats.json` | Leaderboard hook (after every session) |
| `/journey` | `public/journey-data.json` | You (Claude Code) — after significant work |
| `/architecture` | `public/tech-stack.json` | Leaderboard hook (scans project files) |
| `/pm-log` | `PROJECT.md` (repo root, imported via Vite `?raw`) | You (Claude Code) — throughout the project lifecycle |

Templates: `~/.claude/templates/vibe-stats.md`, `journey.md`, `architecture.md`, `pm-log.md`

**PM Log:** The `/pm-log` page renders `PROJECT.md` directly via `marked` + `mermaid` — no intermediate JSON file. Edit `PROJECT.md`, the page updates. Follow `~/.claude/templates/pm-log.md` for the Vue component structure, dependencies, and styling.

**Journey data:** After completing significant work, update `public/journey-data.json` by reading the project's code, README, and PROJECT.md. Read `~/.claude/templates/journey.md` for the JSON schema and generation rules.

**Tech stack:** The hook auto-detects from package.json/requirements.txt/docker-compose.yml. When you notice missing technologies (Tailscale, external APIs, etc.), add them to tech-stack.json manually — the hook preserves hand-curated entries.

## Observability baseline

Every DAK project ships with:
- **Structured JSON logs** — every log line is a JSON object with `ts`, `level`, `logger`, `msg`, and any `extra` fields.
- **`/healthz` + `/readyz` endpoints** — liveness vs readiness split.
- **Sentry hook wrapped but disabled** — enable with `SENTRY_DSN` env var.

Wired by default in `dak-template/`. Don't bolt them on later.

## Standard auth primitive

Every DAK project ships with a FastAPI dep that validates an admin password (`DETAILED_PASSWORD` env var) via a header or session cookie. Use this — don't reinvent auth per project. Location: `backend/auth.py` in `dak-template/`.

## What NOT To Do

- Static HTML files as a "solution" — use a proper SPA framework
- Tailwind class soup — use the design system
- Component library default themes out of the box
- Skip PROJECT.md or CONVENTIONS.md — both are mandatory
- Build in an un-named or catch-all folder (home, Desktop, OneDrive, a bare `projects`/`code` dir) — scaffold a named project first (`dak init <name>`)
- Pure black (#000) anywhere; pure white (#fff) surfaces — warm neutrals only (#fff is reserved for contrast text on filled color)
- Glassmorphism, gradient text, glow borders, bounce animations
- Modals — use slide-in panels instead
- Hardcode stats in vibe/journey pages — read from JSON files
- Hardcode `$` or `"AED"` strings — use `<Aed>` or the `currency-aed` class
- Silently deviate from the stack — state it, get approval, document in PROJECT.md
- Append to files past their soft cap — extract first
- Create a helper without grepping for an existing one
- Declare a task done without running the finish-line checklist
