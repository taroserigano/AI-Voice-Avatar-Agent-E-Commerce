import type { Nutrition, ProductDetail } from "@ai-commerce/contracts";
import Link from "next/link";

/** FDA Daily Values for adults and children 4+ (21 CFR 101.9), same units as the rows. */
const NUTRITION_ROWS: { key: keyof Nutrition; label: string; unit: string; indent?: boolean; dv?: number }[] = [
  { key: "calories", label: "Calories", unit: "" },
  { key: "total_fat_g", label: "Total fat", unit: "g", dv: 78 },
  { key: "saturated_fat_g", label: "Saturated fat", unit: "g", indent: true, dv: 20 },
  { key: "sodium_mg", label: "Sodium", unit: "mg", dv: 2300 },
  { key: "total_carbs_g", label: "Total carbohydrate", unit: "g", dv: 275 },
  { key: "fiber_g", label: "Dietary fiber", unit: "g", indent: true, dv: 28 },
  { key: "total_sugars_g", label: "Total sugars", unit: "g", indent: true },
  { key: "added_sugars_g", label: "Includes added sugars", unit: "g", indent: true, dv: 50 },
  { key: "protein_g", label: "Protein", unit: "g", dv: 50 },
];

/** Percent of the Daily Value, rounded to a whole number as on a US label. */
export function percentDailyValue(amount: number, dailyValue: number): number {
  return Math.round((amount / dailyValue) * 100);
}

function NutritionFacts({ nutrition }: { nutrition: Nutrition }) {
  return (
    <div className="mt-3 w-full max-w-sm">
      <table className="w-full border-collapse border-2 border-ink text-sm">
        <caption className="border-2 border-b-0 border-ink px-3 pt-2 text-left">
          <span className="block text-xl font-extrabold">Nutrition Facts</span>
          <span className="block pb-1">Serving size {nutrition.serving_size}</span>
        </caption>
        <thead>
          <tr className="border-t-4 border-ink text-xs">
            <th scope="col" className="px-3 py-1 text-left font-semibold">
              Amount per serving
            </th>
            <th scope="col" className="px-3 py-1 text-right font-semibold">
              % Daily Value*
            </th>
          </tr>
        </thead>
        <tbody>
          {NUTRITION_ROWS.map((row) => {
            const amount = nutrition[row.key];
            const numeric = typeof amount === "number" ? amount : Number(amount);
            return (
              <tr key={row.key} className="border-t border-stone-400">
                <th scope="row" className={`px-3 py-1 text-left font-normal ${row.indent ? "pl-7" : "font-semibold"}`}>
                  {row.label}{" "}
                  <span className="font-normal">
                    {amount}
                    {row.unit ? ` ${row.unit}` : ""}
                  </span>
                </th>
                <td className="px-3 py-1 text-right font-semibold tabular-nums">
                  {row.dv !== undefined && Number.isFinite(numeric) ? `${percentDailyValue(numeric, row.dv)}%` : ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs leading-relaxed text-muted">
        * The % Daily Value tells you how much a nutrient in a serving contributes to a daily diet. 2,000 calories
        a day is used for general nutrition advice.
      </p>
    </div>
  );
}

const linkClasses =
  "font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700";

/**
 * "Specifications" (brand, type, department, then the product's own key facts) and, for food,
 * the nutrition panel, ingredients and allergens. Nothing here is invented: rows come straight
 * from the catalog record.
 */
export function ProductFacts({ product, typeLabel }: { product: ProductDetail; typeLabel: string }) {
  const specs = Object.entries(product.specs);
  return (
    <>
      <section aria-labelledby="specs" className="mt-8 border-t border-line pt-6">
        <h3 id="specs" className="text-lg font-semibold text-ink">
          Specifications
        </h3>
        <table className="mt-3 w-full border-collapse text-sm">
          <caption className="sr-only">Specifications</caption>
          <tbody className="divide-y divide-line">
            <tr>
              <th scope="row" className="w-2/5 py-2.5 pr-4 text-left align-top font-normal text-muted">
                Brand
              </th>
              <td className="py-2.5">
                <Link href={`/search?brand=${encodeURIComponent(product.brand)}`} className={linkClasses}>
                  {product.brand}
                </Link>
              </td>
            </tr>
            <tr>
              <th scope="row" className="py-2.5 pr-4 text-left align-top font-normal text-muted">
                Type
              </th>
              <td className="py-2.5">
                <Link
                  href={`/c/${product.category.slug}?product_type=${encodeURIComponent(product.product_type)}`}
                  className={linkClasses}
                >
                  {typeLabel}
                </Link>
              </td>
            </tr>
            <tr>
              <th scope="row" className="py-2.5 pr-4 text-left align-top font-normal text-muted">
                Department
              </th>
              <td className="py-2.5">
                <Link href={`/c/${product.category.slug}`} className={linkClasses}>
                  {product.category.name}
                </Link>
              </td>
            </tr>
            {specs.map(([k, v]) => (
              <tr key={k}>
                <th scope="row" className="py-2.5 pr-4 text-left align-top font-normal text-muted">
                  {k}
                </th>
                <td className="py-2.5 text-ink">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {product.nutrition || product.ingredients ? (
        <section aria-labelledby="nutrition" className="mt-8 border-t border-line pt-6">
          <h3 id="nutrition" className="text-lg font-semibold text-ink">
            Nutrition and ingredients
          </h3>
          {product.nutrition ? <NutritionFacts nutrition={product.nutrition} /> : null}
          {product.ingredients ? (
            <p className="mt-4 text-sm leading-relaxed">
              <span className="font-semibold">Ingredients: </span>
              {product.ingredients}
            </p>
          ) : null}
          <p className="mt-2 text-sm">
            <span className="font-semibold">Allergens: </span>
            {product.allergens.length > 0 ? `Contains ${product.allergens.join(", ")}.` : "None of the major food allergens."}
          </p>
        </section>
      ) : null}
    </>
  );
}
