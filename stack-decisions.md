# DAK Stack Decisions — "when the kit isn't enough"

Read this when a project's requirement smells non-standard. Most "need more" cases have kit-compatible answers; only a few genuinely need a different stack.

## Decision tree

### Frontend

| Requirement | Kit answer | Deviate? |
|---|---|---|
| Standard web app | React 19 + Vite + React Router (`createHashRouter`) | ✅ kit |
| Static marketing site | React 19 + Vite SSG (`vite-react-ssg`) or Astro with React components | ✅ kit (Vite SSG preferred) |
| Content-heavy site with CMS | React + a headless CMS (Strapi / Sanity / Directus) | ✅ kit |
| Real-time collaborative editing | React + FastAPI WebSockets + Yjs/CRDT library | ✅ kit |
| Maintaining an existing Vue/EZ app | Vue 3 + EZ Design System — **legacy, existing projects only** | ⚠ legacy — never for NEW apps |
| Mobile app | **React Native** or **Flutter** | ⚠ deviate — kit is web-only |
| Desktop app | **Electron** wrapping the React app, or **Tauri** (Rust core + React UI) | ⚠ partial — UI stays React, wrapper deviates |
| VSCode extension | **VSCode API** — not DAK | ⚠ deviate |
| Browser extension | React + `vite-plugin-web-extension` | ✅ kit |

### Backend

| Requirement | Kit answer | Deviate? |
|---|---|---|
| Standard REST API | FastAPI + SQLAlchemy 2 async | ✅ kit |
| GraphQL API | FastAPI + `strawberry-graphql` | ✅ kit |
| Real-time (WebSockets, SSE) | FastAPI native WebSocket support | ✅ kit |
| High-throughput streaming | FastAPI + `aiokafka` / `redis-streams` | ✅ kit |
| ML serving | FastAPI + the ML library (`torch`/`transformers`/`scikit-learn`) | ✅ kit |
| Background jobs | FastAPI + `arq` (Redis) or `apscheduler` | ✅ kit |
| Heavy compute / long jobs | FastAPI + Celery + Redis | ✅ kit |
| CLI tool (no HTTP) | Python + `typer` — skip FastAPI | ⚠ partial — no FastAPI, same Python |
| System programming / performance-critical | **Rust** or **Go** — not DAK | ⚠ deviate |

### Database

| Requirement | Kit answer | Deviate? |
|---|---|---|
| Shared app, multi-user | Postgres 16+ via Docker | ✅ kit |
| Local dev tool, single user | SQLite | ✅ kit |
| Time-series (metrics, IoT) | **TimescaleDB** (Postgres extension) | ✅ kit — still Postgres |
| Full-text search | Postgres `tsvector` + GIN indexes | ✅ kit |
| Vector search (RAG, embeddings) | **pgvector** Postgres extension | ✅ kit — still Postgres |
| Graph queries | **Apache AGE** (Postgres extension) or **Neo4j** | ⚠ AGE ✅ kit; Neo4j deviates |
| Key-value cache | **Redis** — complements kit, doesn't replace | ✅ kit add-on |
| Document store | Postgres JSONB — not MongoDB | ✅ kit |
| Analytics warehouse | **ClickHouse** or **DuckDB** | ⚠ deviate |

### AI / LLM features

| Requirement | Kit answer | Deviate? |
|---|---|---|
| Chat with an LLM | FastAPI + `anthropic` SDK | ✅ kit |
| RAG pipeline | FastAPI + pgvector + embeddings via `anthropic` | ✅ kit |
| Agentic workflows | FastAPI + `claude-agent-sdk` | ✅ kit |
| Voice in/out | FastAPI + Whisper (local) or ElevenLabs API | ✅ kit |
| Image generation | FastAPI proxying to a provider API | ✅ kit |

## How to deviate — the process

1. **Read this document** before deciding — if your case is in the green column above, use the kit.
2. **State the deviation in the first message** of the conversation: what you need, what the kit can't do, what you propose.
3. **Get explicit approval** — don't assume.
4. **Document in PROJECT.md under a "Stack Deviation" heading**: the why, the alternative considered, and the mitigation if the new tech has unusual operational cost.

## Things that NEVER justify deviation

- "I'm more familiar with X" — familiarity is a 1-hour problem, stack drift is a 1-year problem.
- "I'd rather build the frontend in Vue" — Vue/EZ is legacy; new apps are React 19 + Astryx + the DEWA theme. Vue is only for maintaining existing projects.
- "X is newer / trendier" — the kit is the stable choice on purpose.
- "It's a quick prototype" — prototypes become production 80% of the time. Build on the kit.
- "We don't need Docker for this" — yes you do.
