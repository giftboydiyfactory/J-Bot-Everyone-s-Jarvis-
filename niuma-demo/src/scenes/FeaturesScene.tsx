import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";
import { FeatureCard } from "../components/FeatureCard";

const FEATURES = [
  {
    icon: "💬",
    title: "Teams-Native",
    description: "@jbot trigger in any channel. Zero terminal switching needed.",
    appearFrame: 30,
  },
  {
    icon: "🧠",
    title: "Persistent Coordinator",
    description: "Persistent memory across sessions — remembers previous tasks and context.",
    appearFrame: 80,
  },
  {
    icon: "⚙️",
    title: "Concurrent Sessions",
    description: "Up to 5 parallel Claude Code sessions running simultaneously.",
    appearFrame: 130,
  },
  {
    icon: "📡",
    title: "Live Progress",
    description: "60-second heartbeat updates keep the whole team informed in real time.",
    appearFrame: 180,
  },
  {
    icon: "🔐",
    title: "Permission Control",
    description: "Admin vs member roles. Fine-grained access control per channel.",
    appearFrame: 230,
  },
  {
    icon: "💰",
    title: "Cost Tracking",
    description: "Per-session USD monitoring with aggregated team cost reporting.",
    appearFrame: 280,
  },
];

export const FeaturesScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const headerTranslate = interpolate(frame, [0, 20], [-20, 0], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        flexDirection: "column",
        padding: "50px 80px",
        boxSizing: "border-box",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          opacity: headerOpacity,
          transform: `translateY(${headerTranslate}px)`,
          marginBottom: 48,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div style={{ width: 6, height: 48, backgroundColor: COLORS.nvidiaGreen, borderRadius: 3 }} />
        <div style={{ fontSize: 48, fontWeight: 800, color: COLORS.textPrimary }}>Core Capabilities</div>
      </div>

      {/* Feature grid: 3 columns x 2 rows */}
      <div
        style={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gridTemplateRows: "1fr 1fr",
          gap: 28,
        }}
      >
        {FEATURES.map((feature, i) => (
          <FeatureCard
            key={i}
            icon={feature.icon}
            title={feature.title}
            description={feature.description}
            appearFrame={feature.appearFrame}
            globalFrame={frame}
            index={i}
          />
        ))}
      </div>
    </div>
  );
};
