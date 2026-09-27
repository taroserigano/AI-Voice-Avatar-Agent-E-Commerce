import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { formatEffectiveDate, parsePolicy, tableOfContents } from "./policy-doc";

const SAMPLE = `---
id: x
title: X
version: v1
effective_date: 2026-09-26
section_prefix: xx
summary:
  - One
---

# X

Intro text.

## 1. First

One.

### 1.2 Sub

Two.

## 2. Second

Three.
`;

describe("parsePolicy", () => {
  it("numbers sections the same way as the commerce API", () => {
    const doc = parsePolicy(SAMPLE);
    expect(doc.intro).toBe("Intro text.");
    expect(doc.effectiveDate).toBe("2026-09-26");
    expect(doc.summary).toEqual(["One"]);
    expect(doc.sections.map((s) => [s.id, s.number, s.level, s.body])).toEqual([
      ["xx-1", "1", 2, "One."],
      ["xx-1-2", "1.2", 3, "Two."],
      ["xx-2", "2", 2, "Three."],
    ]);
  });

  it("builds a nested table of contents", () => {
    const toc = tableOfContents(parsePolicy(SAMPLE));
    expect(toc.map((e) => [e.id, e.children.map((c) => c.id)])).toEqual([
      ["xx-1", ["xx-1-2"]],
      ["xx-2", []],
    ]);
  });

  it("parses the real return policy with its rules and citable sections", () => {
    const text = readFileSync(join(__dirname, "../../../content/policies/returns-and-refunds.md"), "utf8");
    const doc = parsePolicy(text);
    expect(doc.rules.return_window_days).toBe(30);
    expect(doc.summary.length).toBeGreaterThan(3);
    expect(doc.summary.filter((line) => line.includes("[object"))).toEqual([]);
    const ids = doc.sections.map((s) => s.id);
    expect(ids).toContain("rr-7-2");
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("formatEffectiveDate", () => {
  it("formats without shifting the day", () => {
    expect(formatEffectiveDate("2026-09-26")).toBe("September 26, 2026");
  });
});

describe("pages that restate the policy", () => {
  it("'How returns work' uses the policy's numbers", () => {
    const repo = join(__dirname, "../../..");
    const rules = parsePolicy(readFileSync(join(repo, "content/policies/returns-and-refunds.md"), "utf8")).rules;
    const page = readFileSync(join(repo, "apps/web/app/(shop)/help/returns/page.tsx"), "utf8");
    expect(page).toContain(`const WINDOW_DAYS = ${rules.return_window_days};`);
    expect(page).toContain(`const PERISHABLE_DAYS = ${rules.perishable_report_days};`);
    expect(page).toContain(`const INSTANT_UNDER = "$${Number(rules.instant_refund_under_minor) / 100}";`);
  });
});
