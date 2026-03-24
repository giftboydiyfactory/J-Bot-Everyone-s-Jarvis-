import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";
import { ArchitectureDiagram } from "../components/ArchitectureDiagram";

export const ArchitectureScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const headerTranslate = interpolate(frame, [0, 20], [-30, 0], { extrapolateRight: "clamp" });
  const diagramOpacity = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        flexDirection: "column",
        padding: "50px 80px 40px",
        boxSizing: "border-box",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          opacity: headerOpacity,
          transform: `translateY(${headerTranslate}px)`,
          marginBottom: 40,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div style={{ width: 6, height: 48, backgroundColor: COLORS.nvidiaGreen, borderRadius: 3 }} />
        <div style={{ fontSize: 48, fontWeight: 800, color: COLORS.textPrimary }}>
          Two-Tier Architecture
        </div>
      </div>

      {/* Architecture diagram */}
      <div
        style={{
          opacity: diagramOpacity,
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <ArchitectureDiagram />
      </div>

      {/* Bottom stats bar */}
      <div
        style={{
          opacity: interpolate(frame, [180, 220], [0, 1], { extrapolateRight: "clamp" }),
          display: "flex",
          gap: 24,
          marginTop: 20,
        }}
      >
        {[
          {
            icon: "🧠",
            label: "1 Coordinator",
            sub: "Persistent stateful memory",
            color: COLORS.nvidiaGreen,
          },
          {
            icon: "⚙️",
            label: "Up to 5 Sessions",
            sub: "Concurrent Claude sessions",
            color: COLORS.textSecondary,
          },
          {
            icon: "⏱️",
            label: "60s Heartbeat",
            sub: "Live progress updates in Teams",
            color: COLORS.statusWarning,
          },
          {
            icon: "🔄",
            label: "30s Poll Cycle",
            sub: "Always listening for @jbot",
            color: COLORS.statusInfo,
          },
          {
            icon: "💰",
            label: "Cost Tracking",
            sub: "Per-session USD monitoring",
            color: COLORS.statusSuccess,
          },
        ].map((stat, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              backgroundColor: "rgba(255,255,255,0.04)",
              border: `1px solid ${stat.color}30`,
              borderTop: `3px solid ${stat.color}`,
              borderRadius: 10,
              padding: "14px 16px",
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
            }}
          >
            <span style={{ fontSize: 24 }}>{stat.icon}</span>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: stat.color, marginBottom: 4 }}>
                {stat.label}
              </div>
              <div style={{ fontSize: 12, color: COLORS.textMuted }}>{stat.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
