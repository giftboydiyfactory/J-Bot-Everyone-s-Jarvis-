import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../styles";

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 60, mass: 1 },
  });

  const subtitleOpacity = interpolate(frame, [20, 45], [0, 1], {
    extrapolateRight: "clamp",
  });
  const subtitleTranslateY = interpolate(frame, [20, 45], [20, 0], {
    extrapolateRight: "clamp",
  });

  const badgeOpacity = interpolate(frame, [40, 60], [0, 1], {
    extrapolateRight: "clamp",
  });

  const glowScale = 1 + Math.sin(frame * 0.05) * 0.03;

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      {/* Animated background gradient orbs */}
      <div
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(118,185,0,0.15) 0%, transparent 70%)",
          top: "50%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 800,
          height: 400,
          borderRadius: "50%",
          background:
            "radial-gradient(ellipse, rgba(74,79,199,0.12) 0%, transparent 70%)",
          top: "30%",
          left: "20%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* NVIDIA branding pill */}
      <div
        style={{
          opacity: badgeOpacity,
          backgroundColor: "rgba(118,185,0,0.12)",
          border: `1px solid ${COLORS.nvidiaGreen}`,
          borderRadius: 24,
          padding: "6px 20px",
          marginBottom: 32,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: COLORS.nvidiaGreen,
          }}
        />
        <span
          style={{
            color: COLORS.nvidiaGreen,
            fontSize: 16,
            fontWeight: 600,
            letterSpacing: 2,
          }}
        >
          NVIDIA INTERCONNECT SHANGHAI
        </span>
      </div>

      {/* Robot emoji */}
      <div
        style={{
          fontSize: 80,
          marginBottom: 16,
          transform: `scale(${interpolate(titleProgress, [0, 1], [0.5, 1])})`,
          opacity: titleProgress,
        }}
      >
        🤖
      </div>

      {/* Main title */}
      <div
        style={{
          fontSize: 96,
          fontWeight: 900,
          color: COLORS.textPrimary,
          textAlign: "center",
          lineHeight: 1,
          marginBottom: 16,
          transform: `scale(${interpolate(titleProgress, [0, 1], [0.8, 1])})`,
          opacity: titleProgress,
          letterSpacing: -2,
        }}
      >
        J-Bot
      </div>

      {/* Green underline accent */}
      <div
        style={{
          width: interpolate(titleProgress, [0, 1], [0, 320]),
          height: 4,
          backgroundColor: COLORS.nvidiaGreen,
          borderRadius: 2,
          marginBottom: 28,
          boxShadow: `0 0 20px ${COLORS.nvidiaGreen}`,
        }}
      />

      {/* Subtitle / tagline */}
      <div
        style={{
          fontSize: 32,
          color: COLORS.textSecondary,
          textAlign: "center",
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleTranslateY}px)`,
          fontWeight: 400,
        }}
      >
        Everyone's Jarvis
      </div>

      {/* Secondary subtitle */}
      <div
        style={{
          fontSize: 22,
          color: COLORS.textMuted,
          textAlign: "center",
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleTranslateY}px)`,
          fontWeight: 400,
          marginTop: 12,
        }}
      >
        Claude Code Meets Microsoft Teams
      </div>

      {/* Bottom tagline */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          opacity: badgeOpacity,
          color: COLORS.textMuted,
          fontSize: 18,
          textAlign: "center",
        }}
      >
        AI-Powered Engineering Assistant for Teams Channels
      </div>
    </div>
  );
};
