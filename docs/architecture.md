# Systemarchitektur - Linux Cowork Agent

## Übersicht

Der **Linux Cowork Agent** besteht aus einer dreigeteilten, isolierten Container-Struktur, die über ein geschlossenes Netzwerk kommuniziert. 

```
                                  +-----------------------+
                                  |   Nutzer-Browser      |
                                  +-----------+-----------+
                                              |
                            HTTP / WebSocket  |  noVNC Stream (Port 6080)
                                              v
+------------------+  REST API    +-----------+-----------+
|  backend         | ------------>|  sandbox (Ubuntu)     |
|  (FastAPI)       |              |  - Xvfb (Display :1)  |
|  Port 8000       |              |  - XFCE4 Desktop      |
+--------+---------+              |  - TigerVNC / noVNC   |
         |                        |  - Sandbox Agent API  |
         | REST API               +-----------------------+
         v
+--------+---------+
|  LLM Provider    | (Claude / OpenAI / Ollama)
+------------------+
```

## Container-Rollen

### 1. `sandbox` (Virtueller Desktop)
Der Sandbox-Container stellt das isolierte Betriebssystem dar:
- **Xvfb**: Ein virtueller Framebuffer, der einen X11-Server ohne physische Grafikkarte emuliert.
- **XFCE4**: Eine ressourcenschonende Desktop-Umgebung mit allen Standardprogrammen (Terminal, Texteditor, Dateimanager).
- **VNC & noVNC**: TigerVNC/x11vnc stellt den Bildschirminhalt auf Port 5900 bereit. Websockify (noVNC) übersetzt diesen Stream in WebSockets und stellt eine HTML5-Oberfläche auf Port 6080 zur Verfügung.
- **Sandbox Agent**: Eine Python FastAPI REST-API, die intern auf Port 5001 läuft. Sie erhält Anweisungen wie `/mouse/click`, `/keyboard/type`, `/shell`, `/screenshot`, `/desktop/windows`, `/desktop/apps` oder `/clipboard` und führt diese mithilfe von `pyautogui`, `xdotool`, `wmctrl`, `xclip` und `scrot` direkt im virtuellen Desktop aus.

### 2. `backend` (FastAPI Server)
Das Backend steuert den intelligenten Agenten-Loop und verwaltet den Status:
- **Session-Management**: Erstellt, pausiert, stoppt und setzt Agentensitzungen in einem thread-sicheren In-Memory-Speicher zurück.
- **Agent Loop**: Holt in jedem Schritt einen Screenshot aus der Sandbox, leitet diesen zusammen mit der Aufgabe, der kompakten Historie, dem vorherigen Screenshot und optional einem vergrößerten `inspect_region`-Ausschnitt an das LLM weiter, holt die strukturierte JSON-Aktion ab, jagt sie durch die Sicherheitsprüfung und führt sie in der Sandbox aus.
- **Autonomie-Schicht**: Der Agent pflegt pro Sitzung einen Arbeitsplan aus Teilschritten (`update_plan`), persistente Notizen als Gedächtnis und reflektiert nach jedem Schritt. Der Loop erkennt wiederholte, wirkungslose Aktionen (Stillstand) und injiziert eine Strategie-Aufforderung in den Kontext des nächsten Schritts.
- **Bildschirmwahrnehmung**: Vor dem LLM-Aufruf kann der Loop dem Screenshot ein beschriftetes Koordinatenraster überlagern (`annotate_grid`), damit das Modell exakte Pixelkoordinaten ablesen kann; der Original-Screenshot wird unverändert für Log und UI gespeichert. Zusätzlich misst `compute_change_ratio` die Änderungsrate zwischen aufeinanderfolgenden Screenshots. Aktionen mit zu geringer Wirkung werden als wirkungslos markiert, dem Modell gemeldet und in die Stillstand-Erkennung eingerechnet. Steuerbar über `VISION_GRID_OVERLAY`, `VISION_GRID_SPACING`, `VISION_CHANGE_DETECTION` und `VISION_NO_EFFECT_THRESHOLD`.
- **Safety Engine**: Validiert alle eingehenden Aktionen auf Risiken (siehe `docs/safety.md`).
- **Realtime Event Stream**: Veröffentlicht Session-Snapshots, neue Logeinträge, Statuswechsel und Freigabezustände über `/api/sessions/{session_id}/events` per WebSocket.
- **Native Desktop Bridge**: Stellt strukturierte Tools für Fensterliste, aktives Fenster, Fensterfokus, Fensterschließen, App-Katalog, URL-Start und Zwischenablage bereit.

### 3. `frontend` (React + Vite Dashboard)
Das Frontend ist eine Premium-Weboberfläche für den Anwender:
- **noVNC-Integration**: Bettet die Live-Ansicht des virtuellen Desktops direkt per Iframe ein.
- **Steuerungs-Konsole**: Ermöglicht die Eingabe der Aufgabe, das Starten, Pausieren und Abbrechen.
- **Schritt-Verlauf**: Zeigt jeden vom Agenten ausgeführten Schritt in Echtzeit, inklusive Screenshot, Erklärung des Agenten, Konsolenausgaben und Status.
- **Freigabedialoge**: Zeigt interaktive Modals, wenn eine risikoreiche Aktion auf Freigabe wartet.
