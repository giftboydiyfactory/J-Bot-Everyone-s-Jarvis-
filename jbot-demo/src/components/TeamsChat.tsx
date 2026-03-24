import React from "react";
import { COLORS } from "../styles";

interface TeamsChatProps {
  channelName: string;
  memberCount?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

const SidebarItem: React.FC<{ icon: string; label: string; active?: boolean }> = ({
  icon,
  label,
  active = false,
}) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "8px 12px",
      borderRadius: 4,
      backgroundColor: active ? "rgba(118, 185, 0, 0.15)" : "transparent",
      cursor: "pointer",
    }}
  >
    <span style={{ fontSize: 16 }}>{icon}</span>
    <span
      style={{
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        fontSize: 13,
        color: active ? COLORS.nvidiaGreen : COLORS.textSecondary,
        fontWeight: active ? 600 : 400,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {label}
    </span>
  </div>
);

export const TeamsChat: React.FC<TeamsChatProps> = ({
  channelName,
  memberCount = 12,
  children,
  style = {},
}) => {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        backgroundColor: COLORS.teamsPanel,
        borderRadius: 12,
        overflow: "hidden",
        border: `1px solid ${COLORS.teamsBorder}`,
        boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        ...style,
      }}
    >
      {/* Left nav bar */}
      <div
        style={{
          width: 56,
          backgroundColor: "#1a1a1a",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          paddingTop: 12,
          gap: 8,
          borderRight: `1px solid ${COLORS.teamsBorder}`,
        }}
      >
        {/* Teams logo area */}
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            backgroundColor: COLORS.nvidiaGreen,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            marginBottom: 8,
          }}
        >
          🤖
        </div>
        {["💬", "👥", "📁", "📅", "⋯"].map((icon, i) => (
          <div
            key={i}
            style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 20,
              backgroundColor: i === 0 ? "rgba(118,185,0,0.2)" : "transparent",
              cursor: "pointer",
            }}
          >
            {icon}
          </div>
        ))}
      </div>

      {/* Channel sidebar */}
      <div
        style={{
          width: 220,
          backgroundColor: COLORS.teamsPanel,
          display: "flex",
          flexDirection: "column",
          borderRight: `1px solid ${COLORS.teamsBorder}`,
          overflowY: "hidden",
        }}
      >
        {/* Team header */}
        <div
          style={{
            padding: "16px 12px 8px",
            borderBottom: `1px solid ${COLORS.teamsBorder}`,
          }}
        >
          <div
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 14,
              fontWeight: 700,
              color: COLORS.textPrimary,
              marginBottom: 4,
            }}
          >
            NVIDIA AI Team
          </div>
          <div
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 12,
              color: COLORS.textMuted,
            }}
          >
            {memberCount} members
          </div>
        </div>

        {/* Channel list */}
        <div style={{ padding: "8px 4px", overflowY: "auto" }}>
          <div
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 11,
              fontWeight: 600,
              color: COLORS.textMuted,
              padding: "4px 12px",
              textTransform: "uppercase",
              letterSpacing: 1,
            }}
          >
            Channels
          </div>
          <SidebarItem icon="#" label="general" />
          <SidebarItem icon="#" label="ai-tools" active />
          <SidebarItem icon="#" label="interconnect-sh-ai" />
          <SidebarItem icon="#" label="dev-ops" />
          <SidebarItem icon="#" label="announcements" />
        </div>
      </div>

      {/* Main chat area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          backgroundColor: COLORS.teamsBg,
          overflow: "hidden",
        }}
      >
        {/* Chat header */}
        <div
          style={{
            height: 52,
            borderBottom: `1px solid ${COLORS.teamsBorder}`,
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 8,
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 15,
              fontWeight: 700,
              color: COLORS.textPrimary,
            }}
          >
            # {channelName}
          </span>
          <span
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 13,
              color: COLORS.textMuted,
            }}
          >
            · {memberCount} members
          </span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 18, cursor: "pointer" }}>🔍</span>
          <span style={{ fontSize: 18, cursor: "pointer" }}>⋯</span>
        </div>

        {/* Messages area */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px 8px",
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          {children}
        </div>

        {/* Message input */}
        <div
          style={{
            height: 50,
            borderTop: `1px solid ${COLORS.teamsBorder}`,
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 8,
            flexShrink: 0,
          }}
        >
          <div
            style={{
              flex: 1,
              height: 34,
              backgroundColor: COLORS.teamsPanel,
              borderRadius: 6,
              border: `1px solid ${COLORS.teamsBorder}`,
              display: "flex",
              alignItems: "center",
              padding: "0 12px",
            }}
          >
            <span
              style={{
                fontFamily: "'Segoe UI', system-ui, sans-serif",
                fontSize: 13,
                color: COLORS.textMuted,
              }}
            >
              Message ai-tools
            </span>
          </div>
          <span style={{ fontSize: 18, color: COLORS.textMuted }}>😊</span>
          <span style={{ fontSize: 18, color: COLORS.textMuted }}>📎</span>
        </div>
      </div>
    </div>
  );
};
