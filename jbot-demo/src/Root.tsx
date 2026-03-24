import React from "react";
import { Composition, Series } from "remotion";
import { TitleScene } from "./scenes/TitleScene";
import { ProblemScene } from "./scenes/ProblemScene";
import { SolutionScene } from "./scenes/SolutionScene";
import { LiveDemoScene } from "./scenes/LiveDemoScene";
import { ArchitectureScene } from "./scenes/ArchitectureScene";
import { FeaturesScene } from "./scenes/FeaturesScene";
import { MultiUserScene } from "./scenes/MultiUserScene";
import { EasterEggScene } from "./scenes/EasterEggScene";
import { OutroScene } from "./scenes/OutroScene";
import { SCENE_DURATIONS, TOTAL_FRAMES, FPS } from "./styles";

const NiumaBotDemo: React.FC = () => {
  return (
    <Series>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.title}>
        <TitleScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.problem}>
        <ProblemScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.solution}>
        <SolutionScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.liveDemo}>
        <LiveDemoScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.architecture}>
        <ArchitectureScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.features}>
        <FeaturesScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.multiUser}>
        <MultiUserScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.easterEgg}>
        <EasterEggScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_DURATIONS.outro}>
        <OutroScene />
      </Series.Sequence>
    </Series>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="JBotDemo"
        component={NiumaBotDemo}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
