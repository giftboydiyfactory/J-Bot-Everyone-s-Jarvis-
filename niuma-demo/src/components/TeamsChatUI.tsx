import React from "react";
import { COLORS } from "../styles";
import { ChatMessage, MessageData } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";

interface TeamsChatUIProps {
  channelName: string;
  messages: MessageData[];
  showTyping?: boolean;
  globalFrame: number;
  style?: React.CSSProperties;
}

const MEMBER_AVATARS = ["JW", "AC", "SL", "MK"];

export const TeamsChatUI: React.FC<TeamsChatUIProps> = ({
  channelName,
  messages,
  showTyping = false,
  globalFrame,
  style,
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        backgroundColor: COLORS.teamsBg,
        borderRadius: 8,
        overflow: "hidden",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        ...style,
      }}
    >
      {/* Channel header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "12px 16px",
          backgroundColor: COLORS.teamsPanel,
          borderBottom: `1px solid ${COLORS.teamsBorder}`,
          flexShrink: 0,
        }}
      >
        {/* Channel icon */}
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            backgroundColor: "#5b67d8",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginRight: 10,
            fontSize: 16,
          }}
        >
          #
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: COLORS.textPrimary,
            }}
          >
            {channelName}
          </div>
          <div
            style={{
              fontSize: 11,
              color: COLORS.textSecondary,
            }}
          >
            4 members
          </div>
        </div>
        {/* Member avatars */}
        <div style={{ display: "flex", gap: -6 }}>
          {MEMBER_AVATARS.map((name, i) => (
            <div
              key={i}
              style={{
                width: 26,
                height: 26,
                borderRadius: "50%",
                backgroundColor: [
                  COLORS.avatarUser1,
                  COLORS.avatarUser2,
                  COLORS.avatarUser3,
                  COLORS.avatarUser4,
                ][i],
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 10,
                color: "#fff",
                fontWeight: "bold",
                marginLeft: -4,
                border: `2px solid ${COLORS.teamsPanel}`,
              }}
            >
              {name}
            </div>
          ))}
        </div>
        {/* Teams-style icons */}
        <div
          style={{
            marginLeft: 12,
            display: "flex",
            gap: 12,
            color: COLORS.textSecondary,
            fontSize: 16,
          }}
        >
          <span>🔍</span>
          <span>📹</span>
          <span>☎️</span>
        </div>
      </div>

      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: "hidden",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          padding: "8px 0",
        }}
      >
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} globalFrame={globalFrame} />
        ))}
        {showTyping && (
          <TypingIndicator visible={showTyping} name="J-Bot 🤖" />
        )}
      </div>

      {/* Message input box */}
      <div
        style={{
          padding: "10px 16px",
          borderTop: `1px solid ${COLORS.teamsBorder}`,
          backgroundColor: COLORS.teamsPanel,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            backgroundColor: COLORS.teamsBg,
            border: `1px solid ${COLORS.teamsBorder}`,
            borderRadius: 6,
            padding: "10px 14px",
            color: COLORS.textMuted,
            fontSize: 14,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span style={{ flex: 1 }}>Type a message...</span>
          <span style={{ fontSize: 16 }}>😊</span>
          <span style={{ fontSize: 16 }}>📎</span>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              backgroundColor: COLORS.nvidiaGreen,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              color: "#000",
            }}
          >
            ➤
          </div>
        </div>
      </div>
    </div>
  );
};
