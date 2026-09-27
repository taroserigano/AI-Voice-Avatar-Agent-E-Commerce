import "server-only";

import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { type PolicyDoc, parsePolicy } from "./policy-doc";

/** content/policies at the repo root, found by walking up from the web app's directory. */
function policyDir(): string {
  let dir = process.cwd();
  for (let i = 0; i < 5; i++) {
    const candidate = join(dir, "content", "policies");
    if (existsSync(candidate)) return candidate;
    dir = dirname(dir);
  }
  throw new Error("content/policies not found");
}

/** Read one approved policy document. Read per request, so an edit shows without a rebuild. */
export async function loadPolicy(id: string): Promise<PolicyDoc> {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error("bad policy id");
  return parsePolicy(await readFile(join(policyDir(), `${id}.md`), "utf8"));
}
