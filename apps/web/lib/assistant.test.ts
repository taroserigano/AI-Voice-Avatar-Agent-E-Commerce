import { describe, expect, it } from "vitest";
import { parseSse } from "./assistant-client";
import { answerBlocks, plainAnswer } from "./assistant-text";
import type { CitationCard } from "./assistant-types";

const CITE: CitationCard = {
  kind: "citation",
  cite: "returns-and-refunds#rr-2-1",
  doc_title: "Return and refund policy",
  number: "2.1",
  title: "Standard and inspected items",
  version: "sandbox-2026-09",
  url: "/returns-policy#rr-2-1",
  excerpt: "You can start a return up to 30 days after the delivery date.",
};

describe("parseSse", () => {
  it("splits complete events and keeps a partial one for later", () => {
    const { events, rest } = parseSse(
      'event: text\ndata: {"delta":"Hi"}\n\nevent: card\ndata: {"kind":"cart"}\n\nevent: te',
    );
    expect(events).toEqual([
      { event: "text", data: { delta: "Hi" } },
      { event: "card", data: { kind: "cart" } },
    ]);
    expect(rest).toBe("event: te");
  });

  it("skips malformed events", () => {
    expect(parseSse("event: text\ndata: {nope\n\n").events).toEqual([]);
  });
});

describe("answerBlocks", () => {
  it("numbers valid citations and drops unknown ones", () => {
    const blocks = answerBlocks(
      "You have 30 days. [[cite:returns-and-refunds#rr-2-1]] Also [[cite:made-up#xx-1]]",
      [CITE],
    );
    expect(blocks).toHaveLength(1);
    const segs = blocks[0]!.kind === "paragraph" ? blocks[0]!.segments : [];
    expect(segs.map((s) => (s.kind === "cite" ? `[${s.n}]` : s.text)).join("")).toBe("You have 30 days. [1] Also");
  });

  it("hides markers, even half-received ones, while streaming", () => {
    const blocks = answerBlocks("30 days. [[cite:returns-and-ref", [], true);
    const segs = blocks[0]!.kind === "paragraph" ? blocks[0]!.segments : [];
    expect(segs.map((s) => (s.kind === "text" ? s.text : "?")).join("")).toBe("30 days.");
  });

  it("turns dash lines into a list", () => {
    const blocks = answerBlocks("Top picks:\n- Milk A, $3.49\n- Milk B, $4.49\nWant one?", []);
    expect(blocks.map((b) => b.kind)).toEqual(["paragraph", "list", "paragraph"]);
    expect(blocks[1]!.kind === "list" && blocks[1]!.items.length).toBe(2);
  });

  it("gives screen readers the answer without markers", () => {
    expect(plainAnswer("Yes. [[cite:returns-and-refunds#rr-6-2]]\n\nOpen now.")).toBe("Yes. Open now.");
  });
});
