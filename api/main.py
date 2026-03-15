"""
POC AI Lab — FastAPI Backend
Serves experiment data, AI chat (Gemini), and admin CRUD endpoints.
Includes comprehensive structured logging for monitoring and debugging.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import time
import logging
import traceback
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("poc_ai_lab")

load_dotenv()
logger.info("🚀 POC AI Lab backend starting up…")

# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    exps = load_exps()
    logger.info("✅ Startup complete — %d experiments loaded", len(exps))
    key = get_gemini_key()
    if key:
        logger.info("✅ Gemini API key is configured")
    else:
        logger.warning("⚠️  Gemini API key is NOT configured — chat will fail")
    yield
    logger.info("🛑 Shutting down POC AI Lab backend")

app = FastAPI(title="POC AI Lab API", version="1.0.0", lifespan=lifespan)

# CORS — configurable via ALLOWED_ORIGINS env var
# Testing:    ALLOWED_ORIGINS=*
# Production: ALLOWED_ORIGINS=https://your-domain.vercel.app
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]
logger.info("🌐 CORS allowed origins: %s", ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
DATA_PATH = os.path.join(DATA_DIR, "exps.json")

logger.info("📂 BASE_DIR   = %s", BASE_DIR)
logger.info("📂 DATA_DIR   = %s", DATA_DIR)
logger.info("📂 DATA_PATH  = %s (exists=%s)", DATA_PATH, os.path.exists(DATA_PATH))
logger.info("📂 SETTINGS   = %s (exists=%s)", SETTINGS_PATH, os.path.exists(SETTINGS_PATH))

# ---------------------------------------------------------------------------
# Request Logging Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and its response time."""
    start = time.time()
    method = request.method
    path = request.url.path
    client = request.client.host if request.client else "unknown"
    logger.info("➡️  %s %s from %s", method, path, client)

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        logger.error("💥 %s %s — unhandled exception after %.0fms: %s", method, path, elapsed, exc)
        raise

    elapsed = (time.time() - start) * 1000
    status = response.status_code
    log_fn = logger.warning if status >= 400 else logger.info
    log_fn("⬅️  %s %s → %s (%.0fms)", method, path, status, elapsed)
    return response

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: str, default=None):
    """Read a JSON file, returning *default* if it doesn't exist."""
    if default is None:
        default = {}
    if not os.path.exists(path):
        logger.warning("📄 File not found: %s — returning default", path)
        return default
    try:
        # utf-8-sig strips BOM if present (Windows editors often add it)
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        logger.debug("📄 Read %s — %d top-level keys", path, len(data) if isinstance(data, dict) else 0)
        return data
    except json.JSONDecodeError as e:
        logger.error("📄 JSON parse error in %s: %s", path, e)
        return default
    except Exception as e:
        logger.error("📄 Unexpected error reading %s: %s", path, e)
        return default


def _write_json(path: str, data):
    """Write *data* as pretty-printed JSON."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)
        logger.info("💾 Wrote %s (%d bytes)", path, os.path.getsize(path))
    except PermissionError:
        logger.error("🔒 Permission denied writing to %s — filesystem may be read-only (Vercel?)", path)
        raise
    except Exception as e:
        logger.error("💾 Failed to write %s: %s", path, e)
        raise


def load_settings() -> dict:
    logger.debug("⚙️  Loading settings…")
    return _read_json(SETTINGS_PATH, {"GEMINI_API_KEY": ""})


def save_settings(data: dict):
    logger.info("⚙️  Saving settings…")
    _write_json(SETTINGS_PATH, data)


def load_exps() -> dict:
    logger.debug("🔬 Loading experiments…")
    return _read_json(DATA_PATH, {})


def save_exps(data: dict):
    logger.info("🔬 Saving experiments (%d entries)…", len(data))
    _write_json(DATA_PATH, data)


def get_gemini_key() -> str | None:
    """Return the best available Gemini key (settings.json → env vars)."""
    settings = load_settings()
    key = settings.get("GEMINI_API_KEY", "")
    if key:
        logger.info("🔑 Gemini key loaded from settings.json (ends …%s)", key[-4:] if len(key) > 4 else "****")
        return key
    env_key = os.getenv("GKEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        logger.info("🔑 Gemini key loaded from environment variable (ends …%s)", env_key[-4:] if len(env_key) > 4 else "****")
        return env_key
    logger.error("🔑 No Gemini API key found in settings.json or env vars!")
    return None


def _admin_token() -> str:
    token = os.getenv("ADMIN_TOKEN", "supersecret")
    logger.debug("🛡️  Admin token loaded (length=%d)", len(token))
    return token

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str
    experiment_id: str
    history: Optional[List[dict]] = None


class AdminUpdateRequest(BaseModel):
    secret_token: str
    data: dict
    api_key: Optional[str] = None

# (Startup / Shutdown handled by lifespan context manager above)

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    logger.debug("💓 Health check")
    return {"status": "ok"}


@app.get("/api/experiments")
async def list_experiments():
    """Return a lightweight list of experiments (id + apparatus + thumbnail)."""
    exps = load_exps()
    count = len(exps)
    logger.info("📋 Listing experiments — %d found", count)
    return [
        {
            "id": k,
            "apparatus": v.get("apparatus", "Untitled"),
            "narration_script": v.get("narration_script", ""),
            "thumbnail": v["images"][0] if v.get("images") else None,
        }
        for k, v in exps.items()
    ]


@app.get("/api/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    """Return full detail for a single experiment."""
    logger.info("🔍 Fetching experiment detail: %s", exp_id)
    exps = load_exps()
    if exp_id not in exps:
        logger.warning("❌ Experiment not found: %s (available: %s)", exp_id, list(exps.keys()))
        raise HTTPException(status_code=404, detail="Experiment not found")
    logger.info("✅ Returning detail for %s (%s)", exp_id, exps[exp_id].get("apparatus", "?"))
    return {**exps[exp_id], "id": exp_id}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Send a question to the Gemini model with experiment context."""
    logger.info("💬 Chat request — exp=%s, prompt_length=%d chars", req.experiment_id, len(req.prompt))
    logger.debug("💬 Full prompt: %s", req.prompt[:200])

    exps = load_exps()
    if req.experiment_id not in exps:
        logger.warning("❌ Chat failed — experiment not found: %s", req.experiment_id)
        raise HTTPException(status_code=404, detail="Experiment not found")

    key = get_gemini_key()
    if not key:
        logger.error("🔑 Chat failed — no API key configured")
        raise HTTPException(status_code=500, detail="Gemini API key is not configured. Ask your admin to set it.")

    genai.configure(api_key=key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)
    logger.info("🤖 Using model: %s", model_name)

    exp = exps[req.experiment_id]

    # Build rich context from ALL available experiment fields
    exp_context_lines = []
    if exp.get("apparatus"):
        exp_context_lines.append(f"Apparatus / Equipment: {exp['apparatus']}")
    if exp.get("narration_script"):
        exp_context_lines.append(f"Description / Narration:\n{exp['narration_script']}")
    # Include any extra metadata fields present in the JSON
    skip_fields = {"apparatus", "narration_script", "images", "audio_loc", "qr_addr"}
    for field, value in exp.items():
        if field not in skip_fields and isinstance(value, (str, int, float, bool)):
            exp_context_lines.append(f"{field.replace('_', ' ').title()}: {value}")

    exp_context = "\n".join(exp_context_lines)
    exp_json_snippet = json.dumps(exp, ensure_ascii=False, indent=2)[:1500]  # cap at ~1500 chars

    system_context = (
        "You are an expert AI lab assistant for a metrology and instrumentation lab. "
        "Your role is to help students understand experiments, equipment usage, measurement principles, "
        "calibration procedures, and related theory.\n"
        "Answer accurately and concisely. If the question is unrelated to this experiment, "
        "politely redirect the student.\n\n"
        "=== EXPERIMENT CONTEXT ===\n"
        f"{exp_context}\n\n"
        "=== FULL EXPERIMENT DATA (JSON) ===\n"
        f"{exp_json_snippet}\n"
        "========================"
    )
    full_prompt = f"{system_context}\n\nStudent Question: {req.prompt}"
    logger.debug("🤖 Full prompt length: %d chars", len(full_prompt))

    start = time.time()
    try:
        response = model.generate_content(full_prompt)
        elapsed = (time.time() - start) * 1000
        reply_text = response.text.strip()
        logger.info("✅ Gemini responded in %.0fms — reply_length=%d chars", elapsed, len(reply_text))
        logger.debug("🤖 First 200 chars of reply: %s", reply_text[:200])
        return {"reply": reply_text}
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        logger.error("💥 Gemini API error after %.0fms: %s", elapsed, exc)
        logger.error("💥 Traceback:\n%s", traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}")

# ---------------------------------------------------------------------------
# Admin endpoints  (protected by ADMIN_TOKEN)
# ---------------------------------------------------------------------------

@app.get("/api/admin/settings")
async def admin_get_settings(token: str):
    logger.info("🛡️  Admin settings request")
    if token != _admin_token():
        logger.warning("🚫 Admin auth FAILED — invalid token provided")
        raise HTTPException(status_code=403, detail="Unauthorized")
    logger.info("✅ Admin auth successful — returning settings")
    return load_settings()


@app.post("/api/admin/update")
async def admin_update(req: AdminUpdateRequest):
    logger.info("🛡️  Admin update request — %d experiment entries, api_key_provided=%s",
                len(req.data), req.api_key is not None)
    if req.secret_token != _admin_token():
        logger.warning("🚫 Admin update FAILED — invalid token")
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Save experiment data
    logger.info("💾 Saving %d experiments…", len(req.data))
    save_exps(req.data)

    # Optionally update the API key
    if req.api_key is not None:
        logger.info("🔑 Updating Gemini API key via admin portal")
        settings = load_settings()
        settings["GEMINI_API_KEY"] = req.api_key
        save_settings(settings)

    logger.info("✅ Admin update completed successfully")
    return {"status": "success"}
