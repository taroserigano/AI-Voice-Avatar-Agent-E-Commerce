import { describe, expect, it } from "vitest";
import { captionFor, joinWords, visibleText, type CaptionSegment } from "./voice-captions";
import { splitAudioFrame } from "./voice-protocol";

const seg = (over: Partial<CaptionSegment>): CaptionSegment => ({
  segment: 1,
  text: "Your refund is $12.63, to your card.",
  words: [
    { w: "Your", start_ms: 0, end_ms: 200 },
    { w: "refund", start_ms: 220, end_ms: 500 },
    { w: "is", start_ms: 520, end_ms: 600 },
    { w: "$12.63,", start_ms: 640, end_ms: 1600 },
    { w: "to", start_ms: 1650, end_ms: 1700 },
    { w: "your", start_ms: 1720, end_ms: 1850 },
    { w: "card.", start_ms: 1870, end_ms: 2200 },
  ],
  playedMs: 0,
  done: false,
  ...over,
});

describe("captions follow the voice", () => {
  it("shows nothing before the first word is spoken", () => {
    expect(visibleText(seg({ playedMs: 0 }))).toBe("Your");
    expect(visibleText(seg({ playedMs: -1 }))).toBe("");
  });

  it("shows only the words already spoken", () => {
    expect(visibleText(seg({ playedMs: 530 }))).toBe("Your refund is");
    expect(visibleText(seg({ playedMs: 1700 }))).toBe("Your refund is $12.63, to");
  });

  it("shows the full text once the segment has played", () => {
    expect(visibleText(seg({ playedMs: 900, done: true }))).toBe("Your refund is $12.63, to your card.");
  });

  it("without word timings shows the text as soon as audio plays", () => {
    expect(visibleText(seg({ words: [], playedMs: 0 }))).toBe("");
    expect(visibleText(seg({ words: [], playedMs: 20 }))).toBe("Your refund is $12.63, to your card.");
  });

  it("joins segments into one caption", () => {
    const a = seg({ segment: 1, playedMs: 99999, done: true });
    const b = seg({ segment: 2, text: "Anything else?", words: [], playedMs: 10 });
    expect(captionFor([a, b])).toBe("Your refund is $12.63, to your card. Anything else?");
  });

  it("joins engine words without stray spaces before punctuation", () => {
    expect(joinWords(["Hi", ",", "Alice", "!"])).toBe("Hi, Alice!");
    expect(joinWords(["(", "about", "$", "5", ")"])).toBe("(about $5)");
  });
});

describe("audio frames", () => {
  it("reads the segment number and samples", () => {
    const buf = new ArrayBuffer(4 + 6);
    new DataView(buf).setUint32(0, 7, true);
    new Int16Array(buf, 4).set([1, -2, 3]);
    const frame = splitAudioFrame(buf);
    expect(frame?.segment).toBe(7);
    expect(Array.from(frame?.pcm ?? [])).toEqual([1, -2, 3]);
  });

  it("rejects frames that aren't whole samples", () => {
    expect(splitAudioFrame(new ArrayBuffer(3))).toBeNull();
    expect(splitAudioFrame(new ArrayBuffer(7))).toBeNull();
  });
});
