import type { CitationCard } from "./assistant-types";

/** A piece of an answer: plain text, or a numbered reference to a cited policy section. */
export type Segment = { kind: "text"; text: string } | { kind: "cite"; n: number; citation: CitationCard };

export type Block = { kind: "paragraph"; segments: Segment[] } | { kind: "list"; items: Segment[][] };

const MARKER = /\[\[cite:([^\]\s]+)\]\]/g;

/**
 * Turn an answer into paragraphs and bullet lists, replacing `[[cite:doc#section]]` markers
 * with numbered references. Markers for sections the server didn't validate are dropped; while
 * an answer is still streaming (`pending`), every marker (and a half-received one) is hidden.
 */
export function answerBlocks(text: string, citations: CitationCard[], pending = false): Block[] {
  const numbers = new Map(citations.map((c, i) => [c.cite, i + 1]));
  const clean = pending ? text.replace(/\[\[[^\]]*\]?$/, "") : text;

  const segmentsOf = (line: string): Segment[] => {
    const out: Segment[] = [];
    let last = 0;
    for (const m of line.matchAll(MARKER)) {
      const before = line.slice(last, m.index);
      if (before) out.push({ kind: "text", text: before });
      const n = pending ? undefined : numbers.get(m[1] ?? "");
      const citation = n ? citations[n - 1] : undefined;
      if (n && citation) out.push({ kind: "cite", n, citation });
      last = (m.index ?? 0) + m[0].length;
    }
    const tail = line.slice(last);
    if (tail) out.push({ kind: "text", text: tail });
    // Drop the space a removed marker leaves before punctuation or the end.
    return out.map((s, i) =>
      s.kind === "text" && out[i + 1]?.kind !== "text" && i === out.length - 1 ? { ...s, text: s.text.trimEnd() } : s,
    );
  };

  const blocks: Block[] = [];
  for (const para of clean.split(/\n{2,}/)) {
    const lines = para.split("\n").filter((l) => l.trim());
    if (!lines.length) continue;
    let list: Segment[][] | null = null;
    let prose: string[] = [];
    const flushProse = () => {
      if (prose.length) blocks.push({ kind: "paragraph", segments: segmentsOf(prose.join(" ")) });
      prose = [];
    };
    for (const line of lines) {
      const bullet = /^\s*(?:[-*•]|\d+\.)\s+(.*)$/.exec(line);
      if (bullet) {
        flushProse();
        if (!list) {
          list = [];
          blocks.push({ kind: "list", items: list });
        }
        list.push(segmentsOf(bullet[1] ?? ""));
      } else {
        list = null;
        prose.push(line.trim());
      }
    }
    flushProse();
  }
  return blocks;
}

/** The answer as plain text, for screen-reader announcements. */
export function plainAnswer(text: string): string {
  return text.replace(MARKER, "").replace(/\[\[[^\]]*\]?$/, "").replace(/\s+/g, " ").trim();
}
