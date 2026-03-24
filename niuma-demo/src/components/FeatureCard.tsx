import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";
import { COLORS } from "../styles";

interface FeatureCardProps {
  icon: string;
  title: string;
  description: string;
  appearFrame: number;
  globalFrame: number;
  index: number;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  appearFrame,
  globalFrame,
  index,
}) => {
  const { fps } = useVideoConfig();
  const framesSince = Math.max(0, globalFrame - appearFrame);

  const progress = spring({
    frame: framesSince,
    fps,
    config: { damping: 14, stiffness: 80, mass: 1 },
  });

  const opacity = interpolate(framesSince, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(progress, [0, 1], [0.7, 1]);
  const translateY = interpolate(progress, [0, 1], [30, 0]);

  if (globalFrame < appearFrame) return null;

  return (
    <div
      style={{
        opacity,
        transform: `scale(${scale}) translateY(${translateY}px)`,
        backgroundColor: COLORS.teamsMessage,
        border: `1px solid ${COLORS.teamsBorder}`,
        borderRadius: 12,
        padding: "20px 22px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Green accent line */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          backgroundColor: COLORS.nvidiaGreen,
          borderRadius: "12px 12px 0 0",
        }}
      />

      <div style={{ fontSize: 32 }}>{icon}</div>
      <div
        style={{
          fontSize: 16,
          fontWeight: 700,
          color: COLORS.textPrimary,
          fontFamily: "'Segoe UI', system-ui, sans-serif",
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 13,
          color: COLORS.textSecondary,
          fontFamily: "'Segoe UI', system-ui, sans-serif",
          lineHeight: 1.5,
        }}
      >
        {description}
      </div>
    </div>
  );
};
