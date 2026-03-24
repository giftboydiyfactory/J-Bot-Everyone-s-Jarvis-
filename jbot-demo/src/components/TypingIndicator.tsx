import React from "react";
import { useCurrentFrame } from "remotion";
import { COLORS } from "../styles";

interface TypingIndicatorProps {
  visible: boolean;
  name?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  visible,
  name = "J-Bot",
}) => {
  const frame = useCurrentFrame();
  if (!visible) return null;

  const dot1 = Math.sin(frame * 0.3) * 0.5 + 0.5;
  const dot2 = Math.sin(frame * 0.3 - 1.0) * 0.5 + 0.5;
  const dot3 = Math.sin(frame * 0.3 - 2.0) * 0.5 + 0.5;

  const dotStyle = (opacity: number): React.CSSProperties => ({
    width: 8,
    height: 8,
    borderRadius: "50%",
    backgroundColor: COLORS.textSecondary,
    opacity: 0.3 + opacity * 0.7,
    display: "inline-block",
    margin: "0 3px",
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 16px",
        margin: "4px 0",
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          backgroundColor: COLORS.avatarBot,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          color: "#000",
          fontWeight: "bold",
          flexShrink: 0,
        }}
      >
        N
      </div>
      <div
        style={{
          backgroundColor: COLORS.teamsMessage,
          borderRadius: 8,
          padding: "10px 14px",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        <span style={dotStyle(dot1)} />
        <span style={dotStyle(dot2)} />
        <span style={dotStyle(dot3)} />
      </div>
      <span
        style={{
          color: COLORS.textMuted,
          fontSize: 12,
          fontFamily: "'Segoe UI', system-ui, sans-serif",
        }}
      >
        {name} is typing...
      </span>
    </div>
  );
};
