# 7. Return and refund policy — implementation

Status: **done** (2026-09-26)

## Tasks

- [x] `content/policies/returns-and-refunds.md` — full policy in 17 sections, `rr-*` section IDs, `summary:` and machine-readable `rules:` front matter
- [x] `content/policies/returns-regulations.md` — operating rules for every channel (each marked System or Procedure), AI may/may-not table, voice confirmation rules, escalation, refunds, records, regulatory map
- [x] `services/commerce/src/commerce/policies/documents.py` — loader/parser shared with policy search (item 5)
- [x] `services/commerce/tests/unit/test_policy_documents.py` — rules vs category policy classes, shipping, version, the oracle's windows and threshold; worked example recomputed; unique IDs; internal links and eval citations resolve; summary lines are strings
- [x] `apps/web/lib/policy-doc.ts` (+ test) — same parser for the page; `policy-files.ts` reads the files per request
- [x] `apps/web/app/(legal)/returns-policy/page.tsx` — facts, summary, where to start, sticky TOC (details on mobile), both documents, section anchors, print styles
- [x] Legal layout widened (short pages use `LegalArticle`); legal footer nav
- [x] `lib/public-paths.ts` (+ test) — `/returns-policy` public
- [x] Links: shop footer, sign-in legal nav, Terms page, product-page return note (per policy class → section)
- [x] Eval `cite` values use section anchors (`returns-and-refunds#rr-7-3`); README documents it
- [x] e2e `returns-policy.spec.ts`: signed-out load, deep links, axe; product page → policy section
- [x] PRODUCT_REQUIREMENTS.md pointers

## Log

- The money rules are unchanged; the policy explains them in depth and adds process (canceling a
  return, inspection outcomes, missing packages, disputes, recalls, gifts, fair use, escalation).
- Found by the screenshot check: an unquoted `a: b` summary line parsed as a YAML mapping and
  rendered as `[object Object]`; fixed and covered by both parsers' tests.
- Merge follow-ups (other branch) are listed in `06-xana-voice-support/IMPL.md`.
