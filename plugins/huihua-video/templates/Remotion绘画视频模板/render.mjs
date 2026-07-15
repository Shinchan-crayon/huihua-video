import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import {bundle} from "@remotion/bundler";
import {renderMedia, selectComposition} from "@remotion/renderer";

const readArg = (name) => {
  const index = process.argv.indexOf(name);
  return index === -1 ? undefined : process.argv[index + 1];
};

const propsPath = readArg("--props");
const output = readArg("--output");
if (!propsPath || !output) {
  throw new Error("Usage: npm run render -- --props <props.json> --output <video.mp4>");
}

const inputProps = JSON.parse(await fs.readFile(path.resolve(propsPath), "utf8"));
const serveUrl = await bundle(path.resolve("src/index.ts"));
const composition = await selectComposition({
  serveUrl,
  id: "HuihuaVideo",
  inputProps,
});
await renderMedia({
  composition,
  serveUrl,
  codec: "h264",
  audioCodec: "aac",
  outputLocation: path.resolve(output),
  inputProps,
});
console.log(path.resolve(output));
