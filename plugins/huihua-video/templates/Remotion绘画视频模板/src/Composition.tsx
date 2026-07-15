import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type {HuihuaVideoProps, ImageAsset, MotionScene, Scene} from "./types";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const progress = (frame: number, fps: number, start = 0, end = 1) =>
  interpolate(frame / fps, [start, Math.max(start + 0.001, end)], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.22, 0.72, 0.22, 1),
  });

const revealMask = (value: number, direction = "left"): React.CSSProperties => {
  const percent = Math.max(0, Math.min(100, value * 100));
  const axis =
    direction === "top" ? "180deg" : direction === "bottom" ? "0deg" : direction === "right" ? "270deg" : "90deg";
  const mask = `linear-gradient(${axis}, #000 0%, #000 ${Math.max(0, percent - 8)}%, rgba(0,0,0,.65) ${percent}%, transparent ${Math.min(100, percent + 6)}%)`;
  return {WebkitMaskImage: mask, maskImage: mask};
};

const assetStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  width: "100%",
  height: "100%",
  objectFit: "contain",
};

const SceneView: React.FC<{
  scene: Scene;
  assets: ImageAsset[];
  motion?: MotionScene;
}> = ({scene, assets, motion}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const color = assets.find((asset) => asset.role === "color");
  const line = assets.find((asset) => asset.role === "line");
  if (!color) {
    return <AbsoluteFill style={{backgroundColor: "#f6f0e6"}} />;
  }

  const lineStart = motion?.line_reveal.start ?? 0;
  const lineEnd = motion?.line_reveal.end ?? Math.min(2.2, scene.end - scene.start);
  const colorStart = motion?.color_reveal.start ?? Math.max(0.7, lineEnd - 0.4);
  const colorEnd = motion?.color_reveal.end ?? Math.min(5.4, scene.end - scene.start);
  const lineProgress = progress(frame, fps, lineStart, lineEnd);
  const colorProgress = progress(frame, fps, colorStart, colorEnd);
  const cameraProgress = progress(frame, fps, 0, Math.max(0.1, scene.end - scene.start));
  const cameraAmount = motion?.camera.amount ?? 0.025;
  const cameraType = motion?.camera.type ?? "push";
  const scale = cameraType === "push" ? 1 + cameraProgress * cameraAmount : 1;
  const translateX = cameraType === "pan-x" ? (cameraProgress - 0.5) * cameraAmount * 100 : 0;
  const translateY = cameraType === "pan-y" ? (cameraProgress - 0.5) * cameraAmount * 100 : 0;

  return (
    <AbsoluteFill style={{overflow: "hidden", backgroundColor: "#f6f0e6"}}>
      <AbsoluteFill
        style={{
          transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
          transformOrigin: "center",
        }}
      >
        {line ? (
          <Img
            src={staticFile(line.file)}
            style={{
              ...assetStyle,
              opacity: interpolate(colorProgress, [0.75, 1], [1, 0.18], clamp),
              ...revealMask(lineProgress, motion?.line_reveal.direction),
            }}
          />
        ) : null}
        <Img
          src={staticFile(color.file)}
          style={{
            ...assetStyle,
            ...revealMask(colorProgress, motion?.color_reveal.direction),
          }}
        />
        {assets
          .filter((asset) => !["color", "line"].includes(asset.role))
          .map((asset, index) => {
            const beat = motion?.object_beats.find((item) => item.asset_id === asset.id);
            const appear = progress(frame, fps, beat?.at ?? 0.5 + index * 0.3, (beat?.at ?? 0.5 + index * 0.3) + 0.55);
            const parallax = motion?.parallax.enabled ? (index + 1) * (motion.parallax.amount ?? 4) : 0;
            return (
              <Img
                key={asset.id}
                src={staticFile(asset.file)}
                style={{
                  ...assetStyle,
                  opacity: appear,
                  transform: `translateY(${(1 - appear) * 18 + parallax * (cameraProgress - 0.5)}px)`,
                }}
              />
            );
          })}
      </AbsoluteFill>
      {(motion?.text_beats ?? []).map((beat, index) => {
        const appear = progress(frame, fps, beat.at, beat.at + 0.5);
        return (
          <div
            key={`${beat.text}-${index}`}
            style={{
              position: "absolute",
              left: `${beat.x ?? 10}%`,
              top: `${beat.y ?? 10 + index * 8}%`,
              maxWidth: "72%",
              color: "#201e1b",
              fontFamily: "system-ui, sans-serif",
              fontWeight: 700,
              fontSize: "clamp(26px, 4.2vw, 66px)",
              lineHeight: 1.18,
              opacity: appear,
              transform: `translateY(${(1 - appear) * 16}px)`,
            }}
          >
            {beat.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const SubtitleLayer: React.FC<{items: HuihuaVideoProps["subtitles"]}> = ({items}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const current = items.find((item) => frame >= Math.floor(item.start * fps) && frame < Math.ceil(item.end * fps));
  if (!current) return null;
  const local = frame - current.start * fps;
  const opacity = interpolate(local, [0, Math.min(6, (current.end - current.start) * fps * 0.2)], [0, 1], clamp);
  return (
    <div
      style={{
        position: "absolute",
        left: "7%",
        right: "7%",
        bottom: "5.5%",
        textAlign: "center",
        color: "#fff",
        fontFamily: "system-ui, sans-serif",
        fontWeight: 700,
        fontSize: "clamp(26px, 3.4vw, 54px)",
        lineHeight: 1.35,
        textShadow: "0 2px 3px rgba(0,0,0,.92), 0 0 8px rgba(0,0,0,.55)",
        opacity,
      }}
    >
      {current.text}
    </div>
  );
};

export const HuihuaComposition: React.FC<HuihuaVideoProps> = (props) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: props.backgroundColor ?? "#f6f0e6"}}>
      <Audio src={staticFile(props.audio)} />
      {props.scenes.map((scene) => {
        const from = Math.floor(scene.start * fps);
        const durationInFrames = Math.max(1, Math.ceil((scene.end - scene.start) * fps));
        return (
          <Sequence key={scene.id} from={from} durationInFrames={durationInFrames} premountFor={Math.min(fps, from)}>
            <SceneView
              scene={scene}
              assets={props.images.filter((asset) => asset.scene_id === scene.id)}
              motion={props.motion.find((item) => item.scene_id === scene.id)}
            />
          </Sequence>
        );
      })}
      <SubtitleLayer items={props.subtitles} />
    </AbsoluteFill>
  );
};
