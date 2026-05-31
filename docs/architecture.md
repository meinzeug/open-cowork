# Systemarchitektur - Linux Cowork Agent

## Übersicht

Der **Linux Cowork Agent** besteht aus einer dreigeteilten, isolierten Container-Struktur, die über ein geschlossenes Netzwerk kommuniziert. 

```
                                  +-----------------------+
                                  |   Nutzer-Browser      |
                                  +-----------+-----------+
                                              |
                            HTTP / Websocket  |  noVNC Stream (Port 6080)
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
- **Sandbox Agent**: Eine Python FastAPI REST-API, die intern auf Port 5001 läuft. Sie erhält Anweisungen wie `/mouse/click`, `/keyboard/type`, `/shell` oder `/screenshot` und führt diese mithilfe von `pyautogui`, `xdotool` und `scrot` direkt im virtuellen Desktop aus.

### 2. `backend` (FastAPI Server)
Das Backend steuert den intelligenten Agenten-Loop und verwaltet den Status:
- **Session-Management**: Erstellt, pausiert, stoppt und setzt Agentensitzungen in einem thread-sicheren In-Memory-Speicher zurück.
- **Agent Loop**: Holt in jedem Schritt einen Screenshot aus der Sandbox, leitet diesen zusammen mit der Aufgabe und der Historie an das LLM weiter, holt die strukturierte JSON-Aktion ab, jagt sie durch die Sicherheitsprüfung und führt sie in der Sandbox aus.
- **Safety Engine**: Validiert alle eingehenden Aktionen auf Risiken (siehe `docs/safety.md`).

### 3. `frontend` (React + Vite Dashboard)
Das Frontend ist eine Premium-Weboberfläche für den Anwender:
- **noVNC-Integration**: Bettet die Live-Ansicht des virtuellen Desktops direkt per Iframe ein.
- **Steuerungs-Konsole**: Ermöglicht die Eingabe der Aufgabe, das Starten, Pausieren und Abbrechen.
- **Schritt-Verlauf**: Zeigt jeden vom Agenten ausgeführten Schritt, inklusive Screenshot, Erklärung des Agenten, Konsolenausgaben und Status.
- **Freigabedialoge**: Zeigt interaktive Modals, wenn eine risikoreiche Aktion auf Freigabe wartet.
