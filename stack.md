# DAK — Tech Stack Guide

This is the opinionated tech stack for your projects. Use this unless explicitly told otherwise.

## Why These Choices

### Frontend: Vue 3 + Vite

**Why Vue 3 over React:**
- Composition API is cleaner than hooks — no rules of hooks, no stale closures
- `<script setup>` eliminates boilerplate — less code, same power
- Vue Router is first-party, not a third-party dependency
- Reactivity system is intuitive — `ref()` and `reactive()` just work
- Smaller bundle size, faster cold starts

**Why Vite:**
- Instant dev server startup (no bundling in dev)
- Fast HMR that actually works
- Built-in TypeScript, CSS modules, asset handling
- Production builds via Rollup — optimized and tree-shaken

**What to use:**
```bash
npm create vite@latest my-project -- --template vue
cd my-project
npm install vue-router@4
```

**Project structure:**
```
frontend/
  src/
    views/           # Page-level components (one per route)
    components/      # Reusable components
    router/          # Vue Router config
    assets/          # Static assets
    App.vue          # Root component
    main.js          # Entry point
  public/
  index.html
```

### Backend: Python FastAPI

**Why FastAPI over Express/Flask/Django:**
- Async by default — handles concurrent requests efficiently
- Pydantic models = automatic request validation + documentation
- Auto-generated OpenAPI/Swagger docs at /docs
- Type hints everywhere — catches bugs before runtime
- SQLAlchemy 2 async = clean database access with modern Python

**What to use:**
```bash
mkdir backend && cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg pydantic
```

**Project structure:**
```
backend/
  app.py             # FastAPI app, routes, lifespan
  database.py        # SQLAlchemy engine, session, base
  models.py          # SQLAlchemy ORM models
  schemas.py         # Pydantic request/response schemas
  venv/
```

**Standard app.py pattern:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="My Project")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Database: PostgreSQL via Docker

**Why PostgreSQL over SQLite:**
- Concurrent access — multiple users, multiple connections
- Full-text search, JSONB columns, array types
- Proper migrations with Alembic
- Production-ready from day one

**Use SQLite ONLY for:** local-only tools, personal dashboards, prototypes you'll throw away.

### Docker

Docker is not optional. Every project that has a database or needs to run on another machine uses Docker.

**Why Docker:**
- One `docker compose up -d` and the database is running — no installing PostgreSQL locally
- Reproducible environments — works on your machine AND everyone else's
- Isolated containers — each project gets its own database, no conflicts
- Easy cleanup — `docker compose down -v` removes everything cleanly
- Production-like from day one — same container in dev and production

**Install Docker Desktop:** https://www.docker.com/products/docker-desktop/

**Essential commands:**
```bash
docker compose up -d          # Start all services in background
docker compose down           # Stop all services
docker compose down -v        # Stop and delete volumes (fresh start)
docker compose logs -f        # Stream logs from all services
docker compose ps             # Show running containers
docker exec -it <name> bash   # Shell into a running container
```

**Standard docker-compose.yml for a project:**
```yaml
services:
  db:
    image: postgres:16
    container_name: myproject-pg
    environment:
      POSTGRES_DB: myproject
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5440:5432"  # Always use a unique port per project!
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-ONLY", "pg_isready", "-U", "dev"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

**Naming convention:**
- Container names: `projectname-pg`, `projectname-redis`, etc.
- Volume names: `projectname_pgdata`
- This prevents collisions between projects.

**Multi-service pattern (backend + db):**
```yaml
services:
  db:
    image: postgres:16
    container_name: myproject-pg
    environment:
      POSTGRES_DB: myproject
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5440:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    container_name: myproject-api
    ports:
      - "8001:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev@db:5432/myproject
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

**Backend Dockerfile pattern:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**When to dockerize the frontend too:**
- For deployment / sharing with others — yes, add an nginx container
- For local development — no, `npm run dev` with Vite is faster and has HMR

**Common gotchas:**
- Port already in use → change the left side of the port mapping (host port)
- Database not connecting → make sure you're using `localhost` from host, but the service name (e.g., `db`) from within Docker
- Data disappeared → you probably ran `docker compose down -v` which deletes volumes
- Container won't start → check logs with `docker compose logs db`

**Useful Docker patterns:**
```bash
# Connect to PostgreSQL inside a container
docker exec -it myproject-pg psql -U dev -d myproject

# Backup a database
docker exec myproject-pg pg_dump -U dev myproject > backup.sql

# Restore a database
cat backup.sql | docker exec -i myproject-pg psql -U dev -d myproject

# See disk usage of all containers/volumes
docker system df
```

### Styling: EZ Design System

**Why a custom design system over Tailwind/Bootstrap:**
- Consistent look across all your projects
- Semantic class names that read like English, not `px-4 py-2 bg-gray-100`
- Dark mode built in — one class toggle
- Presentation-ready by default — no styling debt
- One UI family (Inter), warm neutrals, green primary + violet secondary — done

**How to use** — one import (pulls tokens → base → components in order, plus Inter):

```css
@import '~/design-system/index.css';
```

Or copy the design-system/ directory into your project and import from there. Hand-wiring the three layers individually is also fine — order matters, tokens first (see `~/design-system/DESIGN_SYSTEM.md`).

**Currency display:** All financial values use AED with the UAE Dirham symbol font (`design-system/fonts/dirham-symbol.woff2`, loaded by base.css — use `.dirham-symbol` / `.currency-aed`, or `<Aed>` in Vue). See the Currency section of `design-system/DESIGN_SYSTEM.md`. Backend stores USD; convert on the frontend using the fixed peg rate (3.6725).

## Common Patterns

### Full-Stack Project Setup
```bash
# 1. Create project directory
mkdir my-project && cd my-project

# 2. Frontend
npm create vite@latest frontend -- --template vue
cd frontend && npm install vue-router@4 && cd ..

# 3. Backend
mkdir backend && cd backend
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy asyncpg pydantic
cd ..

# 4. Database
# Create docker-compose.yml with PostgreSQL (see above)
docker compose up -d

# 5. Design system
cp -r ~/design-system frontend/src/design-system

# 6. Git
git init && echo "node_modules/\nvenv/\n__pycache__/\n.env" > .gitignore
```

### Port Allocation
Check what's in use: `lsof -iTCP -sTCP:LISTEN | grep -E ':[0-9]+ ' | sort -t: -k2 -n`

Convention:
- Frontend dev server: 3xxx (e.g., 3100, 3200, 3300)
- Backend API: 8xxx (e.g., 8001, 8002, 8003)
- PostgreSQL: 54xx (e.g., 5432, 5433, 5434)

### Environment Variables
Always use a `.env` file for secrets. Never commit it.
```bash
echo ".env" >> .gitignore

cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://dev:dev@localhost:5440/myproject
SECRET_KEY=change-me-in-production
EOF
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]
```

### CORS Setup
Always configure CORS in development. The FastAPI pattern above allows all origins — restrict in production.

## What NEVER To Build

- **Static HTML pages** as a "web app" — if it has more than one page, it needs a router
- **Express + EJS templates** — this is not 2015
- **jQuery anything** — Vue handles reactivity better
- **Inline styles everywhere** — use the design system classes
- **Single-file monoliths** — split into views, components, and API modules
