#!/usr/bin/env python3
"""
Claude Code Leaderboard — Stats Push Script
Parses ~/.claude/ session data and POSTs stats to the leaderboard.
Runs as a Claude Code hook (Stop event) or standalone.

Usage:
  python3 push_stats.py              # parse + push
  python3 push_stats.py --force      # ignore throttle, push immediately

Env vars:
  PLAYER_NAME       — your display name on the leaderboard (required)
  LEADERBOARD_URL   — leaderboard endpoint (default: https://leaderboard.hadismac.com)
  PUSH_INTERVAL     — seconds between pushes (default: 300 = 5 min)
"""

import hashlib
import json
import math
import os
import re
import socket
import sys
import ssl
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# GST timezone for daily bucketing (UAE = UTC+4, no DST)
GST = timezone(timedelta(hours=4))


def _bucket_date(ts):
    """Return YYYY-MM-DD string for a datetime in GST."""
    return ts.astimezone(GST).strftime("%Y-%m-%d")


def _parse_day_key(day_key):
    """Parse YYYY-MM-DD to a date, returning None if invalid."""
    try:
        return datetime.strptime(day_key, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _is_after_hours(ts):
    """
    Working hours: Sun-Thu 09:00-18:00 GST.
    Python weekday(): 0=Mon..6=Sun. Friday=4, Saturday=5 are weekend.
    """
    local = ts.astimezone(GST)
    wd = local.weekday()
    if wd in (4, 5):  # Fri, Sat
        return True
    # Sun-Thu: check hour
    return local.hour < 9 or local.hour >= 18

# ── Config ──
# 2.3.0: include machine_id + hostname so the leaderboard can keep per-machine
# rows for the same player name (fixes stats overwrite when same PLAYER_NAME is
# used on multiple machines — prior versions clobbered whoever pushed last).
# 2.5.0: token-based auth for /api/leaderboard/submit (C4). First push
# from a new laptop is queued as 'pending'; after admin approves, the next
# push bootstraps the token and caches it at TOKEN_FILE for every future
# submit. During the dual-accept migration window the server still accepts
# tokenless pushes with a warning — behaviour flips to reject-on-missing
# once ENROLLMENT_ENFORCE_TOKEN is set on the server.
# 2.5.1: enable real TLS verification. Previous versions set CERT_NONE +
# check_hostname=False as a workaround for a now-retired self-signed /
# Tailscale-Funnel setup. The leaderboard is behind Cloudflare with a real
# Let's Encrypt cert, so default verification just works — and closes the
# MITM-update hole where any intermediate proxy could swap in code that
# self_update() would write to disk and os.execv.
# 2.5.2: DESC cybersec compliance — capture full prompt text (no 200-char
# preview truncation) and uncap the recent_prompts list so every input a
# player ever sent is archived. Loop-injected repeats still don't inflate
# the human_prompts counter, but they ARE logged (with is_scheduled=True)
# so the audit trail is complete. Matching server-side caps were raised
# to 50 MB body + uncapped recent_prompts in backend commit b6a3156.
# 2.5.3: player-level prompt-archive exemption. Players named in
# PROMPT_LOG_EXEMPT_PLAYERS (comma-separated, case-insensitive, default
# "Hadi") still push all metrics but recent_prompts is stripped to an
# empty list before send. Saves ~10-15 MB per push for heavy users whose
# content doesn't need to be archived (e.g., the admin's own sessions).
# Server enforces the same list defensively.
# 2.7.0: SkillOps — per-tool usage detail (tool_detail). Classifies every
# tool_use into skill / mcp / builtin (with plugin + mcp-server taxonomy) and
# attributes two token figures per tool: gen_tokens (the invoking turn's output,
# split across its tool_use blocks) and result_tokens (the tool_result payload
# size injected back into context, ~chars/4). Counts are exact; tokens are a
# documented attribution, not billed per-tool. Additive field — older servers
# ignore it; the new server stores it in players.tool_detail.
# 2.7.1: tool_detail rows gain a `models` dict ({family: calls}) — which model
# family invoked each skill / plugin / MCP tool.
# 2.8.0: SkillOps v2 — (a) typed /<skill> slash commands counted (cmd_calls;
# CLI built-ins denylisted), (b) per-tool `errors` from tool_result is_error,
# (c) daily_buckets gain capped per-day `skills` / `mcp_servers` dicts so the
# server can chart adoption trends (backfills to local history depth on next
# push, since daily_buckets are re-parsed from local JSONL every run).
# 2.8.1: fable/mythos model families (Mythos-class, 2026-06-09) with correct
# 2x-opus pricing. Previously collapsed into "opus" and costed at half price;
# costs self-correct fleet-wide on the next push (full local re-parse).
# 2.9.0: DAK first-run-reliability batch — (a) ensure_dak_path() puts
# ~/.claude/bin on PATH (idempotent, marker-guarded) so `dak`/`dak-init` are
# runnable fleet-wide; (b) write_tech_stack stamps schema_version and preserves
# unknown top-level keys instead of silently dropping hand-curated data on the
# first push; (c) per-project doc-staleness flags (journey/PROJECT.md
# placeholder + mtime age) attached to projects_data so the leaderboard can see
# doc rot. All additive + best-effort (try/except) — older servers ignore the
# new fields.
# 2.10.0: data-spine phase 1 — attach a `project_meta` block to each
# projects_data entry: stable identity from `.dak/project.json` (project_id,
# created_utc, scaffold_kit_version, ports) + intent from PROJECT.md YAML
# front-matter (status, goal, domain, audience). Additive; lets the leaderboard
# key on a UUID and finally answer "what is each project, and why".
# 2.11.0: journey-schema unification — JOURNEY_DEFAULT_SHAS is now a SET of the
# new unified default (schema_version 1: phases spine + optional rich blocks) AND
# the pre-3.6 {phases} default, so placeholder detection is rollout-skew-tolerant
# (push_stats self-updates before the kit zip) and pre-3.6 default projects stay
# correctly flagged. Lockstep with the kit default-file change.
SCRIPT_VERSION = "2.11.0"
PLAYER_NAME = os.environ.get("PLAYER_NAME", "")
LEADERBOARD_URL = os.environ.get("LEADERBOARD_URL", "https://leaderboard.hadismac.com")
PUSH_INTERVAL = int(os.environ.get("PUSH_INTERVAL", "300"))
THROTTLE_FILE = Path.home() / ".claude" / ".leaderboard_last_push"
MACHINE_ID_FILE = Path.home() / ".claude" / ".machine-id"
HOSTNAME_FILE = Path.home() / ".claude" / ".machine-hostname"
TOKEN_FILE = Path.home() / ".claude" / ".leaderboard_token"


def read_token() -> str:
    """Load the cached per-laptop token. Empty string if not yet issued."""
    try:
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
    except OSError:
        pass
    return ""


def write_token(token: str) -> None:
    """Persist a token issued by the server. Best-effort — never crash push."""
    if not token:
        return
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token)
        try:
            os.chmod(TOKEN_FILE, 0o600)  # reduce casual readability
        except OSError:
            pass
    except OSError:
        pass


def get_machine_id():
    """
    Return a stable per-machine UUID, creating one on first invocation.
    The leaderboard uses (PLAYER_NAME, machine_id) as its primary key, so two
    machines running as the same player don't overwrite each other.
    """
    try:
        if MACHINE_ID_FILE.exists():
            val = MACHINE_ID_FILE.read_text().strip()
            if val:
                return val
        MACHINE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        new_id = uuid.uuid4().hex
        MACHINE_ID_FILE.write_text(new_id)
        return new_id
    except OSError:
        # Filesystem issue — derive a stable ID from hostname so we still
        # avoid collisions, even without persistence.
        try:
            host = socket.gethostname() or "unknown"
        except Exception:
            host = "unknown"
        return f"host-{host}"


def get_hostname():
    """
    Return a stable, human-readable hostname. Prefers ~/.claude/.machine-hostname
    if present (written by this script on the real host) — this lets the Docker
    dashboard container, whose socket.gethostname() returns an ephemeral container
    ID like '9831b9db998f', surface the real host's name instead.
    """
    try:
        if HOSTNAME_FILE.exists():
            val = HOSTNAME_FILE.read_text().strip()
            if val:
                return val
    except OSError:
        pass
    try:
        host = socket.gethostname() or ""
    except Exception:
        host = ""
    # Persist for containers/services to read (best-effort only).
    if host:
        try:
            HOSTNAME_FILE.parent.mkdir(parents=True, exist_ok=True)
            HOSTNAME_FILE.write_text(host)
        except OSError:
            pass
    return host

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
IDLE_THRESHOLD = 600  # 10 min

# Dirs that are NOT projects (system/personal folders)
SKIP_DIRS = {
    ".claude", ".config", ".local", ".cache", ".npm", ".nvm", ".cargo",
    ".rustup", ".pyenv", ".rbenv", ".ssh", ".gnupg", ".vscode",
    "node_modules", "venv", ".venv", "__pycache__",
    # Personal/system dirs
    "desktop", "documents", "downloads", "library", "movies", "music",
    "pictures", "public", "sites", "applications",
    "go", "opt", "tmp", "bin",
}

# Container dirs — go one level deeper to find the actual project
CONTAINER_DIRS = {
    "projects", "repos", "code", "dev", "src", "workspace", "workspaces",
    "github", "gitlab", "bitbucket", "work", "personal", "apps",
}

# ── Pricing per token (USD) ──
PRICING = {
    "opus":   {"input": 5/1e6, "output": 25/1e6, "cache_read": 0.50/1e6, "cache_write": 6.25/1e6},
    "sonnet": {"input": 3/1e6, "output": 15/1e6, "cache_read": 0.30/1e6, "cache_write": 3.75/1e6},
    "haiku":  {"input": 1/1e6, "output": 5/1e6,  "cache_read": 0.10/1e6, "cache_write": 1.25/1e6},
    # Mythos-class (2026-06-09): claude-fable-5 / claude-mythos-5 — 2x opus
    # (platform.claude.com/docs pricing: $10 in / $50 out / $1 cr / $12.50 cw)
    "fable":  {"input": 10/1e6, "output": 50/1e6, "cache_read": 1.00/1e6, "cache_write": 12.50/1e6},
    "mythos": {"input": 10/1e6, "output": 50/1e6, "cache_read": 1.00/1e6, "cache_write": 12.50/1e6},
}


def should_push():
    if "--force" in sys.argv:
        return True
    if THROTTLE_FILE.exists():
        try:
            last = float(THROTTLE_FILE.read_text().strip())
            if time.time() - last < PUSH_INTERVAL:
                return False
        except (ValueError, OSError):
            pass
    return True


def mark_pushed():
    try:
        THROTTLE_FILE.write_text(str(time.time()))
    except OSError:
        pass


def model_family(model):
    m = (model or "").lower()
    if "haiku" in m: return "haiku"
    if "sonnet" in m: return "sonnet"
    # 2.8.1: Mythos-class models (released 2026-06-09) — priced 2x opus
    if "fable" in m: return "fable"
    if "mythos" in m: return "mythos"
    return "opus"


def cost_for(inp, out, cr, cw, model):
    p = PRICING[model_family(model)]
    return inp * p["input"] + out * p["output"] + cr * p["cache_read"] + cw * p["cache_write"]


# ── Hygiene findings (2.6.0) ──
# Per-day cybersec score signals. Patterns are scoped:
#   "code"   — applied to executed Bash commands and Edit/Write file content
#   "prompt" — applied only to user prompt text (intent flags, not code patterns)
# Server computes 100 - Σ severity*log10(1+count) over 30d. Samples are short
# hashes so the server can dedupe without seeing the underlying text.
HYGIENE_PATTERNS = {
    "secrets_in_code": [
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
        re.compile(r"\bxox[bp]-[A-Za-z0-9-]{10,}"),
        re.compile(r"""(?im)^[^\n#/'"\\]*\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_!@#$%^&*+/=\-]{20,}["']"""),
    ],
    "tls_disabled": [
        re.compile(r"\bverify\s*=\s*False\b"),
        re.compile(r"\brejectUnauthorized\s*:\s*false"),
        re.compile(r"\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0"),
        re.compile(r"\bcurl\b[^\n]*\s(?:-k\b|--insecure\b)"),
    ],
    "pipe_to_shell": [
        re.compile(r"\b(?:curl|wget)\s+[^\n|]+\|\s*(?:ba)?sh\b"),
    ],
    "shell_injection": [
        re.compile(r"\bsubprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True"),
        re.compile(r"\bos\.system\(\s*[fF]['\"]"),
    ],
    "sql_concat": [
        # Require multi-word SQL grammar so "Would delete {n}" doesn't match.
        # Matches: f"INSERT INTO …{var}…", f"DELETE FROM …{var}…",
        # f"UPDATE x SET …{var}…", f"SELECT … FROM …{var}…".
        re.compile(r"""[fF]["'][^"']*\b(?i:INSERT\s+INTO|DELETE\s+FROM|UPDATE\s+\w+\s+SET|SELECT\b[^"']+\bFROM)\b[^"']*\{[^}]+\}"""),
        # String concat with SQL clause: "... WHERE id = " + user_input
        re.compile(r"""["'][^"']*\b(?i:WHERE|VALUES)\b[^"']{0,40}["']\s*\+\s*\w"""),
    ],
    "no_verify_commit": [
        re.compile(r"\bgit\s+(?:commit|push|merge|rebase|tag)\b[^&;|\n]*--no-verify\b"),
        re.compile(r"\bgit\s+(?:commit|push|merge|rebase|tag)\b[^&;|\n]*--no-gpg-sign\b"),
    ],
    "destructive_rm": [
        # Match wholesale targets only: `rm -rf /`, `rm -rf ~`, `rm -rf *` —
        # NOT `rm -rf ~/something/specific` which is normal cleanup.
        re.compile(r"\brm\s+(?:-[rRf]+\s+)+(?:/(?:\s|$)|~(?:\s|$)|\*(?:\s|$))"),
    ],
    "chmod_world": [
        re.compile(r"\bchmod\s+(?:777|a\+rwx)\b"),
    ],
    "skip_intent_prompt": [
        re.compile(r"(?i)\bskip\s+(?:the\s+)?(?:test|hook|verif|check)"),
        re.compile(r"(?i)\bbypass\s+(?:the\s+)?(?:security|auth|verif|hook)"),
        re.compile(r"(?i)\bignore\s+(?:the\s+)?(?:warning|error|security)"),
        re.compile(r"(?i)\bdisable\s+(?:tls|ssl|verif)"),
        re.compile(r"(?i)--no-verify\b"),
    ],
}

HYGIENE_SEVERITY = {
    "secrets_in_code":    25,
    "tls_disabled":       15,
    "pipe_to_shell":      15,
    "shell_injection":    12,
    "sql_concat":         12,
    "no_verify_commit":   10,
    "destructive_rm":     10,
    "chmod_world":         5,
    "skip_intent_prompt":  3,
}

HYGIENE_CODE_CATS = [c for c in HYGIENE_PATTERNS if c != "skip_intent_prompt"]
HYGIENE_PROMPT_CATS = ["skip_intent_prompt"]
HYGIENE_SAMPLE_CAP = 10  # max per-category sample hashes shipped per day


def _scan_hygiene(text, scope="code"):
    """Return list of (category, sample_hash) for matches in text."""
    if not text or not isinstance(text, str):
        return []
    cats = HYGIENE_PROMPT_CATS if scope == "prompt" else HYGIENE_CODE_CATS
    findings = []
    seen = set()
    for category in cats:
        for pat in HYGIENE_PATTERNS[category]:
            for m in pat.finditer(text):
                snippet = m.group(0)[:200]
                h = hashlib.sha256(snippet.encode("utf-8", "replace")).hexdigest()[:12]
                key = (category, h)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(key)
    return findings


def _record_findings(day_bucket, findings):
    """Merge findings into day_bucket['hygiene_findings']: {cat: {count, samples:set}}."""
    if day_bucket is None or not findings:
        return
    hf = day_bucket.setdefault("hygiene_findings", {})
    for category, h in findings:
        b = hf.get(category)
        if b is None:
            b = {"count": 0, "samples": set()}
            hf[category] = b
        b["count"] += 1
        if len(b["samples"]) < HYGIENE_SAMPLE_CAP:
            b["samples"].add(h)


# ── Project Detection (CWD-based — no pre-scanning needed) ──

def extract_project_from_path(path_str):
    """Extract project name from any path under home dir.
    /Users/alice/my-project/src/file.py → my-project
    /home/bob/Projects/app/main.go → app  (skips container dirs)
    /home/bob/code → None  (container dir with nothing deeper)
    """
    if not path_str:
        return None
    home = str(Path.home())
    # Normalize separators
    path_str = path_str.replace("\\", "/")
    home = home.replace("\\", "/")
    # Case-insensitive prefix match
    if not path_str.lower().startswith(home.lower()):
        return None
    remainder = path_str[len(home):].strip("/")
    if not remainder:
        return None
    parts = remainder.split("/")
    first_dir = parts[0]
    # Skip hidden/system dirs
    if first_dir.startswith(".") or first_dir.lower() in SKIP_DIRS:
        return None
    # If first dir is a container (Projects, repos, code, etc.), go one level deeper
    if first_dir.lower() in CONTAINER_DIRS:
        if len(parts) >= 2 and parts[1] and not parts[1].startswith("."):
            return parts[1]
        return None  # just the container dir itself, no project
    return first_dir


def detect_project_from_msg(msg):
    """Detect project from CWD, falling back to file paths in tool inputs."""
    # Primary: CWD
    cwd = msg.get("cwd", "")
    if cwd:
        proj = extract_project_from_path(cwd)
        if proj:
            return proj
    # Fallback: file paths in tool inputs
    inner = msg.get("message") or {}
    content = inner.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                tool_input = block.get("input") or {}
                for key in ("file_path", "path"):
                    val = tool_input.get(key, "")
                    if isinstance(val, str) and val:
                        proj = extract_project_from_path(val)
                        if proj:
                            return proj
    return None


def detect_project_from_files(file_paths):
    """Detect project name from the file paths touched in a session.
    Detects home dir from the paths themselves (not Path.home()) so this
    works inside Docker where the host home differs from container home."""
    if not file_paths:
        return None

    # Detect home directory from common path patterns (/Users/X/, /home/X/, C:\\Users\\X\\)
    home = None
    for fp in file_paths:
        if "/Users/" in fp:
            # macOS: /Users/hadi/... → home = /Users/hadi
            idx = fp.index("/Users/")
            parts = fp[idx:].split("/")
            if len(parts) >= 3:
                home = "/".join(parts[:3])  # /Users/hadi
                break
        elif "/home/" in fp:
            # Linux: /home/user/... → home = /home/user
            idx = fp.index("/home/")
            parts = fp[idx:].split("/")
            if len(parts) >= 3:
                home = "/".join(parts[:3])
                break

    if not home:
        # Fallback to Path.home() (works when running natively, not in Docker)
        home = str(Path.home())

    project_votes = {}
    for fp in file_paths:
        if not fp.startswith(home):
            continue
        relative = fp[len(home):].strip("/")
        parts = relative.split("/")
        if not parts or not parts[0]:
            continue
        candidate_lower = parts[0].lower()
        if candidate_lower in SKIP_DIRS or candidate_lower.startswith("."):
            # Try second level for dirs like .claude, Projects, etc.
            if len(parts) > 1 and parts[1] and parts[1].lower() not in SKIP_DIRS and not parts[1].startswith("."):
                candidate = parts[1]
            else:
                continue
        else:
            candidate = parts[0]  # keep original case
        project_votes[candidate] = project_votes.get(candidate, 0) + 1
    if not project_votes:
        return None
    return max(project_votes, key=project_votes.get)


def detect_project_description(proj_name):
    """Try to read a description from common project files."""
    home = Path.home()
    # Check common locations
    for base in (home, home / "Projects", home / "dev", home / "code", home / "repos"):
        p = base / proj_name
        if not p.is_dir():
            continue
        # package.json
        pkg = p / "package.json"
        if pkg.exists():
            try:
                d = json.loads(pkg.read_text(errors="replace"))
                desc = d.get("description", "")
                if desc: return desc[:200]
                name = d.get("name", "")
                if name: return f"Node.js: {name}"
            except (json.JSONDecodeError, OSError):
                pass
        # pyproject.toml
        pyproj = p / "pyproject.toml"
        if pyproj.exists():
            try:
                for line in pyproj.read_text(errors="replace").splitlines():
                    if line.strip().startswith("description"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val: return val[:200]
            except OSError:
                pass
        # README
        for rn in ("README.md", "readme.md", "README.rst", "README"):
            readme = p / rn
            if readme.exists():
                try:
                    for line in readme.read_text(errors="replace").splitlines():
                        stripped = line.strip().lstrip("#").strip()
                        if stripped and len(stripped) > 5 and not stripped.startswith("!["):
                            return stripped[:200]
                except OSError:
                    pass
        return ""
    return ""


# ── Doc-staleness signals (2.9.0) ──
# Cheap, truthful flags about whether a project's narrative docs are still the
# scaffold default (placeholder) and how long since they were touched. Lets the
# leaderboard surface real docs vs fossils — and lets Claude offer to fill them.
# Known scaffold-default journey-data.json shas. A project whose file matches
# ANY of these is an untouched placeholder. Multiple entries keep the rollout
# skew-tolerant (self_update swaps push_stats BEFORE the kit zip, so a machine
# briefly has the new sha but old-default projects) AND keep pre-3.6 default
# files correctly flagged as placeholders.
JOURNEY_DEFAULT_SHAS = frozenset({
    "557e0bf253b6ea7bfbe27f6013ff6ef8af240800406b455a7290c840c1540b7a",  # 3.6 unified default
    "80fa17317c8b0d10aa15a4a475cf0431a0fbb39a91a792c352881abf1fafac14",  # pre-3.6 {phases} default
})
PROJECT_MD_PLACEHOLDER_MARKERS = (
    "One-line description of what this project does. Replace this.",
    "Fill in what this project is trying to achieve",
)


def _find_project_dir(proj_name):
    """Locate a project directory by name across the common project roots."""
    home = Path.home()
    for base in (home, home / "Projects", home / "code", home / "dev", home / "repos"):
        p = base / proj_name
        if p.is_dir():
            return p
    return None


def collect_doc_flags(project_dir):
    """Best-effort doc-freshness flags for one project. Never raises."""
    flags = {}
    try:
        journey = None
        for sub in ("frontend/public", "public"):
            cand = project_dir / sub / "journey-data.json"
            if cand.exists():
                journey = cand
                break
        if journey is not None:
            raw = journey.read_bytes()
            flags["journey_is_placeholder"] = (
                hashlib.sha256(raw).hexdigest() in JOURNEY_DEFAULT_SHAS
            )
            flags["journey_mtime_days"] = int((time.time() - journey.stat().st_mtime) / 86400)

        pm = project_dir / "PROJECT.md"
        if pm.exists():
            txt = pm.read_text(errors="replace")
            flags["project_md_is_placeholder"] = any(
                m in txt for m in PROJECT_MD_PLACEHOLDER_MARKERS
            )
            flags["project_md_mtime_days"] = int((time.time() - pm.stat().st_mtime) / 86400)
    except Exception:  # never raise — doc flags are advisory, never worth a push
        pass
    return flags


# ── Project identity + intent (2.10.0, data-spine phase 1) ──

def _parse_front_matter(text):
    """Parse a leading `--- ... ---` block into {key: value} (stdlib only — no
    yaml dep). Values are stripped of quotes and any trailing # comment."""
    meta = {}
    if not text.startswith("---"):
        return meta
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            # strip only whitespace-preceded inline comments (YAML style) so a
            # literal '#' inside a value (e.g. a URL fragment) survives.
            v = re.sub(r"\s+#.*$", "", v).strip().strip('"').strip("'")
            if k:
                meta[k] = v
    return meta


def collect_project_meta(project_dir):
    """Identity (`.dak/project.json`) + intent (PROJECT.md front-matter) for one
    project. Best-effort, never raises; strictly additive to projects_data."""
    meta = {}
    try:
        dak = project_dir / ".dak" / "project.json"
        if dak.exists():
            d = json.loads(dak.read_text(errors="replace"))
            if isinstance(d, dict):
                for k in ("project_id", "created_utc", "scaffold_kit_version"):
                    if d.get(k):
                        meta[k] = d[k]
                if isinstance(d.get("ports"), dict):
                    meta["ports"] = d["ports"]
        pm = project_dir / "PROJECT.md"
        if pm.exists():
            fm = _parse_front_matter(pm.read_text(errors="replace"))
            for k in ("status", "goal", "domain", "audience"):
                if fm.get(k):
                    meta[k] = fm[k]
            if "project_id" not in meta and fm.get("project_id"):
                meta["project_id"] = fm["project_id"]
    except Exception:
        pass
    return meta


# ── Session Parsing ──

def _classify_tool(name, tool_input):
    """Classify a tool_use into (key, kind, display, server, plugin) for the
    SkillOps breakdown. `key` is a stable, human-readable id used as the dict key.

      • Skill dispatcher  → kind=skill, display=<skill arg>, plugin=<ns before ':'>
      • mcp__server__tool → kind=mcp,   display=<tool>, server=<server>,
                            plugin=<X> when the server is 'plugin_X_Y'
      • everything else   → kind=builtin (Bash, Read, Edit, Task, ...)

    Token attribution is added by the caller; this only does naming/taxonomy.
    """
    name = name or ""
    if name == "Skill":
        skill = ((tool_input or {}).get("skill") or "unknown").strip() or "unknown"
        plugin = skill.split(":")[0] if ":" in skill else ""
        return (f"skill:{skill}", "skill", skill, "", plugin)
    if name.startswith("mcp__"):
        parts = name.split("__")
        server = parts[1] if len(parts) > 1 else "unknown"
        tool = "__".join(parts[2:]) if len(parts) > 2 else (parts[1] if len(parts) > 1 else name)
        plugin = ""
        if server.startswith("plugin_"):
            # plugin_<plugin>_<server> — best-effort split (plugin token first)
            rest = server[len("plugin_"):]
            plugin = rest.split("_")[0]
        return (f"mcp:{server}/{tool}", "mcp", tool, server, plugin)
    return (f"builtin:{name}", "builtin", name, "", "")


def _result_token_estimate(block):
    """~tokens injected back into context by a tool_result block (chars/4)."""
    content = block.get("content")
    chars = 0
    if isinstance(content, str):
        chars = len(content)
    elif isinstance(content, list):
        for c in content:
            if isinstance(c, dict):
                if isinstance(c.get("text"), str):
                    chars += len(c["text"])
                elif c.get("type") == "image":
                    chars += 1500  # nominal: an image block is heavy but not text
    return chars // 4


def _td_row():
    return {"kind": "", "name": "", "server": "", "plugin": "",
            "calls": 0, "gen_tokens": 0, "result_tokens": 0, "models": {},
            "errors": 0, "cmd_calls": 0}


# 2.8.0: skills are also invoked by the user typing /<name> — those don't go
# through the Skill tool and were invisible to 2.7.x. They appear in the JSONL
# as <command-name> tags (in user messages and system/local_command lines).
# CLI built-ins (session plumbing, not skills) are excluded; built-in *skills*
# like /init, /review, /security-review stay countable.
_CMD_RE = re.compile(r"<command-name>\s*/?([^<\s]+)\s*</command-name>")
_CMD_DENYLIST = {
    "clear", "compact", "model", "effort", "plugin", "plugins", "reload-plugins",
    "remote-control", "help", "login", "logout", "status", "config", "cost",
    "doctor", "memory", "bug", "fast", "mcp", "agents", "hooks", "ide", "install",
    "permissions", "resume", "rewind", "terminal-setup", "todos", "vim", "upgrade",
    "usage", "whoami", "exit", "quit", "context", "export", "add-dir", "bashes",
    "statusline", "output-style", "release-notes", "privacy-settings", "theme",
    "migrate-installer", "tasks", "teleport", "workflows", "desktop",
}


def parse_jsonl(filepath):
    """Parse a single JSONL file. Returns stats + detected project + quality metrics."""
    timestamps = []
    human = api = inp_t = out_t = cr_t = cw_t = lines = 0
    cost = 0.0
    models = {}
    project_votes = {}

    # Per-model breakdown
    model_breakdown = {}  # {family: {prompts, input_tokens, output_tokens, cache_read, cache_write, cost}}

    # Quality metrics
    tool_calls = {}       # {tool_name: count}
    # SkillOps: per-tool detail keyed by stable id (skill:/mcp:/builtin:).
    # id_to_key maps a tool_use id -> that key so the later tool_result can
    # attribute its payload size (result_tokens) back to the right tool.
    tool_detail = {}
    id_to_key = {}
    unique_files = set()  # unique file paths touched
    prompt_hashes = set() # hashes of human prompt content
    total_prompt_count = 0
    prompt_previews = []  # [{timestamp, preview, model}] — human prompts with context

    # Per-day buckets for the Productivity page (GST = UTC+4).
    # day_key: YYYY-MM-DD. Each bucket carries everything needed to compute a
    # monthly Q score: active_sec (via timestamps), prompts, api_calls, after_hours,
    # lines, tokens (input/output/cache), tool_calls dict, and file_hashes set
    # for monthly unique-file counting (set-union across days).
    per_day = {}
    def _get_day_bucket(ts):
        day_key = _bucket_date(ts)
        b = per_day.get(day_key)
        if b is None:
            b = {
                "timestamps": [],
                "prompts": 0,
                "api_calls": 0,
                "after_hours_prompts": 0,
                "lines": 0,
                "first_ts_gst": None,
                "last_ts_gst": None,
                # Added for monthly Q (v5 schema)
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read": 0,
                "cache_write": 0,
                # 2.5.4: cost is now bucketed per-message-day, not per-session-start-day,
                # so long-running sessions that span days don't dump all cost on day 1.
                "cost": 0.0,
                "tool_calls": {},
                "models": {},
                # 2.8.0: per-day skill / MCP-server usage for SkillOps trends
                "skills": {},
                "mcp_servers": {},
                "file_hashes": set(),
                "file_extensions": {},
                # 2.6.0: per-day cybersec hygiene findings. {cat: {count, samples:set}}
                "hygiene_findings": {},
            }
            per_day[day_key] = b
        b["timestamps"].append(ts)
        local = ts.astimezone(GST)
        if b["first_ts_gst"] is None or local < b["first_ts_gst"]:
            b["first_ts_gst"] = local
        if b["last_ts_gst"] is None or local > b["last_ts_gst"]:
            b["last_ts_gst"] = local
        return day_key, b

    def _record_command(text, day_bucket):
        """2.8.0: count /<skill> slash-command invocations found in `text`.
        These don't dispatch the Skill tool, so tokens aren't attributable —
        only calls/cmd_calls move (and the per-day skills bucket)."""
        for raw_name in _CMD_RE.findall(text or ""):
            cname = raw_name.strip().strip("/")
            if not cname or cname.lower() in _CMD_DENYLIST:
                continue
            row = tool_detail.setdefault(f"skill:{cname}", _td_row())
            row["kind"] = "skill"
            row["name"] = cname
            if ":" in cname and not row["plugin"]:
                row["plugin"] = cname.split(":")[0]
            row["calls"] += 1
            row["cmd_calls"] += 1
            if day_bucket is not None:
                sk = day_bucket["skills"]
                sk[cname] = sk.get(cname, 0) + 1

    # Pre-pass: count how often each human-prompt content appears in this file.
    # Scheduled / loop-injected prompts (e.g., /loop firing "check discord ..." every minute)
    # show up as normal user messages but repeat ≥3 times. We collapse them to a single
    # count so scheduled automation doesn't inflate human_prompts. First occurrence counts;
    # repeats are skipped entirely.
    DUPLICATE_THRESHOLD = 3
    content_counts = {}
    try:
        with open(filepath, "r", errors="replace") as f:
            for line in f:
                try:
                    msg = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if msg.get("type") != "user" or msg.get("toolUseResult"):
                    continue
                inner_pre = msg.get("message") or {}
                c_pre = inner_pre.get("content", "")
                text_pre = ""
                if isinstance(c_pre, str) and c_pre.strip():
                    text_pre = c_pre.strip()
                elif isinstance(c_pre, list):
                    for c in c_pre:
                        if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                            text_pre = c["text"].strip()
                            break
                if text_pre:
                    key = hashlib.md5(text_pre.encode()).digest()
                    content_counts[key] = content_counts.get(key, 0) + 1
    except OSError:
        pass

    dupe_hashes = {k for k, v in content_counts.items() if v >= DUPLICATE_THRESHOLD}
    seen_once_dupes = set()  # dupe hashes we've already processed (first occurrence kept)

    try:
        with open(filepath, "r", errors="replace") as f:
            for line in f:
                try:
                    msg = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                if msg.get("type") == "file-history-snapshot":
                    continue

                ts = None
                day_bucket = None
                ts_str = msg.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        timestamps.append(ts)
                        _, day_bucket = _get_day_bucket(ts)
                    except (ValueError, TypeError):
                        pass

                # Detect project
                proj = detect_project_from_msg(msg)
                if proj:
                    project_votes[proj] = project_votes.get(proj, 0) + 1

                msg_type = msg.get("type", "")
                inner = msg.get("message") or {}

                # Human prompts
                if msg_type == "user" and not msg.get("toolUseResult"):
                    content = inner.get("content", "")
                    is_human = False
                    prompt_text = ""
                    if isinstance(content, str) and content.strip():
                        is_human = True
                        prompt_text = content.strip()
                    elif isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                                is_human = True
                                prompt_text = c["text"].strip()
                                break
                    if is_human:
                        # Separate "counted" (for human_prompts metric) from
                        # "logged" (for DESC audit archive). Loop-injected
                        # repeats get is_scheduled=True but still ship full
                        # text so the audit trail is complete.
                        full_hash = hashlib.md5(prompt_text.encode()).digest()
                        is_scheduled = full_hash in dupe_hashes
                        is_counted = True
                        if is_scheduled:
                            if full_hash in seen_once_dupes:
                                is_counted = False
                            else:
                                seen_once_dupes.add(full_hash)

                        if is_counted:
                            human += 1
                            total_prompt_count += 1
                            # Diversity hash on first 200 chars — near-dupes
                            # collapse when counting prompt uniqueness.
                            h = hashlib.md5(prompt_text[:200].lower().encode()).hexdigest()
                            prompt_hashes.add(h)
                            if day_bucket is not None:
                                day_bucket["prompts"] += 1
                                if ts is not None and _is_after_hours(ts):
                                    day_bucket["after_hours_prompts"] += 1

                        # Full-text audit log — every occurrence, no truncation.
                        # Field name stays "preview" for backward-compat with
                        # the server-side DB column and frontend drawer.
                        prompt_previews.append({
                            "timestamp": ts_str or "",
                            "preview": prompt_text,
                            "is_scheduled": is_scheduled,
                        })

                        # 2.6.0: scan prompt for skip-intent flags (cybersec hygiene)
                        _record_findings(day_bucket, _scan_hygiene(prompt_text, scope="prompt"))

                        # 2.8.0: typed /<skill> commands arrive as user text
                        _record_command(prompt_text, day_bucket)

                # 2.8.0: some command invocations are logged as system lines
                # (subtype local_command) instead of user text — scan those too.
                # CLI built-ins are denylisted inside _record_command.
                if msg_type == "system" and msg.get("subtype") == "local_command":
                    _record_command(msg.get("content") or "", day_bucket)

                # Tool results (user messages carrying tool_result blocks) —
                # attribute the payload size back to the invoking tool.
                if msg_type == "user":
                    rc = inner.get("content")
                    if isinstance(rc, list):
                        for block in rc:
                            if isinstance(block, dict) and block.get("type") == "tool_result":
                                key = id_to_key.get(block.get("tool_use_id"))
                                if key:
                                    row = tool_detail.setdefault(key, _td_row())
                                    row["result_tokens"] += _result_token_estimate(block)
                                    # 2.8.0: per-tool failure count
                                    if block.get("is_error"):
                                        row["errors"] = row.get("errors", 0) + 1

                # Assistant responses
                if msg_type == "assistant":
                    api += 1
                    model = inner.get("model", "unknown")
                    family = model_family(model)
                    if day_bucket is not None:
                        day_bucket["api_calls"] += 1
                        usage_m = (inner.get("usage") or {})
                        day_bucket["input_tokens"] += usage_m.get("input_tokens", 0) or 0
                        day_bucket["output_tokens"] += usage_m.get("output_tokens", 0) or 0
                        day_bucket["cache_read"] += usage_m.get("cache_read_input_tokens", 0) or 0
                        day_bucket["cache_write"] += usage_m.get("cache_creation_input_tokens", 0) or 0
                        day_bucket["models"][family] = day_bucket["models"].get(family, 0) + 1
                    models[model] = models.get(model, 0) + 1

                    usage = inner.get("usage") or {}
                    i = usage.get("input_tokens", 0) or 0
                    o = usage.get("output_tokens", 0) or 0
                    cr = usage.get("cache_read_input_tokens", 0) or 0
                    cw = usage.get("cache_creation_input_tokens", 0) or 0
                    msg_cost = cost_for(i, o, cr, cw, model)

                    if day_bucket is not None:
                        day_bucket["cost"] += msg_cost

                    inp_t += i; out_t += o; cr_t += cr; cw_t += cw
                    cost += msg_cost

                    # Per-model breakdown
                    if family not in model_breakdown:
                        model_breakdown[family] = {
                            "api_calls": 0, "input_tokens": 0, "output_tokens": 0,
                            "cache_read": 0, "cache_write": 0, "cost": 0.0,
                        }
                    mb = model_breakdown[family]
                    mb["api_calls"] += 1
                    mb["input_tokens"] += i
                    mb["output_tokens"] += o
                    mb["cache_read"] += cr
                    mb["cache_write"] += cw
                    mb["cost"] += msg_cost

                    # SkillOps gen-token attribution: split this turn's output
                    # tokens evenly across the tool_use blocks it emitted (a turn
                    # that calls a tool spent its generation producing that call).
                    _tu = [b for b in (inner.get("content") or [])
                           if isinstance(b, dict) and b.get("type") == "tool_use"]
                    gen_each = (o // len(_tu)) if _tu else 0

                    # Track tool usage and file diversity
                    for block in (inner.get("content") or []):
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            name = block.get("name", "")
                            tool_calls[name] = tool_calls.get(name, 0) + 1
                            if day_bucket is not None:
                                day_bucket["tool_calls"][name] = day_bucket["tool_calls"].get(name, 0) + 1
                            bi = block.get("input") or {}

                            # SkillOps per-tool detail (counts + token attribution)
                            _k, _kind, _disp, _srv, _plg = _classify_tool(name, bi)
                            _row = tool_detail.setdefault(_k, _td_row())
                            _row["kind"] = _kind
                            _row["name"] = _disp
                            _row["server"] = _srv
                            _row["plugin"] = _plg
                            _row["calls"] += 1
                            _row["gen_tokens"] += gen_each
                            # 2.7.1: which model family invoked this tool
                            _m = _row.setdefault("models", {})
                            _m[family] = _m.get(family, 0) + 1
                            # 2.8.0: per-day skill/MCP usage for trends
                            if day_bucket is not None:
                                if _kind == "skill":
                                    _sk = day_bucket["skills"]
                                    _sk[_disp] = _sk.get(_disp, 0) + 1
                                elif _kind == "mcp":
                                    _ms = day_bucket["mcp_servers"]
                                    _ms[_srv] = _ms.get(_srv, 0) + 1
                            bid = block.get("id")
                            if bid:
                                id_to_key[bid] = _k

                            # Lines written
                            line_delta = 0
                            if name == "Write" and bi.get("content"):
                                line_delta = bi["content"].count("\n") + 1
                            elif name == "Edit" and bi.get("new_string"):
                                line_delta = bi["new_string"].count("\n") + 1
                            lines += line_delta
                            if line_delta and day_bucket is not None:
                                day_bucket["lines"] += line_delta

                            # 2.6.0: hygiene scan on tool inputs that execute or
                            # land in files. Bash commands, Write content, Edit
                            # new_string. Skip Read/Glob/Grep — they don't write
                            # state, so anything matched there is incidental.
                            if name == "Bash":
                                cmd = bi.get("command") or ""
                                _record_findings(day_bucket, _scan_hygiene(cmd, scope="code"))
                            elif name == "Write":
                                _record_findings(day_bucket, _scan_hygiene(bi.get("content") or "", scope="code"))
                            elif name == "Edit":
                                _record_findings(day_bucket, _scan_hygiene(bi.get("new_string") or "", scope="code"))

                            # Track unique files (lifetime + per-day hash)
                            for key in ("file_path", "path"):
                                fp = bi.get(key, "")
                                if isinstance(fp, str) and fp and "/" in fp:
                                    unique_files.add(fp)
                                    if day_bucket is not None:
                                        # 8-char hash keeps payload small; collisions near-impossible for per-user scale
                                        fh = hashlib.md5(fp.encode()).hexdigest()[:8]
                                        day_bucket["file_hashes"].add(fh)
                                    # After the unique_files tracking
                                    if day_bucket is not None:
                                        ext = os.path.splitext(fp)[1].lower()
                                        if ext and len(ext) <= 10:  # reasonable extension length
                                            day_bucket["file_extensions"][ext] = day_bucket["file_extensions"].get(ext, 0) + 1
    except OSError:
        pass

    timestamps.sort()
    active = 0
    for idx in range(1, len(timestamps)):
        gap = (timestamps[idx] - timestamps[idx - 1]).total_seconds()
        if gap <= IDLE_THRESHOLD:
            active += gap

    # Per-day active time — same gap algorithm, but bucketed by day of earlier timestamp.
    per_day_final = {}
    for day_key, b in per_day.items():
        ts_list = sorted(b["timestamps"])
        day_active = 0
        for idx in range(1, len(ts_list)):
            gap = (ts_list[idx] - ts_list[idx - 1]).total_seconds()
            if gap <= IDLE_THRESHOLD:
                day_active += gap
        per_day_final[day_key] = {
            "active_sec": int(day_active),
            "prompts": b["prompts"],
            "api_calls": b["api_calls"],
            "after_hours_prompts": b["after_hours_prompts"],
            "lines": b["lines"],
            "first_hhmm": b["first_ts_gst"].strftime("%H:%M") if b["first_ts_gst"] else "",
            "last_hhmm": b["last_ts_gst"].strftime("%H:%M") if b["last_ts_gst"] else "",
            # v5 fields for monthly Q
            "input_tokens": b["input_tokens"],
            "output_tokens": b["output_tokens"],
            "cache_read": b["cache_read"],
            "cache_write": b["cache_write"],
            "cost": round(b.get("cost", 0.0), 2),
            "tool_calls": dict(b["tool_calls"]),
            "models": dict(b.get("models", {})),
            "file_hashes": sorted(b["file_hashes"]),
            "file_extensions": dict(b.get("file_extensions", {})),
            # 2.8.0: capped per-day skill/MCP usage for SkillOps trends
            "skills": dict(sorted((b.get("skills") or {}).items(), key=lambda x: -x[1])[:15]),
            "mcp_servers": dict(sorted((b.get("mcp_servers") or {}).items(), key=lambda x: -x[1])[:15]),
            # 2.6.0: hygiene findings — convert sample sets to sorted lists for JSON
            "hygiene_findings": {
                cat: {"count": v["count"], "samples": sorted(v["samples"])[:HYGIENE_SAMPLE_CAP]}
                for cat, v in (b.get("hygiene_findings") or {}).items()
            },
        }

    dominant_project = max(project_votes, key=project_votes.get) if project_votes else None
    # Fix A: if project is None or "Other", try to detect from file paths
    if not dominant_project or dominant_project == "Other":
        file_project = detect_project_from_files(unique_files)
        if file_project:
            dominant_project = file_project

    return {
        "human_prompts": human, "api_calls": api,
        "input_tokens": inp_t, "output_tokens": out_t,
        "cache_read": cr_t, "cache_write": cw_t,
        "lines_written": lines, "cost": cost,
        "active_seconds": active, "model_usage": models,
        "first_ts": timestamps[0].isoformat() if timestamps else None,
        "last_ts": timestamps[-1].isoformat() if timestamps else None,
        "project": dominant_project,
        # New fields
        "model_breakdown": model_breakdown,
        "tool_calls": tool_calls,
        "tool_detail": tool_detail,
        "unique_files": len(unique_files),
        "unique_prompts": len(prompt_hashes),
        "total_prompt_count": total_prompt_count,
        "prompt_previews": prompt_previews,
        "per_day": per_day_final,
    }


def merge_model_breakdown(target, source):
    """Merge source model_breakdown into target."""
    for family, stats in source.items():
        if family not in target:
            target[family] = {
                "api_calls": 0, "input_tokens": 0, "output_tokens": 0,
                "cache_read": 0, "cache_write": 0, "cost": 0.0,
            }
        for k in ("api_calls", "input_tokens", "output_tokens", "cache_read", "cache_write", "cost"):
            target[family][k] += stats[k]


def merge_tool_calls(target, source):
    """Merge source tool_calls into target."""
    for name, count in source.items():
        target[name] = target.get(name, 0) + count


def merge_tool_detail(target, source):
    """Merge source tool_detail into target: sum counters (incl. per-model
    counts), keep taxonomy strings."""
    for key, row in source.items():
        t = target.setdefault(key, _td_row())
        for f in ("calls", "gen_tokens", "result_tokens", "errors", "cmd_calls"):
            t[f] = t.get(f, 0) + (row.get(f, 0) or 0)
        tm = t.setdefault("models", {})
        for fam, c in (row.get("models") or {}).items():
            tm[fam] = tm.get(fam, 0) + c
        for f in ("kind", "name", "server", "plugin"):
            if not t.get(f) and row.get(f):
                t[f] = row[f]


def merge_daily_buckets(target, source):
    """Merge source per-day buckets into target. Sums counters, merges tool_calls dict,
    unions file_hashes, keeps earliest/latest HH:MM."""
    for day_key, src in source.items():
        if day_key not in target:
            target[day_key] = {
                "active_sec": 0, "prompts": 0, "api_calls": 0,
                "after_hours_prompts": 0, "lines": 0, "sessions": 0, "cost": 0.0,
                "first_hhmm": "", "last_hhmm": "",
                "input_tokens": 0, "output_tokens": 0, "cache_read": 0, "cache_write": 0,
                "tool_calls": {}, "models": {}, "file_hashes": [],
            }
        t = target[day_key]
        t["active_sec"] += src.get("active_sec", 0)
        t["prompts"] += src.get("prompts", 0)
        t["api_calls"] += src.get("api_calls", 0)
        t["after_hours_prompts"] += src.get("after_hours_prompts", 0)
        t["lines"] += src.get("lines", 0)
        # v5 numeric sums
        t["input_tokens"] = t.get("input_tokens", 0) + src.get("input_tokens", 0)
        t["output_tokens"] = t.get("output_tokens", 0) + src.get("output_tokens", 0)
        t["cache_read"] = t.get("cache_read", 0) + src.get("cache_read", 0)
        t["cache_write"] = t.get("cache_write", 0) + src.get("cache_write", 0)
        t["cost"] = round(t.get("cost", 0.0) + src.get("cost", 0.0), 2)
        # 2.6.0: merge hygiene_findings — sum counts, union sample hashes (cap 10)
        t_hf = t.get("hygiene_findings") or {}
        for cat, v in (src.get("hygiene_findings") or {}).items():
            row = t_hf.get(cat) or {"count": 0, "samples": []}
            row["count"] = row.get("count", 0) + (v.get("count", 0) or 0)
            merged = set(row.get("samples") or []) | set(v.get("samples") or [])
            row["samples"] = sorted(merged)[:10]
            t_hf[cat] = row
        t["hygiene_findings"] = t_hf
        # Merge tool_calls dict
        t_tools = t.get("tool_calls") or {}
        for name, count in (src.get("tool_calls") or {}).items():
            t_tools[name] = t_tools.get(name, 0) + count
        t["tool_calls"] = t_tools
        # Merge models dict
        t_models = t.get("models") or {}
        for fam, count in (src.get("models") or {}).items():
            t_models[fam] = t_models.get(fam, 0) + count
        t["models"] = t_models
        # Union file_hashes — stored as sorted list for JSON, re-sort after union
        hset = set(t.get("file_hashes") or [])
        hset.update(src.get("file_hashes") or [])
        t["file_hashes"] = sorted(hset)
        # Merge file_extensions
        t_ext = t.get("file_extensions") or {}
        for ext, count in (src.get("file_extensions") or {}).items():
            t_ext[ext] = t_ext.get(ext, 0) + count
        t["file_extensions"] = t_ext
        # 2.8.0: merge per-day skills / mcp_servers
        for fld in ("skills", "mcp_servers"):
            t_d = t.get(fld) or {}
            for k2, c2 in (src.get(fld) or {}).items():
                t_d[k2] = t_d.get(k2, 0) + c2
            t[fld] = t_d
        # First/last HH:MM across sessions for the same day
        sf, sl = src.get("first_hhmm", ""), src.get("last_hhmm", "")
        if sf and (not t["first_hhmm"] or sf < t["first_hhmm"]):
            t["first_hhmm"] = sf
        if sl and (not t["last_hhmm"] or sl > t["last_hhmm"]):
            t["last_hhmm"] = sl


# M3: Q-score computation lived here as a duplicate of backend/quality_score.py
# Removed 2026-04-17 — server is the single source of truth (see app.py
# leaderboard_submit handler, which overwrites whatever the client sends).
# Keeping a second copy would only invite drift; the authoritative formula
# now exists in one place.


def collect_all_stats():
    """Walk ~/.claude/projects/ and aggregate stats with quality metrics."""
    totals = {
        "total_prompts": 0, "total_api_calls": 0, "total_active_hours": 0,
        "total_subagent_api_calls": 0,
        "total_input_tokens": 0, "total_output_tokens": 0,
        "total_cache_read": 0, "total_cache_write": 0,
        "total_lines_written": 0, "total_cost": 0, "total_sessions": 0,
        "total_projects": 0, "model_usage": {},
        "earliest_session": None, "latest_session": None,
        "projects_data": [],
        # New fields
        "model_breakdown": {},
        "tool_calls": {},
        "tool_detail": {},
        "unique_files": 0,
        "unique_prompts": 0,
        "avg_prompts_per_session": 0,
        "quality_score": 0,
        "sessions_data": [],
        "recent_prompts": [],
        "daily_buckets": {},
    }

    if not PROJECTS_DIR.exists():
        return totals

    # Accumulate per-project stats
    by_project = {}
    all_unique_files = 0
    all_unique_prompts = 0
    all_sessions = []      # per-session detail
    all_prompts = []        # every prompt ever sent — no cap (DESC audit)

    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue

        for f in proj_dir.iterdir():
            if f.suffix != ".jsonl" or f.stat().st_size == 0:
                continue

            s = parse_jsonl(f)

            # Add subagent stats
            sub_api = sub_inp = sub_out = sub_cr = sub_cw = sub_lines = 0
            sub_cost = 0.0
            sub_model_breakdown = {}
            sub_tool_calls = {}
            sub_tool_detail = {}
            session_sub = proj_dir / f.stem / "subagents"
            if session_sub.exists():
                for sf in session_sub.iterdir():
                    if sf.suffix == ".jsonl":
                        sub = parse_jsonl(sf)
                        sub_api += sub["api_calls"]
                        sub_inp += sub["input_tokens"]
                        sub_out += sub["output_tokens"]
                        sub_cr += sub["cache_read"]
                        sub_cw += sub["cache_write"]
                        sub_lines += sub["lines_written"]
                        sub_cost += sub["cost"]
                        merge_model_breakdown(sub_model_breakdown, sub["model_breakdown"])
                        merge_tool_calls(sub_tool_calls, sub["tool_calls"])
                        merge_tool_detail(sub_tool_detail, sub.get("tool_detail") or {})
                        all_unique_files += sub["unique_files"]

            sess_api = s["api_calls"] + sub_api
            sess_inp = s["input_tokens"] + sub_inp
            sess_out = s["output_tokens"] + sub_out
            sess_cr = s["cache_read"] + sub_cr
            sess_cw = s["cache_write"] + sub_cw
            sess_lines = s["lines_written"] + sub_lines
            sess_cost = s["cost"] + sub_cost

            # Global totals
            totals["total_sessions"] += 1
            totals["total_prompts"] += s["human_prompts"]
            totals["total_api_calls"] += sess_api
            totals["total_subagent_api_calls"] += sub_api
            totals["total_input_tokens"] += sess_inp
            totals["total_output_tokens"] += sess_out
            totals["total_cache_read"] += sess_cr
            totals["total_cache_write"] += sess_cw
            totals["total_lines_written"] += sess_lines
            totals["total_cost"] += sess_cost
            totals["total_active_hours"] += s["active_seconds"] / 3600

            for m, c in s["model_usage"].items():
                totals["model_usage"][m] = totals["model_usage"].get(m, 0) + c

            # Merge model breakdown
            merge_model_breakdown(totals["model_breakdown"], s["model_breakdown"])
            merge_model_breakdown(totals["model_breakdown"], sub_model_breakdown)

            # Merge tool calls
            merge_tool_calls(totals["tool_calls"], s["tool_calls"])
            merge_tool_calls(totals["tool_calls"], sub_tool_calls)

            # Merge per-tool SkillOps detail (main session + subagents)
            merge_tool_detail(totals["tool_detail"], s.get("tool_detail") or {})
            merge_tool_detail(totals["tool_detail"], sub_tool_detail)

            # Merge daily buckets — each session's per-day stats roll up into the player's totals
            if s.get("per_day"):
                merge_daily_buckets(totals["daily_buckets"], s["per_day"])

            # Also record one session per day for the sessions count.
            # 2.5.4: cost no longer dumped here — it's now bucketed per-message-day
            # in parse_jsonl, so long sessions don't smear cost onto their start day.
            if s.get("first_ts"):
                try:
                    first_ts = datetime.fromisoformat(s["first_ts"].replace("Z", "+00:00"))
                    day_key = _bucket_date(first_ts)
                    b = totals["daily_buckets"].setdefault(day_key, {
                        "active_sec": 0, "prompts": 0, "api_calls": 0,
                        "after_hours_prompts": 0, "lines": 0, "sessions": 0, "cost": 0.0,
                        "first_hhmm": "", "last_hhmm": "",
                    })
                    b["sessions"] = b.get("sessions", 0) + 1
                except (ValueError, TypeError):
                    pass

            # Accumulate quality metrics
            all_unique_files += s["unique_files"]
            all_unique_prompts += s["unique_prompts"]

            # Collect session detail
            proj_name = s["project"] or "Other"
            all_sessions.append({
                "first_msg_at": s["first_ts"],
                "last_msg_at": s["last_ts"],
                "active_hours": round(s["active_seconds"] / 3600, 2),
                "prompts": s["human_prompts"],
                "api_calls": sess_api,
                "cost": round(sess_cost, 2),
                "lines_written": sess_lines,
                "project": proj_name,
            })

            # Collect prompt previews with project context
            for pp in s.get("prompt_previews", []):
                all_prompts.append({
                    "timestamp": pp["timestamp"],
                    "preview": pp["preview"],
                    "project": proj_name,
                })

            if s["first_ts"]:
                if not totals["earliest_session"] or s["first_ts"] < totals["earliest_session"]:
                    totals["earliest_session"] = s["first_ts"]
            if s["last_ts"]:
                if not totals["latest_session"] or s["last_ts"] > totals["latest_session"]:
                    totals["latest_session"] = s["last_ts"]

            # Per-project accumulation
            proj_name = s["project"] or "Other"
            if proj_name not in by_project:
                by_project[proj_name] = {
                    "name": proj_name, "sessions": 0, "prompts": 0,
                    "api_calls": 0, "active_seconds": 0,
                    "input_tokens": 0, "output_tokens": 0,
                    "cache_read": 0, "cache_write": 0,
                    "lines_written": 0, "cost": 0,
                    "description": detect_project_description(proj_name) if proj_name != "Other" else "",
                    "model_breakdown": {},
                    "tool_calls": {},
                }
            p = by_project[proj_name]
            p["sessions"] += 1
            p["prompts"] += s["human_prompts"]
            p["api_calls"] += sess_api
            p["active_seconds"] += s["active_seconds"]
            p["input_tokens"] += sess_inp
            p["output_tokens"] += sess_out
            p["cache_read"] += sess_cr
            p["cache_write"] += sess_cw
            p["lines_written"] += sess_lines
            p["cost"] += sess_cost
            merge_model_breakdown(p["model_breakdown"], s["model_breakdown"])
            merge_model_breakdown(p["model_breakdown"], sub_model_breakdown)
            merge_tool_calls(p["tool_calls"], s["tool_calls"])
            merge_tool_calls(p["tool_calls"], sub_tool_calls)

    # Finalize totals
    totals["total_cost"] = round(totals["total_cost"], 2)
    totals["total_active_hours"] = round(totals["total_active_hours"], 2)
    totals["total_projects"] = len(by_project)
    totals["unique_files"] = all_unique_files
    totals["unique_prompts"] = all_unique_prompts

    if totals["total_sessions"] > 0:
        totals["avg_prompts_per_session"] = round(
            totals["total_prompts"] / totals["total_sessions"], 1
        )

    # Round model breakdown costs
    for family in totals["model_breakdown"]:
        totals["model_breakdown"][family]["cost"] = round(
            totals["model_breakdown"][family]["cost"], 2
        )

    # Trim daily buckets to the last 90 days (GST)
    today_gst = datetime.now(timezone.utc).astimezone(GST).date()
    cutoff = today_gst - timedelta(days=90)
    totals["daily_buckets"] = {
        k: v for k, v in totals["daily_buckets"].items()
        if _parse_day_key(k) and _parse_day_key(k) >= cutoff
    }

    # Source C: collect tech stack data from projects' public/tech-stack.json
    tech_stacks = {}
    home = Path.home()
    for proj_name in by_project.keys():
        if proj_name == "Other":
            continue
        # Try common project locations
        for base in [home, home / "Projects"]:
            ts_path = base / proj_name / "public" / "tech-stack.json"
            if ts_path.exists():
                try:
                    ts_data = json.loads(ts_path.read_text())
                    tech_stacks[proj_name] = ts_data
                except Exception:
                    pass
                break

    totals["tech_stacks"] = tech_stacks

    # Aggregate file extensions across all days
    all_extensions = {}
    for day_key, bucket in totals["daily_buckets"].items():
        for ext, count in bucket.get("file_extensions", {}).items():
            all_extensions[ext] = all_extensions.get(ext, 0) + count
    totals["file_extensions"] = all_extensions

    # quality_score is NOT computed client-side anymore (M3). Server
    # recomputes from raw inputs on every submit — we just ship a 0 so
    # the payload schema stays stable for older server versions.
    totals["quality_score"] = 0

    # Sessions sorted by time (most recent first)
    totals["sessions_data"] = sorted(
        all_sessions,
        key=lambda x: x["first_msg_at"] or "",
        reverse=True,
    )

    # Recent prompts: last 100, sorted newest first
    all_prompts.sort(key=lambda x: x["timestamp"], reverse=True)
    # No cap — DESC cybersec policy requires full prompt archive per player.
    # Server-side body middleware (50 MB) bounds total payload size.
    totals["recent_prompts"] = all_prompts

    # Exemption: named players opt out of prompt archiving. Their stats still
    # ship (ranking, cost, prompt counters, daily buckets) — only the full
    # text list is blanked. Default "Hadi"; override with PROMPT_LOG_EXEMPT_PLAYERS
    # env var (comma-separated, case-insensitive).
    _exempt = {n.strip().lower() for n in
               os.environ.get("PROMPT_LOG_EXEMPT_PLAYERS", "Hadi").split(",")
               if n.strip()}
    if PLAYER_NAME.strip().lower() in _exempt:
        totals["recent_prompts"] = []
        totals["prompt_log_exempt"] = True
    totals["script_version"] = SCRIPT_VERSION
    totals["kit_version"] = KIT_VERSION_FILE.read_text().strip() if KIT_VERSION_FILE.exists() else ""

    # Build projects_data sorted by cost
    totals["projects_data"] = sorted(
        [
            {
                "name": p["name"], "sessions": p["sessions"], "prompts": p["prompts"],
                "api_calls": p["api_calls"],
                "active_hours": round(p["active_seconds"] / 3600, 2),
                "input_tokens": p["input_tokens"], "output_tokens": p["output_tokens"],
                "cache_read": p["cache_read"], "cache_write": p["cache_write"],
                "lines_written": p["lines_written"], "cost": round(p["cost"], 2),
                "description": p.get("description", ""),
                "model_breakdown": {
                    fam: {k: round(v, 2) if k == "cost" else v for k, v in stats.items()}
                    for fam, stats in p["model_breakdown"].items()
                },
                "tool_calls": p["tool_calls"],
            }
            for p in by_project.values()
        ],
        key=lambda x: x["cost"],
        reverse=True,
    )

    # 2.9.0 doc-staleness flags + 2.10.0 project identity/intent (additive).
    for entry in totals["projects_data"]:
        if entry.get("name") in (None, "Other"):
            continue
        pdir = _find_project_dir(entry["name"])
        if pdir is not None:
            entry.update(collect_doc_flags(pdir))
            pmeta = collect_project_meta(pdir)
            if pmeta:
                entry["project_meta"] = pmeta

    return totals


# ── Local Data Files (auto-update pages) ──

def detect_project_dir():
    """Get the current project directory from CWD."""
    cwd = os.getcwd()
    proj = extract_project_from_path(cwd)
    if proj:
        home = str(Path.home())
        # Reconstruct full project path
        remainder = cwd[len(home):].strip("/")
        parts = remainder.split("/")
        if parts[0].lower() in CONTAINER_DIRS and len(parts) >= 2:
            return Path(home) / parts[0] / parts[1]
        return Path(home) / parts[0]
    return None


def find_public_dir(project_dir):
    """Find where to write JSON files the frontend can serve."""
    # Vite/Vue projects serve from public/
    for sub in ("frontend/public", "public"):
        d = project_dir / sub
        if d.is_dir():
            return d
    # Fallback: project root
    return project_dir


def write_vibe_stats(project_dir, stats):
    """Write vibe-stats.json for the current project."""
    proj_name = project_dir.name
    # Find this project's stats from the collected data
    proj_stats = None
    for p in stats.get("projects_data", []):
        if p["name"].lower() == proj_name.lower():
            proj_stats = p
            break

    if not proj_stats:
        return

    out_dir = find_public_dir(project_dir)
    vibe = {
        "project": proj_stats["name"],
        "prompts": proj_stats["prompts"],
        "api_calls": proj_stats["api_calls"],
        "active_hours": proj_stats["active_hours"],
        "input_tokens": proj_stats["input_tokens"],
        "output_tokens": proj_stats["output_tokens"],
        "total_tokens": proj_stats["input_tokens"] + proj_stats["output_tokens"],
        "cache_read": proj_stats["cache_read"],
        "cache_write": proj_stats["cache_write"],
        "lines_written": proj_stats["lines_written"],
        "cost": proj_stats["cost"],
        "cost_per_prompt": round(proj_stats["cost"] / proj_stats["prompts"], 2) if proj_stats["prompts"] else 0,
        "cost_per_line": round(proj_stats["cost"] / proj_stats["lines_written"], 4) if proj_stats["lines_written"] else 0,
        "sessions": proj_stats["sessions"],
        "model_breakdown": proj_stats.get("model_breakdown", {}),
        "tool_calls": proj_stats.get("tool_calls", {}),
        "updated_at": datetime.now().isoformat(),
    }

    try:
        (out_dir / "vibe-stats.json").write_text(json.dumps(vibe, indent=2))
    except OSError:
        pass


def scan_tech_stack(project_dir):
    """Auto-detect tech stack from project files. Returns a stack dict."""
    stack = {
        "languages": [],
        "frontend": [],
        "backend": [],
        "database": [],
        "ai": [],
        "infra": [],
        "tools": [],
    }

    # ── package.json ──
    pkg_path = project_dir / "package.json"
    if not pkg_path.exists():
        # Check frontend subdirectory
        pkg_path = project_dir / "frontend" / "package.json"

    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(errors="replace"))
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))

            if "typescript" in all_deps or (pkg_path.parent / "tsconfig.json").exists():
                stack["languages"].append("TypeScript")
            else:
                stack["languages"].append("JavaScript")

            # Frontend frameworks
            for dep, name in [("vue", "Vue 3"), ("react", "React"), ("svelte", "Svelte"),
                              ("@angular/core", "Angular"), ("next", "Next.js"), ("nuxt", "Nuxt")]:
                if dep in all_deps:
                    stack["frontend"].append(name)

            # Build tools
            for dep, name in [("vite", "Vite"), ("webpack", "webpack"), ("esbuild", "esbuild"),
                              ("tailwindcss", "Tailwind CSS"), ("d3", "D3.js"),
                              ("vis-network", "vis-network")]:
                if dep in all_deps:
                    stack["tools"].append(name)

            # AI SDKs
            for dep, name in [("@anthropic-ai/sdk", "Claude API"), ("openai", "OpenAI API"),
                              ("@google/generative-ai", "Gemini API")]:
                if dep in all_deps:
                    stack["ai"].append(name)
        except (json.JSONDecodeError, OSError):
            pass

    # ── Python: requirements.txt / pyproject.toml ──
    for req_file in [project_dir / "requirements.txt", project_dir / "backend" / "requirements.txt"]:
        if req_file.exists():
            try:
                reqs = req_file.read_text(errors="replace").lower()
                if "python" not in [l.lower() for l in stack["languages"]]:
                    stack["languages"].append("Python")

                for pkg_name, name in [("fastapi", "FastAPI"), ("flask", "Flask"),
                                        ("django", "Django"), ("uvicorn", "Uvicorn")]:
                    if pkg_name in reqs and name not in stack["backend"]:
                        stack["backend"].append(name)

                for pkg_name, name in [("sqlalchemy", "SQLAlchemy"), ("asyncpg", "asyncpg"),
                                        ("psycopg", "psycopg")]:
                    if pkg_name in reqs and name not in stack["backend"]:
                        stack["backend"].append(name)

                for pkg_name, name in [("anthropic", "Claude API"), ("openai", "OpenAI API"),
                                        ("google-generativeai", "Gemini API")]:
                    if pkg_name in reqs and name not in stack["ai"]:
                        stack["ai"].append(name)
            except OSError:
                pass

    # ── docker-compose.yml ──
    for dc_name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
        dc_path = project_dir / dc_name
        if dc_path.exists():
            try:
                dc_text = dc_path.read_text(errors="replace").lower()
                if "docker" not in stack["infra"]:
                    stack["infra"].append("Docker")
                if "postgres" in dc_text and "PostgreSQL" not in stack["database"]:
                    stack["database"].append("PostgreSQL")
                if "redis" in dc_text and "Redis" not in stack["database"]:
                    stack["database"].append("Redis")
                if "mongo" in dc_text and "MongoDB" not in stack["database"]:
                    stack["database"].append("MongoDB")
                if "mysql" in dc_text and "MySQL" not in stack["database"]:
                    stack["database"].append("MySQL")
            except OSError:
                pass

    # ── SQLite detection ──
    for f in project_dir.rglob("*.db"):
        if "node_modules" not in str(f) and "venv" not in str(f):
            if "SQLite" not in stack["database"]:
                stack["database"].append("SQLite")
            break

    # Remove empty categories
    return {k: v for k, v in stack.items() if v}


def write_tech_stack(project_dir, stats):
    """Write tech-stack.json for the architecture page."""
    out_dir = find_public_dir(project_dir)

    # If tech-stack.json already exists, merge (preserve hand-curated data)
    existing = {}
    ts_path = out_dir / "tech-stack.json"
    if ts_path.exists():
        try:
            existing = json.loads(ts_path.read_text(errors="replace"))
        except (json.JSONDecodeError, OSError):
            pass
    if not isinstance(existing, dict):  # malformed (e.g. a JSON array) — start clean
        existing = {}

    # Auto-detect this project's stack
    detected_stack = scan_tech_stack(project_dir)

    # Build project entry
    proj_entry = {
        "id": project_dir.name,
        "name": project_dir.name,
        "path": str(project_dir),
        "purpose": existing.get("projects", [{}])[0].get("purpose", "") if existing.get("projects") else "",
        "category": "Application",
        "status": "running",
        "ports": {},
        "stack": detected_stack,
    }

    # Preserve hand-curated fields from existing data
    if existing.get("projects"):
        for ep in existing["projects"]:
            if ep.get("id") == project_dir.name:
                proj_entry["purpose"] = ep.get("purpose", proj_entry["purpose"])
                proj_entry["category"] = ep.get("category", proj_entry["category"])
                proj_entry["status"] = ep.get("status", proj_entry["status"])
                proj_entry["ports"] = ep.get("ports", proj_entry["ports"])
                # Merge: keep curated stack items, add auto-detected ones
                curated_stack = ep.get("stack", {})
                for cat, items in detected_stack.items():
                    curated_items = curated_stack.get(cat, [])
                    merged = list(dict.fromkeys(curated_items + items))  # dedupe, preserve order
                    proj_entry["stack"][cat] = merged
                for cat, items in curated_stack.items():
                    if cat not in proj_entry["stack"]:
                        proj_entry["stack"][cat] = items
                break

    # Build the output — keep existing projects, update/add current one
    categories = existing.get("categories", {
        "languages": {"label": "Languages", "color": "#3B82F6"},
        "frontend": {"label": "Frontend", "color": "#8B5CF6"},
        "backend": {"label": "Backend", "color": "#10B981"},
        "database": {"label": "Database", "color": "#F59E0B"},
        "ai": {"label": "AI / ML", "color": "#EC4899"},
        "infra": {"label": "Infrastructure", "color": "#6B7280"},
        "tools": {"label": "Build Tools", "color": "#14B8A6"},
    })

    projects = existing.get("projects", [])
    updated = False
    for i, ep in enumerate(projects):
        if ep.get("id") == project_dir.name:
            projects[i] = proj_entry
            updated = True
            break
    if not updated:
        projects.append(proj_entry)

    # 2.9.0: preserve any pre-existing top-level keys we don't manage (e.g. a
    # legacy "groups" block from an older scaffold, or hand-added metadata)
    # instead of silently dropping them — older scaffolds shipped a different
    # shape and we must not lose hand-curated data on the first push.
    output = dict(existing)
    output.update({
        "schema_version": 2,
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "categories": categories,
        "projects": projects,
        "tech_details": existing.get("tech_details", {}),
    })

    try:
        ts_path.write_text(json.dumps(output, indent=2))
    except OSError:
        pass


def write_local_data(stats):
    """Write vibe-stats.json and tech-stack.json into the current project."""
    try:
        project_dir = detect_project_dir()
        if not project_dir or not project_dir.is_dir():
            return
        write_vibe_stats(project_dir, stats)
        write_tech_stack(project_dir, stats)
    except Exception:
        pass  # silent — never break Claude Code


def push(stats):
    """POST stats to the leaderboard.

    Sends X-Player-Token when we have one cached at TOKEN_FILE. If the
    server bootstraps a new token in the response body (happens once, right
    after admin approval), we persist it silently. Non-2xx status codes are
    logged when run interactively (--force) and swallowed otherwise so the
    Claude Code Stop hook never blocks.
    """
    stats["name"] = PLAYER_NAME
    stats["machine_id"] = get_machine_id()
    stats["hostname"] = get_hostname()
    stats["script_version"] = SCRIPT_VERSION
    stats["kit_version"] = KIT_VERSION_FILE.read_text().strip() if KIT_VERSION_FILE.exists() else ""
    data = json.dumps(stats).encode()

    # Default context verifies the Let's Encrypt cert served by Cloudflare.
    ctx = ssl.create_default_context()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"DAK-LeaderboardPush/{SCRIPT_VERSION}",
    }
    token = read_token()
    if token:
        headers["X-Player-Token"] = token

    req = urllib.request.Request(
        f"{LEADERBOARD_URL.rstrip('/')}/api/leaderboard/submit",
        data=data,
        headers=headers,
        method="POST",
    )
    interactive = "--force" in sys.argv

    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        body = resp.read()
    except urllib.error.HTTPError as e:
        # 401 unauthorized / 403 rejected / 202 pending (enforce mode only).
        # Read body so we can surface a useful message.
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        if interactive:
            try:
                msg = json.loads(body.decode()).get("reason") or e.reason
            except Exception:
                msg = e.reason
            print(f"leaderboard push rejected ({e.code}): {msg}", file=sys.stderr)
        return

    # Server may hand back a freshly-minted token on the bootstrap push that
    # follows admin approval. Cache it for next time.
    try:
        payload = json.loads(body.decode()) if body else {}
    except Exception:
        payload = {}
    new_token = (payload.get("token") or "").strip()
    if new_token and new_token != token:
        write_token(new_token)
        if interactive:
            print("leaderboard enrollment approved — token cached", file=sys.stderr)

    status = payload.get("status")
    if interactive and status and status != "ok":
        msg = payload.get("message") or status
        print(f"leaderboard push status={status}: {msg}", file=sys.stderr)


# ── Self-Update ──

SCRIPT_PATH = Path(__file__).resolve()
UPDATE_CHECK_FILE = Path.home() / ".claude" / ".leaderboard_last_update_check"
UPDATE_CHECK_INTERVAL = 3600  # check for updates once per hour
KIT_VERSION_FILE = Path.home() / ".claude" / ".dak_version"


def _ssl_ctx():
    # Verifying TLS context used by self_update / _update_kit. Previously
    # accepted any cert (CERT_NONE) — that was the MITM-update hole.
    return ssl.create_default_context()


def self_update():
    """Check server for newer push_stats.py and kit files. Update if found."""
    if "--no-update" in sys.argv:
        return False

    # Throttle to once per hour
    if UPDATE_CHECK_FILE.exists():
        try:
            last = float(UPDATE_CHECK_FILE.read_text().strip())
            if time.time() - last < UPDATE_CHECK_INTERVAL:
                return False
        except (ValueError, OSError):
            pass

    try:
        UPDATE_CHECK_FILE.write_text(str(time.time()))
        ctx = _ssl_ctx()

        # 1. Update push_stats.py itself
        _hdrs = {"User-Agent": f"DAK-LeaderboardPush/{SCRIPT_VERSION}"}
        req = urllib.request.Request(f"{LEADERBOARD_URL.rstrip('/')}/push_stats.py", method="GET", headers=_hdrs)
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        remote_code = resp.read()

        local_code = SCRIPT_PATH.read_bytes()
        if hashlib.sha256(local_code).hexdigest() != hashlib.sha256(remote_code).hexdigest():
            SCRIPT_PATH.write_bytes(remote_code)
            os.execv(sys.executable, [sys.executable, str(SCRIPT_PATH), "--no-update"] + sys.argv[1:])

        # 2. Update the full kit (CLAUDE.md, design system, templates, etc.)
        # Opt-out: pass --no-kit to skip the kit download and keep the
        # script + stats push working as normal. Useful for users who
        # maintain their own ~/.claude layout and don't want DAK files
        # landing in their home directory.
        if "--no-kit" not in sys.argv:
            _update_kit(ctx)

    except Exception:
        pass  # silent
    return False


def _update_kit(ctx):
    """Check kit version and update all kit files if newer version available."""
    import zipfile
    import io

    try:
        # Check remote version
        _hdrs = {"User-Agent": f"DAK-LeaderboardPush/{SCRIPT_VERSION}"}
        req = urllib.request.Request(f"{LEADERBOARD_URL.rstrip('/')}/dak-version", method="GET", headers=_hdrs)
        resp = urllib.request.urlopen(req, timeout=5, context=ctx)
        remote_version = resp.read().decode().strip()

        # Check local version
        local_version = ""
        if KIT_VERSION_FILE.exists():
            local_version = KIT_VERSION_FILE.read_text().strip()

        if remote_version == local_version:
            return

        # Download and extract the kit update
        req = urllib.request.Request(f"{LEADERBOARD_URL.rstrip('/')}/dak-update.zip", method="GET", headers=_hdrs)
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        zip_data = resp.read()

        home = Path.home()
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Strip the top-level directory from the zip path
                parts = info.filename.split("/", 1)
                if len(parts) < 2:
                    continue
                relative = parts[1]

                # Route files to their install locations
                make_exec = False
                if relative.startswith("design-system/"):
                    dest = home / relative
                elif relative.startswith("skills/"):
                    dest = home / ".claude" / relative
                elif relative == "CLAUDE.md":
                    dest = home / ".claude" / "CLAUDE.md"
                elif relative.startswith("hooks/"):
                    # Skip — push_stats.py is updated separately above
                    continue
                elif relative in (
                    "stack.md", "git-workflow.md", "deploy.md", "api-patterns.md",
                    # DAK v3.0.0 — new root-level guides that land in ~/.claude/
                    "stack-decisions.md", "conventions-template.md",
                ):
                    dest = home / ".claude" / relative
                elif relative == "project-management.md":
                    dest = home / ".claude" / "project-management-template.md"
                elif relative.startswith("templates/"):
                    dest = home / ".claude" / relative
                elif relative.startswith("dak-template/"):
                    # Project starter that dak-init copies for each new project.
                    dest = home / ".claude" / relative
                elif relative.startswith("bin/"):
                    # CLI tools — land under ~/.claude/bin and need the exec bit.
                    dest = home / ".claude" / relative
                    make_exec = True
                else:
                    continue

                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(info.filename))
                if make_exec:
                    try:
                        dest.chmod(dest.stat().st_mode | 0o111)
                    except Exception:
                        pass

        KIT_VERSION_FILE.write_text(remote_version)
    except Exception:
        pass  # silent


def ensure_cron():
    """One-time setup: add an hourly cron so stats push during long-running sessions.
    Without this, a 10-hour session is invisible until the player closes Claude Code.
    Runs once per machine, then writes a marker file and never runs again."""
    cron_marker = Path.home() / ".claude" / ".cron_installed"
    if cron_marker.exists() or not PLAYER_NAME:
        return
    try:
        import subprocess
        # Check if already in crontab
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""
        if "push_stats.py" in existing:
            cron_marker.write_text("1")
            return
        # Add the hourly entry — uses SCRIPT_PATH so it points to the actual file.
        # If the user invoked this run with --no-kit, carry the flag into the
        # cron entry so their kit-opt-out persists across hourly pushes.
        extra_flags = " --no-kit" if "--no-kit" in sys.argv else ""
        entry = f'0 * * * * PLAYER_NAME="{PLAYER_NAME}" python3 {SCRIPT_PATH} --force{extra_flags} > /dev/null 2>&1'
        lines = [l for l in existing.strip().split("\n") if l.strip()] if existing.strip() else []
        lines.append(entry)
        new_crontab = "\n".join(lines) + "\n"
        proc = subprocess.run(["crontab", "-"], input=new_crontab, capture_output=True, text=True)
        if proc.returncode == 0:
            cron_marker.write_text("1")
    except Exception:
        pass


def ensure_dak_path():
    """One-time: put ~/.claude/bin on PATH via the shell rc so `dak`,
    `dak-init`, etc. are runnable as commands. Idempotent + marker-guarded;
    best-effort — never raises. Mirrors ensure_cron's "modify host config once"
    approach. Without this the kit advertises `dak init` but the command isn't
    found, which blocks non-technical players at the very first keystroke."""
    marker = Path.home() / ".claude" / ".dak_path_installed"
    if marker.exists():
        return
    sentinel = "# DAK CLI on PATH (added by push_stats.py)"
    block = f'\n{sentinel}\nexport PATH="$HOME/.claude/bin:$PATH"\n'
    # Append to whichever rc files already exist; only CREATE a .zshrc (macOS
    # default) on a machine that has neither — never drop a surprise .zshrc on a
    # bash-only box. The leading newline + the ".claude/bin" guard keep it
    # well-formed and idempotent (never a duplicate PATH line).
    rcs = [Path.home() / ".zshrc", Path.home() / ".bashrc"]
    targets = [rc for rc in rcs if rc.exists()] or [Path.home() / ".zshrc"]
    for rc in targets:
        try:
            existing = rc.read_text() if rc.exists() else ""
            if ".claude/bin" in existing:
                continue  # already on PATH (by us or by the user)
            with open(rc, "a") as f:
                f.write(block)
        except OSError:
            pass
    # Mark done unconditionally: the guard above prevents duplicate appends even
    # if this re-runs, and a locked/unwritable rc won't become writable — so
    # retrying every hour would only waste syscalls without ever succeeding.
    try:
        marker.write_text("1")
    except OSError:
        pass


def main():
    if not PLAYER_NAME:
        return

    # Auto-update before doing anything else
    self_update()

    # One-time: ensure hourly cron is set up for mid-session pushes
    ensure_cron()

    # One-time: put ~/.claude/bin on PATH so `dak`/`dak-init` are runnable
    ensure_dak_path()

    if not should_push():
        return

    try:
        stats = collect_all_stats()
        push(stats)
        write_local_data(stats)
        mark_pushed()
    except Exception:
        pass  # silent — don't break Claude Code


if __name__ == "__main__":
    main()
