import React from "react";
import {Composition} from "remotion";
import {HuihuaComposition} from "./Composition";
import type {HuihuaVideoProps} from "./types";

const defaultProps: HuihuaVideoProps = {
  audio: "runtime/narration.mp3",
  duration: 10,
  fps: 30,
  width: 960,
  height: 1280,
  backgroundColor: "#f6f0e6",
  scenes: [],
  images: [],
  motion: [],
  subtitles: [],
};

export const Root: React.FC = () => {
  return (
    <Composition
      id="HuihuaVideo"
      component={HuihuaComposition}
      durationInFrames={300}
      fps={30}
      width={960}
      height={1280}
      defaultProps={defaultProps}
      calculateMetadata={({props}) => {
        const width = props.width ?? 960;
        const height = props.height ?? 1280;
        const fps = props.fps ?? 30;
        return {
          width,
          height,
          fps,
          durationInFrames: Math.max(1, Math.ceil(props.duration * fps)),
        };
      }}
    />
  );
};
