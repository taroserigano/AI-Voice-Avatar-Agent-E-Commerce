/**
 * Per-department tint, used for icon tiles and department headers. Class strings are written out
 * in full so Tailwind can see them. Pairs follow docs/design/DESIGN.md: 50/100 surfaces with
 * 700/800 text (text) and 600-700 icons (UI).
 */
export type DepartmentTint = {
  /** Soft surface for a panel or header band. */
  surface: string;
  /** Small icon tile (background + glyph color). */
  tile: string;
  /** Hairline ring that matches the surface. */
  ring: string;
  /** Eyebrow / accent text on the surface. */
  text: string;
};

const tints = {
  brand: {
    surface: "bg-brand-50",
    tile: "bg-brand-100 text-brand-700",
    ring: "ring-brand-100",
    text: "text-brand-800",
  },
  info: {
    surface: "bg-info-50",
    tile: "bg-info-100 text-info-700",
    ring: "ring-info-100",
    text: "text-info-800",
  },
  accent: {
    surface: "bg-accent-50",
    tile: "bg-accent-100 text-accent-800",
    ring: "ring-accent-100",
    text: "text-accent-800",
  },
  success: {
    surface: "bg-success-50",
    tile: "bg-success-100 text-success-700",
    ring: "ring-success-100",
    text: "text-success-800",
  },
  danger: {
    surface: "bg-danger-50",
    tile: "bg-danger-100 text-danger-700",
    ring: "ring-danger-100",
    text: "text-danger-800",
  },
  warning: {
    surface: "bg-warning-50",
    tile: "bg-warning-100 text-warning-800",
    ring: "ring-warning-100",
    text: "text-warning-800",
  },
  neutral: {
    surface: "bg-neutral-100",
    tile: "bg-raised text-neutral-700",
    ring: "ring-neutral-200",
    text: "text-neutral-700",
  },
} satisfies Record<string, DepartmentTint>;

const bySlug: Record<string, keyof typeof tints> = {
  "dairy-eggs": "info",
  produce: "success",
  "meat-seafood": "danger",
  bakery: "accent",
  frozen: "info",
  pantry: "warning",
  snacks: "accent",
  beverages: "info",
  household: "neutral",
  "health-wellness": "success",
  baby: "brand",
  pet: "warning",
  electronics: "info",
  "home-kitchen": "accent",
  "clothing-shoes": "brand",
  outdoor: "success",
  sports: "danger",
  toys: "warning",
  beauty: "success",
  office: "neutral",
  "gift-cards": "brand",
  grocery: "success",
  groceries: "success",
};

export function departmentTint(slug: string): DepartmentTint {
  return tints[bySlug[slug] ?? "brand"];
}
