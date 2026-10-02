// Standalone voice launcher with the same allowlisted shared credentials as pnpm dev.
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readEnvFile, voiceEnvironment } from "./voice-env.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const local = readEnvFile(resolve(root, ".env"));
const sharedFile = process.env.VOICE_SHARED_SECRETS_FILE ?? local.VOICE_SHARED_SECRETS_FILE;
const shared = readEnvFile(sharedFile ? resolve(root, sharedFile) : undefined);
const child = spawn("uv", ["run", "--directory", "services/voice", "xana-voice"], {
  cwd: root, env: voiceEnvironment(process.env, local, shared), stdio: "inherit",
});
child.on("error", () => { console.error("Could not start the voice service. Check that uv is installed."); process.exitCode = 1; });
child.on("exit", (code) => { process.exitCode = code ?? 1; });
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
