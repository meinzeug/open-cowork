import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.models.messages import SessionState, TaskRequest, ConfirmationRequest
from app.sessions.manager import session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backend_main")

app = FastAPI(title="Linux Cowork Agent Backend", version="1.0")

# Setup CORS to allow React Frontend to connect from any origin (development environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SettingsUpdateRequest(BaseModel):
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    max_steps: Optional[int] = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": {
            "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
            "ollama_base": settings.OLLAMA_API_BASE,
            "sandbox_url": settings.SANDBOX_AGENT_URL
        }
    }


@app.get("/api/sessions", response_model=List[SessionState])
def list_sessions():
    return session_manager.list_sessions()


@app.get("/api/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    return session


@app.post("/api/sessions", response_model=SessionState)
def create_session(req: TaskRequest):
    provider = req.provider or settings.DEFAULT_PROVIDER
    model = req.model or settings.DEFAULT_MODEL
    max_steps = req.max_steps or settings.MAX_STEPS
    
    session = session_manager.create_session(
        task=req.task,
        provider=provider,
        model=model,
        max_steps=max_steps
    )
    return session


@app.post("/api/sessions/{session_id}/start")
def start_session(session_id: str, x_api_key: Optional[str] = Header(None)):
    try:
        session_manager.start_session(session_id, api_key=x_api_key or "")
        return {"success": True, "status": "running"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/pause")
def pause_session(session_id: str):
    try:
        session_manager.pause_session(session_id)
        return {"success": True, "status": "paused"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sessions/{session_id}/stop")
def stop_session(session_id: str):
    try:
        session_manager.stop_session(session_id)
        return {"success": True, "status": "stopped"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sessions/{session_id}/reset")
def reset_session(session_id: str):
    try:
        session_manager.reset_session(session_id)
        return {"success": True, "status": "idle"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sessions/{session_id}/confirm")
async def confirm_action(session_id: str, req: ConfirmationRequest, x_api_key: Optional[str] = Header(None)):
    try:
        await session_manager.confirm_action(
            session_id=session_id, 
            approved=req.approved, 
            feedback=req.feedback,
            api_key=x_api_key or ""
        )
        return {"success": True, "status": "resumed" if req.approved else "stopped"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/screenshot")
async def get_live_screenshot(session_id: str):
    # Proxy screenshot directly from sandbox
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(f"{settings.SANDBOX_AGENT_URL}/screenshot")
            if res.status_code == 200:
                return res.json()
            else:
                raise HTTPException(status_code=502, detail="Sandbox-Screenshot-Dienst fehlgeschlagen")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei Verbindung zur Sandbox: {str(e)}")


@app.get("/api/settings")
def get_settings():
    return {
        "anthropic_api_key_set": bool(settings.ANTHROPIC_API_KEY),
        "openai_api_key_set": bool(settings.OPENAI_API_KEY),
        "openrouter_api_key_set": bool(settings.OPENROUTER_API_KEY),
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "max_steps": settings.MAX_STEPS,
        "sandbox_url": settings.SANDBOX_AGENT_URL,
        "ollama_base": settings.OLLAMA_API_BASE
    }


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    if req.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = req.anthropic_api_key
    if req.openai_api_key is not None:
        settings.OPENAI_API_KEY = req.openai_api_key
    if req.openrouter_api_key is not None:
        settings.OPENROUTER_API_KEY = req.openrouter_api_key
    if req.default_provider is not None:
        settings.DEFAULT_PROVIDER = req.default_provider
    if req.default_model is not None:
        settings.DEFAULT_MODEL = req.default_model
    if req.max_steps is not None:
        settings.MAX_STEPS = req.max_steps
        
    logger.info("Settings updated successfully.")
    return {"success": True, "settings": get_settings()}
