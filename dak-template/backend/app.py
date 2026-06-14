# {{PROJECT_NAME}} — FastAPI aggregator.
#
# This file intentionally stays thin (<200 lines). Route modules live
# in backend/api/*.py; business logic in backend/services/. The
# aggregator wires them together and exposes health endpoints.
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logging_config import configure_logging
from database import lifespan

# Route modules — import each and mount it below.
from api import items

configure_logging()
logger = logging.getLogger("app")

app = FastAPI(
    title="{{PROJECT_NAME}}",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — open in dev, restrict in prod via ALLOWED_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health endpoints ─────────────────────────────────────────────
# /healthz — the process is alive (no DB check).
# /readyz  — the process can serve traffic (DB reachable).


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    from database import db_ping
    ok = await db_ping()
    return {"status": "ok" if ok else "not-ready", "db": ok}


# ─── Mount route modules here ──────────────────────────────────────
# Worked example — a full CRUD resource at /api/items. Delete it (and
# api/items.py, services/items.py, models/item.py) once you have real
# resources, or add one with `dak add-model <Name>`.
app.include_router(items.router, prefix="/api/items", tags=["items"])
# DAK:ROUTERS  (dak add-model inserts new routers above this line — keep it)


@app.get("/")
def root():
    return {"service": "{{PROJECT_NAME}}", "healthz": "/healthz", "readyz": "/readyz"}
