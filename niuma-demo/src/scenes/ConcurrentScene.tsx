import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../styles";
import { TeamsChatUI } from "../components/TeamsChatUI";
import { MessageData } from "../components/ChatMessage";

export const ConcurrentScene: React.FC = () => {
  const frame = useCurrentFrame();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const workerCountOpacity = interpolate(frame, [200, 230], [0, 1], {
    extrapolateRight: "clamp",
  });

  const workerCount = frame >= 200 ? 3 : frame >= 130 ? 2 : frame >= 50 ? 1 : 0;

  const messages: MessageData[] = [
    {
      id: "1",
      sender: "Alex Chen",
      avatar: "AC",
      avatarColor: COLORS.avatarUser2,
      text: "@jbot generate unit tests for utils/parser.ts",
      isBot: false,
      timestamp: "Today 10:31 AM",
      appearFrame: 20,
    },
    {
      id: "2",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:31 AM",
      appearFrame: 70,
      text: (
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          <span style={{ color: COLORS.nvidiaGreen }}>Session [0324-b2c1] started</span>{" "}
          for test generation on{" "}
          <span
            style={{
              fontFamily: "'Consolas', monospace",
              backgroundColor: "rgba(255,255,255,0.08)",
              padding: "1px 5px",
              borderRadius: 3,
            }}
          >
            utils/parser.ts
          </span>
        </div>
      ),
    },
    {
      id: "3",
      sender: "Sarah Liu",
      avatar: "SL",
      avatarColor: COLORS.avatarUser3,
      text: "@jbot explain the CI/CD pipeline architecture",
      isBot: false,
      timestamp: "Today 10:31 AM",
      appearFrame: 120,
    },
    {
      id: "4",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:31 AM",
      appearFrame: 170,
      text: (
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          <span style={{ color: COLORS.nvidiaGreen }}>Session [0324-c3d2] started</span>{" "}
          for architecture analysis of CI/CD pipeline
        </div>
      ),
    },
    {
      id: "5",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:31 AM",
      appearFrame: 215,
      text: (
        <div
          style={{
            backgroundColor: "rgba(118,185,0,0.08)",
            border: "1px solid rgba(118,185,0,0.25)",
            borderRadius: 6,
            padding: "10px 12px",
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 13,
            lineHeight: 1.7,
          }}
        >
          <div style={{ color: COLORS.nvidiaGreen, fontWeight: 700, marginBottom: 6 }}>
            Status Update
          </div>
          <div
            style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: COLORS.statusSuccess,
              }}
            />
            <span style={{ color: COLORS.textPrimary }}>
              3 / 5 session slots active
            </span>
          </div>
          <div style={{ color: COLORS.textMuted, fontSize: 12 }}>
            Auth review, test generation, architecture analysis — all running in parallel
          </div>
        </div>
      ),
    },
  ];

  // Worker status cards
  const workerCards = [
    {
      id: "0324-a7f3",
      task: "Auth security review",
      user: "Jackey Wang",
      status: "running",
      elapsed: "62s",
      color: COLORS.avatarUser1,
      appearFrame: 30,
    },
    {
      id: "0324-b2c1",
      task: "Test gen: utils/parser.ts",
      user: "Alex Chen",
      status: "running",
      elapsed: "12s",
      color: COLORS.avatarUser2,
      appearFrame: 80,
    },
    {
      id: "0324-c3d2",
      task: "Architecture analysis",
      user: "Sarah Liu",
      status: "running",
      elapsed: "3s",
      color: COLORS.avatarUser3,
      appearFrame: 175,
    },
  ];

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
        SCENE 4 — CONCURRENT TASKS
      </div>

      {/* Worker count badge */}
      <div
        style={{
          position: "absolute",
          top: 36,
          right: 60,
          opacity: workerCountOpacity,
          backgroundColor: "rgba(118,185,0,0.15)",
          border: "1px solid rgba(118,185,0,0.5)",
          borderRadius: 20,
          padding: "6px 18px",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: COLORS.nvidiaGreen,
            boxShadow: `0 0 8px ${COLORS.nvidiaGreen}`,
          }}
        />
        <span
          style={{
            color: COLORS.nvidiaGreen,
            fontSize: 16,
            fontWeight: 700,
          }}
        >
          {workerCount} / 5 sessions active
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: 32,
          width: 1760,
          height: 900,
          alignItems: "stretch",
        }}
      >
        {/* Teams Chat */}
        <div style={{ flex: 1.3 }}>
          <TeamsChatUI
            channelName="Interconnect Engineering"
            messages={messages}
            showTyping={false}
            globalFrame={frame}
            style={{ height: "100%" }}
          />
        </div>

        {/* Right panel: Worker status cards */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: 1,
              padding: "8px 16px",
              backgroundColor: "rgba(255,255,255,0.04)",
              borderRadius: 6,
              textAlign: "center",
            }}
          >
            ACTIVE TASK SESSIONS
          </div>

          {workerCards.map((worker) => {
            const cardOpacity = interpolate(
              frame,
              [worker.appearFrame, worker.appearFrame + 12],
              [0, 1],
              { extrapolateRight: "clamp" }
            );
            const cardY = interpolate(
              frame,
              [worker.appearFrame, worker.appearFrame + 15],
              [20, 0],
              { extrapolateRight: "clamp" }
            );

            return (
              <div
                key={worker.id}
                style={{
                  opacity: cardOpacity,
                  transform: `translateY(${cardY}px)`,
                  backgroundColor: COLORS.teamsMessage,
                  border: `1px solid ${COLORS.teamsBorder}`,
                  borderRadius: 10,
                  padding: "16px 18px",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                {/* Left accent bar */}
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: 4,
                    backgroundColor: COLORS.nvidiaGreen,
                  }}
                />

                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    marginBottom: 10,
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontFamily: "'Consolas', monospace",
                        fontSize: 13,
                        color: COLORS.nvidiaGreen,
                        fontWeight: 600,
                        marginBottom: 4,
                      }}
                    >
                      [{worker.id}]
                    </div>
                    <div
                      style={{
                        fontSize: 14,
                        color: COLORS.textPrimary,
                        fontWeight: 500,
                      }}
                    >
                      {worker.task}
                    </div>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      backgroundColor: "rgba(63,185,80,0.1)",
                      border: "1px solid rgba(63,185,80,0.3)",
                      borderRadius: 12,
                      padding: "3px 10px",
                    }}
                  >
                    <div
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        backgroundColor: COLORS.statusSuccess,
                        animation: "pulse 2s infinite",
                      }}
                    />
                    <span
                      style={{
                        fontSize: 12,
                        color: COLORS.statusSuccess,
                        fontWeight: 600,
                      }}
                    >
                      Running
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: 16,
                    fontSize: 12,
                    color: COLORS.textMuted,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <div
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: "50%",
                        backgroundColor: worker.color,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 9,
                        color: "#fff",
                        fontWeight: 700,
                      }}
                    >
                      {worker.user.split(" ").map((n) => n[0]).join("")}
                    </div>
                    <span>{worker.user}</span>
                  </div>
                  <span>⏱ {worker.elapsed}</span>
                </div>
              </div>
            );
          })}

          {/* Empty slots */}
          <div
            style={{
              backgroundColor: "rgba(255,255,255,0.02)",
              border: `1px dashed ${COLORS.teamsBorder}`,
              borderRadius: 10,
              padding: "14px 18px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              flex: 1,
            }}
          >
            <span style={{ color: COLORS.textMuted, fontSize: 13 }}>
              2 session slots available
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
