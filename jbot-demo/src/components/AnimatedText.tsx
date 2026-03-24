import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface AnimatedTextProps {
  text: string;
  style?: React.CSSProperties;
  delay?: number;
  animation?: "fadeIn" | "slideUp" | "typewriter" | "spring";
}

export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  style = {},
  delay = 0,
  animation = "fadeIn",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - delay);

  if (animation === "fadeIn") {
    const opacity = interpolate(localFrame, [0, 20], [0, 1], {
      extrapolateRight: "clamp",
    });
    return <span style={{ ...style, opacity }}>{text}</span>;
  }

  if (animation === "slideUp") {
    const opacity = interpolate(localFrame, [0, 20], [0, 1], {
      extrapolateRight: "clamp",
    });
    const translateY = interpolate(localFrame, [0, 20], [30, 0], {
      extrapolateRight: "clamp",
    });
    return (
      <span style={{ ...style, opacity, transform: `translateY(${translateY}px)`, display: "block" }}>
        {text}
      </span>
    );
  }

  if (animation === "spring") {
    const progress = spring({
      frame: localFrame,
      fps,
      config: { damping: 12, stiffness: 100 },
    });
    const scale = interpolate(progress, [0, 1], [0.5, 1]);
    const opacity = interpolate(progress, [0, 1], [0, 1]);
    return (
      <span style={{ ...style, opacity, transform: `scale(${scale})`, display: "inline-block" }}>
        {text}
      </span>
    );
  }

  if (animation === "typewriter") {
    const charsToShow = Math.floor(
      interpolate(localFrame, [0, text.length * 2], [0, text.length], {
        extrapolateRight: "clamp",
      })
    );
    return (
      <span style={style}>
        {text.slice(0, charsToShow)}
        {charsToShow < text.length && (
          <span style={{ opacity: Math.floor(localFrame / 10) % 2 === 0 ? 1 : 0 }}>|</span>
        )}
      </span>
    );
  }

  return <span style={style}>{text}</span>;
};
