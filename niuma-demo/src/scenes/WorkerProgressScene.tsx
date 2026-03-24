import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../styles";
import { TeamsChatUI } from "../components/TeamsChatUI";
import { MessageData } from "../components/ChatMessage";
import { TerminalWindow, TerminalLine } from "../components/TerminalWindow";

export const WorkerProgressScene: React.FC = () => {
  const frame = useCurrentFrame();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Terminal lines with timed appearance
  const terminalLines: TerminalLine[] = [
    {
      text: "$ claude --session 0324-a7f3",
      color: COLORS.terminalGreen,
      appearFrame: 15,
    },
    {
      text: "",
      color: COLORS.terminalText,
      appearFrame: 25,
    },
    {
      text: "● Session 0324-a7f3 | Working...",
      color: COLORS.terminalGreen,
      appearFrame: 30,
    },
    {
      text: "",
      color: COLORS.terminalText,
      appearFrame: 35,
    },
    {
      text: "  Reading src/auth/middleware.ts...",
      color: COLORS.terminalBlue,
      appearFrame: 50,
    },
    {
      text: "  ✓ File loaded (342 lines)",
      color: COLORS.terminalGreen,
      appearFrame: 75,
    },
    {
      text: "",
      color: COLORS.terminalText,
      appearFrame: 80,
    },
    {
      text: "  Analyzing authentication flow...",
      color: COLORS.terminalBlue,
      appearFrame: 90,
    },
    {
      text: "  → Checking JWT validation logic...",
      color: COLORS.terminalText,
      appearFrame: 115,
    },
    {
      text: "  → Scanning route middleware chain...",
      color: COLORS.terminalText,
      appearFrame: 140,
    },
    {
      text: "  → Reviewing session management...",
      color: COLORS.terminalText,
      appearFrame: 165,
    },
    {
      text: "",
      color: COLORS.terminalText,
      appearFrame: 185,
    },
    {
      text: "  Found 3 potential security issues",
      color: COLORS.terminalYellow,
      appearFrame: 195,
    },
    {
      text: "  Preparing detailed report...",
      color: COLORS.terminalBlue,
      appearFrame: 220,
    },
  ];

  // Teams chat messages during worker run
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
      text: "Got it! Starting task session [0324-a7f3] to analyze auth middleware...",
      isBot: true,
      timestamp: "Today 10:24 AM",
      appearFrame: 0,
    },
    {
      id: "3",
      sender: "J-Bot 🤖",
      avatar: "N",
      avatarColor: COLORS.avatarBot,
      isBot: true,
      timestamp: "Today 10:25 AM",
      appearFrame: 130,
      text: (
        <div
          style={{
            backgroundColor: "rgba(118,185,0,0.06)",
            border: "1px solid rgba(118,185,0,0.2)",
            borderRadius: 6,
            padding: "8px 12px",
            fontSize: 13,
            lineHeight: 1.6,
            fontFamily: "'Segoe UI', system-ui, sans-serif",
          }}
        >
          <span style={{ fontSize: 15 }}>⏱️</span>{" "}
          <span style={{ color: COLORS.textSecondary }}>[0324-a7f3]</span>{" "}
          <span style={{ color: COLORS.nvidiaGreen, fontWeight: 600 }}>60s</span>{" "}
          <span style={{ color: COLORS.textSecondary }}>—</span>{" "}
          <span style={{ color: COLORS.textPrimary }}>
            Reading auth/middleware.ts, analyzing security patterns...
          </span>
        </div>
      ),
    },
  ];

  // Progress bar
  const progressPct = interpolate(frame, [30, 280], [0, 75], {
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
        SCENE 2 — SESSION IN PROGRESS
      </div>

      {/* Split screen layout */}
      <div
        style={{
          display: "flex",
          gap: 32,
          width: 1760,
          height: 900,
          alignItems: "stretch",
        }}
      >
        {/* Left: Teams Chat */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: 1,
              textAlign: "center",
              padding: "8px 16px",
              backgroundColor: "rgba(255,255,255,0.04)",
              borderRadius: 6,
            }}
          >
            MICROSOFT TEAMS — Interconnect Engineering
          </div>
          <TeamsChatUI
            channelName="Interconnect Engineering"
            messages={chatMessages}
            showTyping={false}
            globalFrame={frame}
            style={{ flex: 1 }}
          />
        </div>

        {/* Divider */}
        <div
          style={{
            width: 2,
            backgroundColor: COLORS.teamsBorder,
            borderRadius: 1,
            alignSelf: "stretch",
          }}
        />

        {/* Right: Terminal */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: 1,
              textAlign: "center",
              padding: "8px 16px",
              backgroundColor: "rgba(255,255,255,0.04)",
              borderRadius: 6,
            }}
          >
            CLAUDE CODE TASK SESSION
          </div>

          <TerminalWindow
            lines={terminalLines}
            title="jbot-session — 0324-a7f3"
            globalFrame={frame}
            style={{ flex: 1 }}
          />

          {/* Progress section */}
          <div
            style={{
              backgroundColor: COLORS.teamsMessage,
              border: `1px solid ${COLORS.teamsBorder}`,
              borderRadius: 8,
              padding: "14px 18px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <span style={{ color: COLORS.textSecondary, fontSize: 13 }}>
                Session Progress
              </span>
              <span
                style={{
                  color: COLORS.nvidiaGreen,
                  fontSize: 13,
                  fontFamily: "'Consolas', monospace",
                }}
              >
                {Math.round(progressPct)}%
              </span>
            </div>
            <div
              style={{
                height: 6,
                backgroundColor: "#333",
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
                  boxShadow: `0 0 8px ${COLORS.nvidiaGreen}`,
                }}
              />
            </div>
            <div
              style={{
                marginTop: 8,
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <span style={{ color: COLORS.textMuted, fontSize: 11 }}>
                Session ID: 0324-a7f3
              </span>
              <span style={{ color: COLORS.textMuted, fontSize: 11 }}>
                Elapsed: ~{Math.round((frame / 30) + 10)}s
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
