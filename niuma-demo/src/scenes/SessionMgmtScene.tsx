import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../styles";
import { TeamsChatUI } from "../components/TeamsChatUI";
import { MessageData } from "../components/ChatMessage";

const SessionTable: React.FC<{
  frame: number;
  showStopResult: boolean;
}> = ({ frame, showStopResult }) => {
  const sessions = [
    {
      id: "0324-a7f3",
      task: "Auth review",
      status: "Done",
      duration: "45s",
      done: true,
    },
    {
      id: "0324-b2c1",
      task: "Test gen",
      status: showStopResult ? "Running" : "Running",
      duration: "30s",
      done: false,
    },
    {
      id: "0324-c3d2",
      task: "Architecture",
      status: showStopResult ? "Stopped" : "Running",
      duration: "15s",
      done: showStopResult,
      stopped: showStopResult,
    },
  ];

  return (
    <div
      style={{
        backgroundColor: "rgba(15,20,35,0.8)",
        border: "1px solid rgba(118,185,0,0.25)",
        borderRadius: 8,
        overflow: "hidden",
        fontFamily: "'Consolas', 'Courier New', monospace",
        fontSize: 13,
      }}
    >
      {/* Table header */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "130px 1fr 100px 90px",
          gap: 0,
          backgroundColor: "rgba(118,185,0,0.12)",
          borderBottom: "1px solid rgba(118,185,0,0.25)",
          padding: "8px 14px",
        }}
      >
        {["Session ID", "Task", "Status", "Duration"].map((h) => (
          <div
            key={h}
            style={{ color: COLORS.nvidiaGreen, fontWeight: 600, fontSize: 12 }}
          >
            {h}
          </div>
        ))}
      </div>

      {sessions.map((session, i) => {
        const rowOpacity = interpolate(
          frame,
          [60 + i * 20, 75 + i * 20],
          [0, 1],
          { extrapolateRight: "clamp" }
        );

        return (
          <div
            key={session.id}
            style={{
              display: "grid",
              gridTemplateColumns: "130px 1fr 100px 90px",
              gap: 0,
              padding: "9px 14px",
              borderBottom:
                i < sessions.length - 1
                  ? "1px solid rgba(255,255,255,0.06)"
                  : "none",
              opacity: rowOpacity,
              backgroundColor: session.stopped
                ? "rgba(248,81,73,0.06)"
                : "transparent",
            }}
          >
            <div style={{ color: COLORS.nvidiaGreen }}>{session.id}</div>
            <div style={{ color: COLORS.textPrimary }}>{session.task}</div>
            <div>
              {session.done && !session.stopped && (
                <span style={{ color: COLORS.statusSuccess }}>✅ Done</span>
              )}
              {!session.done && !session.stopped && (
                <span style={{ color: COLORS.statusWarning }}>⏳ Running</span>
              )}
              {session.stopped && (
                <span style={{ color: COLORS.statusError }}>🛑 Stopped</span>
              )}
            </div>
            <div style={{ color: COLORS.textSecondary }}>{session.duration}</div>
          </div>
        );
      })}
    </div>
  );
};

export const SessionMgmtScene: React.FC = () => {
  const frame = useCurrentFrame();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const showStopResult = frame >= 330;

  const messages: MessageData[] = [
    {
      id: "1",
      sender: "Jackey Wang",
      avatar: "JW",
      avatarColor: COLORS.avatarUser1,
      text: "@jbot report",
      isBot: false,
      timestamp: "Today 10:32 AM",
      appearFrame: 20,
    },
    {
      id: "2",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:32 AM",
      appearFrame: 50,
      text: (
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
          }}
        >
          <div
            style={{
              color: COLORS.nvidiaGreen,
              fontWeight: 700,
              fontSize: 14,
              marginBottom: 10,
            }}
          >
            Active Sessions
          </div>
          <SessionTable frame={frame} showStopResult={false} />
        </div>
      ),
    },
    {
      id: "3",
      sender: "Jackey Wang",
      avatar: "JW",
      avatarColor: COLORS.avatarUser1,
      text: "@jbot stop 0324-c3d2",
      isBot: false,
      timestamp: "Today 10:33 AM",
      appearFrame: 240,
    },
    {
      id: "4",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:33 AM",
      appearFrame: 290,
      text: (
        <div style={{ fontFamily: "'Segoe UI', system-ui, sans-serif" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 8,
              fontSize: 14,
            }}
          >
            <span>🛑</span>
            <span style={{ color: COLORS.textPrimary }}>
              Session{" "}
              <span
                style={{
                  fontFamily: "'Consolas', monospace",
                  color: COLORS.nvidiaGreen,
                }}
              >
                [0324-c3d2]
              </span>{" "}
              stopped.
            </span>
          </div>
          <div style={{ color: COLORS.textMuted, fontSize: 12 }}>
            Session process terminated. 2 sessions still running.
          </div>
        </div>
      ),
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
        SCENE 5 — SESSION MANAGEMENT
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
            messages={messages}
            showTyping={false}
            globalFrame={frame}
            style={{ height: "100%" }}
          />
        </div>

        {/* Right panel: Command reference */}
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
            ADMIN COMMANDS
          </div>

          {[
            {
              cmd: "@jbot report",
              desc: "View all active and completed sessions with status, task, and duration",
              icon: "📊",
              highlight: frame >= 20,
            },
            {
              cmd: "@jbot stop <session-id>",
              desc: "Immediately terminate a running task session",
              icon: "🛑",
              highlight: frame >= 240,
            },
            {
              cmd: "@jbot resume <session-id>",
              desc: "Resume a paused or interrupted session",
              icon: "▶️",
              highlight: false,
            },
            {
              cmd: "@jbot history",
              desc: "View completed sessions and their full output",
              icon: "📜",
              highlight: false,
            },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                backgroundColor: item.highlight
                  ? "rgba(118,185,0,0.08)"
                  : COLORS.teamsMessage,
                border: `1px solid ${
                  item.highlight
                    ? "rgba(118,185,0,0.4)"
                    : COLORS.teamsBorder
                }`,
                borderRadius: 10,
                padding: "14px 16px",
                transition: "all 0.3s",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 6,
                }}
              >
                <span style={{ fontSize: 20 }}>{item.icon}</span>
                <div
                  style={{
                    fontFamily: "'Consolas', monospace",
                    fontSize: 13,
                    color: COLORS.nvidiaGreen,
                    fontWeight: 600,
                  }}
                >
                  {item.cmd}
                </div>
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
          ))}
        </div>
      </div>
    </div>
  );
};
