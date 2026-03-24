import React from "react";
import { interpolate } from "remotion";
import { COLORS } from "../styles";

export interface TerminalLine {
  text: string;
  color?: string;
  appearFrame: number;
}

interface TerminalWindowProps {
  lines: TerminalLine[];
  title?: string;
  globalFrame: number;
  style?: React.CSSProperties;
}

export const TerminalWindow: React.FC<TerminalWindowProps> = ({
  lines,
  title = "bash — jbot-session",
  globalFrame,
  style,
}) => {
  const visibleLines = lines.filter((l) => globalFrame >= l.appearFrame);

  return (
    <div
      style={{
        backgroundColor: COLORS.terminalBg,
        borderRadius: 8,
        overflow: "hidden",
        fontFamily: "'Consolas', 'Courier New', monospace",
        ...style,
      }}
    >
      {/* Title bar */}
      <div
        style={{
          backgroundColor: "#21262d",
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          borderBottom: "1px solid #30363d",
        }}
      >
        <div style={{ display: "flex", gap: 6 }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              backgroundColor: "#ff5f57",
            }}
          />
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              backgroundColor: "#febc2e",
            }}
          />
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              backgroundColor: "#28c840",
            }}
          />
        </div>
        <span
          style={{
            flex: 1,
            textAlign: "center",
            color: "#8b949e",
            fontSize: 12,
          }}
        >
          {title}
        </span>
      </div>

      {/* Terminal content */}
      <div
        style={{
          padding: "16px 20px",
          minHeight: 200,
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {visibleLines.map((line, i) => {
          const framesSince = globalFrame - line.appearFrame;
          const opacity = interpolate(framesSince, [0, 6], [0, 1], {
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                opacity,
                fontSize: 14,
                lineHeight: 1.6,
                color: line.color || COLORS.terminalText,
                whiteSpace: "pre",
              }}
            >
              {line.text}
            </div>
          );
        })}
        {/* Blinking cursor */}
        {visibleLines.length > 0 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              marginTop: 2,
            }}
          >
            <span style={{ color: COLORS.terminalGreen, fontSize: 14 }}>
              $
            </span>
            <span
              style={{
                display: "inline-block",
                width: 8,
                height: 16,
                backgroundColor: COLORS.terminalText,
                opacity: Math.sin(globalFrame * 0.15) > 0 ? 1 : 0,
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};
