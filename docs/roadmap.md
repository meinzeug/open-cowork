# Projekt-Roadmap - Linux Cowork Agent

Dieses Dokument beschreibt die geplanten Erweiterungen für zukünftige Releases von **Linux Cowork Agent**.

## Kurzfristige Erweiterungen (v1.1 - v1.2)

- [x] **Erweiterte Koordinatenlogik & Zoom**:
  - Implementierung einer Zoom-Funktion für das LLM, um sehr kleine UI-Elemente in dicht gedrängten Anwendungen (wie verschachtelten Menüs oder Excel) exakt lesen zu können.
- [x] **Screenshot-Historie & Reflection**:
  - Ermögliche dem Agenten das Vergleichen des aktuellen Screenshots mit dem vorherigen, um festzustellen, ob ein Klick tatsächlich gewirkt hat (Selbstreflexion).
- [x] **WebSocket Real-time Logs**:
  - Umstellung des Frontend-Pollings auf bidirektionale WebSockets für sofortige Echtzeit-Logeinträge und Screenshot-Updates.
- [x] **Native Linux Desktop Bridge**:
  - Strukturierte X11-Integration für Fensterverwaltung, aktive Fenster, App-Katalog, URL-Start und Zwischenablage.
- [x] **Autonome Planung & Selbstkorrektur**:
  - Der Agent zerlegt komplexe Aufgaben über die Aktion `update_plan` in nachverfolgbare Teilschritte (pending/in_progress/done), führt persistente Notizen als Gedächtnis und reflektiert nach jedem Schritt anhand des Screenshots. Eine Stillstand-Erkennung zählt wiederholte, wirkungslose Aktionen und zwingt das Modell zur Strategieänderung. Plan, Fortschritt und Notizen werden live im Dashboard angezeigt.
- [x] **Erweiterte Bildschirmwahrnehmung (Vision 2.0)**:
  - Optionales Koordinatenraster-Overlay auf dem an das LLM gesendeten Screenshot, damit das Modell exakte x/y-Pixel ablesen und präziser klicken kann (der Original-Screenshot bleibt für Log/UI unverändert).
  - Automatische Wirkungskontrolle: Das Backend vergleicht jeden neuen Screenshot mit dem vorherigen und berechnet die Bildschirm-Änderungsrate. Wirkungslose Aktionen (Änderung unter Schwellwert) werden erkannt, in den Kontext des Modells injiziert und fließen in die Stillstand-Erkennung ein. Alle Parameter sind über `VISION_*`-Einstellungen konfigurierbar.

## Mittelfristige Erweiterungen (v1.5 - v2.0)

- [ ] **Parallele Sandbox-Sitzungen**:
  - Dynamisches Erzeugen und Verwalten mehrerer Docker-Sandbox-Container direkt über das Dashboard ("Neue Sandbox starten").
- [ ] **Lokale Audiounterstützung**:
  - Erfassung und Streaming von Sound aus der Sandbox an das Web-Frontend über WebRTC oder Pulseaudio-Web-Sinks.
- [x] **Erweiterte Allowlist/Blocklist für Internetzugriff**:
  - Zentrale Netzwerk-Richtlinie im FastAPI-Backend mit umschaltbarem Blocklist-/Allowlist-Modus. Im Allowlist-Modus sind ausschließlich freigegebene Domains erreichbar, wodurch unkontrollierter Datenabfluss (Data Exfiltration) durch den Agenten verhindert wird. Die Prüfung greift bei `open_url`, Firefox-Starts und Netzwerk-Shell-Befehlen (`curl`, `wget`, `scp`, ...) und ist live über das Dashboard sowie die REST-API steuerbar.
