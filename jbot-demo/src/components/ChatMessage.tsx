import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../styles";

export interface MessageData {
  id: string;
  sender: string;
  avatar: string;
  avatarColor: string;
  text: string | React.ReactNode;
  isBot?: boolean;
  timestamp?: string;
  appearFrame: number;
}

interface ChatMessageProps {
  message: MessageData;
  globalFrame: number;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  globalFrame,
}) => {
  const framesSinceAppear = globalFrame - message.appearFrame;
  if (framesSinceAppear < 0) return null;

  const opacity = interpolate(framesSinceAppear, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(framesSinceAppear, [0, 10], [12, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        padding: "6px 16px",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          backgroundColor: message.avatarColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          color: message.isBot ? "#000" : "#fff",
          fontWeight: "bold",
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {message.avatar}
      </div>

      {/* Message content */}
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
              fontWeight: 600,
              fontSize: 14,
              color: message.isBot ? COLORS.nvidiaGreen : COLORS.textPrimary,
            }}
          >
            {message.sender}
          </span>
          {message.isBot && (
            <span
              style={{
                fontSize: 10,
                color: "#fff",
                backgroundColor: COLORS.nvidiaGreen,
                padding: "1px 6px",
                borderRadius: 3,
                fontFamily: "'Segoe UI', system-ui, sans-serif",
                fontWeight: 600,
              }}
            >
              BOT
            </span>
          )}
          <span
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 11,
              color: COLORS.textMuted,
            }}
          >
            {message.timestamp || "Today 10:24 AM"}
          </span>
        </div>
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 14,
            color: COLORS.textPrimary,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {message.text}
        </div>
      </div>
    </div>
  );
};
