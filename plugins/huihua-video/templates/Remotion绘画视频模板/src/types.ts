export type SubtitleItem = {
  id: string;
  sentence_id: string;
  start: number;
  end: number;
  text: string;
};

export type ImageAsset = {
  id: string;
  scene_id: string;
  file: string;
  role: "color" | "line" | "foreground" | "midground" | "background" | "detail";
  width: number;
  height: number;
  fit: "contain";
  crop_allowed: false;
  prompt: string;
};

export type Scene = {
  id: string;
  start: number;
  end: number;
  sentence_ids: string[];
  visual_function: string;
  composition: string;
  safe_zones: unknown[];
  beats: Array<{at: number; type: string; label?: string}>;
};

export type MotionScene = {
  scene_id: string;
  line_reveal: {start?: number; end?: number; direction?: "left" | "right" | "top" | "bottom"};
  color_reveal: {start?: number; end?: number; direction?: "left" | "right" | "top" | "bottom"};
  object_beats: Array<{at: number; asset_id?: string; x?: number; y?: number}>;
  camera: {type?: "push" | "pan-x" | "pan-y" | "static"; amount?: number};
  parallax: {enabled?: boolean; amount?: number};
  text_beats: Array<{at: number; text: string; x?: number; y?: number}>;
  transition: {type?: "crossfade" | "ink-wipe" | "page-turn"};
};

export type HuihuaVideoProps = {
  audio: string;
  duration: number;
  fps?: number;
  backgroundColor?: string;
  scenes: Scene[];
  images: ImageAsset[];
  motion: MotionScene[];
  subtitles: SubtitleItem[];
};
