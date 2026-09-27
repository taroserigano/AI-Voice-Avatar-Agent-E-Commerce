# 7. Return and refund policy, regulations, and page — plan

## Goal

A detailed, versioned return and refund policy that the site shows, Steph and Xana cite, and the
returns engine enforces, plus the "regulations": the binding rules staff and AI agents follow
when handling a return, and how the policy meets US consumer rules. One public page presents it.

## Constraints

- **The numbers don't change.** The sandbox rules Taro accepted (30 days, final sale, electronics
  inspection, perishables 7 days with no return shipment, instant refund under $25, shipping back
  only on a whole-order return, no restocking fee, cent rounding, original card only) are
  enforced by the returns engine and checked by the assistant eval oracle. The detailed policy
  explains them; it adds no new money rules.
- New text-only rules must not contradict code: for example "we pay return shipping" is already
  true (prepaid label), "exchanges aren't offered" is true (no exchange flow).
- It's a sandbox policy for a demo store, and it says so. It is not legal advice.

## Deliverables

1. `content/policies/returns-and-refunds.md` rewritten in depth, with **stable section IDs**
   (`rr-1` … `rr-N`) that citations link to:
   scope and definitions; windows by item type; condition; final sale; perishables; electronics
   and inspection outcomes; damaged, defective, and wrong items; missing and late packages;
   how to start a return (orders page, Steph, Xana); quotes and confirmation (15-minute quote,
   explicit confirm); labels and drop-off; statuses; refund amount (price, discount, tax,
   shipping, rounding); refund timing and method; partial returns; gifts; gift cards;
   exchanges and price changes; recalls and warranties; canceled and undelivered orders;
   rejected returns; abuse and fraud; disputes and chargebacks; changes to the policy;
   contact and escalation.
2. `content/policies/returns-regulations.md` — "How we handle returns": the rules every channel
   (orders page, Steph, Xana, staff) follows:
   identity and ownership; who decides eligibility and amounts (the policy engine, never an AI
   model); quote-bound confirmation; voice confirmation rules (full read-back, clear yes, no
   "mm-hmm"); what AI assistants may and may not do; escalation to a person; recording and
   transcript notice for voice; data handling; service levels; record keeping; plus a
   **regulatory map** (FTC Mail, Internet, or Telephone Order Merchandise Rule, Fair Credit
   Billing Act, Magnuson-Moss Warranty Act, state refund-policy disclosure laws such as
   California Civil Code §1723, Texas DTPA, sales-tax refunds, CPSC recalls, bot disclosure
   such as California SB 1001, call-recording consent, ADA/WCAG) with how the policy complies.
3. Machine-readable front matter on the policy (`rules:` block) with the numeric rules, and a
   unit test that checks them against the eval oracle's constants and the category policy
   classes, so the text and the code can't drift.
4. `/returns-policy` page (public, in the `(legal)` group): version and effective date, a
   summary card ("the short version"), a sticky table of contents, the full policy, the
   regulations document as a second section, anchors for every section, print-friendly
   styles. Rendered from the markdown files at request time, so there's one source of truth.
5. Links: footer/legal links, sign-up page's legal line, product page return note, and the
   existing `ReturnPolicyNote` point to `/returns-policy#…`. Public path allowlist updated.
6. The assistant eval scripts' `cite` fields use the new IDs where they cite sections.

## Out of scope

Changing any money rule; a staff policy editor (Milestone 5).

## Tests

- Unit: policy front matter matches oracle constants and `PolicyClass` of each category; every
  section has an ID; IDs are unique; citations in `evals/assistant/*.jsonl` resolve.
- Web unit: markdown-to-sections parser (IDs, headings, TOC).
- e2e: `/returns-policy` loads signed out, has the TOC, deep link scrolls to a section, axe
  passes; public-path test includes it.
