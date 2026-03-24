import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../styles";
import { TeamsChatUI } from "../components/TeamsChatUI";
import { MessageData } from "../components/ChatMessage";

const ResultCard: React.FC<{
  frame: number;
  appearFrame: number;
  fps: number;
  children: React.ReactNode;
}> = ({ frame, appearFrame, fps, children }) => {
  const progress = spring({
    frame: Math.max(0, frame - appearFrame),
    fps,
    config: { damping: 14, stiffness: 80 },
  });
  const opacity = interpolate(Math.max(0, frame - appearFrame), [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        opacity,
        transform: `translateX(${interpolate(progress, [0, 1], [-20, 0])}px)`,
      }}
    >
      {children}
    </div>
  );
};

export const ResultsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const ResultContent = () => (
    <div
      style={{
        backgroundColor: "rgba(15,25,15,0.6)",
        border: "1px solid rgba(63,185,80,0.3)",
        borderRadius: 8,
        padding: "14px 16px",
        fontSize: 13,
        lineHeight: 1.8,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      <ResultCard frame={frame} appearFrame={60} fps={fps}>
        <div
          style={{
            color: COLORS.statusSuccess,
            fontWeight: 700,
            marginBottom: 8,
            fontSize: 14,
          }}
        >
          ✅ Session [0324-a7f3] completed
        </div>
      </ResultCard>

      <ResultCard frame={frame} appearFrame={90} fps={fps}>
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.1)",
            paddingTop: 10,
            marginBottom: 10,
          }}
        >
          <div
            style={{
              color: COLORS.textPrimary,
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Security Review — src/auth/middleware.ts
          </div>
        </div>
      </ResultCard>

      <ResultCard frame={frame} appearFrame={130} fps={fps}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            marginBottom: 8,
            backgroundColor: "rgba(248,81,73,0.1)",
            borderRadius: 6,
            padding: "8px 10px",
          }}
        >
          <span style={{ fontSize: 16 }}>🔴</span>
          <div>
            <div
              style={{
                color: COLORS.statusError,
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              Critical:
            </div>
            <div style={{ color: COLORS.textPrimary, fontSize: 13 }}>
              JWT token not validated on /api/admin routes
            </div>
          </div>
        </div>
      </ResultCard>

      <ResultCard frame={frame} appearFrame={185} fps={fps}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            marginBottom: 8,
            backgroundColor: "rgba(210,153,34,0.1)",
            borderRadius: 6,
            padding: "8px 10px",
          }}
        >
          <span style={{ fontSize: 16 }}>🟡</span>
          <div>
            <div
              style={{
                color: COLORS.statusWarning,
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              Warning:
            </div>
            <div style={{ color: COLORS.textPrimary, fontSize: 13 }}>
              Session timeout set to 24h (recommend 4h)
            </div>
          </div>
        </div>
      </ResultCard>

      <ResultCard frame={frame} appearFrame={240} fps={fps}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            marginBottom: 12,
            backgroundColor: "rgba(63,185,80,0.1)",
            borderRadius: 6,
            padding: "8px 10px",
          }}
        >
          <span style={{ fontSize: 16 }}>🟢</span>
          <div>
            <div
              style={{
                color: COLORS.statusSuccess,
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              Good:
            </div>
            <div style={{ color: COLORS.textPrimary, fontSize: 13 }}>
              CSRF protection properly implemented
            </div>
          </div>
        </div>
      </ResultCard>

      <ResultCard frame={frame} appearFrame={295} fps={fps}>
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.1)",
            paddingTop: 10,
            display: "flex",
            gap: 20,
            fontSize: 12,
            color: COLORS.textSecondary,
          }}
        >
          <span>
            <span style={{ color: COLORS.statusWarning }}>3</span> issues found
          </span>
          <span>
            Cost:{" "}
            <span style={{ color: COLORS.nvidiaGreen }}>$0.12</span>
          </span>
          <span>
            Duration:{" "}
            <span style={{ color: COLORS.nvidiaGreen }}>45s</span>
          </span>
        </div>
      </ResultCard>
    </div>
  );

  const chatMessages: MessageData[] = [
    {
      id: "1",
      sender: "Jackey Wang",
      avatar: "JW",
      avatarColor: COLORS.avatarUser1,
      text: "@jbot review the auth middleware in src/auth/ for security vulnerabilities",
      isBot: false,
      timestamp: "Today 10:24 AM",
      appearFrame: 0,
    },
    {
      id: "2",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:25 AM",
      appearFrame: 30,
      text: <ResultContent />,
    },
  ];

  // Highlight overlay that pulses on the result
  const highlightOpacity = interpolate(frame, [310, 340, 380, 400], [0, 0.3, 0.3, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: COLORS.bgPrimary,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: containerOpacity,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        position: "relative",
      }}
    >
      {/* Scene label */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 60,
          color: COLORS.nvidiaGreen,
          fontSize: 15,
          fontWeight: 600,
          letterSpacing: 2,
        }}
      >
        SCENE 3 — RESULTS DELIVERED
      </div>

      <div
        style={{
          display: "flex",
          gap: 40,
          width: 1760,
          height: 900,
          alignItems: "stretch",
        }}
      >
        {/* Teams Chat */}
        <div style={{ flex: 1.4 }}>
          <TeamsChatUI
            channelName="Interconnect Engineering"
            messages={chatMessages}
            showTyping={false}
            globalFrame={frame}
            style={{ height: "100%" }}
          />
        </div>

        {/* Right panel: Callout annotations */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          <div
            style={{
              color: COLORS.nvidiaGreen,
              fontSize: 24,
              fontWeight: 700,
              marginBottom: 8,
            }}
          >
            Structured Security Report
          </div>

          {[
            {
              icon: "🎯",
              title: "Actionable Findings",
              desc: "Each issue is clearly categorized as Critical, Warning, or Good with specific file references",
              appearFrame: 100,
            },
            {
              icon: "💰",
              title: "Cost Transparency",
              desc: "Every session reports exact token cost so your team can track AI spending",
              appearFrame: 220,
            },
            {
              icon: "⚡",
              title: "Fast Turnaround",
              desc: "Full security analysis of auth middleware completed in just 45 seconds",
              appearFrame: 320,
            },
            {
              icon: "📋",
              title: "Team Visible",
              desc: "Results posted directly in Teams channel — no context switching needed",
              appearFrame: 380,
            },
          ].map((item, i) => {
            const itemOpacity = interpolate(
              frame,
              [item.appearFrame, item.appearFrame + 15],
              [0, 1],
              { extrapolateRight: "clamp" }
            );
            const itemY = interpolate(
              frame,
              [item.appearFrame, item.appearFrame + 20],
              [15, 0],
              { extrapolateRight: "clamp" }
            );

            return (
              <div
                key={i}
                style={{
                  opacity: itemOpacity,
                  transform: `translateY(${itemY}px)`,
                  backgroundColor: COLORS.teamsMessage,
                  border: `1px solid ${COLORS.teamsBorder}`,
                  borderRadius: 10,
                  padding: "14px 16px",
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-start",
                }}
              >
                <span style={{ fontSize: 24, flexShrink: 0 }}>{item.icon}</span>
                <div>
                  <div
                    style={{
                      color: COLORS.textPrimary,
                      fontWeight: 600,
                      fontSize: 14,
                      marginBottom: 4,
                    }}
                  >
                    {item.title}
                  </div>
                  <div
                    style={{
                      color: COLORS.textSecondary,
                      fontSize: 13,
                      lineHeight: 1.5,
                    }}
                  >
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
