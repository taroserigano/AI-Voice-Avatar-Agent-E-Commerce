import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("../../tests/e2e/node_modules/@playwright/test");
const dir = dirname(fileURLToPath(import.meta.url));
const preview = process.argv.includes("--preview");
const fps = 24;
const frames = 15 * fps;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(dir, "demo.html")).href);

if (preview) {
  const out = join(dir, "previews");
  mkdirSync(out, { recursive: true });
  for (const second of [1, 4.5, 7.6, 10.5, 11.9, 13.5]) {
    await page.evaluate((t) => window.render(t), second);
    const path = join(out, `${second}.png`);
    await page.screenshot({ path });
    process.stdout.write(`${path}\n`);
  }
} else {
  const audio = join(dir, "narration.wav");
  const args = ["-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-vcodec", "png", "-i", "pipe:0"];
  if (existsSync(audio)) args.push("-i", audio);
  args.push("-map", "0:v:0");
  if (existsSync(audio)) args.push("-map", "1:a:0", "-af", "adelay=600|600,apad,atrim=0:15");
  args.push("-t", "15", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart");
  if (existsSync(audio)) args.push("-c:a", "aac", "-b:a", "160k");
  args.push(join(dir, "xana-demo-15s.mp4"));
  const ffmpeg = spawn("ffmpeg", args, { stdio: ["pipe", "inherit", "inherit"] });
  try {
    for (let i = 0; i < frames; i++) {
      await page.evaluate((t) => window.render(t), i / fps);
      const png = await page.screenshot({ type: "png" });
      if (!ffmpeg.stdin.write(png)) await once(ffmpeg.stdin, "drain");
      if (i % 48 === 0) process.stdout.write(`Rendered ${i}/${frames} frames\n`);
    }
    ffmpeg.stdin.end();
    const [code] = await once(ffmpeg, "close");
    if (code !== 0) throw new Error(`ffmpeg exited with ${code}`);
    process.stdout.write(`Created ${join(dir, "xana-demo-15s.mp4")}\n`);
  } finally {
    if (!ffmpeg.killed && ffmpeg.exitCode === null) ffmpeg.kill();
  }
}
await browser.close();
