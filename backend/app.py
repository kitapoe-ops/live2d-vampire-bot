# live2d_xiaob/backend/app.py
# BAZOOKA Live2D Vanilla Backend — mount static + vampire model + health
# Reference: live2d_xiaob/docs/deployment_spec.md
#
# Architecture (vanilla, minimal):
#   GET  /                          Welcome / index
#   GET  /health                    Health check + telemetry
#   GET  /api/v1/models             List all deployed Live2D models
#   GET  /api/v1/models/{name}      Get one model's metadata
#   WS   /api/v1/live2d/control     60 FPS Live2D parameter push (mock LLM)
#   GET  /static/...                Static model assets (auto via StaticFiles)

import os
import sys
import json
import time
import asyncio
import secrets
import base64
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI(title="BAZOOKA Live2D Backend")


# ---------------------------------------------------------------------------
# Security & cache headers (audit 2026-06-12: address webhint/axe warnings)
#   - X-Content-Type-Options: nosniff   → block MIME sniffing
#   - Cache-Control: no-cache           → HTML files always revalidate (fix cache-control
#                                          missing-for-HTML warning; widget.html changes
#                                          frequently and must not be served stale)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_and_cache_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    path = request.url.path
    if path.endswith(".html") or path == "/" or path.endswith("/"):
        # HTML always revalidate (FastAPI default is no Cache-Control, browser may cache 30 days)
        resp.headers.setdefault("Cache-Control", "no-cache, must-revalidate")
    return resp

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent
STATIC_DIR = BACKEND_DIR / "static"
LIVE2D_DIR = STATIC_DIR / "live2d"

# Mount /static/ for direct asset access
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Ticket-based Auth (in-memory)
# ---------------------------------------------------------------------------
TICKET_STORE: dict = {}


async def validate_ticket(token: str) -> bool:
    if not token or token not in TICKET_STORE:
        return False
    entry = TICKET_STORE[token]
    if entry["expires_at"] < time.time():
        TICKET_STORE.pop(token, None)
        return False
    return True

# ---------------------------------------------------------------------------
# Per-IP connection limiter
# ---------------------------------------------------------------------------
ACTIVE_CONNECTIONS: dict = {}


async def check_connection_limit(client_ip: str) -> bool:
    if ACTIVE_CONNECTIONS.get(client_ip, 0) >= 1:
        return False
    ACTIVE_CONNECTIONS[client_ip] = ACTIVE_CONNECTIONS.get(client_ip, 0) + 1
    return True


def release_connection(client_ip: str) -> None:
    if client_ip in ACTIVE_CONNECTIONS:
        ACTIVE_CONNECTIONS[client_ip] = max(0, ACTIVE_CONNECTIONS[client_ip] - 1)
        if ACTIVE_CONNECTIONS[client_ip] == 0:
            ACTIVE_CONNECTIONS.pop(client_ip, None)


# ---------------------------------------------------------------------------
# Telemetry counters
# ---------------------------------------------------------------------------
TELEMETRY = {
    "total_ws_connections": 0,
    "active_ws_connections": 0,
    "total_frames_pushed": 0,
    "started_at": time.time()
}


# ── MiniMax TTS ──────────────────────────────────────────────────────────────
MINIMAX_TTS_ENDPOINT = "https://api.minimax.chat/v1/t2a_v2"
MINIMAX_GROUP_ID     = os.getenv("MINIMAX_GROUP_ID", "2031609952837050448")

# Voice map: Azure-style names + friendly aliases → MiniMax voice_id.
# Lets the widget keep using familiar names (zh-TW-HsiaoChenNeural, zh-HK-HiuMaanNeural, …)
# while the backend transparently maps to the correct MiniMax voice.
#
# Note: the F/M suffix in some MiniMax voice_ids uses full-width parentheses.
VOICE_MAP: Dict[str, str] = {
    # ── Friendly aliases (recommended) ────────────────────────────────
    "cantonese-female":      "Cantonese_ProfessionalHost（F)",   # 粵語女主持 (default)
    "cantonese-male":        "Cantonese_ProfessionalHost（M)",   # 粵語男主持
    "cantonese-gentle":      "Cantonese_GentleLady",              # 粵語溫柔女聲
    "cantonese-cute":        "Cantonese_CuteGirl",                # 粵語可愛女孩
    "cantonese-playful":     "Cantonese_PlayfulMan",              # 粵語活潑男聲
    "cantonese-kind":        "Cantonese_KindWoman",               # 粵語善良女聲
    "mandarin-female":       "female-tianmei",                    # 普通話甜美女聲
    "mandarin-male":         "presenter_male",                    # 普通話男主播
    "mandarin-shaonv":       "female-shaonv",                     # 普通話少女音色
    "mandarin-yujie":        "female-yujie",                      # 普通話御姐音色
    "mandarin-chengshu":     "female-chengshu",                   # 普通話成熟女性
    # ── Azure-style names (the widget's defaults) ─────────────────────
    "zh-tw-hsiaochenneural":  "female-tianmei",                   # 台灣女聲
    "zh-tw-yunjhenneural":   "presenter_male",                   # 台灣男聲
    "zh-hk-hiumaanneural":   "Cantonese_ProfessionalHost（F)",   # 港式粵語女聲
    "zh-hk-wanluneural":     "Cantonese_ProfessionalHost（M)",   # 港式粵語男聲
    "zh-cn-xiaoxiaoneural":  "female-shaonv",                     # 普通話女聲
    "zh-cn-yunxineural":     "presenter_male",                    # 普通話男聲
    "zh-cn-yunyangneural":   "Chinese (Mandarin)_Male_Announcer",# 普通話新聞男
}

# Friendly reverse-lookup: expose `/api/voices` so the widget can list choices
VOICE_CATALOG = [
    {"id": "cantonese-female",  "lang": "zh-HK", "name": "粵語女主持 (Cantonese female host)"},
    {"id": "cantonese-male",    "lang": "zh-HK", "name": "粵語男主持 (Cantonese male host)"},
    {"id": "cantonese-gentle",  "lang": "zh-HK", "name": "粵語溫柔女聲 (Cantonese gentle lady)"},
    {"id": "cantonese-cute",    "lang": "zh-HK", "name": "粵語可愛女孩 (Cantonese cute girl)"},
    {"id": "cantonese-playful", "lang": "zh-HK", "name": "粵語活潑男聲 (Cantonese playful man)"},
    {"id": "cantonese-kind",    "lang": "zh-HK", "name": "粵語善良女聲 (Cantonese kind woman)"},
    {"id": "mandarin-female",   "lang": "zh-CN", "name": "普通話甜美女聲 (Mandarin sweet female)"},
    {"id": "mandarin-male",     "lang": "zh-CN", "name": "普通話男主播 (Mandarin male presenter)"},
    {"id": "mandarin-shaonv",   "lang": "zh-CN", "name": "普通話少女音色 (Mandarin young girl)"},
    {"id": "mandarin-yujie",    "lang": "zh-CN", "name": "普通話御姐音色 (Mandarin mature lady)"},
    {"id": "mandarin-chengshu", "lang": "zh-CN", "name": "普通話成熟女性 (Mandarin mature woman)"},
]

# Default voice when client doesn't supply one
DEFAULT_VOICE_ID = "cantonese-female"  # user explicit 2026-06-11: 粵語 default


def resolve_voice(voice: str) -> str:
    """Resolve a user-supplied voice name to a MiniMax voice_id.
    Accepts: friendly aliases ('cantonese-female'), Azure names, or raw MiniMax IDs.
    """
    if not voice:
        return VOICE_MAP[DEFAULT_VOICE_ID]
    key = voice.strip().lower()
    if key in VOICE_MAP:
        return VOICE_MAP[key]
    # Already a raw MiniMax voice_id? Pass through.
    return voice

# ---------------------------------------------------------------------------
# LERP-based parameter generator (mock LLM-driven emotion)
# ---------------------------------------------------------------------------
EMOTION_PRESETS = {
    "neutral":  {"ParamAngleX": 0.0,  "ParamMouthOpenY": 0.0, "ParamEyeLOpen": 1.0, "ParamEyeROpen": 1.0},
    "happy":    {"ParamAngleX": 5.0,  "ParamMouthOpenY": 0.6, "ParamEyeLOpen": 0.7, "ParamEyeROpen": 0.7},
    "sad":      {"ParamAngleX": -3.0, "ParamMouthOpenY": 0.1, "ParamEyeLOpen": 0.5, "ParamEyeROpen": 0.5},
    "angry":    {"ParamAngleX": 2.0,  "ParamMouthOpenY": 0.3, "ParamEyeLOpen": 0.9, "ParamEyeROpen": 0.9},
    "surprised":{"ParamAngleX": 0.0,  "ParamMouthOpenY": 1.0, "ParamEyeLOpen": 1.2, "ParamEyeROpen": 1.2},
    "thinking": {"ParamAngleX": -8.0, "ParamMouthOpenY": 0.2, "ParamEyeLOpen": 0.8, "ParamEyeROpen": 0.8}
}

current_emotion = "neutral"
target_params = dict(EMOTION_PRESETS["neutral"])
current_params = dict(EMOTION_PRESETS["neutral"])


def lerp_params() -> dict:
    """Smooth LERP from current -> target. Called per frame at 60 FPS."""
    global current_params
    speed = 0.15
    for k in current_params:
        c = current_params[k]
        t = target_params[k]
        current_params[k] = c + (t - c) * speed
    return current_params


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def index():
    return {
        "service": "BAZOOKA Live2D Backend",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "models": "GET /api/v1/models",
            "model": "GET /api/v1/models/{name}",
            "ticket": "GET /api/v1/auth/ticket",
            "ws": "WS /api/v1/live2d/control?token=***&model=vampire",
            "static": "GET /static/live2d/{model}/..."
        }
    }


@app.get("/health")
async def health():
    uptime_sec = int(time.time() - TELEMETRY["started_at"])
    return {
        "status": "healthy",
        "uptime_sec": uptime_sec,
        "active_connections": TELEMETRY["active_ws_connections"],
        "total_connections": TELEMETRY["total_ws_connections"],
        "total_frames_pushed": TELEMETRY["total_frames_pushed"]
    }


@app.get("/api/v1/models")
async def list_models():
    """List all Live2D models deployed in /static/live2d/."""
    if not LIVE2D_DIR.exists():
        return {"models": []}
    models = []
    for model_dir in LIVE2D_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        # Cubism's model JSON can have various names — find the .model3.json
        model_json = None
        for f in model_dir.glob("*.model3.json"):
            model_json = f
            break
        if not model_json:
            continue
        try:
            with open(model_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        refs = data.get("FileReferences", {})
        models.append({
            "name": model_dir.name,
            "path": f"/static/live2d/{model_dir.name}/",
            "moc": refs.get("Moc", ""),
            "textures": refs.get("Textures", []),
            "physics": refs.get("Physics", ""),
            "display_info": refs.get("DisplayInfo", ""),
            "version": data.get("Version", 3)
        })
    return {"models": models}


@app.get("/api/v1/models/{name}")
async def get_model(name: str):
    """Get one model's full metadata."""
    model_dir = LIVE2D_DIR / name
    if not model_dir.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {name}")
    model_json = None
    for f in model_dir.glob("*.model3.json"):
        model_json = f
        break
    if not model_json:
        raise HTTPException(status_code=404, detail="model3.json not found")
    with open(model_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "name": name,
        "model3_json": data,
        "directory": str(model_dir.absolute())
    }


@app.get("/api/voices")
async def list_voices():
    """Return the curated voice catalog (friendly IDs + Chinese names)."""
    return {"default": DEFAULT_VOICE_ID, "voices": VOICE_CATALOG}


@app.get("/api/tts")
async def tts_endpoint(voice: str = Query(default=DEFAULT_VOICE_ID), text: str = Query(...)):
    """MiniMax TTS proxy — GET /api/tts?text=...&voice=...
    Voice param accepts:
      - Friendly alias: 'cantonese-female', 'mandarin-male', etc.
      - Azure name: 'zh-TW-HsiaoChenNeural', 'zh-HK-HiuMaanNeural', etc.
      - Raw MiniMax voice_id (e.g. 'female-tianmei')
    Returns 502 only when MiniMax itself fails after a successful auth.
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        return Response(status_code=400, media_type="text/plain",
                         content="MINIMAX_API_KEY not set")
    voice_id = resolve_voice(voice)
    try:
        payload = {
            "model": "speech-02-hd",
            "text": text[:150],   # hard cap at 150 chars (≈ 15-25s of speech)
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "format": "mp3",
                "bitrate": 128000,
                "channel": 1,
            },
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{MINIMAX_TTS_ENDPOINT}?group_id={MINIMAX_GROUP_ID}"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return Response(status_code=502,
                             media_type="text/plain",
                             content=f"MiniMax error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        base_status = data.get("base_resp", {}).get("status_code", 0)
        if base_status != 0:
            msg = data.get("base_resp", {}).get("status_msg", "unknown")
            return Response(status_code=502,
                             media_type="text/plain",
                             content=f"MiniMax voice error (voice_id={voice_id}): {msg}")
        audio_data = data.get("data", {}).get("audio", "")
        if not audio_data:
            return Response(status_code=502,
                             media_type="text/plain",
                             content="No audio in MiniMax response")
        # MiniMax returns hex-encoded MP3 in data.audio
        audio_bytes = bytes.fromhex(audio_data)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        return Response(status_code=500, media_type="text/plain",
                         content=f"TTS error: {e}")



@app.get("/api/v1/auth/ticket")
async def issue_ticket(user_id: str = "anonymous"):
    """Issue a one-time ticket for WebSocket auth. 1 hour expiry."""
    ticket = f"tk_{secrets.token_urlsafe(24)}"
    TICKET_STORE[ticket] = {
        "user_id": user_id,
        "expires_at": time.time() + 3600
    }
    return {"ticket": ticket, "expires_in": 3600, "user_id": user_id}


@app.websocket("/api/v1/live2d/control")
async def ws_live2d_control(
    websocket: WebSocket,
    token: str = Query(default=""),
    model: str = Query(default="vampire")
):
    """
    60 FPS Live2D parameter push.
    Auth: ?token=***  Model: ?model=***
    """
    if not await validate_ticket(token):
        await websocket.close(code=4001, reason="Invalid or expired ticket")
        return

    client_ip = websocket.client.host if websocket.client else "unknown"
    if not await check_connection_limit(client_ip):
        await websocket.close(code=4002, reason="Connection limit exceeded for IP")
        return

    await websocket.accept()
    TELEMETRY["total_ws_connections"] += 1
    TELEMETRY["active_ws_connections"] += 1

    FRAME_TIME = 1.0 / 60.0
    next_frame = time.perf_counter()

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "model": model,
            "fps": 60,
            "client_ip": client_ip
        })

        # 60 FPS push loop
        while True:
            now = time.perf_counter()
            if now < next_frame:
                await asyncio.sleep(next_frame - now)
            next_frame += FRAME_TIME
            if next_frame < now - FRAME_TIME:
                next_frame = now + FRAME_TIME

            params = lerp_params()
            await websocket.send_json({
                "type": "frame",
                "model": model,
                "params": params
            })
            TELEMETRY["total_frames_pushed"] += 1

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS Error] {e}", flush=True)
    finally:
        TELEMETRY["active_ws_connections"] = max(0, TELEMETRY["active_ws_connections"] - 1)
        release_connection(client_ip)
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
