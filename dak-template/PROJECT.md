# {{PROJECT_NAME}}

> One-line description of what this project does. Replace this.

## Current state

_{{DATE}}_ — fresh DAK scaffold. Services boot, four auto-pages render, and a worked `items` data model is wired end-to-end (delete it once you add real models).

## Goals

- _Fill in what this project is trying to achieve. 3 bullets max._
- _What "done" looks like for v1._

## Stack

See `/architecture` (live) or `public/tech-stack.json`.

_Stack deviations: **none** yet._

## Log

### Phase 1 — Scaffolded ({{DATE}})

Initialized via `dak init`. Vue 3 + FastAPI + Postgres + Docker wired out of the box. Four auto-pages in place (`/journey`, `/architecture`, `/vibe-code`, `/pm-log`).

**What's done**
- Docker Compose brings up db, backend, frontend.
- `/healthz` + `/readyz` live.
- Admin auth via `DETAILED_PASSWORD` env (generated into `.env` at scaffold).
- Data layer: `items` model + CRUD at `/api/items`, tables auto-created on boot, `pytest` green.

**Open questions**
- _List any decisions deferred to a later session._

**Lessons**
- _As this grows, capture what went wrong and how you fixed it._
