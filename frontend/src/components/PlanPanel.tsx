import React from "react";
import { ListChecks, CircleCheck, CircleDot, Circle, StickyNote } from "lucide-react";

interface PlanStep {
  description: string;
  status: string; // pending, in_progress, done
}

interface PlanPanelProps {
  plan: PlanStep[];
  notes?: string | null;
  stuckCounter?: number;
}

const statusIcon = (status: string) => {
  if (status === "done") return <CircleCheck size={16} style={{ color: "var(--accent-teal, #06d6a0)" }} />;
  if (status === "in_progress") return <CircleDot size={16} style={{ color: "#ffd166" }} />;
  return <Circle size={16} style={{ color: "var(--text-secondary)" }} />;
};

export const PlanPanel: React.FC<PlanPanelProps> = ({ plan, notes, stuckCounter }) => {
  const total = plan.length;
  const done = plan.filter((s) => s.status === "done").length;
  const progress = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="glass-card">
      <div className="card-header">
        <h2>
          <ListChecks size={18} />
          Arbeitsplan & Fortschritt
        </h2>
      </div>
      <div className="card-content">
        {total === 0 && (
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            Noch kein Plan. Der Agent erstellt bei komplexen Aufgaben automatisch Teilschritte.
          </span>
        )}

        {total > 0 && (
          <>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                {done}/{total} erledigt
              </span>
              <span style={{ fontSize: "12px", fontWeight: 600 }}>{progress}%</span>
            </div>
            <div
              style={{
                height: "6px",
                borderRadius: "999px",
                background: "rgba(255,255,255,0.08)",
                overflow: "hidden",
                marginBottom: "14px"
              }}
            >
              <div
                style={{
                  width: `${progress}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #06d6a0, #4cc9f0)",
                  transition: "width 0.4s ease"
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "240px", overflowY: "auto" }}>
              {plan.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "8px",
                    padding: "8px 10px",
                    background: step.status === "in_progress" ? "rgba(255, 209, 102, 0.08)" : "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "13px"
                  }}
                >
                  <span style={{ marginTop: "1px" }}>{statusIcon(step.status)}</span>
                  <span
                    style={{
                      textDecoration: step.status === "done" ? "line-through" : "none",
                      color: step.status === "done" ? "var(--text-secondary)" : "var(--text-primary, #fff)"
                    }}
                  >
                    {step.description}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {notes && (
          <div
            style={{
              marginTop: "14px",
              padding: "10px 12px",
              background: "rgba(76, 201, 240, 0.06)",
              border: "1px solid rgba(76, 201, 240, 0.2)",
              borderRadius: "var(--radius-md)",
              fontSize: "12px",
              color: "var(--text-secondary)",
              display: "flex",
              gap: "8px"
            }}
          >
            <StickyNote size={14} style={{ color: "#4cc9f0", flexShrink: 0, marginTop: "1px" }} />
            <span style={{ whiteSpace: "pre-wrap" }}>{notes}</span>
          </div>
        )}

        {typeof stuckCounter === "number" && stuckCounter >= 2 && (
          <div
            style={{
              marginTop: "12px",
              padding: "10px 12px",
              background: "rgba(239, 71, 111, 0.08)",
              border: "1px solid rgba(239, 71, 111, 0.3)",
              borderRadius: "var(--radius-md)",
              fontSize: "12px",
              color: "#ff8fa3"
            }}
          >
            ⚠️ Mögliche Wiederholungsschleife erkannt – der Agent wird zur Strategieänderung angehalten.
          </div>
        )}
      </div>
    </div>
  );
};

export default PlanPanel;
