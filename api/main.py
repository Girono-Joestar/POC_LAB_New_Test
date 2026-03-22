"""
POC AI Lab — FastAPI Backend (v2.0 — MQC LangChain Agent)
Serves experiment data, multi-lab management, LangChain RAG agent chat, and admin CRUD.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os, json, time, logging, traceback
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("poc_ai_lab")

load_dotenv()
logger.info("🚀 POC AI Lab v2.0 — MQC LangChain Agent — starting up…")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.join(BASE_DIR, "..")
DATA_DIR    = os.path.join(ROOT_DIR, "data")
AUDIO_DIR   = os.path.join(ROOT_DIR, "public", "audio")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
DATA_PATH   = os.path.join(DATA_DIR, "exps.json")
LABS_PATH   = os.path.join(DATA_DIR, "labs.json")

# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------
def _read_json(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        logger.warning("📄 File not found: %s", path)
        return default
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception as e:
        logger.error("📄 Error reading %s: %s", path, e)
        return default


def _write_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)
        logger.info("💾 Wrote %s (%d bytes)", path, os.path.getsize(path))
    except PermissionError:
        logger.error("🔒 Permission denied: %s — filesystem may be read-only (Vercel?)", path)
        raise
    except Exception as e:
        logger.error("💾 Write failed: %s: %s", path, e)
        raise


def load_settings() -> dict:
    return _read_json(SETTINGS_PATH, {"universal_api_key": "", "GEMINI_API_KEY": ""})


def save_settings(data: dict):
    _write_json(SETTINGS_PATH, data)


def load_exps() -> dict:
    return _read_json(DATA_PATH, {})


def save_exps(data: dict):
    _write_json(DATA_PATH, data)


def load_labs() -> dict:
    return _read_json(LABS_PATH, {})


def save_labs(data: dict):
    _write_json(LABS_PATH, data)


def get_api_key(lab_id: str = None) -> Optional[str]:
    """
    Key resolution order:
    1. Per-lab override (labs.json → api_key_override)
    2. Universal key (settings.json → universal_api_key)
    3. Legacy (settings.json → NVIDIA_API_KEY / GEMINI_API_KEY)
    4. Env vars: NVIDIA_API_KEY, GKEY, GEMINI_API_KEY
    """
    settings = load_settings()

    if lab_id:
        labs = load_labs()
        lab = labs.get(lab_id, {})
        if not lab.get("use_universal_key", True):
            override = lab.get("api_key_override", "")
            if override:
                logger.info("🔑 Using per-lab key for %s", lab_id)
                return override

    for field in ("universal_api_key", "NVIDIA_API_KEY", "GEMINI_API_KEY"):
        key = settings.get(field, "")
        if key:
            logger.info("🔑 Using settings key (%s)", field)
            return key

    env_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GKEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        logger.info("🔑 Using env var key")
        return env_key

    logger.error("🔑 No API key found!")
    return None


def _admin_token() -> str:
    return os.getenv("ADMIN_TOKEN", "supersecret")


# ---------------------------------------------------------------------------
# Lifespan — RAG build at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    exps = load_exps()
    labs = load_labs()
    logger.info("✅ Startup — %d experiments, %d labs loaded", len(exps), len(labs))

    # Build RAG stores
    # Pre-loading RAG at startup is disabled to avoid rate limits
    # rag_builder.build_all(labs, get_api_key)
    logger.info("🚀 POC AI Lab v2.0 — READY (Lazy Loading enabled)")

    yield
    logger.info("🛑 POC AI Lab shutting down")


app = FastAPI(title="POC AI Lab API v2", version="2.0.0", lifespan=lifespan)

# CORS
_raw = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",")] if _raw != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves public/ files at root locally (Vercel does this automatically via vercel.json)
# Mount at root *last* so it doesn't mask API routes
@app.get("/")
async def root():
    return FileResponse(os.path.join(ROOT_DIR, "public", "index.html"))

@app.get("/secret-admin-portal")
async def admin_portal():
    return FileResponse(os.path.join(ROOT_DIR, "public", "admin_5502.html"))

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    method, path = request.method, request.url.path
    client = request.client.host if request.client else "unknown"
    logger.info("➡️  %s %s from %s", method, path, client)
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error("💥 %s %s — exception: %s", method, path, exc)
        raise
    elapsed = (time.time() - start) * 1000
    logger.info("⬅️  %s %s → %s (%.0fms)", method, path, response.status_code, elapsed)
    return response


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    prompt: str
    experiment_id: str
    history: Optional[List[dict]] = None
    session_id: Optional[str] = "default"


class AdminUpdateRequest(BaseModel):
    secret_token: str
    data: dict
    api_key: Optional[str] = None


class LabCreateRequest(BaseModel):
    secret_token: str
    lab_id: str
    name: str
    description: Optional[str] = ""
    api_key_override: Optional[str] = ""
    use_universal_key: Optional[bool] = True


class ExpCreateRequest(BaseModel):
    secret_token: str
    exp_id: str
    data: dict


class ExpUpdateRequest(BaseModel):
    secret_token: str
    data: dict


class SettingsUpdateRequest(BaseModel):
    secret_token: str
    universal_api_key: Optional[str] = None
    per_lab_keys: Optional[dict] = None   # {lab_id: key}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/labs")
async def list_labs():
    """Return public list of labs (no API keys exposed)."""
    labs = load_labs()
    return [
        {
            "id": k,
            "name": v.get("name", k),
            "description": v.get("description", ""),
            "exp_count": len(v.get("exp_ids", [])),
        }
        for k, v in labs.items()
    ]


@app.get("/api/experiments")
async def list_experiments(lab: Optional[str] = None):
    """Return lightweight experiment list with optional lab filter."""
    exps = load_exps()
    result = []
    for k, v in exps.items():
        if lab and v.get("lab_id") != lab:
            continue
        result.append({
            "id": k,
            "apparatus": v.get("apparatus", "Untitled"),
            "short_desc": v.get("short_desc", v.get("narration_script", "")[:80]),
            "lab_id": v.get("lab_id", ""),
            "thumbnail": v.get("thumbnail") or (v["images"][0] if v.get("images") else ""),
        })
    logger.info("📋 Listing experiments — %d found (lab_filter=%s)", len(result), lab)
    return result


@app.get("/api/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    """Return full experiment detail."""
    exps = load_exps()
    if exp_id not in exps:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {**exps[exp_id], "id": exp_id}


# ---------------------------------------------------------------------------
# Chat — LangChain agent
# ---------------------------------------------------------------------------
@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Send a student question to the LangChain lab agent."""
    logger.info("💬 Chat — exp=%s session=%s prompt_len=%d",
                req.experiment_id, req.session_id, len(req.prompt))

    exps = load_exps()
    if req.experiment_id not in exps:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp = exps[req.experiment_id]
    lab_id = exp.get("lab_id", "MQC")

    api_key = get_api_key(lab_id)
    if not api_key:
        raise HTTPException(status_code=500,
            detail="No API key configured. Ask your admin to set an NVIDIA API key.")

    # Get the lab's RAG retriever
    retriever = None
    try:
        from api import rag_builder
        # Get or build retriever on-demand
        retriever = rag_builder.get_retriever(lab_id)
        if not retriever:
            logger.info("⚡ Building RAG store on-demand for lab: %s", lab_id)
            _, retriever = rag_builder.build_lab_store(lab_id, api_key)
    except Exception as e:
        logger.warning("⚠️ Could not get retriever for lab %s: %s", lab_id, e)

    start = time.time()
    try:
        from api.agent import run_agent
        reply = run_agent(
            lab_id=lab_id,
            exp_id=req.experiment_id,
            exp_data=exp,
            api_key=api_key,
            retriever=retriever,
            session_id=req.session_id or "default",
            user_message=req.prompt,
            history=req.history or [],
        )
        elapsed = (time.time() - start) * 1000
        logger.info("✅ Agent replied in %.0fms — %d chars", elapsed, len(reply))
        return {"reply": reply}
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        logger.error("💥 Agent error after %.0fms: %s\n%s", elapsed, exc, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}")


# ---------------------------------------------------------------------------
# Admin — Settings
# ---------------------------------------------------------------------------
@app.get("/api/admin/settings")
async def admin_get_settings(token: str):
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    settings = load_settings()
    labs = load_labs()
    return {
        "settings": {k: v for k, v in settings.items()},
        "labs": labs,
    }


@app.post("/api/admin/settings")
async def admin_update_settings(req: SettingsUpdateRequest):
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    settings = load_settings()
    if req.universal_api_key is not None:
        settings["universal_api_key"] = req.universal_api_key
        settings["NVIDIA_API_KEY"] = req.universal_api_key  # keep legacy field in sync
        settings["GEMINI_API_KEY"] = req.universal_api_key 
    save_settings(settings)

    if req.per_lab_keys:
        labs = load_labs()
        for lab_id, key in req.per_lab_keys.items():
            if lab_id in labs:
                labs[lab_id]["api_key_override"] = key
        save_labs(labs)

    return {"status": "success"}


# ---------------------------------------------------------------------------
# Admin — Labs
# ---------------------------------------------------------------------------
@app.get("/api/admin/labs")
async def admin_list_labs(token: str):
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    return load_labs()


@app.post("/api/admin/labs")
async def admin_create_lab(req: LabCreateRequest):
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    labs = load_labs()
    if req.lab_id in labs:
        raise HTTPException(status_code=409, detail="Lab ID already exists")
    labs[req.lab_id] = {
        "name": req.name,
        "description": req.description,
        "api_key_override": req.api_key_override,
        "use_universal_key": req.use_universal_key,
        "exp_ids": [],
    }
    save_labs(labs)
    logger.info("✅ Created lab: %s", req.lab_id)
    return {"status": "created", "lab_id": req.lab_id}


@app.delete("/api/admin/labs/{lab_id}")
async def admin_delete_lab(lab_id: str, token: str):
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    labs = load_labs()
    if lab_id not in labs:
        raise HTTPException(status_code=404, detail="Lab not found")
    del labs[lab_id]
    save_labs(labs)
    logger.info("🗑️ Deleted lab: %s", lab_id)
    return {"status": "deleted", "lab_id": lab_id}


@app.put("/api/admin/labs/{lab_id}")
async def admin_update_lab(lab_id: str, req: LabCreateRequest):
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    labs = load_labs()
    if lab_id not in labs:
        raise HTTPException(status_code=404, detail="Lab not found")
    labs[lab_id].update({
        "name": req.name,
        "description": req.description,
        "api_key_override": req.api_key_override,
        "use_universal_key": req.use_universal_key,
    })
    save_labs(labs)
    return {"status": "updated", "lab_id": lab_id}


# ---------------------------------------------------------------------------
# Admin — Experiments CRUD
# ---------------------------------------------------------------------------
@app.post("/api/admin/labs/{lab_id}/experiments")
async def admin_add_experiment(lab_id: str, req: ExpCreateRequest):
    """Add a new experiment to a lab."""
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")

    exps = load_exps()
    labs = load_labs()

    if req.exp_id in exps:
        raise HTTPException(status_code=409, detail="Experiment ID already exists")

    exp_data = dict(req.data)
    exp_data["lab_id"] = lab_id
    exp_data.setdefault("audio_loc", f"audio/{req.exp_id}.mp3")
    exp_data.setdefault("thumbnail", "")
    exp_data.setdefault("images", [])

    exps[req.exp_id] = exp_data

    # Register in lab
    if lab_id in labs:
        if req.exp_id not in labs[lab_id]["exp_ids"]:
            labs[lab_id]["exp_ids"].append(req.exp_id)
        save_labs(labs)

    save_exps(exps)

    # Invalidate RAG cache so next chat picks up new experiment
    try:
        from api.rag_builder import invalidate
        invalidate(lab_id)
    except Exception:
        pass

    logger.info("✅ Added experiment %s to lab %s", req.exp_id, lab_id)
    return {"status": "created", "exp_id": req.exp_id}


@app.put("/api/admin/experiments/{exp_id}")
async def admin_update_experiment(exp_id: str, req: ExpUpdateRequest):
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    exps = load_exps()
    if exp_id not in exps:
        raise HTTPException(status_code=404, detail="Experiment not found")

    old_lab = exps[exp_id].get("lab_id")
    exps[exp_id].update(req.data)
    save_exps(exps)

    # Invalidate RAG
    try:
        from api.rag_builder import invalidate
        invalidate(old_lab or "MQC")
    except Exception:
        pass

    logger.info("✅ Updated experiment: %s", exp_id)
    return {"status": "updated", "exp_id": exp_id}


@app.delete("/api/admin/experiments/{exp_id}")
async def admin_delete_experiment(exp_id: str, token: str):
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    exps = load_exps()
    if exp_id not in exps:
        raise HTTPException(status_code=404, detail="Experiment not found")

    lab_id = exps[exp_id].get("lab_id")
    del exps[exp_id]
    save_exps(exps)

    # Remove from labs.json
    if lab_id:
        labs = load_labs()
        if lab_id in labs and exp_id in labs[lab_id].get("exp_ids", []):
            labs[lab_id]["exp_ids"].remove(exp_id)
            save_labs(labs)

    # Invalidate RAG
    try:
        from api.rag_builder import invalidate
        invalidate(lab_id or "MQC")
    except Exception:
        pass

    logger.info("🗑️ Deleted experiment: %s", exp_id)
    return {"status": "deleted", "exp_id": exp_id}


# ---------------------------------------------------------------------------
# Admin — Audio generation (runs locally; returns 501 on Vercel read-only)
# ---------------------------------------------------------------------------
@app.post("/api/admin/experiments/{exp_id}/generate-audio")
async def admin_generate_audio(exp_id: str, token: str):
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")

    exps = load_exps()
    if exp_id not in exps:
        raise HTTPException(status_code=404, detail="Experiment not found")

    os.makedirs(AUDIO_DIR, exist_ok=True)
    out_path = os.path.join(AUDIO_DIR, f"{exp_id}.mp3")

    # Check if filesystem is writable
    try:
        test = os.path.join(AUDIO_DIR, ".write_test")
        with open(test, "w") as f:
            f.write("test")
        os.remove(test)
    except PermissionError:
        raise HTTPException(status_code=501,
            detail="Audio generation is not available on the deployed server (filesystem is read-only). "
                   "Run generate_audio.py locally and redeploy.")

    try:
        from gtts import gTTS
        exp = exps[exp_id]
        text = exp.get("narration_script", exp.get("short_desc", exp.get("apparatus", exp_id)))
        text = text.replace("\n\n", "... ").strip()

        if not text:
            raise HTTPException(status_code=400, detail="No narration text available for this experiment")

        tts = gTTS(text=text[:4000], lang="en", slow=False)
        tts.save(out_path)
        size = os.path.getsize(out_path)
        logger.info("🎙️ Generated audio for %s: %s (%d bytes)", exp_id, out_path, size)
        return {"status": "generated", "file": f"audio/{exp_id}.mp3", "size_bytes": size}
    except Exception as e:
        logger.error("❌ Audio generation failed for %s: %s", exp_id, e)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {e}")


# ---------------------------------------------------------------------------
# Legacy admin/update endpoint (backward compat)
# ---------------------------------------------------------------------------
@app.post("/api/admin/update")
async def admin_update(req: AdminUpdateRequest):
    if req.secret_token != _admin_token():
        raise HTTPException(status_code=403, detail="Unauthorized")
    save_exps(req.data)
    if req.api_key is not None:
        settings = load_settings()
        settings["GEMINI_API_KEY"] = req.api_key
        settings["universal_api_key"] = req.api_key
        save_settings(settings)
    logger.info("✅ Legacy admin update completed — %d experiments", len(req.data))
    return {"status": "success"}

# ---------------------------------------------------------------------------
# Static mounting (only for local dev)
# Vercel handles static files via vercel.json — mounting here would crash the
# serverless function because StaticFiles validates the directory at import time
# and the path resolution differs in the Lambda environment.
# ---------------------------------------------------------------------------
if not os.getenv("VERCEL"):
    try:
        _static_dir = os.path.join(ROOT_DIR, "public")
        if os.path.isdir(_static_dir):
            app.mount("/", StaticFiles(directory=_static_dir, html=True), name="public")
            logger.info("📂 Mounted StaticFiles from %s (local dev mode)", _static_dir)
        else:
            logger.warning("📂 Static dir not found: %s — skipping mount", _static_dir)
    except Exception as _e:
        logger.warning("📂 Could not mount StaticFiles: %s — skipping", _e)
