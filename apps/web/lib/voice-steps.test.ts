import { describe, expect, it } from "vitest";
import { addStep } from "./use-voice-agent";

describe("voice steps", () => {
  it("marks earlier steps done when a new one starts", () => {
    const one = addStep([], "Looking up your orders…");
    expect(one).toEqual([{ label: "Looking up your orders…", done: false }]);
    const two = addStep(one, "Checking our policies…");
    expect(two).toEqual([
      { label: "Looking up your orders…", done: true },
      { label: "Checking our policies…", done: false },
    ]);
  });

  it("doesn't repeat a step that's still running", () => {
    const one = addStep([], "Searching the catalog…");
    expect(addStep(one, "Searching the catalog…")).toBe(one);
  });
});
