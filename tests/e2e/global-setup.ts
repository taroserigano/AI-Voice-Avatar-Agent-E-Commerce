import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * The suite signs in many times from one address, which trips the real sign-in rate
 * limiter (by design). Clear only the sign-in rate-limit counters in the local Redis
 * cache before each run; nothing else is touched.
 */
export default function globalSetup() {
  const compose = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../infra/compose.yaml");
  try {
    execSync(
      `docker compose -f "${compose}" exec -T redis sh -c "redis-cli --scan --pattern 'rl:signin:*' | xargs -r redis-cli del"`,
      { stdio: "ignore" },
    );
  } catch {
    console.warn("global-setup: couldn't clear sign-in rate-limit keys (is `pnpm infra:up` running?)");
  }
}
