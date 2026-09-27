/** One searchable piece of the help center: a topic, a fact, a label, or a question. */
export type HelpEntry = { id: string; section: string; title: string; text: string; href: string };

/** Lowercase, no accents or punctuation, so “fat-free” matches "fat free". */
function normalize(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9$]+/g, " ")
    .trim();
}

/** "returns" finds "return", "labels" finds "label": a light plural fold, nothing fancier. */
function stem(word: string): string {
  return word.length > 3 && word.endsWith("s") ? word.slice(0, -1) : word;
}

/** Entries containing every word of the query (in title, text, or section), title matches first. */
export function searchHelp(entries: HelpEntry[], query: string): HelpEntry[] {
  const words = normalize(query).split(" ").filter(Boolean).map(stem);
  if (words.length === 0) return [];
  const scored: { entry: HelpEntry; score: number }[] = [];
  for (const entry of entries) {
    const title = normalize(entry.title);
    const all = `${title} ${normalize(entry.text)} ${normalize(entry.section)}`;
    if (!words.every((w) => all.includes(w))) continue;
    scored.push({ entry, score: words.filter((w) => title.includes(w)).length });
  }
  // Array.prototype.sort is stable, so equal scores keep the page's order.
  return scored.sort((a, b) => b.score - a.score).map((s) => s.entry);
}
