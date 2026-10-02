import { describe, expect, it, vi } from "vitest";
import { HeygenPlayback, type LiveAvatarCommand } from "./heygen-playback";

function setup() {
  let time = 0, id = 0;
  const sent: LiveAvatarCommand[] = [];
  const fail = vi.fn();
  const playback = new HeygenPlayback({
    send: (m) => sent.push(m), fail, now: () => time, newId: () => `id-${++id}`,
  });
  const event = (type: string, source = "id-1") => playback.onEvent({ type, source_event_id: source });
  return { playback, sent, fail, event, at: (t: number) => { time = t; } };
}

describe("LiveAvatar LITE playback", () => {
  it("streams PCM24 in bounded frames, seals once, and waits for actual speaking events", () => {
    const s = setup();
    s.playback.segmentStart(1, "confirm");
    s.playback.audio(1, new Int16Array(48_000).fill(1000));
    s.playback.segmentEnd(1);
    s.playback.turnDone();
    expect(s.sent.filter((m) => m.type === "agent.speak_end")).toHaveLength(1);
    expect(s.sent.filter((m) => m.type === "agent.speak")).toHaveLength(2);
    expect(s.sent[0]?.audio?.length).toBe(64_000);
    s.event("agent.audio_buffer_appended");
    s.event("agent.audio_buffer_committed");
    s.at(2000);
    expect(s.playback.tick()).toEqual([]);
    expect(s.playback.playedMs(1)).toBe(0);
    s.event("agent.speak_started");
    s.event("agent.speak_ended", "old-session-event");
    s.at(4500);
    expect(s.playback.tick()).toEqual([]);
    s.event("agent.speak_ended");
    s.at(4900);
    expect(s.playback.tick()).toEqual([{ segment: 1, playedMs: 2000 }]);
    expect(s.playback.tick()).toEqual([]);
  });

  it("queues the next segment until the current one finishes", () => {
    const s = setup();
    for (const n of [1, 2]) {
      s.playback.segmentStart(n, "answer");
      s.playback.audio(n, new Int16Array(24_000));
      s.playback.segmentEnd(n);
    }
    expect(s.sent.every((m) => m.event_id === "id-1")).toBe(true);
    s.event("agent.speak_started");
    s.at(1000);
    s.event("agent.speak_ended");
    s.at(1400);
    s.playback.tick();
    expect(s.sent.at(-1)).toEqual({ type: "agent.speak_end", event_id: "id-2" });
  });

  it("drops interrupted audio and ignores late completion", () => {
    const s = setup();
    s.playback.segmentStart(1, "confirm");
    s.playback.audio(1, new Int16Array(24_000));
    s.playback.segmentEnd(1);
    s.event("agent.speak_started");
    s.playback.drop([1]);
    s.at(5000);
    s.event("agent.speak_ended");
    expect(s.playback.tick()).toEqual([]);
    expect(s.playback.idle).toBe(true);
    expect(s.sent.at(-1)?.type).toBe("agent.interrupt");
  });

  it("fails back to voice when the provider stalls or the queue limit is exceeded", () => {
    const s = setup();
    s.playback.segmentStart(1, "answer");
    s.playback.audio(1, new Int16Array(24_000));
    s.playback.segmentEnd(1);
    s.at(20_000);
    s.playback.tick();
    expect(s.fail).toHaveBeenCalledOnce();
    const overflow = setup();
    overflow.playback.segmentStart(1, "answer");
    overflow.playback.audio(1, new Int16Array(24_000 * 91));
    expect(overflow.fail).toHaveBeenCalledOnce();
    expect(overflow.sent).toEqual([]);
  });
});
