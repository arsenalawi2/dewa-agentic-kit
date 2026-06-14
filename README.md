# DAK

An opinionated setup for Claude Code that teaches it how to build production-grade applications the right way — consistent stack, consistent design, consistent project management, and automatic stats tracking via the DAK leaderboard.

---

## What's inside

| File / Directory | Purpose |
|---|---|
| `CLAUDE.md` | The master config. Tells Claude which stack to use, which design system to apply, which guides to read, and how to manage projects. |
| `stack.md` | Tech stack rationale — Vue 3 + FastAPI + PostgreSQL + Docker. Why each choice, what to avoid. |
| `api-patterns.md` | REST endpoint naming, response shapes, pagination, error handling. |
| `git-workflow.md` | Commit conventions, branching, `.gitignore` template. |
| `deploy.md` | Docker, Tailscale Funnel, and nginx deployment patterns. |
| `project-management.md` | PMBOK 7-aligned PROJECT.md template (Charter, WBS, Gantt, Risks, Issues, Changes, Lessons, Status). Copied into every new project. |
| `design-system/` | The EZ Design System (warm-neutral / rammas-72k edition) — tokens, base, components + index.css entrypoint. Inter UI family, green primary + violet secondary, sidebar-first with hover-expand rail, dark mode built in. |
| `templates/` | Page templates for every new project: `/vibe-code`, `/journey`, `/architecture`, `/pm-log`. All four auto-update from live data. |
| `skills/owasp-security/` | `/owasp-security` slash command — reviews code against OWASP Top 10, ASVS 5.0, and OWASP Top 10 for LLM Applications. |
| `hooks/push_stats.py` | Stop hook that parses `~/.claude/projects/*.jsonl` at the end of every session and pushes usage stats to the DAK leaderboard. |
| `instructions.txt` | The installer script Claude Code follows when you unzip the kit. |
| `version.txt` | Current kit version. Used for auto-updates. |

---

## Installation

### One-prompt install

1. Download this repo as a zip (or `git clone`) and unzip anywhere.
2. In Claude Code, type:

   ```
   Read the instructions.txt file in ~/Downloads/agentic-kit and follow it
   ```

3. Claude Code asks for your display name (for the leaderboard).
4. Claude Code installs everything: copies `CLAUDE.md` to `~/.claude/`, drops the design system into `~/design-system/`, installs the OWASP skill, wires up the leaderboard Stop hook, and verifies the installation.

### What happens after install

- **New projects** use Vue 3 + FastAPI + PostgreSQL + Docker instead of static HTML. The EZ Design System is applied automatically.
- **Every new project gets a `PROJECT.md`** (PMBOK 7-aligned, includes a Mermaid Gantt chart) and the four auto-updating pages.
- **After every Claude Code session**, your stats are pushed to the leaderboard — prompts, tokens, cost, active hours, lines written, model breakdown. No prompt content is sent.
- **Run `/owasp-security`** any time to review your code against the latest OWASP standards.
- **Auto-updates.** The kit updates itself from the server within an hour of a new version. You never re-download.

---

## The four auto-updating pages

Every project scaffolded with the kit gets these routes by default:

| Route | Data source | What it shows |
|---|---|---|
| `/vibe-code` | `public/vibe-stats.json` | Usage stats — prompts, cost, hours, tokens, efficiency metrics, session timeline |
| `/journey` | `public/journey-data.json` | Narrative showcase — what problem the project solves, how it works, features, tech stats |
| `/architecture` | `public/tech-stack.json` | Interactive tech stack graph — nodes, dependencies, versions, external services |
| `/pm-log` | `PROJECT.md` (root) | Rendered PMBOK project log — charter, scope, WBS, Gantt, risks, issues, changes, lessons, status |

---

## Design philosophy

- **Warm neutrals, not pure black or white.** Backgrounds `#faf9f7`, text `#23221f`. Tinted brown/olive, not cool grey.
- **One accent color.** Dark green `#0f4024`. Used sparingly — never double-encoded with icons and badges.
- **Big and breathable.** Headings at 24–32px. Stat values at 32–56px. White space is a feature.
- **Sidebar first.** 240px collapsible left sidebar, main content takes remaining space, details slide in from the right at 380px.
- **Borders over shadows.** `1px solid` for containers. Shadows only for elevated overlays, barely visible.
- **Presentation ready.** Every screen should look good projected in a meeting. If you wouldn't screenshot it, it's not done.

---

## Tech stack

**Frontend:** Vue 3 + Vite + Vue Router (NOT static HTML, NOT React unless asked)
**Backend:** FastAPI + SQLAlchemy 2 async + Pydantic (NOT Flask, NOT Express unless asked)
**Database:** PostgreSQL via Docker for shared apps. SQLite only for local-only tools.
**Styling:** EZ Design System (not Tailwind, not Bootstrap unless asked)
**Infrastructure:** Docker + Docker Compose for every project with a database. Tailscale Funnel for public exposure.

Read `stack.md` for the rationale behind each choice.

---

## Project management

Every project gets a `PROJECT.md` at the repo root that follows PMBOK 7th Edition structure:

1. **Project Charter** — purpose, objectives, stakeholders, success criteria, assumptions, constraints
2. **Scope Statement** — in / out of scope, definition of done
3. **Work Breakdown Structure** — numbered hierarchical task decomposition
4. **Schedule & Milestones** — milestone list + Mermaid Gantt chart
5. **Deliverables Register** — stable IDs, locations, formats, status
6. **Cost Management** — one-time, recurring, infrastructure, budget vs actual
7. **Risk Register** — impact × likelihood × severity with mitigation
8. **Issue Log** — active problems with resolution tracking
9. **Change Log** — integrated change control
10. **Lessons Learned** — category / lesson / recommendation
11. **Current Status & Next Steps** — status, WP progress, next steps, tech stack

The `/pm-log` page in every project renders this file directly as a browsable, styled management log — the Gantt chart included.

---

## Contributing

This kit is opinionated by design — the choices (Vue over React, FastAPI over Flask, warm neutrals over cool, sidebar-first over top-bar) are intentional. Pull requests are welcome but will be evaluated against those opinions.

---

## License

MIT — see [LICENSE](LICENSE).

---

Built with Claude Code. The kit that teaches Claude Code to build better.
