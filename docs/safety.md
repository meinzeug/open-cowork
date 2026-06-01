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

### 4. Visuelle Inspektion
- `inspect_region` ist eine reine Beobachtungsaktion: Das Backend erzeugt aus dem aktuellen Screenshot einen vergrößerten Ausschnitt und verändert weder Desktop noch Dateisystem.
- Die Aktion wird als niedriges Risiko eingestuft und benötigt keine Freigabe.

### 5. Native Desktop-Aktionen
- `list_windows`, `active_window`, `focus_window`, `list_apps` und `clipboard_get` sind nicht-destruktive Desktop-Abfragen bzw. Fokusoperationen und gelten als niedriges Risiko.
- `close_window` wird als mittleres Risiko bewertet, weil ungespeicherte UI-Daten verloren gehen können.
- `open_url` blockiert nicht-HTTP(S)-Schemata und zahlungs-/loginnahe Domains gemäß Blocklist.
- `clipboard_set` wird wie Texteingabe geprüft und erkennt sensible Begriffe sowie Kreditkartenmuster.
