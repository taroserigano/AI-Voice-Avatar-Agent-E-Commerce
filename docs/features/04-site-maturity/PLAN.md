# 4. A more mature, in-depth site — plan

## Goal

Make the storefront feel like an established retailer's site rather than a demo: depth of
content and information on every page, consistent design, polish in the small states, and
trustworthy detail. Use a group of agents to find what's missing, then improve in rounds.

## When

Last, on the merged branch (this branch + `design-ratings-sitemap`), so the review covers the
other agent's redesign, reviews, order pages, the policy page, Steph, and Xana, and so edits
don't collide with work in progress.

## Method (multi-agent, rounds)

Each round: agents review → findings are verified and ranked → fixes land → the eval agent
re-scores. Stop when the scorecard stops improving or after 3 rounds.

| Agent | Looks at | Output |
|---|---|---|
| **Critique** (×2: shopper, design lead) | Every page at desktop and phone width (Playwright screenshots) against mature retailers' patterns: hierarchy, density, trust signals, merchandising, empty/loading/error states, copy | Ranked findings with screenshots and page paths |
| **Investigator** | Code and data: missing product detail, thin pages, dead ends, inconsistent components, unused data the UI could show (nutrition, specs, reviews, stores), broken links, a11y and performance issues | Ranked findings with file:line |
| **Eval** | A fixed rubric scored 1–5 per page (content depth, visual polish, navigation, trust, accessibility, performance), axe results, Lighthouse-style metrics, e2e pass | A scorecard per round, so progress is measured |

## Likely areas (to be confirmed by the agents)

Home merchandising (departments, deals, seasonal rows, recently viewed), mega-menu navigation
across 21 departments, breadcrumbs, product page depth (gallery, variants, specs table,
nutrition, reviews summary, Q&A with Steph, related items, delivery estimate, return summary),
listing depth (sort, facet counts, chips, pagination), account area (orders, returns, profile),
help center (policy, how returns work, store locator, contact/Xana), footer depth, consistent
empty/loading/error states, and microcopy.

## Guardrails

No new money rules, no guest access, no weaker auth; every change keeps e2e, axe, lint, and
typecheck green; the other agent's files are merged, not overwritten.
