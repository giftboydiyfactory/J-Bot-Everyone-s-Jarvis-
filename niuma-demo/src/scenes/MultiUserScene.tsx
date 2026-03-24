import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";
import { TeamsChat } from "../components/TeamsChat";
import { TeamsChatMessage } from "../components/TeamsChatMessage";

export const MultiUserScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const chatOpacity = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: "clamp" });

  // Message frames
  const F = [0, 50, 100, 130, 160, 210, 260, 310];

  // Concurrent workers visual - pulsing
  const workerPulse = 0.6 + 0.4 * Math.abs(Math.sin(frame * 0.08));
  const worker2Pulse = 0.6 + 0.4 * Math.abs(Math.sin(frame * 0.08 + 1.5));

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
          gap: 16,
        }}
      >
        <div style={{ width: 6, height: 48, backgroundColor: COLORS.nvidiaGreen, borderRadius: 3 }} />
        <div style={{ fontSize: 42, fontWeight: 800, color: COLORS.textPrimary }}>
          Multi-User Parallel Execution
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", gap: 40 }}>
        {/* Teams chat */}
        <div style={{ flex: 1.6, opacity: chatOpacity }}>
          <TeamsChat channelName="ai-tools" memberCount={8}>
            {/* Alice's request */}
            {frame >= F[0] && (
              <TeamsChatMessage
                avatar="AC"
                displayName="Alice Chen"
                timestamp="3:10 PM"
                message="@jbot generate tests for the API module"
                avatarColor={COLORS.avatarUser2}
                delay={F[0]}
                highlight
              />
            )}

            {/* Bob's request (almost simultaneously) */}
            {frame >= F[1] && (
              <TeamsChatMessage
                avatar="BL"
                displayName="Bob Liu"
                timestamp="3:10 PM"
                message="@jbot check CI/CD pipeline logs for today's failures"
                avatarColor={COLORS.avatarUser3}
                delay={F[1]}
                highlight
              />
            )}

            {/* Niuma acknowledges Alice */}
            {frame >= F[2] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="3:10 PM"
                message="🤖 Session [0323-c1a2] → Alice's test generation. Starting now..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={F[2]}
              />
            )}

            {/* Niuma acknowledges Bob */}
            {frame >= F[3] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="3:10 PM"
                message="🤖 Session [0323-d3b4] → Bob's pipeline check. Running in parallel..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={F[3]}
              />
            )}

            {/* Progress for both */}
            {frame >= F[4] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="3:11 PM"
                message="⏱️ [0323-c1a2] Alice: Analyzing API routes... [0323-d3b4] Bob: Reading pipeline logs..."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={F[4]}
              />
            )}

            {/* Alice's result */}
            {frame >= F[5] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="3:12 PM"
                message="✅ Alice: 15 tests generated, all passing. Coverage: 94%. PR ready for review."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={F[5]}
              />
            )}

            {/* Bob's result */}
            {frame >= F[6] && (
              <TeamsChatMessage
                avatar="🤖"
                displayName="J-Bot"
                timestamp="3:13 PM"
                message="✅ Bob: Found 2 failing stages in deploy-prod. Root cause: missing env var. Fix PR ready."
                isBot
                avatarColor={COLORS.nvidiaGreen}
                delay={F[6]}
              />
            )}
          </TeamsChat>
        </div>

        {/* Parallel workers visualization */}
        <div
          style={{
            width: 360,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: COLORS.textPrimary,
              opacity: headerOpacity,
              marginBottom: 4,
            }}
          >
            Parallel Sessions
          </div>

          {/* Worker 1 - Alice */}
          <div
            style={{
              backgroundColor: "rgba(26,26,46,0.9)",
              border: `2px solid ${COLORS.avatarUser2}`,
              borderRadius: 12,
              padding: 20,
              opacity: interpolate(frame, [F[2], F[2] + 20], [0, 1], { extrapolateRight: "clamp" }),
              boxShadow: frame >= F[2] && frame < F[5] ? `0 0 ${20 * workerPulse}px ${COLORS.avatarUser2}40` : "none",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.avatarUser2 }}>
                Session [0323-c1a2]
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: frame >= F[5] ? COLORS.statusSuccess : COLORS.avatarUser2,
                  backgroundColor: frame >= F[5] ? "rgba(76,175,80,0.15)" : `${COLORS.avatarUser2}20`,
                  padding: "2px 8px",
                  borderRadius: 10,
                }}
              >
                {frame >= F[5] ? "DONE" : "RUNNING"}
              </span>
            </div>
            <div style={{ fontSize: 12, color: COLORS.textMuted, marginBottom: 6 }}>
              Owner: Alice Chen
            </div>
            <div style={{ fontSize: 13, color: COLORS.textSecondary, marginBottom: 10 }}>
              {frame >= F[5]
                ? "Generated 15 tests (94% coverage)"
                : "Generating API tests..."}
            </div>
            <div style={{ height: 4, backgroundColor: COLORS.teamsBorder, borderRadius: 2, overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  backgroundColor: frame >= F[5] ? COLORS.statusSuccess : COLORS.avatarUser2,
                  width: frame >= F[5]
                    ? "100%"
                    : `${interpolate(frame, [F[2], F[5]], [10, 90], { extrapolateRight: "clamp" })}%`,
                  borderRadius: 2,
                }}
              />
            </div>
          </div>

          {/* Worker 2 - Bob */}
          <div
            style={{
              backgroundColor: "rgba(26,26,46,0.9)",
              border: `2px solid ${COLORS.avatarUser3}`,
              borderRadius: 12,
              padding: 20,
              opacity: interpolate(frame, [F[3], F[3] + 20], [0, 1], { extrapolateRight: "clamp" }),
              boxShadow: frame >= F[3] && frame < F[6] ? `0 0 ${20 * worker2Pulse}px ${COLORS.avatarUser3}40` : "none",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.avatarUser3 }}>
                Session [0323-d3b4]
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: frame >= F[6] ? COLORS.statusSuccess : COLORS.avatarUser3,
                  backgroundColor: frame >= F[6] ? "rgba(76,175,80,0.15)" : `${COLORS.avatarUser3}20`,
                  padding: "2px 8px",
                  borderRadius: 10,
                }}
              >
                {frame >= F[6] ? "DONE" : "RUNNING"}
              </span>
            </div>
            <div style={{ fontSize: 12, color: COLORS.textMuted, marginBottom: 6 }}>
              Owner: Bob Liu
            </div>
            <div style={{ fontSize: 13, color: COLORS.textSecondary, marginBottom: 10 }}>
              {frame >= F[6]
                ? "Found 2 failing stages, fix ready"
                : "Scanning pipeline logs..."}
            </div>
            <div style={{ height: 4, backgroundColor: COLORS.teamsBorder, borderRadius: 2, overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  backgroundColor: frame >= F[6] ? COLORS.statusSuccess : COLORS.avatarUser3,
                  width: frame >= F[6]
                    ? "100%"
                    : `${interpolate(frame, [F[3], F[6]], [10, 90], { extrapolateRight: "clamp" })}%`,
                  borderRadius: 2,
                }}
              />
            </div>
          </div>

          {/* Key point */}
          {frame >= 180 && (
            <div
              style={{
                backgroundColor: "rgba(118,185,0,0.08)",
                border: `1px solid ${COLORS.nvidiaGreen}40`,
                borderRadius: 10,
                padding: 16,
                opacity: interpolate(frame, [180, 210], [0, 1], { extrapolateRight: "clamp" }),
                marginTop: 8,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.nvidiaGreen, marginBottom: 6 }}>
                Both tasks ran simultaneously
              </div>
              <div style={{ fontSize: 13, color: COLORS.textSecondary, lineHeight: 1.5 }}>
                No queuing. No waiting. Each team member gets their own dedicated task session.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
