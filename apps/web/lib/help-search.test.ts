import { describe, expect, it } from "vitest";
import { type HelpEntry, searchHelp } from "./help-search";

const entry = (id: string, title: string, text: string, section = "Topic"): HelpEntry => ({
  id,
  section,
  title,
  text,
  href: `#${id}`,
});

const ENTRIES = [
  entry("shipping", "How much is shipping?", "Standard shipping is $5.99, free at $35.", "Common questions"),
  entry("returns", "Returns & refunds", "30 days from delivery, free return shipping."),
  entry("gluten", "Gluten free", "Made without wheat, barley, or rye", "Labels"),
  entry("fat", "Fat free", "Less than 0.5 g of fat", "Labels"),
];

const ids = (q: string) => searchHelp(ENTRIES, q).map((e) => e.id);

describe("searchHelp", () => {
  it("finds nothing for an empty or punctuation-only query", () => {
    expect(ids("")).toEqual([]);
    expect(ids("  ?! ")).toEqual([]);
  });

  it("needs every word, ignoring case, hyphens, and accents", () => {
    expect(ids("GLUTEN-free")).toEqual(["gluten"]);
    expect(ids("gluten fat")).toEqual([]);
    expect(ids("réturns")).toEqual(["returns"]);
  });

  it("folds simple plurals both ways", () => {
    expect(ids("refund")).toEqual(["returns"]);
    expect(ids("labels")).toEqual(["gluten", "fat"]);
  });

  it("ranks title matches above text-only matches", () => {
    // "shipping" is in the first entry's title and only in the second entry's text.
    expect(ids("shipping")).toEqual(["shipping", "returns"]);
    expect(ids("free")).toEqual(["gluten", "fat", "shipping", "returns"]);
  });
});
