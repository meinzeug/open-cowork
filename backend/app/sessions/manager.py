import uuid
import logging
from typing import Dict, List, Optional
from app.models.messages import SessionState
from app.agent.loop import agent_loop_manager
from app.events import session_event_hub

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
        if session.status == "pending_confirmation":
            raise ValueError("Die Sitzung wartet auf eine Sicherheitsfreigabe und kann nicht direkt fortgesetzt werden.")
        
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
            await session_event_hub.publish(session, "session.stopped")
            return

        session.status = "running"
        
        action_type = pending_action.action.type
        params = pending_action.action.params
        
        logger.info(f"Executing USER CONFIRMED action: {action_type}")
        action_output, action_error, params = await agent_loop_manager.execute_action_in_sandbox(action_type, params)

        # Update log details
        if session.logs:
            last_log = session.logs[-1]
            last_log.action_params = params
            last_log.output = action_output
            last_log.error = action_error
            last_log.status = "executed" if not action_error else "failed"

        session.current_step += 1

        if action_type == "finish" or pending_action.done or session.current_step >= session.max_steps:
            session.status = "completed"
            await session_event_hub.publish(session, "session.completed")
            logger.info(f"Session {session_id} completed after confirmed action.")
            return
        
        await session_event_hub.publish(session, "log.failed" if action_error else "log.executed")
        agent_loop_manager.start_loop(session, api_key)
        logger.info(f"Session {session_id} resumed background loop after confirmation.")

session_manager = SessionManager()
