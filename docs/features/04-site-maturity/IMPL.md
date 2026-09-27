# 4. Site maturity — implementation

Status: done

## Tasks

- [x] Round 0: eval agent records the baseline scorecard (screenshots, rubric, axe)
- [x] Round 1: critique ×2 + investigator → verified, ranked findings → fixes → re-score
- [x] Round 2: same
- [x] Round 3 (if the score still moves)
- [x] Final scorecard and summary in this file

## Scorecards

Rubric 1–5 (5 = on par with a mature national retailer), 19 pages, desktop 1280 and phone 390,
axe WCAG 2.2 AA with reduced motion. Scripts: `scratchpad/eval-round0/` (eval.mjs, steph.mjs,
build-scorecard.mjs).

| Round | Depth | Polish | Wayfinding | Trust | A11y | Mobile | Average |
|---|---|---|---|---|---|---|---|
| 0 (baseline) | 3.42 | 3.16 | 3.37 | 3.21 | 4.79 | 3.38 | **3.55** |
| 1 | 3.95 | 3.84 | 4.21 | 4.05 | 4.95 | 3.88 | **4.15** (+0.60) |
| 2 | 4.11 | 3.95 | 4.47 | 4.32 | 4.95 | 4.25 | **4.34** (+0.19) |
| 3 (final) | 4.16 | 4.05 | 4.47 | 4.37 | 5.00 | 4.25 | **4.38** (+0.04) |

Round 0 lowest: cart wayfinding (checkout disabled), home trust (stale "coming soon" for live
features), electronics product trust/polish (wrong type art, duplicated reviews), sitemap (20
departments show 0 products), support depth (returns only, dev controls visible), activity
polish, electronics facet labels, empty search, 404 (soft 404, duplicate logo). Axe: only
/help/returns (2 contrast nodes).

Round 1 scores use the same cells as Round 0 (21 pages scored in total, 0 axe violations).
Script and screenshots: `scratchpad/eval-round1/`.

Round 2 is scored on the Round 0 cells; all 25 pages also average 4.34. Axe: 0 violations at
1280; at 390 only /returns-policy (scrollable table wrappers not keyboard-focusable, first
scanned at 390 this round). No horizontal overflow at 390 anywhere. No regressions.
Script and screenshots: `scratchpad/eval-round2/`.

## Summary

Three rounds took the site from 3.55 to 4.38 on the same 19-page, 103-cell rubric (all 25 pages:
4.39). Accessibility reached 5.00: axe is clean on every page at 1280 and 390, and no page
scrolls sideways on phones. Round 3 moved the score by only +0.04, so further rounds of polish
won't move it much. What remains needs product decisions or larger features:

1. Checkout is disabled by design (Stripe test mode, tax, webhooks: its own milestone). The cart
   also has no promo code or save-for-later.
2. One illustration per product type; a photo for every product is on the peer branch.
3. Semantic search is unavailable (the shared `.env` names another project's Pinecone index), so
   search is keyword-only: "milk" page 3 still has milk chocolate.
4. No forgot-password flow.
5. Activity history can't be deleted or paused.
6. Stores: no "my store", pickup, or store inventory.
7. No size facet, no product Q&A or compare, and one image per product page.
8. The returns policy is 25k px long on phones.

Round 3 scorecard and screenshots: `scratchpad/eval-round3/`. After the final eval, the 404
illustration became `loading="lazy"`, so pages no longer preload it (the eval flagged a
site-wide console warning).

## Round 3 (medium findings from the Round 2 eval)

| Owner | Scope |
|---|---|
| Lead | Recently viewed price uses the same rule as cards (cheapest in-stock option) |
| Agent J | "Choose options" lands with no size/color preselected; policy table wrappers keyboard-focusable; Steph launcher stops covering content; session guard via a script that also runs on 404s; support layout (phone header, empty space); "397+" rounding; sitemap "1 products" and phone length |
| Agent K | Xana's case follow-up answers about the named order; no-exact-match fallback stops matching sub-word fragments ("ipad" → puppy pads) |

## Round 2 (from the Round 1 eval, 21 verified findings)

Deferred, with reasons: a real checkout (Stripe test mode, tax, webhooks) is its own
milestone, not polish; per-product imagery waits for the peer branch's 396 product photos
(merge after the commit); forgot-password touches auth, which assistant-v2 is about to change.

| Owner | Scope |
|---|---|
| Agent F | Mobile and page bugs: /activity reflow at 390px, /support send keeps the reply in view, compact phone home hero + one-line sandbox banner, real 404 status and titles for bad product/department/order ids, support case "waiting on you" action and page title, /help order statuses match the order UI + help search |
| Agent G | Search: typeahead (suggest endpoint + header UI), honest totals ("400+"), minimum relevance and product-type boost, "no exact matches" notice, department listing above the fold on phones |
| Agent H | Product data and cards: specs per product type for non-food, type-label overrides (Vitamin C, Omega-3), tags reconciled with descriptions and implied tags collapsed on display, size/color products use "Choose options", stricter "Top rated", `meaningfulSize` on the product page, the React key warning |
| Agent I | Orders and stores: shipping address and a printable receipt on order detail, order search/date filter and Buy again on the list, store search by ZIP/city with every store on the map |

## Round 1 (from 4 reviews: shopper, design lead, investigator, eval)

Themes all four agreed on: placeholder imagery (one icon per department), stale "coming soon"
and developer text, missing everyday retail features (quick add, unit price, delivery promise,
buy again, help center), and hand-rolled components.

| Owner | Scope |
|---|---|
| Lead (backend) | Featured sort (in stock + Bayesian rating, varied) instead of alphabetical; Bayesian top rated; type labels ("TV", "USB-C charger"); all types within a department; true search totals; shopper notice only when keyword search fails; `default_variant_*` + `unit_price` on summaries, `unit_price` on variants; `product_id` on order lines; shipping + free-shipping threshold on the cart |
| Lead (assistants) | Order numbers/status/dates match the site; search summary card with applied filters + "See all"; Steph hands returns to Xana (`suggest_xana`); debug panels opt-in (`?debug=1`); simulated speech only with `?voice=sim`; Steph icon-only launcher on phones; mic → Xana; collapsible sources; SVG avatar marks; Xana voice state machine, switches, scrolling captions, conversation-first on phones; `openSteph()` for any page |
| Agent A | Home (present-tense copy, honest trust items, grocery-first hero, fresh picks per department, shop by diet, under $5), auth copy, legal layout session-aware, help hub `/help`, footer, header, department nav, account menu, sitemap, recently viewed |
| Agent B | Product cards (quick add, size, unit price), instant filters + chips, department landing chips, empty search, PDP (delivery estimate, free-shipping line, unit price, navigable tags/brand/type, similar + more from brand, sticky buy box, variant grouping, %DV, specs table, not-found) |
| Agent C | Cart (no disabled CTA, free-shipping bar, delivery estimate, suggestions), orders (one status vocabulary, product links, buy again, help box, returns tab), activity (dedupe, tabs, day groups), stores (design system, overflow bug, today's hours), support page shell (visible h1, your requests, contact block) |
| Agent D | Distinct product-type illustrations (families), no baked-in labels |
| Agent E | Realistic, department-appropriate sample reviews, no duplicates |

## Log

- Round 1, A/B/C landed. Lead follow-ups from their reports:
  - API: live `price_minor`/`currency`/`in_stock` on activity products (recently viewed shows
    price); `estimated_total_minor` on the cart (the browser no longer adds money); `order_id` on
    returns (Returns tab links each return to its order and to Xana with the order);
    `type_label` + `default_variant_*` + `unit_price` on product detail, with one deterministic
    tie-break (stock, price, option order, SKU) shared with listings; `?rating=` filter on
    reviews, and the rating breakdown rows are now toggle buttons.
  - Web: Xana console sticks below the sticky header; support topic links point at anchors
    that exist; contracts export `VariantOut` and `ActivityProduct`.
  - e2e: the "Stores" link is scoped to the header (the footer has one too now).
- Round 1 verified (all five agents in): commerce 6601 passed / 1 skipped, assistant 64,
  web vitest 117, tsc + eslint + ruff + mypy clean, e2e 32/32 after a stack restart. e2e
  updates: Xana heading matched exactly (the conversation panel has its own h2), Steph's
  sources are opened before checking the citation (they're a disclosure now), and the
  floating launcher is located by `aria-controls` (the home page has its own Ask Steph button).
- Round 2, F landed: /activity reflow fixed (390px wide), Xana transcript anchored to the
  bottom with `overflow-anchor: none` (page no longer moves on reply), compact phone hero and
  one-line banner, real 404s (the shop-wide `loading.tsx` committed a 200 before `notFound()`;
  resources are now checked in segment layouts above per-segment skeletons), support retitled
  with "Continue with Xana" for cases waiting on the customer (server builds the follow-up from
  the customer's own case), /help statuses come from `lib/orders.ts`, and a help search.
  Known gap: on 404 responses Next renders the page client-side, so the inline back/forward
  session guard doesn't run there (those pages show no private data beyond the header).
- Round 2, I landed: migration `4b8e2f6a1d93` (nullable `ship_to_*` on orders, sample-flagged
  seeded DFW addresses), `shipping_address` on order detail (owner-scoped; bob gets 404 with no
  address text), server-computed `amount_subtotal_minor` per line, printable
  `/orders/[id]/receipt` with print CSS; orders list search (number or item words) and date
  ranges in the URL, Buy again on delivered cards; stores search by ZIP/city from a built-in DFW
  table (no geocoding calls), "Use my location" (stays in the browser), distance sort, an
  all-stores overview map without a Maps key, and `/stores/[id]` pages. The address is not in the
  assistant's whitelisted order fields, so it never reaches the model.
- Round 2, H landed: `seed/specs.py` + `spec_notes.py` give every non-food product ≥4 specs
  derived from facts it already states (tests check numbers agree with the text); type labels
  keep hyphens and vitamin letters; tags reconciled with descriptions, implied tags collapsed on
  display (stored tags unchanged, so filters still work); size/color products show "Choose
  options" (one link per card); "Top rated" = Bayesian ≥ 4.45 over ≥ 8 reviews (57 products,
  was 466); placeholder sizes hidden on the product page; React key error fixed; 3 gift cards
  added (final sale). Dev DB reseeded through a wrapper that re-indexed OpenSearch only and
  marked the outbox events published, so nothing was written to Pinecone. Semantic vectors for
  ~888 changed products (and the 3 new gift cards) are stale until an approved reindex; keyword
  search covers them meanwhile.
- Round 2, G landed: `GET /v1/search/suggest` (PostgreSQL only, word-prefix match on sanitized
  tokens) + a WAI-ARIA combobox in the header; `SearchMeta.total_capped` ("400+") and
  `exact_match` ("No exact matches for … — showing related items"); engine-agnostic re-ranking in
  `search/ranking.py` (whole-query matches first, no-overlap candidates pruned when real matches
  exist, relative semantic cut `semantic_relative_score=0.8`); `semantic.py` only gained
  `search_scored()`. milk: 400 capped → 107, all milk; "diapers size 3": paper towels #1 → 4
  diapers first; department page's first product at y≈440 on phones (was ≈960).
- Round 2 verified: commerce 12,043 passed / 1 skipped, assistant 64, web vitest 153, tsc +
  eslint + ruff + mypy clean, e2e 32/32 after a clean stack restart.
- Found while verifying: the semantic leg has been unavailable since before Round 0. The shared
  `.env` sets `PINECONE_INDEX_NAME` for another project's index, `config.py` accepts that alias,
  and the app's guard refuses the foreign index (nothing written). Needs a decision (a
  commerce-specific variable, or the Qdrant replacement) — not changed here.
- Round 3, lead: activity products now carry the card price (the default option: cheapest in
  stock, else cheapest) instead of the lowest price of any option, so a sold-out cheap size no
  longer shows on Recently viewed; test sells out a cheaper option and checks the price.
- Round 3, K landed: `get_order_status` also takes the site's 8-character `order_number`,
  resolved inside the customer's own order list (ownership stays server-side; unknown numbers
  get a 404-style error, no card); `_order_for_model` gains a whitelisted `delivery` block
  (status, carrier, service, tracking, dates, latest update — never addresses or payment);
  scripted Xana/Steph answer a named order directly ("About your request CS-48461: Order
  #E2EA6BC6 … should arrive by Tue, Sep 29"); the Xana prompt tells the model to look the order
  up first. Search: keyword fuzziness `AUTO:5,8` with `prefix_length: 1` (query-time only, no
  reindex), a close-spelling rule in ranking, and a typo fallback in typeahead. "ipad" → 0
  results and the empty state; "bananna", "yoghurt", "lactos" still find the right products.
  Trade-off: misspelled words under 5 letters ("mlik") no longer match. Lead: an empty
  candidate list now reports `exact_match: false`.
- Round 3, J landed: size/color products start with nothing chosen and prompt "Select a size"
  (button and phone bar scroll to the picker); policy table wrappers are focusable regions;
  the Ask Steph pill collapses to an icon after scrolling and the footer's last row is padded
  clear; the back/forward session guard moved to the root `<head>` (plus a layout-effect
  fallback for Next's client-rendered 404 shell) and never redirects public pages; the Xana
  card sizes to content; capped totals round down ("350+"); sitemap pluralization and phone
  disclosures. e2e: shopping spec picks a Grip Yoga Mat color before adding (color products now
  start unselected).
- Round 3 verified: commerce 12,061 passed / 1 skipped, assistant 81, web vitest 160, tsc +
  eslint + ruff + mypy clean, e2e 32/32 after a clean stack restart.
