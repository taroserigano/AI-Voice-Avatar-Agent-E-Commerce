import { existsSync, readFileSync } from "node:fs";

// Only these values may cross from a separate checkout's .env into the voice child.
export const VOICE_ENV_GROUPS = [
  ["TAVUS_APIKEY", "TAVUS_API_KEY"], ["TAVUS_PAL_ID"], ["TAVUS_FACE_ID"],
  ["TAVUS_DEFAULT_LOOK"], ["TAVUS_MAX_LIVE"], ["TAVUS_TEST_MODE"],
  ["LIVEAVATAR_API_KEY", "HEYGEN_LIVE_APIKEY", "HEYGEN_LIVE_API_KEY"], ["HEYGEN_AVATAR_ID"], ["HEYGEN_SANDBOX"],
  ["HEYGEN_MAX_LIVE"], ["HEYGEN_MAX_SESSION_S"], ["VOICE_AVATAR"],
];

export function readEnvFile(path) {
  if (!path || !existsSync(path)) return {};
  const result = {};
  for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
    const match = /^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/.exec(line);
    if (!match) continue;
    const quoted = /^(["'])(.*?)\1\s*(?:#.*)?$/.exec(match[2]);
    result[match[1]] = quoted ? quoted[2] : match[2].replace(/\s*#.*$/, "").trim();
  }
  return result;
}

export function voiceEnvironment(base, local, shared) {
  const result = { ...base };
  for (const group of VOICE_ENV_GROUPS) {
    const source = [base, local, shared].find((values) => group.some((key) => values[key] !== undefined));
    if (!source) continue;
    const key = group.find((key) => source[key] !== undefined);
    // Canonicalize aliases so a lower-precedence alias can never override a local value.
    for (const alias of group) delete result[alias];
    result[group[0]] = source[key];
  }
  return result;
}

export function withoutAvatarSecrets(env) {
  const result = { ...env };
  for (const key of ["TAVUS_APIKEY", "TAVUS_API_KEY", "LIVEAVATAR_API_KEY", "HEYGEN_LIVE_APIKEY", "HEYGEN_LIVE_API_KEY", "HEYGEN_APIKEY", "HEYGEN_API_KEY"]) {
    delete result[key];
  }
  return result;
}
