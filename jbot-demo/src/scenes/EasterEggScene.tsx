import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { COLORS } from "../styles";
import { TeamsChat } from "../components/TeamsChat";
import { TeamsChatMessage } from "../components/TeamsChatMessage";

const GOLD = "#FFD700";
const GOLD_DIM = "rgba(255, 215, 0, 0.15)";
const GOLD_BORDER = "rgba(255, 215, 0, 0.35)";

interface DeliverableCardProps {
  icon: string;
  label: string;
  appearFrame: number;
  globalFrame: number;
}

const DeliverableCard: React.FC<DeliverableCardProps> = ({
  icon,
  label,
  appearFrame,
  globalFrame,
}) => {
  const { fps } = useVideoConfig();
  const framesSince = Math.max(0, globalFrame - appearFrame);

  const progress = spring({
    frame: framesSince,
    fps,
    config: { damping: 14, stiffness: 80, mass: 1 },
  });

  const opacity = interpolate(framesSince, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(progress, [0, 1], [40, 0]);
  const scale = interpolate(progress, [0, 1], [0.75, 1]);

  // Checkmark fades in 20 frames after card appears
  const checkOpacity = interpolate(framesSince, [20, 36], [0, 1], {
    extrapolateRight: "clamp",
  });
  const checkScale = spring({
    frame: Math.max(0, framesSince - 20),
    fps,
    config: { damping: 12, stiffness: 120, mass: 0.8 },
  });

  if (globalFrame < appearFrame) return null;

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
        backgroundColor: COLORS.teamsMessage,
        border: `1px solid ${GOLD_BORDER}`,
        borderRadius: 14,
        padding: "20px 24px",
        display: "flex",
        alignItems: "center",
        gap: 18,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Gold accent line at top */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          backgroundColor: GOLD,
          borderRadius: "14px 14px 0 0",
        }}
      />

      <span style={{ fontSize: 36 }}>{icon}</span>

      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: 18,
            fontWeight: 700,
            color: COLORS.textPrimary,
            fontFamily: "'Segoe UI', system-ui, sans-serif",
          }}
        >
          {label}
        </div>
      </div>

      {/* Checkmark */}
      <div
        style={{
          opacity: checkOpacity,
          transform: `scale(${checkScale})`,
          width: 36,
          height: 36,
          borderRadius: "50%",
          backgroundColor: "rgba(63, 185, 80, 0.2)",
          border: `2px solid ${COLORS.statusSuccess}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 20,
          flexShrink: 0,
        }}
      >
        ✓
      </div>
    </div>
  );
};

export const EasterEggScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
  });
  const headerTranslate = interpolate(frame, [0, 22], [-24, 0], {
    extrapolateRight: "clamp",
  });
  const chatOpacity = interpolate(frame, [18, 45], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Message frames
  const MSG_USER = 25;
  const MSG_NIUMA = 70;

  // Stats bar appears near end
  const statsOpacity = interpolate(frame, [185, 215], [0, 1], {
    extrapolateRight: "clamp",
  });
  const statsTranslate = interpolate(frame, [185, 215], [20, 0], {
    extrapolateRight: "clamp",
  });

  const DELIVERABLE_FRAMES = [80, 120, 160, 200];
  const deliverables = [
    { icon: "📧", label: "Email" },
    { icon: "📊", label: "PowerPoint" },
    { icon: "📄", label: "Confluence" },
    { icon: "🎬", label: "Video (this one!)" },
  ];

  const stats = [
    { value: "4", label: "sessions" },
    { value: "5", label: "systems" },
    { value: "~10 min", label: "total time" },
    { value: "Zero", label: "switching" },
  ];

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        flexDirection: "column",
        padding: "44px 80px 40px",
        boxSizing: "border-box",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          opacity: headerOpacity,
          transform: `translateY(${headerTranslate}px)`,
          marginBottom: 32,
          display: "flex",
          alignItems: "center",
          gap: 18,
        }}
      >
        <div
          style={{
            width: 6,
            height: 52,
            backgroundColor: GOLD,
            borderRadius: 3,
          }}
        />
        <div style={{ fontSize: 44, fontWeight: 800, color: COLORS.textPrimary }}>
          Easter Egg:{" "}
          <span style={{ color: GOLD }}>This Was Built by J-Bot</span>
        </div>
        <div style={{ fontSize: 40 }}>🥚</div>
      </div>

      {/* Main layout */}
      <div style={{ flex: 1, display: "flex", gap: 44, minHeight: 0 }}>
        {/* Left: Teams chat mockup */}
        <div style={{ flex: 1.1, opacity: chatOpacity, minWidth: 0 }}>
          <TeamsChat channelName="launch-prep" memberCount={5}>
            {frame >= MSG_USER && (
              <TeamsChatMessage
                avatar="JW"
                displayName="Jackey Wang"
                timestamp="9:03 AM"
                message="@jbot Create a launch email, PPT, Confluence page, and demo video"
                avatarColor={COLORS.avatarUser1}
                delay={MSG_USER}
                highlight
              />
            )}
            {frame >= MSG_NIUMA && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="9:03 AM"
                message="🤖 Dispatching 4 parallel sessions... Each will handle one deliverable simultaneously."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={MSG_NIUMA}
              />
            )}
          </TeamsChat>
        </div>

        {/* Right: Deliverable cards */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            justifyContent: "center",
          }}
        >
          <div
            style={{
              fontSize: 15,
              fontWeight: 700,
              color: GOLD,
              marginBottom: 4,
              opacity: interpolate(frame, [70, 95], [0, 1], {
                extrapolateRight: "clamp",
              }),
              letterSpacing: 1,
              textTransform: "uppercase",
            }}
          >
            Parallel Deliverables
          </div>
          {deliverables.map((d, i) => (
            <DeliverableCard
              key={i}
              icon={d.icon}
              label={d.label}
              appearFrame={DELIVERABLE_FRAMES[i]}
              globalFrame={frame}
            />
          ))}
        </div>
      </div>

      {/* Bottom stats bar */}
      <div
        style={{
          opacity: statsOpacity,
          transform: `translateY(${statsTranslate}px)`,
          marginTop: 24,
          padding: "16px 32px",
          backgroundColor: GOLD_DIM,
          border: `1px solid ${GOLD_BORDER}`,
          borderRadius: 12,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-around",
        }}
      >
        {stats.map((s, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 4,
            }}
          >
            <div
              style={{
                fontSize: 28,
                fontWeight: 800,
                color: GOLD,
                lineHeight: 1,
              }}
            >
              {s.value}
            </div>
            <div
              style={{
                fontSize: 14,
                color: COLORS.textSecondary,
                textTransform: "uppercase",
                letterSpacing: 1,
              }}
            >
              {s.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
