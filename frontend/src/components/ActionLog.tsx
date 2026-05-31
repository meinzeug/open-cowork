import React from "react";
import { Terminal, CheckCircle2, XCircle, AlertCircle, Clock } from "lucide-react";

interface LogEntry {
  step: number;
  timestamp: string;
  summary: string;
  action_type: string;
  action_params: Record<string, any>;
  screenshot_base64?: string | null;
  output?: string | null;
  error?: string | null;
  risk: string;
  requires_confirmation: boolean;
  confirmed_by_user?: boolean | null;
  status: string;
}

interface ActionLogProps {
  logs: LogEntry[];
}

export const ActionLog: React.FC<ActionLogProps> = ({ logs }) => {
  const getIcon = (status: string) => {
    switch (status) {
      case "executed": return <CheckCircle2 size={14} style={{ color: "var(--accent-teal)" }} />;
      case "failed": return <XCircle size={14} style={{ color: "var(--accent-red)" }} />;
      case "pending": return <AlertCircle size={14} style={{ color: "var(--accent-yellow)" }} />;
      case "denied": return <XCircle size={14} style={{ color: "var(--accent-red)" }} />;
      default: return <Clock size={14} />;
    }
  };

  const getStatusText = (log: LogEntry) => {
    if (log.status === "pending") return "Wartet auf Freigabe";
    if (log.status === "denied") return "Freigabe verweigert";
    if (log.status === "failed") return "Fehlgeschlagen";
    return "Ausgeführt";
  };

  const formatParams = (params: Record<string, any>) => {
    if (!params || Object.keys(params).length === 0) return "";
    return JSON.stringify(params);
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="glass-card" style={{ height: "100%" }}>
      <div className="card-header">
        <h2>
          <Terminal size={18} />
          Ausführungsprotokoll ({logs.length})
        </h2>
      </div>
      <div className="card-content" style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        {logs.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 10px", color: "var(--text-muted)", fontSize: "14px" }}>
            Bislang keine Aktionen protokolliert.
          </div>
        ) : (
          <div className="logs-list">
            {logs.map((log, i) => (
              <div key={i} className={`log-entry ${log.status}`}>
                <div className="log-header">
                  <span className="log-step">Schritt {log.step + 1}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", color: "var(--text-secondary)" }}>
                      {getIcon(log.status)}
                      {getStatusText(log)}
                    </span>
                    <span className="log-time">{formatTimestamp(log.timestamp)}</span>
                  </div>
                </div>

                <div className="log-summary">{log.summary}</div>

                <div className="log-action-badge">
                  {log.action_type} {formatParams(log.action_params)}
                </div>

                {log.screenshot_base64 && (
                  <div style={{ position: "relative", marginTop: "6px" }}>
                    <img 
                      src={`data:image/png;base64,${log.screenshot_base64}`}
                      alt={`Screenshot step ${log.step}`}
                      style={{ 
                        width: "100%", 
                        borderRadius: "var(--radius-sm)", 
                        border: "1px solid var(--border-color)",
                        aspectRatio: "4/3",
                        objectFit: "cover",
                        background: "#000"
                      }}
                    />
                  </div>
                )}

                {log.output && (
                  <pre className="log-output">{log.output}</pre>
                )}

                {log.error && (
                  <pre className="log-output" style={{ color: "var(--accent-red)", borderColor: "rgba(239, 71, 111, 0.15)", background: "rgba(239, 71, 111, 0.05)" }}>
                    {log.error}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
