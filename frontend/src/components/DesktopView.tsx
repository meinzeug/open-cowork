import React, { useState } from "react";
import { Monitor } from "lucide-react";

interface DesktopViewProps {
  vncUrl?: string;
  agentCoords?: { x: number; y: number } | null;
  agentActionType?: string | null;
}

export const DesktopView: React.FC<DesktopViewProps> = ({ 
  vncUrl = "http://localhost:6080/vnc.html?autoconnect=true&resize=scale",
  agentCoords,
  agentActionType
}) => {
  const [hoverCoords, setHoverCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 1024);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 768);
    setHoverCoords({ x, y });
  };

  return (
    <div className="glass-card" style={{ gridColumn: "span 2" }}>
      <div className="card-header">
        <h2>
          <Monitor size={18} className="text-purple" />
          Isolierter Desktop-Sandbox Livestream
        </h2>
        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
          Auflösung: 1024 x 768 (Skaliert)
        </span>
      </div>
      <div className="card-content desktop-view-container">
        <div 
          className="desktop-viewport-wrapper"
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {/* Embedded noVNC display */}
          <iframe 
            src={vncUrl} 
            className="vnc-iframe" 
            title="noVNC Sandbox display"
            allowFullScreen
          />
          
          {/* Hover coordinate mapping overlay */}
          <div className="coordinate-overlay">
            {isHovered && (
              <div className="coordinates-indicator">
                X: {hoverCoords.x} | Y: {hoverCoords.y}
              </div>
            )}
            
            {/* Visual indicator of agent click actions */}
            {agentCoords && agentCoords.x >= 0 && agentCoords.y >= 0 && (
              <div 
                style={{
                  position: "absolute",
                  left: `${(agentCoords.x / 1024) * 100}%`,
                  top: `${(agentCoords.y / 768) * 100}%`,
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  background: agentActionType?.includes("click") ? "rgba(239, 71, 111, 0.6)" : "rgba(157, 78, 221, 0.6)",
                  border: "2px solid #fff",
                  transform: "translate(-50%, -50%)",
                  boxShadow: "0 0 15px #fff",
                  pointerEvents: "none",
                  zIndex: 20,
                  transition: "all 0.1s ease-out"
                }}
              >
                <span 
                  style={{
                    position: "absolute",
                    top: "30px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "rgba(0,0,0,0.85)",
                    border: "1px solid var(--border-color)",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    color: "#fff",
                    fontSize: "9px",
                    fontFamily: "var(--font-mono)",
                    whiteSpace: "nowrap"
                  }}
                >
                  Agent: {agentActionType} ({agentCoords.x}, {agentCoords.y})
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
