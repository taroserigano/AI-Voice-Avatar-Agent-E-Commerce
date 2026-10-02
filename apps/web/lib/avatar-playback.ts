import type { Completed } from "./avatar-echo";

/** Shared contract for the existing Tavus timeline and LiveAvatar's utterance events. */
export interface AvatarPlayback {
  segmentStart(segment: number, kind: "filler" | "answer" | "confirm"): void;
  audio(segment: number, pcm: Int16Array): void;
  segmentEnd(segment: number): void;
  turnDone(): void;
  drop(segments: number[]): void;
  tick(): Completed[];
  playedMs(segment: number): number;
  readonly idle: boolean;
}
