// Run the commerce API, assistant API, outbox worker, and web app together: `pnpm dev`.
// Each process's output is prefixed; Ctrl+C stops all of them.
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { connect } from "node:net";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// The Python services read the repo-root .env themselves; Next.js only reads apps/web/.env.
// Pass through just these keys from the root .env (never the whole file: it may hold other
// projects' secrets). Real environment variables win.
const PASS_THROUGH = ["APP_ENV", "API_PORT", "WEB_PORT", "ASSISTANT_PORT", "VOICE_PORT", "GOOGLE_MAPS_API_KEY"];
const rootEnv = join(dirname(fileURLToPath(import.meta.url)), "..", ".env");
if (existsSync(rootEnv)) {
  for (const line of readFileSync(rootEnv, "utf8").split(/\r?\n/)) {
    const match = /^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/.exec(line);
    if (match && PASS_THROUGH.includes(match[1]) && process.env[match[1]] === undefined) {
      process.env[match[1]] = match[2].replace(/^(["'])(.*)\1$/, "$2");
    }
  }
}

// Send telemetry to the local OTel Collector only when one is listening (it runs in
// infra/compose.yaml; `pnpm local:up` doesn't start it). Otherwise every export would fail
// and flood the output.
function collectorListening() {
  return new Promise((resolve) => {
    const socket = connect({ host: "127.0.0.1", port: 4318 });
    socket.setTimeout(500);
    socket.once("connect", () => (socket.destroy(), resolve(true)));
    socket.once("timeout", () => (socket.destroy(), resolve(false)));
    socket.once("error", () => resolve(false));
  });
}

// API_PORT / ASSISTANT_PORT / WEB_PORT let a second checkout (e.g. a git worktree) run beside
// the first.
const apiPort = process.env.API_PORT ?? "8000";
const assistantPort = process.env.ASSISTANT_PORT ?? "8001";
const webPort = process.env.WEB_PORT ?? "3000";
const voicePort = process.env.VOICE_PORT ?? "8103";
const env = {
  ...process.env,
  // 127.0.0.1, not localhost: on Windows a new connection to localhost tries ::1 first and
  // waits ~2 s for the refusal before falling back (the servers listen on IPv4 only).
  COMMERCE_API_URL: process.env.COMMERCE_API_URL ?? `http://127.0.0.1:${apiPort}`,
  ASSISTANT_API_URL: process.env.ASSISTANT_API_URL ?? `http://127.0.0.1:${assistantPort}`,
  // Xana's voice screen opens its WebSocket straight to the voice agent on this port.
  VOICE_PORT: voicePort,
  NEXT_PUBLIC_VOICE_PORT: voicePort,
};
if (env.OTEL_EXPORTER_OTLP_ENDPOINT === undefined) {
  if (await collectorListening()) env.OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318";
  else console.log("No OTel Collector on :4318, so telemetry isn't exported (start it with `pnpm infra:up`).");
}

const procs = [
  { name: "api", color: 36, cmd: "pnpm", args: ["dev:api", "--port", apiPort] },
  { name: "assist", color: 32, cmd: "pnpm", args: ["dev:assistant", "--port", assistantPort] },
  { name: "outbox", color: 35, cmd: "pnpm", args: ["dev:outbox"] },
  { name: "voice", color: 34, cmd: "pnpm", args: ["dev:voice"] },
  { name: "web", color: 33, cmd: "pnpm", args: ["--filter", "@ai-commerce/web", "exec", "next", "dev", "--port", webPort] },
];

const children = procs.map(({ name, color, cmd, args }) => {
  const child = spawn(cmd, args, { env, shell: process.platform === "win32", stdio: ["ignore", "pipe", "pipe"] });
  const prefix = `\x1b[${color}m${name.padEnd(6)}|\x1b[0m `;
  const pipe = (stream, out) => {
    let buffer = "";
    stream.on("data", (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) out.write(prefix + line + "\n");
    });
  };
  pipe(child.stdout, process.stdout);
  pipe(child.stderr, process.stderr);
  child.on("exit", (code) => {
    process.stdout.write(`${prefix}exited with code ${code}\n`);
    shutdown();
  });
  return child;
});

let stopping = false;
function shutdown() {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode === null) {
      if (process.platform === "win32") spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"]);
      else child.kill("SIGTERM");
    }
  }
  setTimeout(() => process.exit(0), 500);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
