# CONVENTIONS — {{project-name}}

> Claude reads this before any work. Keep it short, specific, and current. This isn't `PROJECT.md` (which is narrative history); this is the project's style rulebook.

## Project identity & status

- `.dak/project.json` holds the project's **immutable identity** (UUID, ports, scaffold version), written once at `dak init`. Don't edit it.
- `PROJECT.md` **front-matter** holds the **editable intent**. Keep `goal`, `domain`, `audience` filled (one line each), and update `status` at phase boundaries (`building` → `live` → `paused`/`archived`). The fleet leaderboard reads these — an empty `goal` or stale `status` makes the project show up blank or misleading in the fleet view.

## Naming

- **Python modules:** `snake_case.py`
- **Python classes:** `PascalCase`
- **Python functions / vars:** `snake_case`
- **Vue components:** `PascalCase.vue` (e.g. `PlayerCard.vue`)
- **Vue composables:** `useX.js` (e.g. `usePlayers.js`)
- **Vue views (top-level routes):** `PascalCase.vue` in `src/views/`
- **CSS classes:** `kebab-case`, no BEM (rely on scoped styles)
- **Env vars:** `SCREAMING_SNAKE_CASE`, prefixed with project code (e.g. `{{PREFIX}}_DB_URL`)

## File structure

```
project-root/
├── backend/
│   ├── app.py              # aggregator, <200 lines (mounts routers)
│   ├── api/                # route modules, one per resource
│   │   └── items.py        # worked CRUD example → /api/items
│   ├── services/           # business logic, no HTTP
│   │   └── items.py
│   ├── models/             # SQLAlchemy models
│   │   ├── base.py         # DeclarativeBase (Base.metadata)
│   │   └── item.py         # worked example model
│   ├── seed.py             # python -m seed  (example data)
│   ├── auth.py             # DAK standard auth dep
│   ├── database.py         # engine + session + create_all-on-boot
│   ├── logging_config.py   # structured JSON logs
│   └── tests/              # pytest: test_health.py, test_items.py
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router.js
│   │   ├── views/          # top-level route pages
│   │   ├── components/     # reusable pieces
│   │   ├── composables/    # shared state logic
│   │   ├── utils/          # pure helpers
│   │   └── styles/
│   ├── public/
│   │   ├── vibe-stats.json      # auto-updated
│   │   ├── journey-data.json    # Claude-updated
│   │   └── tech-stack.json      # auto-updated
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
├── PROJECT.md              # narrative history
├── CONVENTIONS.md          # this file
└── README.md
```

## Soft file size caps

See `~/.claude/CLAUDE.md`. Summary:
- Function: 50 lines · Vue SFC: 250 · composable/util: 200 · backend module: 400 · aggregator: 200 · test: 500.

## Testing

- **Backend:** `pytest` in `backend/tests/`. Mirror source tree: `api/users.py` → `tests/api/test_users.py`.
- **Frontend:** `vitest` in `frontend/src/**/__tests__/` or `*.spec.js` adjacent.
- **Every new module needs:** golden-path test + one edge case. No exceptions for "it's trivial."

## Money

All money displayed to users uses `<Aed>` from `~/design-system/components/Aed.vue`. Never hardcode `$` or `AED` strings. Internal storage can be USD (tag the column; convert on read) but the UI is always AED.

## API patterns

- REST verbs + resource-named paths: `GET /api/users`, `POST /api/users`, `GET /api/users/{id}`.
- Pydantic models for every request/response body.
- Errors: raise `HTTPException(status_code=..., detail=...)`. Never return `{"error": "..."}` with 200.
- ETag / 304 where cheap (read-heavy list endpoints).
- Structured log on every non-2xx.

## Data layer

- **models/** — SQLAlchemy 2 ORM models, one per file, all inheriting `Base` from `models/base.py`. Register each in `models/__init__.py` so `create_all` (and Alembic) see it.
- **services/** — async DB logic (queries, writes). No FastAPI / HTTP here — that's what keeps routers thin and the logic unit-testable.
- **api/** — thin routers: Pydantic in/out models + a `get_session` dependency + a service call.
- **Schema in dev:** `DAK_AUTO_CREATE=1` (the default) creates any missing tables on boot — a fresh project has a working DB with no migration step. For prod, set `DAK_AUTO_CREATE=0` and manage schema with Alembic.
- **Add a resource:** `dak add-model <Name>` scaffolds the model + service + CRUD router and registers it in `app.py`.
- **Seed data:** `python -m seed` (the idempotent example in `seed.py`).
- Delete the worked `items` example (`models/item.py`, `services/items.py`, `api/items.py`, its line in `models/__init__.py`, and the mount in `app.py`) once you have real models.

## Auth

Admin-gated endpoints use the `require_admin` FastAPI dep from `backend/auth.py`. Validates `X-Admin-Key` header or `admin_key` cookie against `DETAILED_PASSWORD`. Don't reinvent.

## Commits

- Conventional-commit style: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- One logical change per commit. Reviewer shouldn't have to untangle two features from one diff.
- Commit message explains the *why*, not the *what* (the diff shows what).

## Conventions specific to this project

> Fill in anything non-standard below. Examples:
> - Timezone: Asia/Dubai
> - Customer IDs: `cus_` prefix
> - Feature flags: `flags.FOO_ENABLED` pattern
> - Third-party APIs used: [list]

- _...add as project grows..._
