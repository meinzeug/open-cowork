# Status-Notiz für die nächste KI — 2026-06-01

## Was bisher passiert ist

- Projekt: **open-cowork** — ein KI-gesteuerter Linux-Desktop-Agent mit Browser/GUI-Zugriff
- Letzter Tag: `v1.1.1` (Bootstrap-Hotfix, bereits gepusht)
- Aktueller Branch: `main` — sauber, nichts uncommittet

## Docker-Status beim letzten Abbruch

Der Befehl `./start.sh` hat `docker compose up --build` gestartet.
Dabei wurden **Backend** und **Frontend** bereits vollständig gebaut:

| Image                  | Status         |
|------------------------|----------------|
| `open-cowork-backend`  | ✅ gebaut (159 MB) |
| `open-cowork-frontend` | ✅ gebaut (307 MB) |
| `open-cowork-sandbox`  | ❌ Bau abgebrochen (Usage-Limit der vorherigen KI) |

Das Sandbox-Image ist das **schwergewichtige** — es installiert XFCE4, X11, noVNC, Firefox (manueller Download ~80 MB tar.bz2), etc. Das dauert 5–15 Minuten je nach Verbindung.

## Was die nächste KI tun muss

1. **Docker-Daemon prüfen:**
   ```bash
   docker info
   ```

2. **Stack starten** (nutzt Cache für Backend + Frontend, baut nur Sandbox neu):
   ```bash
   cd /home/dennis/open-cowork
   ./start.sh
   ```
   Alternativ direkt:
   ```bash
   docker compose up --build
   ```

3. **Auf diese Container warten:**
   - `open_cowork_sandbox` → Port `6080` (noVNC Web-UI) und `5001` (Sandbox REST API)
   - `open_cowork_backend` → Port `8000` (FastAPI)
   - `open_cowork_frontend` → Port `3000` (React/Vite Dashboard)

4. **Im Browser öffnen:**
   - Dashboard: http://localhost:3000
   - noVNC Desktop: http://localhost:6080
   - API-Docs: http://localhost:8000/docs

## .env-Datei

Falls noch keine `.env` vorhanden:
```bash
cp .env.example .env
# API-Keys eintragen: ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY
```
Ohne Key kann auch der Mock-Provider genutzt werden (kein echter LLM-Aufruf).

## Bekannte Eigenheiten

- Das `sandbox/Dockerfile` lädt Firefox manuell via `wget` herunter (kein Snap, wegen Docker-Inkompatibilität) — das ist der langsamste Schritt.
- Der `workspace/`-Ordner wird als Volume in Backend und Sandbox gemountet.
- `shm_size: 512mb` in docker-compose ist nötig, damit Firefox im Container nicht crasht.
