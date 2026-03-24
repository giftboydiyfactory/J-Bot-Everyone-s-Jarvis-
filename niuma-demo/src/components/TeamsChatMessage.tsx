import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../styles";

interface TeamsChatMessageProps {
  avatar: string;
  displayName: string;
  timestamp: string;
  message: string;
  isBot?: boolean;
  avatarColor?: string;
  delay?: number;
  highlight?: boolean;
}

const Avatar: React.FC<{ initials: string; color: string; size?: number }> = ({
  initials,
  color,
  size = 40,
}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: "50%",
      backgroundColor: color,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: size * 0.4,
      fontWeight: 700,
      color: "#ffffff",
      flexShrink: 0,
      fontFamily: "'Segoe UI', system-ui, sans-serif",
    }}
  >
    {initials}
  </div>
);

export const TeamsChatMessage: React.FC<TeamsChatMessageProps> = ({
  avatar,
  displayName,
  timestamp,
  message,
  isBot = false,
  avatarColor = COLORS.avatarUser1,
  delay = 0,
  highlight = false,
}) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - delay);

  const opacity = interpolate(localFrame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(localFrame, [0, 15], [20, 0], {
    extrapolateRight: "clamp",
  });

  // Render message with @jbot highlighted
  const renderMessage = (text: string) => {
    const parts = text.split(/(@jbot)/g);
    return parts.map((part, i) => {
      if (part === "@jbot") {
        return (
          <span
            key={i}
            style={{
              color: COLORS.nvidiaGreen,
              backgroundColor: highlight ? COLORS.nvidiaGlow : "transparent",
              borderRadius: 4,
              padding: "0 2px",
              fontWeight: 600,
            }}
          >
            {part}
          </span>
        );
      }
      // Handle code blocks (text between backticks)
      const codeParts = part.split(/(`[^`]+`)/g);
      return codeParts.map((codePart, j) => {
        if (codePart.startsWith("`") && codePart.endsWith("`")) {
          return (
            <code
              key={`${i}-${j}`}
              style={{
                backgroundColor: "#1a1a1a",
                color: COLORS.nvidiaGreen,
                padding: "2px 6px",
                borderRadius: 4,
                fontFamily: "'Courier New', monospace",
                fontSize: "0.9em",
              }}
            >
              {codePart.slice(1, -1)}
            </code>
          );
        }
        return <span key={`${i}-${j}`}>{codePart}</span>;
      });
    });
  };

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: "12px 16px",
        opacity,
        transform: `translateY(${translateY}px)`,
        backgroundColor: isBot ? "rgba(118, 185, 0, 0.05)" : "transparent",
        borderLeft: isBot ? `3px solid ${COLORS.nvidiaGreen}` : "3px solid transparent",
        borderRadius: 4,
        marginBottom: 4,
      }}
    >
      <Avatar initials={avatar} color={avatarColor} size={36} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <span
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 15,
              fontWeight: 600,
              color: isBot ? COLORS.nvidiaGreen : COLORS.textPrimary,
            }}
          >
            {displayName}
          </span>
          {isBot && (
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: COLORS.teamsBg,
                backgroundColor: COLORS.nvidiaGreen,
                padding: "1px 6px",
                borderRadius: 10,
                fontFamily: "'Segoe UI', system-ui, sans-serif",
              }}
            >
              BOT
            </span>
          )}
          <span
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 12,
              color: COLORS.textMuted,
            }}
          >
            {timestamp}
          </span>
        </div>
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 15,
            color: COLORS.textSecondary,
            lineHeight: 1.5,
            wordBreak: "break-word",
          }}
        >
          {renderMessage(message)}
        </div>
      </div>
    </div>
  );
};
