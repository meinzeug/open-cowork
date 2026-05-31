import uuid
import logging
from typing import Dict, List, Optional
from app.models.messages import SessionState, LogEntry
from app.agent.loop import agent_loop_manager

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}

    def create_session(
        self,
        task: str,
        provider: str = "mock",
        model: str = "mock-model",
        max_steps: int = 30,
        risk_policy: str = "confirm_high"
    ) -> SessionState:
        session_id = str(uuid.uuid4())[:8]  # Short elegant ID
        state = SessionState(
            session_id=session_id,
            task=task,
            status="idle",
            provider=provider,
            model=model,
            max_steps=max_steps
        )
        self.sessions[session_id] = state
        logger.info(f"Created session {session_id} for task: {task[:30]}...")
        return state

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[SessionState]:
        return list(self.sessions.values())

    def start_session(self, session_id: str, api_key: str = ""):
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} nicht gefunden.")
        
        session.status = "running"
        agent_loop_manager.start_loop(session, api_key)
        logger.info(f"Session {session_id} loop started.")

    def pause_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} nicht gefunden.")
        
        session.status = "paused"
        agent_loop_manager.stop_loop(session_id)
        logger.info(f"Session {session_id} paused.")

    def stop_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} nicht gefunden.")
        
        session.status = "stopped"
        agent_loop_manager.stop_loop(session_id)
        logger.info(f"Session {session_id} stopped.")

    def reset_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} nicht gefunden.")
        
        agent_loop_manager.stop_loop(session_id)
        session.status = "idle"
        session.current_step = 0
        session.logs = []
        session.pending_action = None
        logger.info(f"Session {session_id} reset to idle.")

    async def confirm_action(self, session_id: str, approved: bool, feedback: Optional[str] = None, api_key: str = ""):
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} nicht gefunden.")
            
        if session.status != "pending_confirmation" or not session.pending_action:
            raise ValueError("Keine Aktion wartet auf Bestätigung.")

        pending_action = session.pending_action
        session.pending_action = None

        # Update last pending log entry in history
        if session.logs:
            last_log = session.logs[-1]
            if last_log.status == "pending":
                last_log.confirmed_by_user = approved
                last_log.status = "executed" if approved else "denied"
                if not approved:
                    last_log.error = f"Nutzer hat die Freigabe verweigert: {feedback or 'Kein Feedback'}"

        if not approved:
            # Task aborted
            session.status = "stopped"
            logger.info(f"User denied execution of pending action. Session {session_id} stopped.")
            return

        # Execute the action inside sandbox!
        # Set running state to execute this specific approved action in the background, then resume agent loop!
        session.status = "running"
        
        # Execute in sandbox agent
        action_type = pending_action.action.type
        params = pending_action.action.params
        action_output = None
        action_error = None
        
        logger.info(f"Executing USER CONFIRMED action: {action_type}")
        
        try:
            import httpx
            from app.config import settings
            async with httpx.AsyncClient(timeout=40.0) as client:
                url_map = {
                    "open_app": "/open_app",
                    "mouse_move": "/mouse/move",
                    "left_click": "/mouse/click",
                    "right_click": "/mouse/click",
                    "double_click": "/mouse/click",
                    "drag": "/mouse/drag",
                    "scroll": "/mouse/scroll",
                    "type_text": "/keyboard/type",
                    "key": "/keyboard/key",
                    "shell_command": "/shell",
                    "read_file": "/files/read",
                    "write_file": "/files/write",
                    "list_files": "/files/list"
                }
                
                if action_type in ["left_click", "right_click", "double_click"]:
                    button = "left" if action_type == "left_click" else ("right" if action_type == "right_click" else "left")
                    click_type = "double" if action_type == "double_click" else "single"
                    params = {"x": params.get("x"), "y": params.get("y"), "button": button, "click_type": click_type}
                    endpoint = "/mouse/click"
                else:
                    endpoint = url_map.get(action_type)

                if endpoint:
                    res = await client.post(f"{settings.SANDBOX_AGENT_URL}{endpoint}", json=params)
                    if res.status_code == 200:
                        res_data = res.json()
                        if action_type == "shell_command":
                            action_output = f"Exit code: {res_data.get('exit_code')}\nStdout:\n{res_data.get('stdout')}"
                            if res_data.get("stderr"):
                                action_error = res_data.get("stderr")
                        elif action_type in ["read_file", "write_file", "list_files"]:
                            action_output = str(res_data)
                        else:
                            action_output = f"Erfolgreich: {res_data}"
                    else:
                        action_error = f"Sandbox API returned status {res.status_code}: {res.text}"
                elif action_type == "wait":
                    import asyncio
                    wait_seconds = params.get("seconds", 2)
                    await asyncio.sleep(float(wait_seconds))
                    action_output = f"Erfolgreich gewartet für {wait_seconds} Sekunden."
                elif action_type == "finish":
                    action_output = "Task beendet."
                else:
                    action_error = f"Unbekannter Aktionstyp: {action_type}"
        except Exception as e:
            action_error = str(e)

        # Update log details
        if session.logs:
            last_log = session.logs[-1]
            last_log.output = action_output
            last_log.error = action_error
            last_log.status = "executed" if not action_error else "failed"

        session.current_step += 1
        
        # Resume the background loop!
        agent_loop_manager.start_loop(session, api_key)
        logger.info(f"Session {session_id} resumed background loop after confirmation.")

session_manager = SessionManager()
