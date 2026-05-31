import React, { useState } from "react";
import { Settings, ShieldCheck, Key } from "lucide-react";

interface ProviderSettingsProps {
  provider: string;
  model: string;
  maxSteps: number;
  onSettingsChange: (settings: {
    provider: string;
    model: string;
    maxSteps: number;
    apiKey: string;
  }) => void;
}

export const ProviderSettings: React.FC<ProviderSettingsProps> = ({
  provider,
  model,
  maxSteps,
  onSettingsChange
}) => {
  const [localProvider, setLocalProvider] = useState(provider);
  const [localModel, setLocalModel] = useState(model);
  const [localMaxSteps, setLocalMaxSteps] = useState(maxSteps);
  const [apiKey, setApiKey] = useState("");

  const handleApply = () => {
    onSettingsChange({
      provider: localProvider,
      model: localModel,
      maxSteps: localMaxSteps,
      apiKey
    });
  };

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setLocalProvider(val);
    if (val === "mock") {
      setLocalModel("mock-model");
    } else if (val === "anthropic") {
      setLocalModel("claude-3-5-sonnet-20241022");
    } else if (val === "openai") {
      setLocalModel("gpt-4o");
    } else if (val === "ollama") {
      setLocalModel("llama3.2-vision");
    }
  };

  return (
    <div className="glass-card">
      <div className="card-header">
        <h2>
          <Settings size={18} />
          KI-Konfiguration
        </h2>
      </div>
      <div className="card-content">
        <div className="form-group">
          <label className="form-label">LLM Provider</label>
          <select 
            className="form-select"
            value={localProvider}
            onChange={handleProviderChange}
          >
            <option value="mock">MockProvider (Lokaler Test)</option>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="ollama">Ollama (Lokale Vision)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Modellbezeichnung</label>
          <input 
            type="text" 
            className="form-input"
            value={localModel}
            onChange={(e) => setLocalModel(e.target.value)}
            disabled={localProvider === "mock"}
          />
        </div>

        {localProvider !== "mock" && localProvider !== "ollama" && (
          <div className="form-group">
            <label className="form-label" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <Key size={12} />
              API Key (Überschreiben)
            </label>
            <input 
              type="password" 
              className="form-input"
              placeholder="Vom Server geladener Key wird genutzt..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Maximale Schritte ({localMaxSteps})</label>
          <input 
            type="range" 
            min={5} 
            max={60} 
            step={5} 
            className="form-input"
            style={{ padding: 0 }}
            value={localMaxSteps}
            onChange={(e) => setLocalMaxSteps(Number(e.target.value))}
          />
        </div>

        <button 
          type="button" 
          className="btn btn-primary" 
          style={{ width: "100%", marginTop: "10px" }}
          onClick={handleApply}
        >
          Konfiguration übernehmen
        </button>

        <div 
          style={{ 
            marginTop: "20px", 
            padding: "12px", 
            background: "rgba(6, 214, 160, 0.05)",
            border: "1px solid rgba(6, 214, 160, 0.2)",
            borderRadius: "var(--radius-md)",
            fontSize: "12px",
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}
        >
          <ShieldCheck size={16} className="text-teal" style={{ color: "var(--accent-teal)" }} />
          <span>Sicherheitsrichtlinie: <strong>Bestätige hohes Risiko</strong></span>
        </div>
      </div>
    </div>
  );
};
export default ProviderSettings;
