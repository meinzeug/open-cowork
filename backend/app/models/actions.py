from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class Action(BaseModel):
    type: str = Field(..., description="Action type: mouse_move, left_click, right_click, double_click, drag, scroll, type_text, key, wait, open_app, shell_command, read_file, write_file, list_files, inspect_region, list_windows, active_window, focus_window, close_window, list_apps, open_url, clipboard_get, clipboard_set, finish, ask_user_confirmation")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters depending on the action type")

class ActionResponse(BaseModel):
    summary: str = Field(..., description="LLM explanation and rationale for the action")
    risk: str = Field("low", description="Risk level: low, medium, high")
    requires_confirmation: bool = Field(False, description="Whether this action requires user confirmation before execution")
    action: Action
    done: bool = Field(False, description="Set to true if the entire user task is completed")
