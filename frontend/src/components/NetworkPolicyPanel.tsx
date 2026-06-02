import React, { useEffect, useState } from "react";
import { Globe, ShieldAlert, Plus, Trash2, RefreshCw } from "lucide-react";

interface NetworkPolicyState {
  mode: string;
  blocklist: string[];
  allowlist: string[];
}

interface NetworkPolicyPanelProps {
  backendBase: string;
}

export const NetworkPolicyPanel: React.FC<NetworkPolicyPanelProps> = ({ backendBase }) => {
  const [policy, setPolicy] = useState<NetworkPolicyState>({ mode: "blocklist", blocklist: [], allowlist: [] });
  const [newDomain, setNewDomain] = useState("");
  const [loading, setLoading] = useState(false);

  const activeList: "blocklist" | "allowlist" = policy.mode === "allowlist" ? "allowlist" : "blocklist";

  const fetchPolicy = async () => {
    try {
      const res = await fetch(`${backendBase}/api/network-policy`);
      if (res.ok) {
        setPolicy(await res.json());
      }
    } catch (e) {
      console.error("Error fetching network policy:", e);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, [backendBase]);

  const updateMode = async (mode: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${backendBase}/api/network-policy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode })
      });
      if (res.ok) {
        const data = await res.json();
        setPolicy(data.policy);
      }
    } catch (e) {
      console.error("Error updating network mode:", e);
    } finally {
      setLoading(false);
    }
  };

  const addDomain = async () => {
    const domain = newDomain.trim().toLowerCase();
    if (!domain) return;
    setLoading(true);
    try {
      const res = await fetch(`${backendBase}/api/network-policy/domains`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain, list: activeList })
      });
      if (res.ok) {
        const data = await res.json();
        setPolicy(data.policy);
        setNewDomain("");
      }
    } catch (e) {
      console.error("Error adding domain:", e);
    } finally {
      setLoading(false);
    }
  };

  const removeDomain = async (domain: string) => {
    setLoading(true);
    try {
      const res = await fetch(
        `${backendBase}/api/network-policy/domains?domain=${encodeURIComponent(domain)}&list=${activeList}`,
        { method: "DELETE" }
      );
      if (res.ok) {
        const data = await res.json();
        setPolicy(data.policy);
      }
    } catch (e) {
      console.error("Error removing domain:", e);
    } finally {
      setLoading(false);
    }
  };

  const entries = activeList === "allowlist" ? policy.allowlist : policy.blocklist;

  return (
    <div className="glass-card">
      <div className="card-header">
        <h2>
          <Globe size={18} />
          Netzwerk-Richtlinie
        </h2>
      </div>
      <div className="card-content">
        <div className="form-group">
          <label className="form-label">Durchsetzungsmodus</label>
          <select
            className="form-select"
            value={policy.mode}
            disabled={loading}
            onChange={(e) => updateMode(e.target.value)}
          >
            <option value="blocklist">Blocklist (alles erlaubt außer gesperrt)</option>
            <option value="allowlist">Allowlist (nur erlaubte Ziele)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">
            {activeList === "allowlist" ? "Erlaubte Domains" : "Gesperrte Domains"}
          </label>
          <div style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              className="form-input"
              placeholder="z.B. github.com"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") addDomain();
              }}
            />
            <button
              type="button"
              className="btn btn-primary"
              style={{ padding: "0 12px" }}
              onClick={addDomain}
              disabled={loading}
            >
              <Plus size={16} />
            </button>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "180px", overflowY: "auto" }}>
          {entries.length === 0 && (
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              Keine Einträge vorhanden.
            </span>
          )}
          {entries.map((domain) => (
            <div
              key={domain}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "6px 10px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "var(--radius-md)",
                fontSize: "13px"
              }}
            >
              <span style={{ fontFamily: "monospace" }}>{domain}</span>
              <button
                type="button"
                onClick={() => removeDomain(domain)}
                disabled={loading}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center"
                }}
                title="Entfernen"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: "16px",
            padding: "12px",
            background: policy.mode === "allowlist" ? "rgba(239, 71, 111, 0.06)" : "rgba(6, 214, 160, 0.05)",
            border: policy.mode === "allowlist"
              ? "1px solid rgba(239, 71, 111, 0.25)"
              : "1px solid rgba(6, 214, 160, 0.2)",
            borderRadius: "var(--radius-md)",
            fontSize: "12px",
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}
        >
          <ShieldAlert size={16} style={{ color: policy.mode === "allowlist" ? "var(--accent-rose, #ef476f)" : "var(--accent-teal)" }} />
          <span>
            {policy.mode === "allowlist"
              ? "Strenger Modus: Nur gelistete Domains sind erreichbar."
              : "Standardmodus: Gesperrte Domains erfordern Freigabe."}
          </span>
        </div>

        <button
          type="button"
          className="btn"
          style={{ width: "100%", marginTop: "10px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
          onClick={fetchPolicy}
          disabled={loading}
        >
          <RefreshCw size={14} /> Aktualisieren
        </button>
      </div>
    </div>
  );
};

export default NetworkPolicyPanel;
