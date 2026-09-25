// Run the commerce API, outbox worker, and web app together: `pnpm dev`.
// Each process's output is prefixed; Ctrl+C stops all of them.
import { spawn } from "node:child_process";

const env = {
  ...process.env,
  OTEL_EXPORTER_OTLP_ENDPOINT: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318",
  COMMERCE_API_URL: process.env.COMMERCE_API_URL ?? "http://localhost:8000",
};

const procs = [
  { name: "api", color: 36, cmd: "pnpm", args: ["dev:api"] },
  { name: "outbox", color: 35, cmd: "pnpm", args: ["dev:outbox"] },
  { name: "web", color: 33, cmd: "pnpm", args: ["dev:web"] },
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
