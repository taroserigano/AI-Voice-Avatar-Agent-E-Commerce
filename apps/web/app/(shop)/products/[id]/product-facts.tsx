import type { Nutrition, ProductDetail } from "@ai-commerce/contracts";

const NUTRITION_ROWS: { key: keyof Nutrition; label: string; unit: string; indent?: boolean }[] = [
  { key: "calories", label: "Calories", unit: "" },
  { key: "total_fat_g", label: "Total fat", unit: "g" },
  { key: "saturated_fat_g", label: "Saturated fat", unit: "g", indent: true },
  { key: "sodium_mg", label: "Sodium", unit: "mg" },
  { key: "total_carbs_g", label: "Total carbohydrate", unit: "g" },
  { key: "fiber_g", label: "Dietary fiber", unit: "g", indent: true },
  { key: "total_sugars_g", label: "Total sugars", unit: "g", indent: true },
  { key: "added_sugars_g", label: "Includes added sugars", unit: "g", indent: true },
  { key: "protein_g", label: "Protein", unit: "g" },
];

function NutritionFacts({ nutrition }: { nutrition: Nutrition }) {
  return (
    <table className="mt-3 w-full max-w-sm border-collapse border-2 border-ink text-sm">
      <caption className="border-2 border-b-0 border-ink px-3 pt-2 text-left">
        <span className="block text-xl font-extrabold">Nutrition Facts</span>
        <span className="block pb-1">Serving size {nutrition.serving_size}</span>
      </caption>
      <tbody>
        {NUTRITION_ROWS.map((row) => (
          <tr key={row.key} className="border-t border-stone-400">
            <th scope="row" className={`px-3 py-1 text-left font-normal ${row.indent ? "pl-7" : "font-semibold"}`}>
              {row.label}
            </th>
            <td className="px-3 py-1 text-right">
              {nutrition[row.key]}
              {row.unit ? ` ${row.unit}` : ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ProductFacts({ product }: { product: ProductDetail }) {
  const specs = Object.entries(product.specs);
  return (
    <>
      {specs.length > 0 ? (
        <section aria-labelledby="specs" className="mt-8 border-t border-line pt-6">
          <h2 id="specs" className="text-lg font-semibold">
            Details
          </h2>
          <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
            {specs.map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="text-muted">{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}
      {product.nutrition || product.ingredients ? (
        <section aria-labelledby="nutrition" className="mt-8 border-t border-line pt-6">
          <h2 id="nutrition" className="text-lg font-semibold">
            Nutrition and ingredients
          </h2>
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

export function ReturnPolicyNote({ policyClass }: { policyClass: ProductDetail["category"]["policy_class"] }) {
  switch (policyClass) {
    case "final_sale":
      return <p className="mt-3 text-sm font-medium text-red-800">Final sale: this item can&apos;t be returned.</p>;
    case "inspection":
      return <p className="mt-3 text-sm text-muted">Returnable within 30 days of delivery; refunded after inspection.</p>;
    case "perishable":
      return (
        <p className="mt-3 text-sm text-muted">
          Fresh food isn&apos;t sent back. If it arrives damaged or spoiled, tell us within 7 days of delivery for a refund.
        </p>
      );
    default:
      return <p className="mt-3 text-sm text-muted">Returnable within 30 days of delivery.</p>;
  }
}
