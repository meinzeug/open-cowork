import React, { useState, useEffect, useRef } from "react";
import { DesktopView } from "./components/DesktopView";
import { TaskInput } from "./components/TaskInput";
import { ProviderSettings } from "./components/ProviderSettings";
import { ActionLog } from "./components/ActionLog";
import { SafetyDialog } from "./components/SafetyDialog";

const BACKEND_BASE = "http://localhost:8000";

interface LogEntry {
  step: int;
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

interface Session {
  session_id: string;
  task: string;
  status: string;
  provider: string;
  model: string;
  current_step: int;
  max_steps: int;
  logs: LogEntry[];
  pending_action?: any | null;
}

export const App: React.FC = () => {
  const [session, setSession] = useState<Session | null>(null);
  
  // Settings
  const [provider, setProvider] = useState("mock");
  const [model, setModel] = useState("mock-model");
  const [maxSteps, setMaxSteps] = useState(30);
  const [apiKey, setApiKey] = useState("");
  
  // VNC display configuration
  // Direct connect to host Websockify mapped port
  const [vncUrl, setVncUrl] = useState(`http://${window.location.hostname}:6080/vnc.html?autoconnect=true&resize=scale`);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Poll session state
  const fetchSessionState = async (sessionId: string) => {
    try {
      const res = await fetch(`${BACKEND_BASE}/api/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setSession(data);
        
        // Stop polling if session finished
        if (["idle", "stopped", "completed", "error"].includes(data.status)) {
          stopPolling();
        }
      }
    } catch (e) {
      console.error("Error fetching session state:", e);
    }
  };

  const startPolling = (sessionId: string) => {
    stopPolling();
    pollIntervalRef.current = setInterval(() => {
      fetchSessionState(sessionId);
    }, 1500);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  useEffect(() => {
    // Clean up timers on unmount
    return () => stopPolling();
  }, []);

  // Handlers
  const handleTaskSubmit = async (task: string) => {
    try {
      let activeSession = session;
      
      // 1. Create a session if it doesn't exist or is completed
      if (!activeSession || ["completed", "stopped", "error"].includes(activeSession.status)) {
        const res = await fetch(`${BACKEND_BASE}/api/sessions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task,
            provider,
            model,
            max_steps: maxSteps
          })
        });
        
        if (res.ok) {
          activeSession = await res.json();
          setSession(activeSession);
        } else {
          alert("Fehler beim Erstellen der Sitzung.");
          return;
        }
      }
      
      if (!activeSession) return;

      // 2. Start session loop
      const startRes = await fetch(`${BACKEND_BASE}/api/sessions/${activeSession.session_id}/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(apiKey ? { "X-Api-Key": apiKey } : {})
        }
      });

      if (startRes.ok) {
        setSession(prev => prev ? { ...prev, status: "running" } : null);
        startPolling(activeSession.session_id);
      } else {
        alert("Fehler beim Starten des Agenten.");
      }
      
    } catch (e) {
      console.error("Error submitting task:", e);
    }
  };

  const handlePause = async () => {
    if (!session) return;
    try {
      const res = await fetch(`${BACKEND_BASE}/api/sessions/${session.session_id}/pause`, { method: "POST" });
      if (res.ok) {
        stopPolling();
        setSession(prev => prev ? { ...prev, status: "paused" } : null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    if (!session) return;
    try {
      const res = await fetch(`${BACKEND_BASE}/api/sessions/${session.session_id}/stop`, { method: "POST" });
      if (res.ok) {
        stopPolling();
        setSession(prev => prev ? { ...prev, status: "stopped" } : null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    if (!session) return;
    try {
      const res = await fetch(`${BACKEND_BASE}/api/sessions/${session.session_id}/reset`, { method: "POST" });
      if (res.ok) {
        stopPolling();
        setSession(prev => prev ? { ...prev, status: "idle", current_step: 0, logs: [], pending_action: null } : null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSettingsChange = (newSettings: {
    provider: string;
    model: string;
    maxSteps: number;
    apiKey: string;
  }) => {
    setProvider(newSettings.provider);
    setModel(newSettings.model);
    setMaxSteps(newSettings.maxSteps);
    setApiKey(newSettings.apiKey);
    
    // Auto-configure backend default values
    fetch(`${BACKEND_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anthropic_api_key: newSettings.provider === "anthropic" ? newSettings.apiKey : undefined,
        openai_api_key: newSettings.provider === "openai" ? newSettings.apiKey : undefined,
        default_provider: newSettings.provider,
        default_model: newSettings.model,
        max_steps: newSettings.maxSteps
      })
    }).catch(e => console.error("Error setting configs:", e));
    
    alert("Konfiguration erfolgreich übernommen!");
  };

  const handleSafetyConfirm = async (approved: boolean, userFeedback: string) => {
    if (!session) return;
    
    try {
      // 1. Temporarily pause polling
      stopPolling();
      
      // 2. Post confirmation
      const res = await fetch(`${BACKEND_BASE}/api/sessions/${session.session_id}/confirm`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          ...(apiKey ? { "X-Api-Key": apiKey } : {})
        },
        body: JSON.stringify({
          approved,
          feedback: userFeedback
        })
      });

      if (res.ok) {
        if (approved) {
          // Resume polling if approved
          setSession(prev => prev ? { ...prev, status: "running", pending_action: null } : null);
          startPolling(session.session_id);
        } else {
          setSession(prev => prev ? { ...prev, status: "stopped", pending_action: null } : null);
        }
      } else {
        alert("Fehler beim Senden der Bestätigung.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Find agent coordinates of last click action to render red pointer
  const getAgentCoordinates = () => {
    if (!session || session.logs.length === 0) return null;
    const lastLog = [...session.logs].reverse().find(l => l.status === "executed" || l.status === "pending");
    if (lastLog && (lastLog.action_type.includes("click") || lastLog.action_type === "mouse_move" || lastLog.action_type === "drag")) {
      const x = lastLog.action_params.x;
      const y = lastLog.action_params.y;
      if (typeof x === "number" && typeof y === "number") {
        return { x, y, type: lastLog.action_type };
      }
    }
    return null;
  };

  const agentCoordsData = getAgentCoordinates();
  const agentCoords = agentCoordsData ? { x: agentCoordsData.x, y: agentCoordsData.y } : null;
  const agentActionType = agentCoordsData ? agentCoordsData.type : null;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-section">
          <span className="logo-icon">🤖</span>
          <h1 className="logo-text">Linux Cowork Agent</h1>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            Sandbox VNC Host:
          </span>
          <input 
            type="text" 
            className="form-input" 
            style={{ width: "200px", padding: "4px 10px", fontSize: "12px" }}
            value={vncUrl}
            onChange={(e) => setVncUrl(e.target.value)}
          />
        </div>
      </header>

      <main className="dashboard-grid">
        {/* Left pane - Config */}
        <ProviderSettings 
          provider={provider}
          model={model}
          maxSteps={maxSteps}
          onSettingsChange={handleSettingsChange}
        />

        {/* Center pane - Sandbox desktop display & Control */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", height: "100%", overflowY: "auto" }}>
          <DesktopView 
            vncUrl={vncUrl}
            agentCoords={agentCoords}
            agentActionType={agentActionType}
          />
          <TaskInput 
            status={session?.status || "idle"}
            onSubmit={handleTaskSubmit}
            onPause={handlePause}
            onStop={handleStop}
            onReset={handleReset}
          />
        </div>

        {/* Right pane - Execution log history */}
        <ActionLog logs={session?.logs || []} />
      </main>

      {/* Safety popup dialog */}
      <SafetyDialog 
        isOpen={session?.status === "pending_confirmation" && !!session.pending_action}
        actionSummary={session?.pending_action?.summary || ""}
        actionType={session?.pending_action?.action?.type || ""}
        actionParams={session?.pending_action?.action?.params || {}}
        riskLevel={session?.pending_action?.risk || "high"}
        onConfirm={handleSafetyConfirm}
      />
    </div>
  );
};
