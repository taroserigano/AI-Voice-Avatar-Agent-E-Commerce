// Runs `<engine> compose -f infra/compose.yaml ...args` with Docker or Podman.
// CONTAINER_ENGINE=docker|podman picks one; otherwise the first engine that is running wins.
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const composeFile = join(root, "infra", "compose.yaml");

function isRunning(engine) {
  return spawnSync(engine, ["info"], { stdio: "ignore", shell: false }).status === 0;
}

function pickEngine() {
  const chosen = process.env.CONTAINER_ENGINE;
  if (chosen) return chosen;
  for (const engine of ["docker", "podman"]) {
    if (isRunning(engine)) return engine;
  }
  console.error(
    "Neither Docker nor Podman is running. Start Docker Desktop, or run `podman machine start`.",
  );
  process.exit(1);
}

const engine = pickEngine();
const result = spawnSync(engine, ["compose", "-f", composeFile, ...process.argv.slice(2)], {
  stdio: "inherit",
  shell: false,
});
process.exit(result.status ?? 1);
