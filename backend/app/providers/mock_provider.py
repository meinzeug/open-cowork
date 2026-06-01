import asyncio
from typing import List, Dict, Any
from app.providers.base import BaseProvider
from app.models.actions import ActionResponse, Action

class MockProvider(BaseProvider):
    async def generate_action(
        self,
        task: str,
        screenshot_base64: str,
        history: List[Dict[str, Any]],
        system_prompt: str,
        previous_screenshot_base64: str | None = None,
        focused_screenshot_base64: str | None = None,
        model: str | None = None
    ) -> ActionResponse:
        # Simulate small network latency
        await asyncio.sleep(1.0)
        
        step = len(history)
        task_lower = task.lower()

        # Workflow 1: Firefox / Search
        if "firefox" in task_lower or "suche" in task_lower or "browser" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich sehe das leere Desktop-System und starte den Webbrowser Firefox.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="open_app", params={"text": "firefox"}),
                    done=False
                )
            elif step == 1:
                return ActionResponse(
                    summary="Firefox wurde gestartet. Ich klicke nun in die Adressleiste, um eine Suche zu starten.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="left_click", params={"x": 300, "y": 80}),
                    done=False
                )
            elif step == 2:
                return ActionResponse(
                    summary="Ich gebe die Suchadresse für Google ein.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="type_text", params={"text": "https://www.google.com"}),
                    done=False
                )
            elif step == 3:
                return ActionResponse(
                    summary="Ich sende den Befehl ab, um die Seite zu laden.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="key", params={"key": "enter"}),
                    done=False
                )
            elif step == 4:
                return ActionResponse(
                    summary="Ich warte kurz, bis Google geladen wurde.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="wait", params={"seconds": 3}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Die Websuche wurde erfolgreich abgeschlossen. Der Browser läuft.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        # Workflow 2: Text files writing / workspace
        elif "datei" in task_lower or "schreibe" in task_lower or "text" in task_lower or "write" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich erstelle eine Textdatei im Arbeitsverzeichnis, um die geforderte Begrüßung zu sichern.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="write_file", params={
                        "path": "hallo.txt", 
                        "content": "Hallo aus dem Linux Cowork Agent! Dieses System funktioniert einwandfrei."
                    }),
                    done=False
                )
            elif step == 1:
                return ActionResponse(
                    summary="Die Datei wurde geschrieben. Ich überprüfe das Dateiverzeichnis, um die Existenz zu verifizieren.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="list_files", params={}),
                    done=False
                )
            elif step == 2:
                return ActionResponse(
                    summary="Die Textdatei existiert im Arbeitsverzeichnis. Ich führe einen Terminalbefehl aus, um ihren Inhalt anzuzeigen.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="shell_command", params={"command": "cat hallo.txt"}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Datei wurde erfolgreich erstellt, verifiziert und gelesen. Aufgabe abgeschlossen.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        # Workflow 3: Danger / Safety Confirmation Testing
        elif "danger" in task_lower or "rm" in task_lower or "lösch" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich lösche eine sensible Datei im Arbeitsverzeichnis. Da es sich um eine Löschaktion handelt, stufen wir dies als riskant ein.",
                    risk="high",
                    requires_confirmation=True,
                    action=Action(type="shell_command", params={"command": "rm -rf /workspace/sensitive_file.txt"}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Die sensible Datei wurde erfolgreich gelöscht. Aufgabe beendet.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        # Workflow 4: Zoom / region inspection
        elif "zoom" in task_lower or "inspect" in task_lower or "ausschnitt" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich erstelle zuerst einen vergrößerten Screenshot-Ausschnitt, um kleine Desktop-Details genauer zu prüfen.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="inspect_region", params={
                        "x": 120,
                        "y": 80,
                        "width": 320,
                        "height": 220,
                        "scale": 3
                    }),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Der vergrößerte Ausschnitt wurde erzeugt und steht für die nächste Planung zur Verfügung.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        # Workflow 5: Native desktop integration
        elif "fenster" in task_lower or "window" in task_lower or "desktop" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich frage die sichtbaren Linux-Desktop-Fenster über die native X11-Fensterverwaltung ab.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="list_windows", params={}),
                    done=False
                )
            elif step == 1:
                return ActionResponse(
                    summary="Ich prüfe zusätzlich das aktuell aktive Fenster, um Fokus und Geometrie zu kennen.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="active_window", params={}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Die Desktop-Fensterintegration wurde erfolgreich abgefragt.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        elif "app" in task_lower or "programm" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich lese den installierten Linux-App-Katalog aus den .desktop-Dateien aus.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="list_apps", params={}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Der App-Katalog wurde erfolgreich abgefragt.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        elif "clipboard" in task_lower or "zwischenablage" in task_lower:
            if step == 0:
                return ActionResponse(
                    summary="Ich setze testweise die X11-Zwischenablage mit einem harmlosen Text.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="clipboard_set", params={"text": "Open Cowork Clipboard Test"}),
                    done=False
                )
            elif step == 1:
                return ActionResponse(
                    summary="Ich lese die X11-Zwischenablage zurück, um die Integration zu verifizieren.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="clipboard_get", params={}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Die Clipboard-Integration wurde erfolgreich geprüft.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )

        # Default Workflow: Echo shell
        else:
            if step == 0:
                return ActionResponse(
                    summary="Ich führe einen einfachen Echo-Befehl aus, um die Terminalfunktionalität zu prüfen.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="shell_command", params={"command": "echo 'Hallo aus der Linux Sandbox!'"}),
                    done=False
                )
            else:
                return ActionResponse(
                    summary="Der Echo-Befehl wurde ausgeführt. Die Sandbox ist bereit.",
                    risk="low",
                    requires_confirmation=False,
                    action=Action(type="finish", params={}),
                    done=True
                )
