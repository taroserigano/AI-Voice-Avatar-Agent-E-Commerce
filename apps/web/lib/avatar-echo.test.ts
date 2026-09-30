import { describe, expect, it } from "vitest";
import { AvatarEcho, pcmBase64, type EchoMessage } from "./avatar-echo";

/** `ms` of audio at 24 kHz. */
const audio = (ms: number) => new Int16Array((24_000 * ms) / 1000).fill(1000);

function setup() {
  let t = 0;
  const sent: EchoMessage[] = [];
  let n = 0;
  const echo = new AvatarEcho({
    send: (m) => sent.push(m),
    conversationId: "conv-t",
    now: () => t,
    newId: () => `turn-${++n}`,
  });
  return {
    echo,
    sent,
    at: (ms: number) => {
      t = ms;
    },
    echoes: () => sent.filter((m) => m.event_type === "conversation.echo"),
    started: () => echo.onTavus("conversation.pal.started_speaking", null),
    stopped: (interrupted = false) => echo.onTavus("conversation.pal.stopped_speaking", { interrupted }),
  };
}

describe("Xana's audio reaches Tavus", () => {
  it("sends a turn under one id and closes it with a silent done chunk", () => {
    const s = setup();
    s.echo.segmentStart(1, "filler");
    s.echo.audio(1, audio(500));
    s.echo.segmentEnd(1);
    s.echo.segmentStart(2, "answer");
    s.echo.audio(2, audio(1000));
    s.echo.segmentEnd(2);
    s.echo.turnDone();
    const ids = new Set(s.echoes().map((m) => m.properties!.inference_id));
    expect(ids).toEqual(new Set(["turn-1"])); // a new id while Tavus speaks would be dropped
    const last = s.echoes().at(-1)!.properties!;
    expect(last.done).toBe(true);
    expect(last.sample_rate).toBe(24_000);
    expect(s.echoes().slice(0, -1).every((m) => m.properties!.done === false)).toBe(true);
  });

  it("sends the first audio of a turn at once and coalesces the rest", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(20));
    expect(s.echoes()).toHaveLength(1);
    s.echo.audio(1, audio(20));
    s.echo.audio(1, audio(20));
    expect(s.echoes()).toHaveLength(1); // held until ~100 ms or the next tick
    s.echo.tick();
    expect(s.echoes()).toHaveLength(2);
  });

  it("holds the next turn until Tavus has finished the previous one", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(1000));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.echo.segmentStart(2, "answer");
    s.echo.audio(2, audio(500)); // e.g. "confirming your return now" then the outcome
    expect(s.echoes().every((m) => m.properties!.inference_id === "turn-1")).toBe(true);
    s.at(700);
    s.started();
    s.at(1900);
    s.stopped();
    expect(s.echoes().at(-1)!.properties!.inference_id).toBe("turn-2");
  });

  it("encodes little-endian PCM16 as base64", () => {
    expect(pcmBase64(new Int16Array([1, -1]))).toBe(btoa(String.fromCharCode(1, 0, 255, 255)));
  });
});

describe("what the customer has heard", () => {
  it("counts a segment heard in full only on a clean stop after its end", () => {
    const s = setup();
    s.echo.segmentStart(1, "confirm");
    s.echo.audio(1, audio(3000));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.at(650);
    s.started(); // heard from ~800 ms, so it ends ~3800 ms
    s.at(2000);
    s.stopped(); // Tavus split the utterance at a gap: not the end yet
    expect(s.echo.tick()).toEqual([]);
    s.at(3700);
    s.stopped();
    expect(s.echo.tick()).toEqual([{ segment: 1, playedMs: 3000 }]);
  });

  it("never counts an interrupted read-back", () => {
    const s = setup();
    s.echo.segmentStart(1, "confirm");
    s.echo.audio(1, audio(3000));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.at(650);
    s.started();
    s.at(4000);
    s.stopped(true);
    s.at(20_000);
    expect(s.echo.tick()).toEqual([]);
  });

  it("never counts a read-back without Tavus saying it finished", () => {
    const s = setup();
    s.echo.segmentStart(1, "confirm");
    s.echo.audio(1, audio(2000));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.at(60_000);
    expect(s.echo.tick()).toEqual([]);
  });

  it("lets other segments finish on the timeline if Tavus's event is lost", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(1000));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.at(1000);
    expect(s.echo.tick()).toEqual([]);
    s.at(10_000);
    expect(s.echo.tick()).toEqual([{ segment: 1, playedMs: 1000 }]);
  });

  it("drives captions from when Tavus starts speaking", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(2000));
    expect(s.echo.playedMs(1)).toBe(-1);
    s.at(600);
    s.started(); // heard ~150 ms after the event
    s.at(700);
    expect(s.echo.playedMs(1)).toBe(-1);
    s.at(1250);
    expect(s.echo.playedMs(1)).toBe(500);
    s.at(9000);
    expect(s.echo.playedMs(1)).toBe(2000);
  });

  it("starts a segment after the one before it, not over it", () => {
    const s = setup();
    s.echo.segmentStart(1, "filler");
    s.echo.audio(1, audio(1500));
    s.echo.segmentEnd(1);
    s.at(300);
    s.echo.segmentStart(2, "answer");
    s.echo.audio(2, audio(1000));
    s.echo.segmentEnd(2);
    s.echo.turnDone();
    s.at(650);
    s.started(); // the filler, heard from 800 ms to 2300 ms
    s.at(2400);
    expect(s.echo.playedMs(2)).toBe(100);
    s.at(3350);
    s.stopped();
    expect(s.echo.tick().map((c) => c.segment)).toEqual([1, 2]);
  });

  it("ignores Tavus's legacy duplicate events", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(500));
    s.echo.segmentEnd(1);
    s.echo.turnDone();
    s.at(600);
    s.echo.onTavus("conversation.replica.started_speaking", null);
    s.at(2000); // after the segment's end, before the lost-event fallback
    s.echo.onTavus("conversation.replica.stopped_speaking", { interrupted: false });
    s.echo.onTavus("conversation.stopped_speaking", { role: "replica", interrupted: false });
    expect(s.echo.tick()).toEqual([]);
    s.echo.onTavus("conversation.stopped_speaking", { role: "pal", interrupted: false });
    expect(s.echo.tick()).toEqual([{ segment: 1, playedMs: 500 }]);
  });
});

describe("talking over Xana", () => {
  it("interrupts Tavus, stops sending, and lets the next turn go at once", () => {
    const s = setup();
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(5000));
    s.at(1500);
    s.echo.drop([1]);
    expect(s.sent.at(-1)).toEqual({
      message_type: "conversation",
      event_type: "conversation.interrupt",
      conversation_id: "conv-t",
    });
    const before = s.echoes().length;
    s.echo.audio(1, audio(500)); // late audio for the dropped segment
    expect(s.echoes()).toHaveLength(before);
    s.echo.segmentStart(2, "answer");
    s.echo.audio(2, audio(500));
    expect(s.echoes().at(-1)!.properties!.inference_id).toBe("turn-2");
    expect(s.echo.tick().map((c) => c.segment)).not.toContain(1);
  });

  it("is idle once everything is heard or dropped", () => {
    const s = setup();
    expect(s.echo.idle).toBe(true);
    s.echo.segmentStart(1, "answer");
    s.echo.audio(1, audio(500));
    expect(s.echo.idle).toBe(false);
    s.echo.drop([1]);
    expect(s.echo.idle).toBe(true);
  });
});
