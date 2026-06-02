from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.actions import ActionResponse

class PlanStep(BaseModel):
    description: str
    status: str = "pending"  # pending, in_progress, done

class LogEntry(BaseModel):
    step: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: str
    action_type: str
    action_params: Dict[str, Any]
    screenshot_base64: Optional[str] = None
    screenshot_role: str = "desktop"  # desktop, zoom_region
    screenshot_width: Optional[int] = None
    screenshot_height: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    risk: str = "low"
    requires_confirmation: bool = False
    confirmed_by_user: Optional[bool] = None
    status: str = "pending"  # pending, executed, denied, failed
    screen_change_ratio: Optional[float] = None  # how much the screen changed after this action (0..1)

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
    plan: List[PlanStep] = Field(default_factory=list)
    notes: Optional[str] = None
    stuck_counter: int = 0
    last_change_ratio: Optional[float] = None

class TaskRequest(BaseModel):
    task: str
    provider: Optional[str] = None
    model: Optional[str] = None
    max_steps: Optional[int] = None
    risk_policy: Optional[str] = None

class ConfirmationRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
