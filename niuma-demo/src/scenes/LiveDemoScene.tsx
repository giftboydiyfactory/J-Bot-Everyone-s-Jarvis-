import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";
import { TeamsChat } from "../components/TeamsChat";
import { TeamsChatMessage } from "../components/TeamsChatMessage";

export const LiveDemoScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const chatOpacity = interpolate(frame, [10, 35], [0, 1], { extrapolateRight: "clamp" });

  // Message appearance frames
  const MSG_FRAMES = [0, 90, 180, 270, 360];

  // Show typing animation between messages
  const showTyping1 = frame >= 10 && frame < 90;
  const showTyping2 = frame >= 100 && frame < 180;
  const typingDots = Math.floor((frame % 20) / 7);

  // Progress bar for the overall demo
  const progressPct = interpolate(frame, [0, 450], [0, 100], { extrapolateRight: "clamp" });

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
          marginBottom: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 6, height: 48, backgroundColor: COLORS.nvidiaGreen, borderRadius: 3 }} />
          <div style={{ fontSize: 42, fontWeight: 800, color: COLORS.textPrimary }}>
            Live Demo: Task Execution
          </div>
        </div>
        {/* Timeline indicator */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 14, color: COLORS.textMuted, marginBottom: 6 }}>Session Progress</div>
          <div
            style={{
              width: 200,
              height: 6,
              backgroundColor: COLORS.teamsPanel,
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${progressPct}%`,
                height: "100%",
                backgroundColor: COLORS.nvidiaGreen,
                borderRadius: 3,
                transition: "width 0.1s",
              }}
            />
          </div>
        </div>
      </div>

      {/* Main layout: chat + status panel */}
      <div style={{ flex: 1, display: "flex", gap: 40 }}>
        {/* Teams Chat */}
        <div style={{ flex: 1.5, opacity: chatOpacity }}>
          <TeamsChat channelName="ai-tools" memberCount={12}>
            {/* Message 1: User request */}
            <TeamsChatMessage
              avatar="JW"
              displayName="Jackey Wang"
              timestamp="2:14 PM"
              message="@jbot analyze the build system for issues"
              avatarColor={COLORS.avatarUser1}
              delay={MSG_FRAMES[0]}
              highlight
            />

            {/* Typing indicator 1 */}
            {showTyping1 && (
              <div style={{ display: "flex", gap: 12, padding: "6px 16px", alignItems: "center" }}>
                <div style={{ width: 32, height: 32, borderRadius: "50%", backgroundColor: COLORS.nvidiaGreen, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🤖</div>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: COLORS.nvidiaGreen, opacity: typingDots === i ? 1 : 0.3 }} />
                  ))}
                  <span style={{ marginLeft: 8, fontSize: 13, color: COLORS.textMuted }}>J-Bot is typing...</span>
                </div>
              </div>
            )}

            {/* Message 2: Bot acknowledges */}
            {frame >= MSG_FRAMES[1] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="2:14 PM"
                message="🤖 Analyzing... Session [0323-b2c1] started. I'll scan the build system for issues, security concerns, and performance problems."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={MSG_FRAMES[1]}
              />
            )}

            {/* Typing indicator 2 */}
            {showTyping2 && (
              <div style={{ display: "flex", gap: 12, padding: "6px 16px", alignItems: "center" }}>
                <div style={{ width: 32, height: 32, borderRadius: "50%", backgroundColor: COLORS.nvidiaGreen, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🤖</div>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: COLORS.nvidiaGreen, opacity: typingDots === i ? 1 : 0.3 }} />
                  ))}
                  <span style={{ marginLeft: 8, fontSize: 13, color: COLORS.textMuted }}>J-Bot is typing...</span>
                </div>
              </div>
            )}

            {/* Message 3: Progress heartbeat 1 */}
            {frame >= MSG_FRAMES[2] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="2:15 PM"
                message="⏱️ Session [0323-b2c1] running (45s) — Reading `build/pipeline.ts`..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={MSG_FRAMES[2]}
              />
            )}

            {/* Message 4: Progress heartbeat 2 */}
            {frame >= MSG_FRAMES[3] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="2:16 PM"
                message="⏱️ Session [0323-b2c1] running (90s) — Found 3 potential issues, continuing deep analysis..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={MSG_FRAMES[3]}
              />
            )}

            {/* Message 5: Final result */}
            {frame >= MSG_FRAMES[4] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="2:17 PM"
                message="✅ Analysis Complete! Found: 2 bugs, 1 security issue, 3 improvements suggested. Full report: [View Details]"
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={MSG_FRAMES[4]}
              />
            )}
          </TeamsChat>
        </div>

        {/* Status panel */}
        <div
          style={{
            width: 380,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.textPrimary, opacity: headerOpacity }}>
            Session Status
          </div>

          {/* Worker status card */}
          <div
            style={{
              backgroundColor: "rgba(26,26,46,0.9)",
              border: `1px solid ${COLORS.nvidiaGreen}50`,
              borderRadius: 12,
              padding: 20,
              opacity: interpolate(frame, [90, 120], [0, 1], { extrapolateRight: "clamp" }),
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.nvidiaGreen }}>Session [0323-b2c1]</span>
              <span
                style={{
                  fontSize: 12,
                  color: frame >= MSG_FRAMES[4] ? COLORS.statusSuccess : COLORS.nvidiaGreen,
                  fontWeight: 600,
                  backgroundColor: frame >= MSG_FRAMES[4] ? "rgba(76,175,80,0.15)" : "rgba(118,185,0,0.15)",
                  padding: "2px 10px",
                  borderRadius: 10,
                }}
              >
                {frame >= MSG_FRAMES[4] ? "COMPLETE" : "RUNNING"}
              </span>
            </div>
            <div style={{ fontSize: 13, color: COLORS.textMuted, marginBottom: 8 }}>
              Task: analyze build system for issues
            </div>
            <div style={{ fontSize: 13, color: COLORS.textSecondary, marginBottom: 12 }}>
              {frame < MSG_FRAMES[2]
                ? "Starting session..."
                : frame < MSG_FRAMES[3]
                ? "Reading build/pipeline.ts..."
                : frame < MSG_FRAMES[4]
                ? "Analyzing 3 issues found..."
                : "Analysis complete"}
            </div>
            {/* Progress bar */}
            <div style={{ height: 4, backgroundColor: COLORS.teamsBorder, borderRadius: 2, overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  backgroundColor: frame >= MSG_FRAMES[4] ? COLORS.statusSuccess : COLORS.nvidiaGreen,
                  width: frame >= MSG_FRAMES[4]
                    ? "100%"
                    : `${interpolate(frame, [90, 360], [5, 85], { extrapolateRight: "clamp" })}%`,
                  borderRadius: 2,
                }}
              />
            </div>
          </div>

          {/* Results breakdown */}
          {frame >= MSG_FRAMES[4] && (
            <div
              style={{
                backgroundColor: "rgba(26,26,46,0.9)",
                border: `1px solid ${COLORS.statusSuccess}40`,
                borderRadius: 12,
                padding: 20,
                opacity: interpolate(frame, [MSG_FRAMES[4], MSG_FRAMES[4] + 20], [0, 1], { extrapolateRight: "clamp" }),
              }}
            >
              <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.statusSuccess, marginBottom: 14 }}>
                Analysis Results
              </div>
              {[
                { icon: "🐛", label: "Bugs Found", value: "2", color: COLORS.statusError },
                { icon: "🔒", label: "Security Issues", value: "1", color: COLORS.statusWarning },
                { icon: "💡", label: "Improvements", value: "3", color: COLORS.nvidiaGreen },
              ].map((item, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 8,
                    padding: "6px 0",
                    borderBottom: i < 2 ? `1px solid ${COLORS.teamsBorder}` : "none",
                  }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ fontSize: 16 }}>{item.icon}</span>
                    <span style={{ fontSize: 14, color: COLORS.textSecondary }}>{item.label}</span>
                  </div>
                  <span style={{ fontSize: 18, fontWeight: 700, color: item.color }}>{item.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Cost tracking */}
          {frame >= 200 && (
            <div
              style={{
                backgroundColor: "rgba(26,26,46,0.6)",
                border: `1px solid ${COLORS.teamsBorder}`,
                borderRadius: 10,
                padding: 16,
                opacity: interpolate(frame, [200, 230], [0, 1], { extrapolateRight: "clamp" }),
              }}
            >
              <div style={{ fontSize: 13, color: COLORS.textMuted, marginBottom: 8 }}>Session Cost</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.nvidiaGreen }}>
                ${interpolate(frame, [200, 450], [0, 0.08], { extrapolateRight: "clamp" }).toFixed(3)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
