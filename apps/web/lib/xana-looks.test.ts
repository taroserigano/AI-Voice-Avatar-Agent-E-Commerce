import { afterEach, describe, expect, it, vi } from "vitest";
import { BACKGROUNDS, DEFAULT_BACKGROUND, backgroundFor, loadPrefs, savePrefs } from "./xana-looks";

describe("Xana's backgrounds and remembered picks", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to the default background for an unknown or missing choice", () => {
    expect(backgroundFor("disco").key).toBe(DEFAULT_BACKGROUND);
    expect(backgroundFor(null).key).toBe(DEFAULT_BACKGROUND);
    expect(backgroundFor("mint").key).toBe("mint");
    expect(new Set(BACKGROUNDS.map((b) => b.key)).size).toBe(BACKGROUNDS.length);
  });

  it("remembers the look and background in this browser", () => {
    const store = new Map<string, string>();
    vi.stubGlobal("window", {
      localStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => store.set(k, v) },
    });
    savePrefs({ look: "margo", background: "cafe" });
    expect(loadPrefs()).toEqual({ look: "margo", background: "cafe" });
  });

  it("works without storage (private window, blocked site data)", () => {
    vi.stubGlobal("window", {
      localStorage: {
        getItem: () => {
          throw new Error("blocked");
        },
        setItem: () => {
          throw new Error("blocked");
        },
      },
    });
    expect(() => savePrefs({ look: "rose" })).not.toThrow();
    expect(loadPrefs()).toEqual({});
  });

  it("ignores stored junk", () => {
    vi.stubGlobal("window", { localStorage: { getItem: () => '{"look": 5, "background": ["x"]}', setItem: () => {} } });
    expect(loadPrefs()).toEqual({ look: undefined, background: undefined });
  });
});
