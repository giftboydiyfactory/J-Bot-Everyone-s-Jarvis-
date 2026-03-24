import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";

const TerminalMockup: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      opacity,
      width: "100%",
      height: "100%",
      backgroundColor: "#0d1117",
      borderRadius: 10,
      border: "1px solid #30363d",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}
  >
    {/* Terminal titlebar */}
    <div
      style={{
        height: 36,
        backgroundColor: "#161b22",
        display: "flex",
        alignItems: "center",
        padding: "0 12px",
        gap: 8,
        borderBottom: "1px solid #30363d",
      }}
    >
      {["#ff5f57", "#ffbd2e", "#28c840"].map((c, i) => (
        <div key={i} style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: c }} />
      ))}
      <span
        style={{
          marginLeft: 8,
          fontFamily: "monospace",
          fontSize: 13,
          color: "#8b949e",
        }}
      >
        bash — claude session
      </span>
    </div>
    {/* Terminal body */}
    <div style={{ padding: 16, flex: 1 }}>
      {[
        { prompt: "$ ", text: "claude --session auth-review", color: "#e6edf3" },
        { prompt: "", text: "Starting claude session...", color: "#3fb950" },
        { prompt: "", text: "Analyzing auth module...", color: "#8b949e" },
        { prompt: "", text: "Found 3 issues:", color: "#e6edf3" },
        { prompt: "  ", text: "⚠ JWT expiry not validated", color: "#d29922" },
        { prompt: "  ", text: "⚠ Missing rate limiting on /login", color: "#d29922" },
        { prompt: "  ", text: "✗ Secrets in env vars (plain text)", color: "#f85149" },
        { prompt: "", text: "Now what? Copy this to Teams manually...", color: "#6e7681" },
      ].map((line, i) => (
        <div
          key={i}
          style={{
            fontFamily: "'Courier New', monospace",
            fontSize: 14,
            color: line.color,
            marginBottom: 4,
            lineHeight: 1.6,
          }}
        >
          <span style={{ color: "#3fb950" }}>{line.prompt}</span>
          {line.text}
        </div>
      ))}
    </div>
  </div>
);

const TeamsMockup: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      opacity,
      width: "100%",
      height: "100%",
      backgroundColor: "#292929",
      borderRadius: 10,
      border: "1px solid #3a3a3a",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}
  >
    {/* Header */}
    <div
      style={{
        height: 52,
        backgroundColor: "#1f1f1f",
        borderBottom: "1px solid #3a3a3a",
        display: "flex",
        alignItems: "center",
        padding: "0 16px",
        gap: 8,
      }}
    >
      <span style={{ color: "#ffffff", fontWeight: 700, fontFamily: "'Segoe UI', sans-serif", fontSize: 15 }}>
        # dev-discussion
      </span>
      <span style={{ color: "#6e6e6e", fontFamily: "'Segoe UI', sans-serif", fontSize: 13 }}>· 8 members</span>
    </div>
    {/* Messages */}
    <div style={{ padding: 12, flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
      {[
        { name: "Alice Chen", time: "9:15 AM", msg: "Hey, has anyone reviewed the auth module?" },
        { name: "Bob Liu", time: "9:17 AM", msg: "Not yet. @Jackey can you check it?" },
        { name: "Jackey Wang", time: "9:18 AM", msg: "Sure, running claude now... will paste results" },
        { name: "Carol Zhang", time: "9:30 AM", msg: "Still waiting for the auth review results?" },
        { name: "Jackey Wang", time: "9:45 AM", msg: "(copy-pastes terminal output) Here are the results..." },
      ].map((msg, i) => (
        <div key={i} style={{ display: "flex", gap: 8 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              backgroundColor: ["#2196f3", "#9c27b0", "#4a4fc7", "#ff5722", "#4a4fc7"][i],
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              color: "#fff",
              flexShrink: 0,
              fontFamily: "'Segoe UI', sans-serif",
            }}
          >
            {msg.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div>
            <div style={{ display: "flex", gap: 6, marginBottom: 2 }}>
              <span style={{ color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "'Segoe UI', sans-serif" }}>{msg.name}</span>
              <span style={{ color: "#6e6e6e", fontSize: 12, fontFamily: "'Segoe UI', sans-serif" }}>{msg.time}</span>
            </div>
            <div style={{ color: "#b3b3b3", fontSize: 13, fontFamily: "'Segoe UI', sans-serif" }}>{msg.msg}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const leftOpacity = interpolate(frame, [20, 50], [0, 1], { extrapolateRight: "clamp" });
  const rightOpacity = interpolate(frame, [40, 70], [0, 1], { extrapolateRight: "clamp" });
  const arrowOpacity = interpolate(frame, [70, 90], [0, 1], { extrapolateRight: "clamp" });
  const textOpacity = interpolate(frame, [90, 120], [0, 1], { extrapolateRight: "clamp" });

  // Pulsing arrow animation
  const arrowPulse = 0.7 + 0.3 * Math.sin(frame * 0.15);

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
          marginBottom: 40,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div style={{ width: 6, height: 48, backgroundColor: COLORS.nvidiaGreen, borderRadius: 3 }} />
        <div style={{ fontSize: 48, fontWeight: 800, color: COLORS.textPrimary }}>The Problem</div>
      </div>

      {/* Split view */}
      <div style={{ flex: 1, display: "flex", gap: 40, alignItems: "center" }}>
        {/* Terminal */}
        <div style={{ flex: 1, height: 540 }}>
          <div style={{ marginBottom: 12, fontSize: 18, fontWeight: 600, color: COLORS.textSecondary, opacity: leftOpacity }}>
            Terminal (Claude Session)
          </div>
          <div style={{ height: 500 }}>
            <TerminalMockup opacity={leftOpacity} />
          </div>
        </div>

        {/* Arrow */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12,
            opacity: arrowOpacity,
            flexShrink: 0,
          }}
        >
          <div style={{ fontSize: 40, opacity: arrowPulse }}>⟷</div>
          <div
            style={{
              fontSize: 13,
              color: COLORS.statusWarning,
              textAlign: "center",
              fontWeight: 600,
              maxWidth: 100,
            }}
          >
            Manual context switch
          </div>
        </div>

        {/* Teams */}
        <div style={{ flex: 1, height: 540 }}>
          <div style={{ marginBottom: 12, fontSize: 18, fontWeight: 600, color: COLORS.textSecondary, opacity: rightOpacity }}>
            Microsoft Teams (Team Chat)
          </div>
          <div style={{ height: 500 }}>
            <TeamsMockup opacity={rightOpacity} />
          </div>
        </div>
      </div>

      {/* Pain points */}
      <div
        style={{
          opacity: textOpacity,
          display: "flex",
          gap: 40,
          marginTop: 24,
        }}
      >
        {[
          { icon: "😓", text: "Engineers constantly switch between terminal and chat" },
          { icon: "📋", text: "Results need manual copy-paste to share" },
          { icon: "⏱️", text: "Team waits while you manually relay AI output" },
        ].map((item, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              gap: 12,
              backgroundColor: "rgba(255,255,255,0.04)",
              padding: "14px 20px",
              borderRadius: 8,
              border: `1px solid ${COLORS.teamsBorder}`,
            }}
          >
            <span style={{ fontSize: 24 }}>{item.icon}</span>
            <span style={{ fontSize: 16, color: COLORS.textSecondary }}>{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
