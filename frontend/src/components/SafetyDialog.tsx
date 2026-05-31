import React, { useState } from "react";
import { ShieldAlert, Check, X } from "lucide-react";

interface SafetyDialogProps {
  isOpen: boolean;
  actionSummary: string;
  actionType: string;
  actionParams: Record<string, any>;
  riskLevel: string;
  onConfirm: (approved: boolean, feedback: string) => void;
}

export const SafetyDialog: React.FC<SafetyDialogProps> = ({
  isOpen,
  actionSummary,
  actionType,
  actionParams,
  riskLevel,
  onConfirm
}) => {
  const [feedback, setFeedback] = useState("");

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header-danger">
          <ShieldAlert size={24} style={{ color: "var(--accent-red)" }} />
          <h3>Sicherheitsfreigabe erforderlich</h3>
        </div>
        <div className="modal-body">
          <p style={{ fontSize: "14px", lineHeight: "1.5", color: "var(--text-primary)" }}>
            Der KI-Agent beabsichtigt eine Aktion mit erhöhtem Risiko (<strong>{riskLevel.toUpperCase()}</strong>) auszuführen.
          </p>

          <div className="danger-box">
            <strong>Geplante Aktion:</strong>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "4px", margin: "6px 0", color: "#fda4af", wordBreak: "break-all" }}>
              {actionType} {JSON.stringify(actionParams)}
            </div>
            <strong>Begründung des Agenten:</strong>
            <p style={{ marginTop: "4px", color: "var(--text-primary)", fontStyle: "italic" }}>
              "{actionSummary}"
            </p>
          </div>

          <div className="form-group" style={{ marginTop: "20px" }}>
            <label className="form-label" htmlFor="user-feedback">
              Feedback / Korrektur (Optional)
            </label>
            <input
              id="user-feedback"
              type="text"
              className="form-input"
              placeholder="z.B.: Nein, bitte stattdessen Ordner xyz löschen..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
        </div>
        
        <div className="modal-footer">
          <button 
            type="button" 
            className="btn" 
            onClick={() => onConfirm(false, feedback)}
            style={{ display: "flex", gap: "6px" }}
          >
            <X size={16} />
            Aktion ablehnen & Stopp
          </button>
          <button 
            type="button" 
            className="btn btn-danger"
            onClick={() => onConfirm(true, feedback)}
            style={{ display: "flex", gap: "6px" }}
          >
            <Check size={16} />
            Aktion freigeben
          </button>
        </div>
      </div>
    </div>
  );
};
