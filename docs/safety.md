# Sicherheits- und Freigaberichtlinien (Safety)

Der **Linux Cowork Agent** wurde mit einem "Security-by-Design"-Ansatz gebaut. Der Agent läuft ausschließlich in einer vom Host-System isolierten Sandbox.

## Sicherheits-Ebenen

### 1. Physische Isolation (Docker-Sandbox)
- Der Agent hat standardmäßig keinen Zugriff auf die Dateien des Host-Betriebssystems.
- Einzig das Verzeichnis `./workspace` ist explizit gemountet, damit Dateien komfortabel zwischen Host und Agent ausgetauscht werden können.
- Der Container läuft in einem separaten Docker-Bridge-Netzwerk.

### 2. Statische Code- und Befehlsanalyse (SafetyValidator)
Jede Aktion, die das LLM vorschlägt, wird vor der Ausführung vom `SafetyValidator` geprüft.

#### Blockierte Befehle (Risiko: Hoch - Freigabepflichtig)
Folgende Aktionen triggern ausnahmslos eine Blockade oder erfordern eine manuelle Freigabe durch den Nutzer:
- **Destruktive Shell-Befehle**: `rm -rf /`, `dd if=...`, `mkfs`.
- **Privilegieneskalation**: Jegliche Nutzung von `sudo` oder `su`.
- **Systemmanipulationen**: `chmod` / `chown` zur Rechteänderung, `apt install` / `dpkg` zur Installation von Paketen.
- **Unsichere Downloads**: Ausführen von Skripten direkt aus dem Netz (`curl | bash`, `wget | sh`).
- **Git Force Push**: Überschreiben von Remote-Repositorys (`git push -f`).
- **Verzeichniszugriff**: Zugriff auf Pfade außerhalb des Arbeitsverzeichnisses (z.B. `/etc`, `/root`, `.git`, `.env`).

### 3. Interaktives Freigabe-Gateway (User Confirmation)
Triggert eine Aktion das Sicherheits-Gateway:
1. Pausiert das Backend den Agenten-Loop sofort.
2. Der Status der Sitzung wechselt auf `pending_confirmation`.
3. Im Frontend-Dashboard erscheint ein aufmerksamkeitsstarkes Modal-Fenster mit der genauen Begründung der Sperre und der geplanten Aktion.
4. Der Nutzer kann die Aktion entweder **freigeben** (der Agent führt sie einmalig aus und macht weiter) oder **ablehnen** (die Sitzung wird abgebrochen).
5. Über ein Textfeld kann dem Agenten zudem direktes Feedback gegeben werden (z.B. "Nein, lies stattdessen Datei X").
