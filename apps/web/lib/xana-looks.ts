/**
 * What the customer can pick for Xana's face: the look (which face, offered by the server)
 * and the background behind her (drawn in the browser over Tavus's green screen). The choice
 * is remembered in this browser only; nothing breaks if storage is unavailable.
 */

export type Background = { key: string; label: string; src: string; swatch: string };

export const BACKGROUNDS: Background[] = [
  { key: "sunlit", label: "Sunlit room", src: "/xana/backgrounds/sunlit.jpg", swatch: "#f3e9dc" },
  { key: "cafe", label: "Café", src: "/xana/backgrounds/cafe.jpg", swatch: "#f2dcc4" },
  { key: "mint", label: "Mint", src: "/xana/backgrounds/mint.jpg", swatch: "#dcf1e7" },
  { key: "lavender", label: "Lavender", src: "/xana/backgrounds/lavender.jpg", swatch: "#e9e5fb" },
  { key: "night", label: "Night", src: "/xana/backgrounds/night.jpg", swatch: "#1d1740" },
];

export const DEFAULT_BACKGROUND = "sunlit";

export function lookThumb(key: string): string {
  return `/xana/looks/${key}.jpg`;
}

export function backgroundFor(key: string | null | undefined): Background {
  return BACKGROUNDS.find((b) => b.key === key) ?? BACKGROUNDS.find((b) => b.key === DEFAULT_BACKGROUND)!;
}

const STORE_KEY = "xana.avatar.prefs";

export type AvatarPrefs = { look?: string; background?: string };

export function loadPrefs(): AvatarPrefs {
  try {
    const raw = window.localStorage.getItem(STORE_KEY);
    const parsed = raw ? (JSON.parse(raw) as unknown) : null;
    if (!parsed || typeof parsed !== "object") return {};
    const { look, background } = parsed as Record<string, unknown>;
    return {
      look: typeof look === "string" ? look : undefined,
      background: typeof background === "string" ? background : undefined,
    };
  } catch {
    return {};
  }
}

export function savePrefs(prefs: AvatarPrefs): void {
  try {
    window.localStorage.setItem(STORE_KEY, JSON.stringify(prefs));
  } catch {
    // private window or blocked storage: the choice just isn't remembered
  }
}
