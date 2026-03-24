import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../styles";
import { FeatureCard } from "../components/FeatureCard";

const features = [
  {
    icon: "💬",
    title: "Teams-Native",
    description: "Works in any Microsoft Teams group chat or channel. No extra tools required.",
  },
  {
    icon: "🧠",
    title: "Persistent Coordinator",
    description: "Persistent bot remembers all context, sessions, and team history.",
  },
  {
    icon: "⚡",
    title: "5 Parallel Sessions",
    description: "Up to 5 Claude Code sessions run concurrently for maximum throughput.",
  },
  {
    icon: "📡",
    title: "Real-time Updates",
    description: "60-second heartbeat keeps your team informed of session progress.",
  },
  {
    icon: "🎯",
    title: "Smart Routing",
    description: "Auto-decides to start new session, resume existing, or reply in thread.",
  },
];

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const containerOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Fade out at the end
  const fadeOut = interpolate(frame, [490, 530], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const finalOpacity = containerOpacity * fadeOut;

  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 60 },
  });

  const glowScale = 1 + Math.sin(frame * 0.04) * 0.04;

  // CTA appear
  const ctaOpacity = interpolate(frame, [280, 320], [0, 1], {
    extrapolateRight: "clamp",
  });
  const ctaY = interpolate(frame, [280, 320], [20, 0], {
    extrapolateRight: "clamp",
  });

  const footerOpacity = interpolate(frame, [340, 370], [0, 1], {
    extrapolateRight: "clamp",
  });

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
        opacity: finalOpacity,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          width: 800,
          height: 800,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(118,185,0,0.08) 0%, transparent 70%)",
          top: "50%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          pointerEvents: "none",
        }}
      />

      {/* Title section */}
      <div
        style={{
          textAlign: "center",
          marginBottom: 40,
          transform: `scale(${interpolate(titleProgress, [0, 1], [0.9, 1])})`,
          opacity: titleProgress,
        }}
      >
        <div
          style={{
            fontSize: 16,
            color: COLORS.nvidiaGreen,
            fontWeight: 600,
            letterSpacing: 3,
            marginBottom: 12,
          }}
        >
          KEY FEATURES
        </div>
        <div
          style={{
            fontSize: 52,
            fontWeight: 900,
            color: COLORS.textPrimary,
            lineHeight: 1.1,
            marginBottom: 4,
          }}
        >
          J-Bot
        </div>
        <div
          style={{
            fontSize: 22,
            fontWeight: 400,
            color: COLORS.textSecondary,
            marginBottom: 8,
          }}
        >
          Everyone's Jarvis
        </div>
        <div
          style={{
            width: 200,
            height: 3,
            backgroundColor: COLORS.nvidiaGreen,
            borderRadius: 2,
            margin: "0 auto",
            boxShadow: `0 0 16px ${COLORS.nvidiaGreen}`,
          }}
        />
      </div>

      {/* Feature cards grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: 20,
          width: 1680,
          marginBottom: 48,
        }}
      >
        {features.map((feature, i) => (
          <FeatureCard
            key={i}
            icon={feature.icon}
            title={feature.title}
            description={feature.description}
            appearFrame={60 + i * 40}
            globalFrame={frame}
            index={i}
          />
        ))}
      </div>

      {/* CTA section */}
      <div
        style={{
          opacity: ctaOpacity,
          transform: `translateY(${ctaY}px)`,
          textAlign: "center",
          marginBottom: 32,
        }}
      >
        <div
          style={{
            fontSize: 14,
            color: COLORS.textSecondary,
            marginBottom: 10,
            letterSpacing: 1,
          }}
        >
          GET STARTED
        </div>
        <div
          style={{
            backgroundColor: "rgba(118,185,0,0.12)",
            border: `2px solid ${COLORS.nvidiaGreen}`,
            borderRadius: 12,
            padding: "16px 36px",
            display: "inline-block",
            boxShadow: `0 0 30px rgba(118,185,0,0.2)`,
          }}
        >
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: COLORS.nvidiaGreen,
              fontFamily: "'Consolas', monospace",
              letterSpacing: 0.5,
            }}
          >
            confluence.nvidia.com/jbot
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          opacity: footerOpacity,
          textAlign: "center",
          color: COLORS.textMuted,
          fontSize: 14,
          lineHeight: 1.7,
        }}
      >
        <div>
          Built by{" "}
          <span style={{ color: COLORS.textSecondary, fontWeight: 600 }}>
            Jackey Wang
          </span>{" "}
          |{" "}
          <span style={{ color: COLORS.textSecondary }}>
            NVIDIA Interconnect Shanghai
          </span>
        </div>
        <div style={{ marginTop: 4, fontSize: 12 }}>
          Powered by Claude Code + Microsoft Teams Bot Framework
        </div>
      </div>

      {/* NVIDIA branding bottom right */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          right: 60,
          opacity: footerOpacity,
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            backgroundColor: COLORS.nvidiaGreen,
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 900,
            fontSize: 18,
            color: "#000",
          }}
        >
          N
        </div>
        <span
          style={{
            color: COLORS.nvidiaGreen,
            fontWeight: 700,
            fontSize: 18,
            letterSpacing: 1,
          }}
        >
          NVIDIA
        </span>
      </div>
    </div>
  );
};
