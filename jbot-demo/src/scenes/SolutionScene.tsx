import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { COLORS } from "../styles";
import { TeamsChat } from "../components/TeamsChat";
import { TeamsChatMessage } from "../components/TeamsChatMessage";

export const SolutionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const headerTranslate = interpolate(frame, [0, 20], [-20, 0], { extrapolateRight: "clamp" });

  const chatProgress = spring({
    frame: Math.max(0, frame - 20),
    fps,
    config: { damping: 14, stiffness: 80 },
  });
  const chatOpacity = interpolate(chatProgress, [0, 1], [0, 1]);
  const chatScale = interpolate(chatProgress, [0, 1], [0.92, 1]);

  // Show typing indicator between user message and bot response
  const showTyping = frame >= 40 && frame < 80;
  const typingDots = Math.floor((frame % 20) / 7);

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        flexDirection: "column",
        padding: "60px 80px",
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
          The Solution:{" "}
          <span
            style={{
              color: COLORS.nvidiaGreen,
              backgroundColor: "rgba(118,185,0,0.1)",
              borderRadius: 8,
              padding: "0 12px",
            }}
          >
            @jbot
          </span>
        </div>
      </div>

      {/* Chat demo + annotation */}
      <div style={{ flex: 1, display: "flex", gap: 60, alignItems: "center" }}>
        {/* Teams Chat mockup */}
        <div
          style={{
            flex: 1.4,
            height: 620,
            opacity: chatOpacity,
            transform: `scale(${chatScale})`,
            transformOrigin: "left center",
          }}
        >
          <TeamsChat channelName="ai-tools" memberCount={12}>
            <TeamsChatMessage
              avatar="JW"
              displayName="Jackey Wang"
              timestamp="10:23 AM"
              message="@jbot review the auth module for security issues"
              avatarColor={COLORS.avatarUser1}
              delay={30}
              highlight
            />
            {showTyping && (
              <div style={{ display: "flex", gap: 12, padding: "8px 16px", alignItems: "center" }}>
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: "50%",
                    backgroundColor: COLORS.nvidiaGreen,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                  }}
                >
                  🤖
                </div>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        backgroundColor: COLORS.nvidiaGreen,
                        opacity: typingDots === i ? 1 : 0.3,
                      }}
                    />
                  ))}
                  <span
                    style={{
                      marginLeft: 8,
                      fontSize: 13,
                      color: COLORS.textMuted,
                      fontFamily: "'Segoe UI', sans-serif",
                    }}
                  >
                    J-Bot is typing...
                  </span>
                </div>
              </div>
            )}
            {frame >= 80 && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="10:23 AM"
                message="🤖 Got it! Starting task session `0323-a7f3`... I'll analyze the auth module and report back here. ETA ~2 minutes."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={80}
              />
            )}
            {frame >= 110 && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="10:24 AM"
                message="⏱️ Session [0323-a7f3] running (30s) — Reading src/auth/middleware.ts..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={110}
              />
            )}
          </TeamsChat>
        </div>

        {/* Annotation panel */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          {[
            {
              delay: 30,
              icon: "💬",
              title: "Just mention @jbot",
              desc: "Type your task naturally in Teams. No terminal required.",
              color: COLORS.statusInfo,
            },
            {
              delay: 80,
              icon: "🚀",
              title: "Instant session spawn",
              desc: "J-Bot immediately creates a dedicated Claude Code session for your task.",
              color: COLORS.nvidiaGreen,
            },
            {
              delay: 110,
              icon: "📡",
              title: "Live progress in Teams",
              desc: "60-second heartbeat updates keep your whole team informed — no context switching needed.",
              color: COLORS.statusWarning,
            },
          ].map((item, i) => {
            const itemOpacity = interpolate(frame, [item.delay, item.delay + 20], [0, 1], {
              extrapolateRight: "clamp",
            });
            const itemTranslate = interpolate(frame, [item.delay, item.delay + 20], [30, 0], {
              extrapolateRight: "clamp",
            });
            return (
              <div
                key={i}
                style={{
                  opacity: itemOpacity,
                  transform: `translateX(${itemTranslate}px)`,
                  display: "flex",
                  gap: 16,
                  alignItems: "flex-start",
                  backgroundColor: "rgba(255,255,255,0.04)",
                  padding: "20px 24px",
                  borderRadius: 12,
                  borderLeft: `4px solid ${item.color}`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    backgroundColor: `${item.color}20`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 22,
                    flexShrink: 0,
                  }}
                >
                  {item.icon}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: item.color,
                      marginBottom: 6,
                    }}
                  >
                    {item.title}
                  </div>
                  <div style={{ fontSize: 15, color: COLORS.textSecondary, lineHeight: 1.5 }}>
                    {item.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
