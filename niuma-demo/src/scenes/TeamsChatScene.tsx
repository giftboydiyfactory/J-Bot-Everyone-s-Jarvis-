import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../styles";
import { TeamsChatUI } from "../components/TeamsChatUI";
import { MessageData } from "../components/ChatMessage";

export const TeamsChatScene: React.FC = () => {
  const frame = useCurrentFrame();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Message sequence - frames relative to scene start
  const messages: MessageData[] = [
    {
      id: "1",
      sender: "Jackey Wang",
      avatar: "JW",
      avatarColor: COLORS.avatarUser1,
      text: "@jbot review the auth middleware in src/auth/ for security vulnerabilities",
      isBot: false,
      timestamp: "Today 10:24 AM",
      appearFrame: 40,
    },
    {
      id: "2",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      text: "Got it! Starting task session [0324-a7f3] to analyze auth middleware...",
      isBot: true,
      timestamp: "Today 10:24 AM",
      appearFrame: 130,
    },
    {
      id: "3",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:24 AM",
      appearFrame: 200,
      text: (
        <div
          style={{
            backgroundColor: "rgba(118,185,0,0.08)",
            border: "1px solid rgba(118,185,0,0.3)",
            borderRadius: 6,
            padding: "10px 14px",
            fontSize: 13,
            lineHeight: 1.6,
            fontFamily: "'Segoe UI', system-ui, sans-serif",
          }}
        >
          <div style={{ color: COLORS.nvidiaGreen, fontWeight: 600, marginBottom: 4 }}>
            Session Started
          </div>
          <div style={{ color: COLORS.textSecondary }}>
            Session ID: <span style={{ color: COLORS.textPrimary, fontFamily: "'Consolas', monospace" }}>0324-a7f3</span>
          </div>
          <div style={{ color: COLORS.textSecondary }}>
            Task: Security review of <span style={{ color: COLORS.textPrimary, fontFamily: "'Consolas', monospace" }}>src/auth/</span>
          </div>
          <div style={{ color: COLORS.textSecondary }}>
            Starting Claude Code session...
          </div>
        </div>
      ),
    },
  ];

  // Show typing indicator between frame 90 and 130
  const showTyping = frame >= 90 && frame < 130;
  const showTyping2 = frame >= 165 && frame < 200;

  // Side annotation panel
  const annotationOpacity = interpolate(frame, [60, 80], [0, 1], {
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
          opacity: annotationOpacity,
        }}
      >
        SCENE 1 — SENDING A REQUEST
      </div>

      {/* Main Teams chat window */}
      <div
        style={{
          display: "flex",
          gap: 40,
          alignItems: "flex-start",
          width: 1720,
        }}
      >
        {/* Teams sidebar mockup */}
        <div
          style={{
            width: 260,
            backgroundColor: "#1f1f1f",
            borderRadius: 8,
            padding: "16px 0",
            flexShrink: 0,
            alignSelf: "stretch",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Teams logo */}
          <div
            style={{
              padding: "0 16px 16px",
              borderBottom: "1px solid #333",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                backgroundColor: "#5b67d8",
                borderRadius: 6,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: 700,
                fontSize: 18,
              }}
            >
              T
            </div>
            <span style={{ color: "#fff", fontWeight: 600, fontSize: 16 }}>
              Microsoft Teams
            </span>
          </div>

          {/* Nav items */}
          {[
            { icon: "💬", label: "Chat" },
            { icon: "👥", label: "Teams", active: true },
            { icon: "📅", label: "Calendar" },
            { icon: "📁", label: "Files" },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                padding: "10px 16px",
                display: "flex",
                alignItems: "center",
                gap: 10,
                backgroundColor: item.active ? "rgba(91,103,216,0.2)" : "transparent",
                borderLeft: item.active ? "3px solid #5b67d8" : "3px solid transparent",
              }}
            >
              <span style={{ fontSize: 18 }}>{item.icon}</span>
              <span
                style={{
                  color: item.active ? "#fff" : "#999",
                  fontSize: 14,
                }}
              >
                {item.label}
              </span>
            </div>
          ))}

          <div
            style={{
              padding: "12px 16px 6px",
              color: "#666",
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: 1,
              marginTop: 8,
            }}
          >
            CHANNELS
          </div>

          {[
            { name: "General", unread: 0 },
            { name: "Interconnect Engineering", unread: 3, active: true },
            { name: "Code Review", unread: 0 },
            { name: "J-Bot Logs", unread: 1 },
          ].map((ch, i) => (
            <div
              key={i}
              style={{
                padding: "7px 16px",
                display: "flex",
                alignItems: "center",
                gap: 6,
                backgroundColor: ch.active ? "rgba(255,255,255,0.08)" : "transparent",
                cursor: "pointer",
              }}
            >
              <span style={{ color: "#888", fontSize: 13 }}>#</span>
              <span
                style={{
                  color: ch.active ? "#fff" : "#999",
                  fontSize: 13,
                  fontWeight: ch.unread > 0 ? 600 : 400,
                  flex: 1,
                }}
              >
                {ch.name}
              </span>
              {ch.unread > 0 && (
                <div
                  style={{
                    backgroundColor: "#5b67d8",
                    borderRadius: 10,
                    padding: "1px 7px",
                    fontSize: 11,
                    color: "#fff",
                    fontWeight: 600,
                  }}
                >
                  {ch.unread}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Main chat area */}
        <TeamsChatUI
          channelName="Interconnect Engineering"
          messages={messages}
          showTyping={showTyping || showTyping2}
          globalFrame={frame}
          style={{ flex: 1, height: 860 }}
        />

        {/* Right annotation panel */}
        <div
          style={{
            width: 320,
            opacity: annotationOpacity,
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          <div
            style={{
              backgroundColor: "rgba(118,185,0,0.1)",
              border: "1px solid rgba(118,185,0,0.4)",
              borderRadius: 10,
              padding: 20,
            }}
          >
            <div
              style={{
                color: COLORS.nvidiaGreen,
                fontWeight: 700,
                fontSize: 14,
                marginBottom: 10,
                letterSpacing: 1,
              }}
            >
              HOW IT WORKS
            </div>
            <div style={{ color: COLORS.textSecondary, fontSize: 13, lineHeight: 1.7 }}>
              1. Mention <span style={{ color: COLORS.nvidiaGreen }}>@jbot</span> in any Teams channel
              <br />
              2. Describe your task in natural language
              <br />
              3. Bot spawns a dedicated Claude Code session
              <br />
              4. Get results directly in the channel
            </div>
          </div>

          <div
            style={{
              backgroundColor: COLORS.teamsMessage,
              border: `1px solid ${COLORS.teamsBorder}`,
              borderRadius: 10,
              padding: 20,
            }}
          >
            <div
              style={{
                color: COLORS.textPrimary,
                fontWeight: 600,
                fontSize: 13,
                marginBottom: 8,
              }}
            >
              Supported Commands
            </div>
            {[
              { cmd: "@jbot <task>", desc: "Run any coding task" },
              { cmd: "@jbot report", desc: "View all sessions" },
              { cmd: "@jbot stop <id>", desc: "Stop a session" },
            ].map((item, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <div
                  style={{
                    fontFamily: "'Consolas', monospace",
                    fontSize: 12,
                    color: COLORS.nvidiaGreen,
                    marginBottom: 2,
                  }}
                >
                  {item.cmd}
                </div>
                <div style={{ fontSize: 12, color: COLORS.textMuted }}>
                  {item.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
