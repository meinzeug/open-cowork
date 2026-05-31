from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.actions import ActionResponse

class LogEntry(BaseModel):
    step: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: str
    action_type: str
    action_params: Dict[str, Any]
    screenshot_base64: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    risk: str = "low"
    requires_confirmation: bool = False
    confirmed_by_user: Optional[bool] = None
    status: str = "pending"  # pending, executed, denied, failed

class SessionState(BaseModel):
    session_id: str
    task: str
    status: str = "idle"  # idle, running, paused, pending_confirmation, stopped, completed, error
    provider: str
    model: str
    current_step: int = 0
    max_steps: int = 30
    logs: List[LogEntry] = Field(default_factory=list)
    pending_action: Optional[ActionResponse] = None

class TaskRequest(BaseModel):
    task: str
    provider: Optional[str] = None
    model: Optional[str] = None
    max_steps: Optional[int] = None
    risk_policy: Optional[str] = None

class ConfirmationRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
