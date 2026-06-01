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

## Mittelfristige Erweiterungen (v1.5 - v2.0)

- [ ] **Parallele Sandbox-Sitzungen**:
  - Dynamisches Erzeugen und Verwalten mehrerer Docker-Sandbox-Container direkt über das Dashboard ("Neue Sandbox starten").
- [ ] **Lokale Audiounterstützung**:
  - Erfassung und Streaming von Sound aus der Sandbox an das Web-Frontend über WebRTC oder Pulseaudio-Web-Sinks.
- [ ] **Erweiterte Allowlist/Blocklist für Internetzugriff**:
  - Einschränkung des Sandbox-Netzwerks auf DNS-Ebene direkt über das FastAPI-Backend, um Datenabfluss (Data Exfiltration) durch den Agenten unmöglich zu machen.
