# LLM Provider System

Der Linux Cowork Agent unterstützt ein modulares Provider-System, welches über eine einheitliche Abstraktionsschicht (`BaseProvider`) implementiert ist. Dadurch können LLMs verschiedener Anbieter mit minimalem Aufwand eingebunden werden.

## Unterstützte Provider

### 1. MockProvider (Standard)
- **Modellbezeichnung**: `mock-model`
- **Anwendungsfall**: Perfekt für Entwicklungs- und Testzwecke. 
- **Funktionsweise**: Reagiert deterministisch und simuliert einen mehrteiligen Arbeitsablauf basierend auf Schlüsselwörtern im Aufgabentext (z.B. "firefox" startet den Webbrowser-Ablauf, "datei" schreibt eine Textdatei, "danger" triggert eine risikoreiche Aktion für Sicherheitstests).
- **Vorteil**: Erfordert keinen API-Key und erzeugt keine Kosten.

### 2. Anthropic (Claude)
- **Modellbezeichnung**: `claude-3-5-sonnet-20241022`
- **Anwendungsfall**: Produktiver Agentenbetrieb mit maximaler Präzision.
- **Vorteil**: Claude 3.5 Sonnet besitzt herausragende Fähigkeiten im Erkennen von Benutzeroberflächen und präziser Koordinatensteuerung.

### 3. OpenAI (GPT-4o)
- **Modellbezeichnung**: `gpt-4o`
- **Anwendungsfall**: Produktiver Agentenbetrieb.
- **Funktionsweise**: Sendet Screenshots direkt als Image-Blocks und wertet diese über GPT-4o Vision aus.

### 4. Ollama (Lokale Modelle)
- **Modellbezeichnung**: `llama3.2-vision` oder `llava`
- **Anwendungsfall**: 100% lokaler und datenschutzfreundlicher Betrieb ohne Internetverbindung.
- **Anforderung**: Ein lokal laufender Ollama-Server auf dem Host-System mit geladenem Vision-Modell.
