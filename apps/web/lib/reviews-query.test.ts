import type { ReviewOut } from "@ai-commerce/contracts";
import { describe, expect, it } from "vitest";
import {
  BODY_MAX,
  TITLE_MAX,
  distributionRows,
  draftFrom,
  initials,
  mergeReviewPages,
  nextReviewPage,
  ratingWord,
  validateReview,
  wasEdited,
} from "./reviews-query";

function review(id: string, extra: Partial<ReviewOut> = {}): ReviewOut {
  return {
    id,
    rating: 4,
    title: null,
    body: null,
    author_name: "Alice W.",
    created_at: "2026-08-06T08:00:00Z",
    updated_at: "2026-08-06T08:00:00Z",
    is_mine: false,
    verified_purchase: false,
    is_sample: false,
    ...extra,
  };
}

describe("nextReviewPage", () => {
  it("asks for the next page while more reviews remain", () => {
    expect(nextReviewPage({ page: 1, page_size: 10, total: 23, items: Array(10) })).toBe(2);
    expect(nextReviewPage({ page: 2, page_size: 10, total: 23, items: Array(10) })).toBe(3);
  });

  it("stops at the last page, on exact multiples, and on an empty page", () => {
    expect(nextReviewPage({ page: 3, page_size: 10, total: 23, items: Array(3) })).toBeUndefined();
    expect(nextReviewPage({ page: 2, page_size: 10, total: 20, items: Array(10) })).toBeUndefined();
    // Reviews were deleted between loads: the server says more exist but returned nothing.
    expect(nextReviewPage({ page: 2, page_size: 10, total: 30, items: [] })).toBeUndefined();
  });
});

describe("mergeReviewPages", () => {
  it("keeps order and drops a review repeated after offsets shift", () => {
    const merged = mergeReviewPages([{ items: [review("a"), review("b")] }, { items: [review("b"), review("c")] }]);
    expect(merged.map((r) => r.id)).toEqual(["a", "b", "c"]);
  });
});

describe("distributionRows", () => {
  it("always returns five rows from 5 to 1 stars with percents and spoken labels", () => {
    const rows = distributionRows({
      count: 12,
      distribution: [
        { stars: 5, count: 8 },
        { stars: 4, count: 3 },
        { stars: 1, count: 1 },
      ],
    });
    expect(rows.map((r) => r.stars)).toEqual([5, 4, 3, 2, 1]);
    expect(rows.map((r) => r.percent)).toEqual([67, 25, 0, 0, 8]);
    expect(rows[0]?.label).toBe("5 stars, 8 reviews, 67%");
    expect(rows[4]?.label).toBe("1 star, 1 review, 8%");
  });

  it("shows zero percent rather than dividing by zero when there are no reviews", () => {
    const rows = distributionRows({ count: 0, distribution: [] });
    expect(rows.every((r) => r.count === 0 && r.percent === 0)).toBe(true);
  });
});

describe("validateReview", () => {
  it("requires a whole-star rating from 1 to 5", () => {
    expect(validateReview({ rating: null, title: "", body: "" })).toMatchObject({ ok: false, errors: { rating: expect.any(String) } });
    expect(validateReview({ rating: 0, title: "", body: "" }).ok).toBe(false);
    expect(validateReview({ rating: 6, title: "", body: "" }).ok).toBe(false);
    expect(validateReview({ rating: 3.5, title: "", body: "" }).ok).toBe(false);
  });

  it("trims text and sends blank fields as null", () => {
    expect(validateReview({ rating: 5, title: "  Love it  ", body: "   " })).toEqual({
      ok: true,
      value: { rating: 5, title: "Love it", body: null },
    });
  });

  it("enforces the API's length limits after trimming", () => {
    expect(validateReview({ rating: 4, title: `${"x".repeat(TITLE_MAX)}   `, body: "" }).ok).toBe(true);
    const tooLong = validateReview({ rating: 4, title: "x".repeat(TITLE_MAX + 1), body: "y".repeat(BODY_MAX + 1) });
    expect(tooLong).toMatchObject({ ok: false, errors: { title: expect.any(String), body: expect.any(String) } });
  });

  it("keeps line breaks inside the review body", () => {
    const result = validateReview({ rating: 4, title: "", body: "Pros: light\nCons: pricey" });
    expect(result).toMatchObject({ ok: true, value: { body: "Pros: light\nCons: pricey" } });
  });
});

describe("draftFrom", () => {
  it("prefills from a saved review and starts empty without one", () => {
    expect(draftFrom(review("a", { rating: 2, title: "Meh", body: null }))).toEqual({ rating: 2, title: "Meh", body: "" });
    expect(draftFrom(null)).toEqual({ rating: null, title: "", body: "" });
  });
});

describe("display helpers", () => {
  it("names each star value", () => {
    expect([1, 2, 3, 4, 5].map(ratingWord)).toEqual(["Poor", "Fair", "Good", "Very good", "Excellent"]);
    expect(ratingWord(0)).toBe("");
  });

  it("builds avatar initials from the shortened display name", () => {
    expect(initials("Alice W.")).toBe("AW");
    expect(initials("Larkspur shopper")).toBe("LS");
    expect(initials("Cher")).toBe("C");
    expect(initials("  ")).toBe("?");
  });

  it("marks a review edited only when it changed more than a minute after posting", () => {
    expect(wasEdited(review("a"))).toBe(false);
    expect(wasEdited(review("a", { updated_at: "2026-08-06T08:00:30Z" }))).toBe(false);
    expect(wasEdited(review("a", { updated_at: "2026-08-09T10:00:00Z" }))).toBe(true);
  });
});
