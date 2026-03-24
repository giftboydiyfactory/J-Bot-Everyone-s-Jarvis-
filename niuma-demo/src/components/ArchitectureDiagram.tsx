import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { COLORS } from "../styles";

interface BoxProps {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  sublabel?: string;
  icon: string;
  color?: string;
  delay?: number;
}

const DiagramBox: React.FC<BoxProps> = ({
  x,
  y,
  width,
  height,
  label,
  sublabel,
  icon,
  color = COLORS.nvidiaGreen,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - delay);

  const progress = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const opacity = interpolate(progress, [0, 1], [0, 1]);
  const scale = interpolate(progress, [0, 1], [0.7, 1]);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width,
        height,
        opacity,
        transform: `scale(${scale})`,
        transformOrigin: "center center",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: "rgba(26, 26, 46, 0.95)",
          border: `2px solid ${color}`,
          borderRadius: 12,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          boxShadow: `0 0 20px ${color}40`,
        }}
      >
        <div style={{ fontSize: 32 }}>{icon}</div>
        <div
          style={{
            fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontSize: 16,
            fontWeight: 700,
            color: color,
            textAlign: "center",
          }}
        >
          {label}
        </div>
        {sublabel && (
          <div
            style={{
              fontFamily: "'Segoe UI', system-ui, sans-serif",
              fontSize: 12,
              color: COLORS.textMuted,
              textAlign: "center",
              padding: "0 8px",
            }}
          >
            {sublabel}
          </div>
        )}
      </div>
    </div>
  );
};

interface ArrowProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  delay?: number;
  animated?: boolean;
}

const Arrow: React.FC<ArrowProps> = ({ x1, y1, x2, y2, delay = 0, animated = true }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - delay);

  const progress = interpolate(localFrame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.sqrt(dx * dx + dy * dy);

  // Particle animation
  const particlePos = animated ? (localFrame % 40) / 40 : 0;
  const px = x1 + dx * particlePos;
  const py = y1 + dy * particlePos;

  const clipProgress = progress * length;

  return (
    <svg
      style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", overflow: "visible" }}
    >
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={COLORS.nvidiaGreen} />
        </marker>
        <clipPath id={`clip-${x1}-${y1}`}>
          <rect x={Math.min(x1, x2) - 10} y={Math.min(y1, y2) - 10} width={Math.abs(dx) + 20} height={Math.abs(dy) + 20} />
        </clipPath>
      </defs>
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={COLORS.teamsBorder}
        strokeWidth={2}
        opacity={0.3}
      />
      <line
        x1={x1}
        y1={y1}
        x2={x1 + dx * progress}
        y2={y1 + dy * progress}
        stroke={COLORS.nvidiaGreen}
        strokeWidth={2.5}
        markerEnd={progress > 0.9 ? "url(#arrowhead)" : undefined}
      />
      {animated && progress > 0.9 && (
        <circle
          cx={px}
          cy={py}
          r={5}
          fill={COLORS.nvidiaGreenLight}
          opacity={0.8}
        />
      )}
    </svg>
  );
};

export const ArchitectureDiagram: React.FC = () => {
  const frame = useCurrentFrame();

  // Layout: 1680 wide, 500 tall diagram area
  const diagramWidth = 1680;
  const diagramHeight = 500;

  // Box positions
  const teamsBox = { x: 30, y: 190, w: 180, h: 120 };
  const pollerBox = { x: 270, y: 190, w: 180, h: 120 };
  const managerBox = { x: 560, y: 160, w: 220, h: 180 };
  const worker1Box = { x: 880, y: 60, w: 180, h: 110 };
  const worker2Box = { x: 880, y: 200, w: 180, h: 110 };
  const worker3Box = { x: 880, y: 340, w: 180, h: 110 };

  // Arrow endpoints (center of right edge -> center of left edge)
  const a1 = { x1: teamsBox.x + teamsBox.w, y1: teamsBox.y + teamsBox.h / 2, x2: pollerBox.x, y2: pollerBox.y + pollerBox.h / 2 };
  const a2 = { x1: pollerBox.x + pollerBox.w, y1: pollerBox.y + pollerBox.h / 2, x2: managerBox.x, y2: managerBox.y + managerBox.h / 2 };
  const a3 = { x1: managerBox.x + managerBox.w, y1: managerBox.y + managerBox.h / 2, x2: worker1Box.x, y2: worker1Box.y + worker1Box.h / 2 };
  const a4 = { x1: managerBox.x + managerBox.w, y1: managerBox.y + managerBox.h / 2, x2: worker2Box.x, y2: worker2Box.y + worker2Box.h / 2 };
  const a5 = { x1: managerBox.x + managerBox.w, y1: managerBox.y + managerBox.h / 2, x2: worker3Box.x, y2: worker3Box.y + worker3Box.h / 2 };

  const statsOpacity = interpolate(frame, [150, 180], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div style={{ position: "relative", width: diagramWidth, height: diagramHeight }}>
      {/* Arrows (rendered behind boxes via SVG) */}
      <Arrow {...a1} delay={20} />
      <Arrow {...a2} delay={50} />
      <Arrow {...a3} delay={90} />
      <Arrow {...a4} delay={90} />
      <Arrow {...a5} delay={90} />

      {/* Boxes */}
      <DiagramBox
        x={teamsBox.x} y={teamsBox.y} width={teamsBox.w} height={teamsBox.h}
        label="Teams Chat" icon="💬" color={COLORS.statusInfo} delay={0}
      />
      <DiagramBox
        x={pollerBox.x} y={pollerBox.y} width={pollerBox.w} height={pollerBox.h}
        label="Poller" sublabel="Polls every 30s" icon="🔄" color={COLORS.statusWarning} delay={20}
      />
      <DiagramBox
        x={managerBox.x} y={managerBox.y} width={managerBox.w} height={managerBox.h}
        label="Coordinator" sublabel="Stateful — Remembers Everything" icon="🧠" color={COLORS.nvidiaGreen} delay={50}
      />
      <DiagramBox
        x={worker1Box.x} y={worker1Box.y} width={worker1Box.w} height={worker1Box.h}
        label="Session 1" sublabel="Claude session" icon="⚙️" color={COLORS.textSecondary} delay={90}
      />
      <DiagramBox
        x={worker2Box.x} y={worker2Box.y} width={worker2Box.w} height={worker2Box.h}
        label="Session 2" sublabel="Claude session" icon="⚙️" color={COLORS.textSecondary} delay={110}
      />
      <DiagramBox
        x={worker3Box.x} y={worker3Box.y} width={worker3Box.w} height={worker3Box.h}
        label="Session 3" sublabel="Claude session" icon="⚙️" color={COLORS.textSecondary} delay={130}
      />

      {/* Stats label */}
      <div
        style={{
          position: "absolute",
          bottom: 10,
          left: "50%",
          transform: "translateX(-50%)",
          opacity: statsOpacity,
          display: "flex",
          gap: 40,
        }}
      >
        {[
          { label: "1 Coordinator", sub: "Persistent state" },
          { label: "Up to 5 Sessions", sub: "Parallel execution" },
          { label: "60s Heartbeat", sub: "Live progress" },
        ].map((stat, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div
              style={{
                fontFamily: "'Segoe UI', system-ui, sans-serif",
                fontSize: 18,
                fontWeight: 700,
                color: COLORS.nvidiaGreen,
              }}
            >
              {stat.label}
            </div>
            <div
              style={{
                fontFamily: "'Segoe UI', system-ui, sans-serif",
                fontSize: 13,
                color: COLORS.textMuted,
              }}
            >
              {stat.sub}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
