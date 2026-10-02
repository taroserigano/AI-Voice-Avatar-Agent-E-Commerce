import { test } from "node:test";
import assert from "node:assert/strict";
import { voiceEnvironment, withoutAvatarSecrets } from "./voice-env.mjs";

test("shared values are allowlisted and local/process aliases take precedence", () => {
  const result = voiceEnvironment(
    { TAVUS_API_KEY: "process-tavus", VOICE_AVATAR: "both" },
    { TAVUS_APIKEY: "local-tavus", LIVEAVATAR_API_KEY: "local-live" },
    { TAVUS_APIKEY: "shared-tavus", LIVEAVATAR_API_KEY: "shared-live", HEYGEN_AVATAR_ID: "face",
      UNRELATED_SECRET: "never-inherit", HEYGEN_APIKEY: "wrong-product" },
  );
  assert.deepEqual(result, {
    TAVUS_APIKEY: "process-tavus", VOICE_AVATAR: "both", LIVEAVATAR_API_KEY: "local-live",
    HEYGEN_AVATAR_ID: "face",
  });
  assert.deepEqual(withoutAvatarSecrets(result), { VOICE_AVATAR: "both", HEYGEN_AVATAR_ID: "face" });
});

test("the root LiveAvatar key alias is loaded and excluded from other children", () => {
  const env = voiceEnvironment({}, {}, { HEYGEN_LIVE_APIKEY: "live-secret" });
  assert.deepEqual(env, { LIVEAVATAR_API_KEY: "live-secret" });
  assert.deepEqual(withoutAvatarSecrets({ ...env, HEYGEN_LIVE_APIKEY: "live-secret" }), {});
  assert.deepEqual(
    voiceEnvironment({}, { HEYGEN_LIVE_APIKEY: "local" }, { LIVEAVATAR_API_KEY: "shared" }),
    { LIVEAVATAR_API_KEY: "local" },
  );
});
