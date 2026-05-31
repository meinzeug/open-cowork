import React, { useState } from "react";
import { Play, Pause, Square, RotateCcw, AlertTriangle } from "lucide-react";

interface TaskInputProps {
  status: string;
  onSubmit: (task: string) => void;
  onPause: () => void;
  onStop: () => void;
  onReset: () => void;
}

export const TaskInput: React.FC<TaskInputProps> = ({
  status,
  onSubmit,
  onPause,
  onStop,
  onReset
}) => {
  const [taskText, setTaskText] = useState("");

  const handleStartClick = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskText.trim()) return;
    onSubmit(taskText);
  };

  const getStatusText = () => {
    switch (status) {
      case "running": return "Agent führt Aufgabe aus...";
      case "paused": return "Agent angehalten";
      case "pending_confirmation": return "Freigabe erforderlich!";
      case "stopped": return "Sitzung abgebrochen";
      case "completed": return "Aufgabe abgeschlossen!";
      case "error": return "Kritischer Systemfehler";
      default: return "Bereit für neue Aufgabe";
    }
  };

  return (
    <div className="glass-card" style={{ gridColumn: "span 2" }}>
      <div className="card-header">
        <h2>🤖 Agenten-Steuerung & Aufgabe</h2>
        <div className="status-badge">
          <div className={`status-indicator ${status}`} />
          {getStatusText()}
        </div>
      </div>
      <div className="card-content">
        <form onSubmit={handleStartClick}>
          <div className="form-group">
            <label className="form-label" htmlFor="task-prompt">Was soll der Agent tun?</label>
            <textarea
              id="task-prompt"
              className="form-textarea"
              rows={3}
              placeholder="z.B.: Schreibe eine Datei hallo.txt mit einer Begrüßung, lies den Ordner aus..."
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              disabled={status === "running" || status === "pending_confirmation"}
            />
          </div>
          
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="controls-row">
              {status === "idle" || status === "stopped" || status === "completed" || status === "error" ? (
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={!taskText.trim()}
                >
                  <Play size={16} />
                  Aufgabe starten
                </button>
              ) : null}

              {status === "running" ? (
                <button 
                  type="button" 
                  className="btn"
                  onClick={onPause}
                >
                  <Pause size={16} />
                  Pause
                </button>
              ) : null}

              {status === "paused" || status === "pending_confirmation" ? (
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={() => onSubmit(taskText)}
                >
                  <Play size={16} />
                  Fortsetzen
                </button>
              ) : null}

              {status !== "idle" ? (
                <>
                  <button 
                    type="button" 
                    className="btn btn-danger"
                    onClick={onStop}
                  >
                    <Square size={16} />
                    Abbrechen
                  </button>
                  <button 
                    type="button" 
                    className="btn"
                    onClick={onReset}
                  >
                    <RotateCcw size={16} />
                    Zurücksetzen
                  </button>
                </>
              ) : null}
            </div>
            
            {status === "pending_confirmation" && (
              <div 
                style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "6px", 
                  color: "var(--accent-yellow)",
                  fontSize: "13px",
                  fontWeight: 500
                }}
              >
                <AlertTriangle size={16} />
                Aktion blockiert durch Sicherheits-Gateway!
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
