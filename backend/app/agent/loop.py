import asyncio
import logging
import httpx
from typing import Dict, Any, Tuple, Optional

from app.config import settings
from app.models.messages import SessionState, LogEntry
from app.models.actions import ActionResponse
from app.events import session_event_hub
from app.safety.validator import SafetyValidator
from app.providers.mock_provider import MockProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.ollama_provider import OllamaProvider
from app.agent.vision import crop_and_zoom_png

logger = logging.getLogger(__name__)

# The universal system prompt instructing the agent on tools and formatting rules.
SYSTEM_PROMPT = """Du bist ein hochentwickelter KI-Desktop-Agent namens "Linux Cowork Agent". Deine Aufgabe ist es, einen isolierten virtuellen Linux-Desktop (Ubuntu XFCE4) zu steuern, um Aufgaben für den Benutzer zu lösen.

Dir steht ein Bildschirm zur Verfügung, und du kannst Tastatur- und Mausaktionen ausführen, Shell-Befehle ausführen und direkt auf das Dateisystem zugreifen.

### KONTROLLMECHANISMEN UND KOORDINATEN
- Die Bildschirmauflösung beträgt üblicherweise 1024x768 Pixel.
- Die Koordinaten beginnen oben links bei (0,0) und enden unten rechts bei (1024,768).
- WICHTIG: Klicke genau in die Mitte der Elemente (z.B. App-Symbole, Eingabefelder, Schaltflächen), die du bedienen möchtest.
- Warte nach dem Öffnen von Apps immer ein paar Sekunden, bis das Fenster geladen ist.
- Wenn dir ein vorheriger Screenshot bereitgestellt wird, vergleiche ihn mit dem aktuellen Screenshot. Nutze diesen Vergleich, um zu prüfen, ob die letzte Aktion gewirkt hat, bevor du die nächste Aktion auswählst.
- Wenn Text, Icons oder Koordinaten unklar sind, nutze zuerst `inspect_region` für einen vergrößerten Ausschnitt. Plane danach Klicks weiterhin im vollständigen Desktop-Koordinatensystem.

### VERFÜGBARE AKTIONEN (TOOLS)
Die Aktion, die du zurückgibst, MUSS genau einem der folgenden Typen entsprechen:

1. `open_app`: Startet eine App im Hintergrund.
   - Parameter: `{"text": "Befehl_zum_Starten"}` (z.B. `firefox`, `xfce4-terminal`, `mousepad`)
2. `mouse_move`: Bewegt den Mauszeiger.
   - Parameter: `{"x": 123, "y": 456}`
3. `left_click`: Führt einen Linksklick aus.
   - Parameter: `{"x": 123, "y": 456}` (x und y optional, klickt sonst auf aktuelle Position)
4. `right_click`: Führt einen Rechtsklick aus.
   - Parameter: `{"x": 123, "y": 456}` (optional)
5. `double_click`: Führt einen Doppelklick aus.
   - Parameter: `{"x": 123, "y": 456}` (optional)
6. `drag`: Zieht die Maus gedrückt an eine Position.
   - Parameter: `{"x": 123, "y": 456}`
7. `scroll`: Scrollt das aktive Fenster.
   - Parameter: `{"clicks": 3, "direction": "down"}` ("up" oder "down")
8. `type_text`: Tippt einen Text auf der Tastatur ein.
   - Parameter: `{"text": "Einzugebender Text"}`
9. `key`: Drückt eine Taste oder Tastenkombination (Hotkeys).
   - Parameter: `{"key": "Taste"}` (z.B. "enter", "backspace", "tab", "ctrl+l", "ctrl+alt+t", "super+d")
10. `wait`: Wartet eine Zeitspanne ab.
    - Parameter: `{"seconds": 3}`
11. `shell_command`: Führt einen Shell-Befehl im Arbeitsverzeichnis (/workspace) aus.
    - Parameter: `{"command": "Befehl"}` (z.B. `ls -la`, `git status`, `python3 test.py`)
12. `read_file`: Liest den Inhalt einer Datei.
    - Parameter: `{"path": "relativer_oder_absoluter_pfad"}`
13. `write_file`: Schreibt oder überschreibt eine Datei.
    - Parameter: `{"path": "pfad", "content": "inhalt"}`
14. `list_files`: Listet die Dateien im aktuellen Arbeitsverzeichnis auf.
    - Parameter: `{"path": "."}`
15. `inspect_region`: Erstellt einen vergrößerten Screenshot-Ausschnitt zur genaueren visuellen Inspektion. Diese Aktion verändert den Desktop nicht.
    - Parameter: `{"x": 100, "y": 100, "width": 240, "height": 180, "scale": 3}`
16. `list_windows`: Listet sichtbare Desktop-Fenster mit IDs, Titeln und Geometrie.
    - Parameter: `{}`
17. `active_window`: Liefert das aktuell aktive Fenster mit ID, Titel und Geometrie.
    - Parameter: `{}`
18. `focus_window`: Fokussiert ein vorhandenes Fenster anhand seiner ID.
    - Parameter: `{"window_id": "0x01200007"}`
19. `close_window`: Schließt ein vorhandenes Fenster anhand seiner ID.
    - Parameter: `{"window_id": "0x01200007"}`
20. `list_apps`: Listet installierte Linux-Desktop-Apps aus `.desktop`-Einträgen.
    - Parameter: `{}`
21. `open_url`: Öffnet eine URL in Firefox.
    - Parameter: `{"url": "https://example.com"}`
22. `clipboard_get`: Liest die X11-Zwischenablage.
    - Parameter: `{}`
23. `clipboard_set`: Setzt die X11-Zwischenablage auf Text.
    - Parameter: `{"text": "Inhalt"}`
24. `ask_user_confirmation`: Fragt den Benutzer explizit um Erlaubnis vor einer potenziell riskanten Aktion.
    - Parameter: `{"message": "Warum brauchst du die Freigabe?"}`
25. `finish`: Beendet die Aufgabe erfolgreich.
    - Parameter: `{}`

### AUSGABEFORMAT
Du MUSS ausschließlich im folgenden strukturierten JSON-Format antworten. Gib keinen Text vor oder nach dem JSON aus. Setze das JSON nicht in zusätzliche Anführungszeichen.

{
  "summary": "Schrittweise Erklärung: Was sehe ich auf dem Screenshot, was plane ich als nächstes und warum?",
  "risk": "low" | "medium" | "high",
  "requires_confirmation": false | true,
  "action": {
    "type": "Name_der_Aktion",
    "params": { ... Parameter ... }
  },
  "done": false | true
}

### SICHERHEITSEINHALTUNG
- Stufe risikoreiche Aktionen immer mit `risk: "high"` und `requires_confirmation: true` ein.
- Wenn du eine Aktion vorschlägst, die Daten löschen (`rm`), Systempakete installieren (`apt`), sudo-Rechte nutzen oder persönliche Daten/Zahlungen eingeben könnte, frage IMMER zuerst um Erlaubnis über `ask_user_confirmation` oder setze `requires_confirmation: true`.
"""

class AgentLoopManager:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def get_provider(self, provider_name: str, api_key: str = "") -> Any:
        provider_name = provider_name.lower()
        if provider_name == "anthropic":
            return AnthropicProvider(api_key or settings.ANTHROPIC_API_KEY)
        elif provider_name == "openai":
            return OpenAIProvider(api_key or settings.OPENAI_API_KEY)
        elif provider_name == "openrouter":
            return OpenRouterProvider(api_key or settings.OPENROUTER_API_KEY)
        elif provider_name == "ollama":
            return OllamaProvider(settings.OLLAMA_API_BASE)
        else:
            return MockProvider()

    async def execute_action_in_sandbox(
        self,
        action_type: str,
        params: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        action_params = dict(params or {})
        action_output = None
        action_error = None

        try:
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
                    "list_files": "/files/list",
                    "focus_window": "/desktop/focus_window",
                    "close_window": "/desktop/close_window",
                    "open_url": "/desktop/open_url",
                    "clipboard_set": "/clipboard"
                }
                get_endpoint_map = {
                    "list_windows": "/desktop/windows",
                    "active_window": "/desktop/active_window",
                    "list_apps": "/desktop/apps",
                    "clipboard_get": "/clipboard"
                }

                if action_type in ["left_click", "right_click", "double_click"]:
                    button = "left" if action_type == "left_click" else ("right" if action_type == "right_click" else "left")
                    click_type = "double" if action_type == "double_click" else "single"
                    action_params = {
                        "x": action_params.get("x"),
                        "y": action_params.get("y"),
                        "button": button,
                        "click_type": click_type
                    }
                    endpoint = "/mouse/click"
                else:
                    endpoint = url_map.get(action_type)

                get_endpoint = get_endpoint_map.get(action_type)
                if get_endpoint:
                    res = await client.get(f"{settings.SANDBOX_AGENT_URL}{get_endpoint}")
                    if res.status_code == 200:
                        action_output = str(res.json())
                    else:
                        action_error = f"Sandbox API returned status {res.status_code}: {res.text}"
                elif endpoint:
                    res = await client.post(f"{settings.SANDBOX_AGENT_URL}{endpoint}", json=action_params)
                    if res.status_code == 200:
                        res_data = res.json()
                        if action_type == "shell_command":
                            action_output = f"Exit code: {res_data.get('exit_code')}\nStdout:\n{res_data.get('stdout')}"
                            if res_data.get("stderr"):
                                action_error = res_data.get("stderr")
                        elif action_type in [
                            "read_file",
                            "write_file",
                            "list_files",
                            "focus_window",
                            "close_window",
                            "open_url",
                            "clipboard_set"
                        ]:
                            action_output = str(res_data)
                        else:
                            action_output = f"Erfolgreich: {res_data}"
                    else:
                        action_error = f"Sandbox API returned status {res.status_code}: {res.text}"
                elif action_type == "wait":
                    wait_seconds = action_params.get("seconds", 2)
                    await asyncio.sleep(float(wait_seconds))
                    action_output = f"Erfolgreich gewartet für {wait_seconds} Sekunden."
                elif action_type == "ask_user_confirmation":
                    action_output = "Nutzerfreigabe wurde bestätigt. Der Agent kann im nächsten Schritt fortfahren."
                elif action_type == "finish":
                    action_output = "Task beendet durch Agent."
                else:
                    action_error = f"Unbekannter Aktionstyp: {action_type}"

        except Exception as e:
            logger.error(f"Error executing action {action_type} in sandbox: {e}")
            action_error = str(e)

        return action_output, action_error, action_params

    async def execute_step(self, session: SessionState, api_key: str = "") -> bool:
        """
        Executes a single step of the agent loop.
        Returns:
            True if the loop should continue, False if it should pause, stop, or complete.
        """
        step = session.current_step
        logger.info(f"Session {session.session_id} - Executing step {step} / {session.max_steps}")

        # 1. Take a screenshot from the sandbox
        screenshot_data = None
        width = 1024
        height = 768
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{settings.SANDBOX_AGENT_URL}/screenshot")
                if res.status_code == 200:
                    res_json = res.json()
                    screenshot_data = res_json.get("image")
                    width = res_json.get("width", 1024)
                    height = res_json.get("height", 768)
                else:
                    logger.error(f"Failed to fetch screenshot from sandbox: status {res.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to sandbox for screenshot: {e}")
            session.status = "error"
            await session_event_hub.publish(session, "session.error", {"error": str(e)})
            return False

        if not screenshot_data:
            # Fallback mock screenshot if connection failed to prevent hard crash
            screenshot_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

        # 2. Get LLM provider
        provider = self.get_provider(session.provider, api_key)
        previous_desktop_log = next(
            (log for log in reversed(session.logs) if log.screenshot_base64 and log.screenshot_role == "desktop"),
            None
        )
        focused_zoom_log = next(
            (log for log in reversed(session.logs) if log.screenshot_base64 and log.screenshot_role == "zoom_region"),
            None
        )
        previous_screenshot_data = previous_desktop_log.screenshot_base64 if previous_desktop_log else None
        focused_screenshot_data = (
            focused_zoom_log.screenshot_base64
            if focused_zoom_log and (not previous_desktop_log or focused_zoom_log.step >= previous_desktop_log.step)
            else None
        )
        compact_history = [
            log.model_dump(exclude={"screenshot_base64"}) for log in session.logs[-5:]
        ]
        
        # 3. Call LLM
        logger.info(f"Calling LLM provider: {session.provider}")
        action_resp: ActionResponse = await provider.generate_action(
            task=session.task,
            screenshot_base64=screenshot_data,
            history=compact_history,
            system_prompt=SYSTEM_PROMPT,
            previous_screenshot_base64=previous_screenshot_data,
            focused_screenshot_base64=focused_screenshot_data,
            model=session.model
        )
        logger.info(f"LLM proposed action: {action_resp.action.type} (Summary: {action_resp.summary})")

        # 4. Safety validation
        risk_level, requires_conf, safety_reason = SafetyValidator.validate_action(
            action_resp.action, 
            settings.DEFAULT_RISK_POLICY
        )

        # Merge local safety check with LLM self-assessment
        requires_confirmation = requires_conf or action_resp.requires_confirmation
        risk = "high" if risk_level == "high" or action_resp.risk == "high" else ("medium" if risk_level == "medium" or action_resp.risk == "medium" else "low")
        if action_resp.action.type == "inspect_region":
            requires_confirmation = False
            risk = "low"

        if requires_confirmation:
            # Loop halts, updates session state
            session.status = "pending_confirmation"
            session.pending_action = action_resp
            logger.warning(f"Action requires user confirmation: {safety_reason}")
            
            # Log the pending action in history so the user sees it in the dashboard log
            pending_log = LogEntry(
                step=step,
                summary=action_resp.summary,
                action_type=action_resp.action.type,
                action_params=action_resp.action.params,
                screenshot_base64=screenshot_data,
                screenshot_role="desktop",
                screenshot_width=width,
                screenshot_height=height,
                risk=risk,
                requires_confirmation=True,
                status="pending"
            )
            session.logs.append(pending_log)
            await session_event_hub.publish(
                session,
                "action.pending_confirmation",
                {"reason": safety_reason}
            )
            return False

        # 5. Execute action in the sandbox
        action_type = action_resp.action.type
        params = action_resp.action.params
        
        logger.info(f"Executing approved action: {action_type} with params {params}")
        
        screenshot_role = "desktop"
        log_screenshot_data = screenshot_data
        log_screenshot_width = width
        log_screenshot_height = height

        if action_type == "inspect_region":
            try:
                log_screenshot_data, params = crop_and_zoom_png(screenshot_data, params, width, height)
                screenshot_role = "zoom_region"
                log_screenshot_width = params["output_width"]
                log_screenshot_height = params["output_height"]
                action_output = (
                    "Zoom-Ausschnitt erstellt: "
                    f"x={params['x']}, y={params['y']}, width={params['width']}, "
                    f"height={params['height']}, scale={params['scale']}."
                )
                action_error = None
            except Exception as e:
                logger.error("Failed to inspect screenshot region: %s", e)
                action_output = None
                action_error = f"Zoom-Ausschnitt konnte nicht erstellt werden: {e}"
        else:
            action_output, action_error, params = await self.execute_action_in_sandbox(action_type, params)

        # 6. Save log entry
        log_entry = LogEntry(
            step=step,
            summary=action_resp.summary,
            action_type=action_type,
            action_params=params,
            screenshot_base64=log_screenshot_data,
            screenshot_role=screenshot_role,
            screenshot_width=log_screenshot_width,
            screenshot_height=log_screenshot_height,
            output=action_output,
            error=action_error,
            risk=risk,
            requires_confirmation=False,
            status="executed" if not action_error else "failed"
        )
        session.logs.append(log_entry)
        session.current_step += 1

        # 7. Check if task completed
        if action_type == "finish" or action_resp.done or session.current_step >= session.max_steps:
            session.status = "completed"
            logger.info(f"Session {session.session_id} completed successfully.")
            await session_event_hub.publish(session, "session.completed")
            return False

        await session_event_hub.publish(session, "log.failed" if action_error else "log.executed")

        # Sleep a bit to let the environment update and visual elements settle
        await asyncio.sleep(2.0)
        return True

    def start_loop(self, session: SessionState, api_key: str = ""):
        """
        Starts the background async task for the session agent loop.
        """
        if session.session_id in self.active_tasks:
            # Clean up old task
            self.stop_loop(session.session_id)
            
        session.status = "running"
        
        async def run():
            try:
                while session.status == "running":
                    should_continue = await self.execute_step(session, api_key)
                    if not should_continue:
                        if session.status == "running":
                            session.status = "completed"
                            await session_event_hub.publish(session, "session.completed")
                        break
            except asyncio.CancelledError:
                logger.info(f"Session {session.session_id} background task was cancelled.")
            except Exception as e:
                logger.error(f"Fatal error in agent loop for session {session.session_id}: {e}")
                session.status = "error"
                await session_event_hub.publish(session, "session.error", {"error": str(e)})
            finally:
                if session.session_id in self.active_tasks:
                    del self.active_tasks[session.session_id]

        task = asyncio.create_task(run())
        self.active_tasks[session.session_id] = task

    def stop_loop(self, session_id: str):
        """
        Stops the running agent loop.
        """
        task = self.active_tasks.get(session_id)
        if task:
            task.cancel()
            del self.active_tasks[session_id]
            logger.info(f"Agent loop task {session_id} stopped.")
            
agent_loop_manager = AgentLoopManager()
