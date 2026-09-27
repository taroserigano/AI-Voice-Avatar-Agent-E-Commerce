import { describe, expect, it } from "vitest";
import {
  bayesianRating,
  canQuickAdd,
  displayTags,
  isTopRated,
  meaningfulSize,
  needsOptionChoice,
  optionsToChoose,
} from "./product-display";

const multi = (name: string, category = "dairy-eggs") => ({
  variant_count: 3,
  default_variant_name: name,
  category: { slug: category },
});

describe("needsOptionChoice", () => {
  it("asks shoppers to pick a size or color for apparel, shoes, bedding, and colorways", () => {
    const choices: [string, string][] = [
      ["Size 5", "clothing-shoes"], // Chelsea boots
      ["XS", "clothing-shoes"], // tee
      ["Black / S", "clothing-shoes"],
      ["32W x 30L", "clothing-shoes"],
      ["2T", "clothing-shoes"],
      ["10", "clothing-shoes"],
      ["Size 10 Toddler", "clothing-shoes"],
      ["Queen", "home-kitchen"],
      ["Oat / King", "home-kitchen"],
      ["Midnight", "electronics"],
      ["Fair", "beauty"], // foundation shade
      ["For 6.1-inch phones", "electronics"],
      ["64 GB", "electronics"],
      ["10 lb pair", "sports"],
      ["10 lb", "sports"], // kettlebell weight
      ["8 in", "home-kitchen"], // skillet
      ["2 qt", "home-kitchen"], // saucepan
      ["6 ft", "electronics"], // cable length
      ["55 cm (height 5'0\"-5'5\")", "sports"],
      ["Small (dogs up to 26 lb)", "pet"],
      ["Size 3 (16-28 lb), 62 diapers", "baby"],
      ["Newborn (up to 10 lb), 76 diapers", "baby"],
      ["0-6 months", "baby"],
      ["$25", "gift-cards"],
    ];
    for (const [name, category] of choices) expect(needsOptionChoice(multi(name, category)), name).toBe(true);
  });

  it("lets quick add pick the default pack when options are just bigger or smaller packs", () => {
    const packs: [string, string][] = [
      ["Half gallon", "dairy-eggs"],
      ["1 gallon", "dairy-eggs"],
      ["1 quart", "dairy-eggs"],
      ["12 eggs", "dairy-eggs"],
      ["5.3 oz cup", "dairy-eggs"],
      ["4 x 5.3 oz cups", "dairy-eggs"],
      ["1 lb (about 2 apples)", "produce"],
      ["About 2 lb tray", "meat-seafood"],
      ["Family pack, about 4.5 lb", "meat-seafood"],
      ["12 x 12 fl oz cans", "beverages"],
      ["2 x 24 fl oz", "household"],
      ["12 mega rolls (= 48 regular)", "household"],
      ["24 pods", "household"],
      ["100 fl oz (133 loads)", "household"],
      ["8 batteries", "household"],
      ["30 lb bag", "pet"],
      ["17 lb (as much litter as 40 lb of clay)", "pet"],
      ["60 softgels", "health-wellness"],
      ["4-pack", "office"],
      ["1 ream (500 sheets)", "office"],
      ["1 cu ft bag", "outdoor"],
      ["8 qt bag", "outdoor"],
      ["4 bulbs", "electronics"],
      ["1 can (3 balls)", "sports"],
    ];
    for (const [name, category] of packs) expect(needsOptionChoice(multi(name, category)), name).toBe(false);
  });

  it("never asks for a choice when there is only one option", () => {
    expect(needsOptionChoice({ variant_count: 1, default_variant_name: "Size 5" })).toBe(false);
  });

  it("gates quick add on stock and a default option too", () => {
    const base = { ...multi("1 gallon"), in_stock: true, default_variant_id: "v1" };
    expect(canQuickAdd(base)).toBe(true);
    expect(canQuickAdd({ ...base, in_stock: false })).toBe(false);
    expect(canQuickAdd({ ...base, default_variant_id: null })).toBe(false);
    expect(canQuickAdd({ ...base, default_variant_name: "XS", category: { slug: "clothing-shoes" } })).toBe(false);
  });
});

describe("optionsToChoose", () => {
  const shoes = { variant_count: 12, default_variant_name: "Size 5", category: { slug: "clothing-shoes" } };
  it("leaves sizes and colors unselected so the shopper has to pick", () => {
    expect(optionsToChoose(shoes, [["size", ["Size 5", "Size 5.5", "Size 6"]]])).toEqual(["size"]);
    const tee = { variant_count: 6, default_variant_name: "Black / M", category: { slug: "clothing-shoes" } };
    const options: [string, string[]][] = [
      ["color", ["Black", "Navy"]],
      ["size", ["S", "M", "L"]],
    ];
    expect(optionsToChoose(tee, options)).toEqual(["color", "size"]);
  });
  it("keeps the default for packs and containers", () => {
    const milk = { variant_count: 2, default_variant_name: "Half gallon", category: { slug: "dairy-eggs" } };
    expect(optionsToChoose(milk, [["size", ["Half gallon", "1 gallon"]]])).toEqual([]);
    const pods = { variant_count: 2, default_variant_name: "24 pods", category: { slug: "household" } };
    expect(optionsToChoose(pods, [["variant", ["24 pods", "48 pods"]]])).toEqual([]);
  });
  it("asks only for the color when the other option is a pack size", () => {
    const socks = { variant_count: 4, default_variant_name: "Black / 3 pairs", category: { slug: "clothing-shoes" } };
    const options: [string, string[]][] = [
      ["color", ["Black", "White"]],
      ["pack", ["3 pairs", "6 pairs"]],
    ];
    expect(optionsToChoose(socks, options)).toEqual(["color"]);
  });
  it("skips attributes with a single value and never asks on single-option products", () => {
    expect(optionsToChoose(shoes, [["color", ["Brown"]], ["size", ["Size 5", "Size 6"]]])).toEqual(["size"]);
    expect(optionsToChoose({ ...shoes, variant_count: 1 }, [["size", ["Size 5"]]])).toEqual([]);
  });
});

describe("meaningfulSize", () => {
  it("hides placeholder option names", () => {
    for (const name of ["Each", "Standard", "default", " One size "]) expect(meaningfulSize(name)).toBeNull();
    expect(meaningfulSize("1 gallon")).toBe("1 gallon");
    expect(meaningfulSize(null)).toBeNull();
  });
});

describe("isTopRated", () => {
  it("needs a strong average that holds up over enough reviews", () => {
    expect(isTopRated({ rating_average: 5, rating_count: 8 })).toBe(true); // 4.5
    expect(isTopRated({ rating_average: 4.9, rating_count: 10 })).toBe(true); // 4.5
    expect(isTopRated({ rating_average: 5, rating_count: 3 })).toBe(false); // too few reviews
    expect(isTopRated({ rating_average: 4.7, rating_count: 7 })).toBe(false);
    expect(isTopRated({ rating_average: 4.6, rating_count: 12 })).toBe(false); // 4.36: good, not top
    expect(isTopRated({ rating_average: null, rating_count: 0 })).toBe(false);
  });

  it("ranks many good reviews above a few perfect ones", () => {
    expect(bayesianRating(4.8, 40)).toBeGreaterThan(bayesianRating(5, 3));
  });
});

describe("displayTags", () => {
  const tag = (value: string) => ({ value, label: value });
  const values = (tags: { value: string }[]) => tags.map((t) => t.value);

  it("drops tags another tag already implies", () => {
    // The zero-sugar yogurt: eight tags, several saying the same thing.
    const yogurt = ["lactose-free", "kosher", "fat-free", "sugar-free", "no-added-sugar", "low-sugar", "high-protein", "keto"];
    expect(values(displayTags(yogurt.map(tag)))).toEqual(["lactose-free", "fat-free", "sugar-free", "high-protein", "keto", "kosher"]);
    expect(values(displayTags(["vegan", "dairy-free", "lactose-free", "plant-based"].map(tag)))).toEqual(["vegan"]);
    expect(values(displayTags(["waterproof", "water-resistant", "bluetooth", "wireless"].map(tag)))).toEqual([
      "waterproof",
      "bluetooth",
    ]);
  });

  it("puts catalog-wide tags last and caps the count for cards", () => {
    const cheese = ["gluten-free", "kosher", "organic", "grass-fed"].map(tag);
    expect(values(displayTags(cheese, 3))).toEqual(["organic", "grass-fed", "gluten-free"]);
  });
});
