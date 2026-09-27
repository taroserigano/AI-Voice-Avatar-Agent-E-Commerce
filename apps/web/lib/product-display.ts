import type { ProductSummary, TagOut } from "@ai-commerce/contracts";

/*
 * How a product summary reads on a card: which size line to show, whether one tap can add it,
 * whether it earns a "Top rated" badge, and which feature tags are worth the space. Shared by
 * the product grid cards, the cart's suggestions, and the product page.
 */

/** Option names that say nothing about size ("Each", "Standard") aren't worth a line. */
export function meaningfulSize(name: string | null | undefined): string | null {
  if (!name) return null;
  return /^(each|standard|default|one size)$/i.test(name.trim()) ? null : name;
}

// --- Quick add or "Choose options" -------------------------------------------------------------

/** Names that are a choice about the item itself: apparel and shoe sizes, bed sizes, fits. */
const CHOICE = [
  /^size\b/i, // "Size 5", "Size 3 (16-28 lb), 62 diapers"
  /^(xxs|xs|s|m|l|xl|xxl|xxxl|\dxl)\b/i, // "XS", "M (8)", "L (10-12)"
  /^(small|medium|large|x-?large|junior|youth|toddler|newborn|official|pee wee|kids'|men's|women's|girls'|boys')\b/i,
  /\b(twin|full|queen|king)\b/i, // bed sizes
  /\//, // "Black / M", "S/M (54-58 cm)", "Standard/Queen"
  /^\d+T\b/, // toddler sizes: "2T", "3T-4T, 24 pants"
  /\d+W x \d+L\b/, // jeans: "32W x 30L"
  /^\d+(\.\d+)?$/, // bare kids' sizes: "10", "12"
  /\bmonths?\b/i, // "0-6 months"
  /\bages?\b/i, // "23 in (ages 7-8)"
  /\bcm\b/i, // helmets, exercise balls
  /\bpair\b/i, // "10 lb pair" of dumbbells
  /\b(GB|TB)\b/, // storage
  /^\$\d/, // gift card amounts
  /^for\b/i, // "For 6.7-inch phones"
];

/**
 * A count of the same thing: "12 eggs", "24 pods", "4-pack", "1 lb bag", "12 mega rolls",
 * "1 cu ft bag" (up to two words between the number and the noun).
 */
const PACK =
  /\d[\d,.]*\s*(?:x\s*[\d.]+\s*)?-?\s*(?:[a-z.]+\s+){0,2}(?:packs?|pk|pieces?|pc|count|ct|pairs|rolls?|sheets|pods|bags?|cans?|bottles?|jars?|box(?:es)?|cartons?|cups?|tubes?|bars|batteries|bulbs|eggs|tablets|capsules|softgels|gummies|loads|wipes|pads|tortillas|servings|packets|bins?|reams?|patties|pouch(?:es)?|chews|diapers|pants|refills|blades|cartridges|filters|picks|balls|trays?|tubs?|jugs?|canisters?|clamshells?|containers?|folders|protectors|envelopes|staples|tins?)\b|\bset\b|^(?:half|about|family|case of)\b/i;

/** A net amount: weight or volume. */
const AMOUNT = /\d[\d,.]*\s*(fl\.?\s?oz|oz|lbs?|g|kg|ml|l|liters?|gal(lons?)?|quarts?|qt|pints?|pt|cu ft|sq ft)\b|\bgallon\b/i;

/**
 * Departments where options of different amounts are different products ("8 in" vs "12 in"
 * skillet, "2 qt" vs "3 qt" saucepan, a 10 lb vs a 25 lb kettlebell), not bigger packs.
 */
const MERCHANDISE = new Set(["electronics", "home-kitchen", "clothing-shoes", "outdoor", "sports", "toys", "office"]);

type OptionFacts = Pick<ProductSummary, "variant_count" | "default_variant_name"> & {
  category?: Pick<ProductSummary["category"], "slug">;
};

/**
 * Whether a shopper has to pick an option before this goes in the cart. Products sold in
 * sizes or colors (shoes, tees, sheets, headphones in two colors) do; products sold in bigger
 * or smaller packs of the same thing (milk by the half gallon or gallon, pods by the 24 or 48)
 * don't, and quick add puts the default pack in the cart. Decided from the default option's
 * name, which is all a product summary carries.
 */
export function needsOptionChoice(p: OptionFacts): boolean {
  if (p.variant_count <= 1) return false;
  const name = p.default_variant_name?.trim();
  if (!name) return true;
  if (/^(each|standard|default)$/i.test(name)) return false;
  if (CHOICE.some((re) => re.test(name))) return true;
  if (PACK.test(name)) return false;
  if (AMOUNT.test(name)) return MERCHANDISE.has(p.category?.slug ?? "");
  return true; // colors, shades, designs, lengths
}

/**
 * The options the product page leaves unselected until the shopper picks one, so Add to cart
 * never quietly uses a default size or color. Empty for products the cards can quick add (packs,
 * containers): those start on the default option. `options` lists each attribute with its
 * distinct values; the same rule as the cards is applied to each one, so a "Color, pack" product
 * asks for the color and keeps the default pack. If no single attribute qualifies, every
 * attribute with more than one value is left open.
 */
export function optionsToChoose(p: OptionFacts, options: [key: string, values: string[]][]): string[] {
  if (!needsOptionChoice(p)) return [];
  const multiple = options.filter(([, values]) => values.length > 1);
  const open = multiple.filter(([, values]) =>
    needsOptionChoice({ variant_count: values.length, default_variant_name: values[0] ?? null, category: p.category }),
  );
  return (open.length ? open : multiple).map(([key]) => key);
}

/** One tap can add it: in stock, has a default option, and no choice to make. */
export function canQuickAdd(p: OptionFacts & Pick<ProductSummary, "in_stock" | "default_variant_id">): boolean {
  return p.in_stock && !!p.default_variant_id && !needsOptionChoice(p);
}

// --- Top rated ---------------------------------------------------------------------------------

// Same blend as commerce.catalog.display.bayesian_rating: an average pulled toward the
// catalog-wide 4.0 as if by 8 extra reviews, so five 5-star reviews don't beat forty 4.8s.
const PRIOR_MEAN = 4.0;
const PRIOR_WEIGHT = 8;
/** About the top 2-3% of the catalog: a strong average that holds up over many reviews. */
export const TOP_RATED_SCORE = 4.45;
export const TOP_RATED_MIN_REVIEWS = 8;

export function bayesianRating(average: number | null | undefined, count: number): number {
  if (!count || average == null) return PRIOR_MEAN - 0.5;
  return (average * count + PRIOR_MEAN * PRIOR_WEIGHT) / (count + PRIOR_WEIGHT);
}

export function isTopRated(p: Pick<ProductSummary, "rating_average" | "rating_count">): boolean {
  return p.rating_count >= TOP_RATED_MIN_REVIEWS && bayesianRating(p.rating_average, p.rating_count) >= TOP_RATED_SCORE;
}

// --- Feature tags ------------------------------------------------------------------------------

/** Tags another tag already says: "Sugar free" means no added sugar and low sugar. */
const IMPLIES: Record<string, string[]> = {
  "sugar-free": ["no-added-sugar", "low-sugar"],
  unsweetened: ["no-added-sugar"],
  "fat-free": ["low-fat", "reduced-fat"],
  "low-fat": ["reduced-fat"],
  vegan: ["dairy-free", "plant-based"],
  "dairy-free": ["lactose-free"],
  "pasture-raised": ["free-range", "cage-free"],
  "free-range": ["cage-free"],
  waterproof: ["water-resistant"],
  bluetooth: ["wireless"],
};

/** True of so much of the catalog that they go after the more telling tags. */
const COMMON = new Set(["kosher", "gluten-free", "non-gmo"]);

function implied(tags: Set<string>): Set<string> {
  const out = new Set<string>();
  const visit = (t: string) => {
    for (const i of IMPLIES[t] ?? []) {
      if (!out.has(i)) {
        out.add(i);
        visit(i);
      }
    }
  };
  tags.forEach(visit);
  return out;
}

/**
 * The tags worth showing, most telling first: drops any another one implies ("Low sugar" next
 * to "Sugar free") and moves the catalog-wide ones (Kosher, Gluten free) to the end. The
 * product keeps every tag for filtering; this is only what the chips show.
 */
export function displayTags<T extends Pick<TagOut, "value">>(tags: T[], max?: number): T[] {
  const drop = implied(new Set(tags.map((t) => t.value)));
  const kept = tags.filter((t) => !drop.has(t.value));
  const ordered = [...kept.filter((t) => !COMMON.has(t.value)), ...kept.filter((t) => COMMON.has(t.value))];
  return max === undefined ? ordered : ordered.slice(0, max);
}
