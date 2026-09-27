# Assistant conversation scripts

Scripted conversations for the shopping assistant (Milestone 4). They're written now, against
the seed catalog and the development accounts' order history, so the assistant has
known-right answers to be scored against from its first day.

`services/commerce/tests/unit/test_assistant_scenarios.py` checks these files against the
seed data on every test run: every product question must have answers in the catalog (or
none, when a script expects none), and every return outcome is recomputed from the seeded
order and the sandbox return policy. Change the catalog or the orders, and this test tells
you which scripts need updating.

## Files

| File | What it covers |
|---|---|
| `product_qa.jsonl` | Finding products by type, diet tags, allergens, price, and specs; multi-turn refinement; honest "no exact match"; label questions answered from `content/policies/product-labels.md`. |
| `returns.jsonl` | One conversation per seeded order scenario (`services/commerce/src/commerce/seed/orders.py`): inspection, perishables, partial returns with cent rounding, shipping refunds, final sale, not delivered, canceled, another customer's order, prompt injection, "confirm it" in chat; plus policy and store questions. |

Sign in as the `user` of each script (development accounts: `alice@example.com`,
`bob@example.com`). Reseed first (`pnpm db:seed`) so the orders' delivery dates are relative
to today.

## Shape

Each line is one conversation:

```json
{"id": "qa-001", "user": "alice@example.com",
 "turns": [{"user": "find me non fat organic milk and not regular milk",
            "expect": {"action": "search",
                       "search": {"product_type": ["milk"], "tags": ["organic", "fat-free"]},
                       "all_results_match": true}}]}
```

`expect` fields (all optional except `action`):

| Field | Meaning |
|---|---|
| `action` | What the assistant should do this turn: `search`, `product_details`, `answer`, `clarify`, `quote`, `refuse`, `handoff`, `add_to_cart` |
| `search` | The structured filters it should use: `product_type` (any of), `tags` (all of), `exclude_tags` (none of), `max_price_minor`. Same names as `GET /v1/products`. |
| `result_constraints` | Facts every shown product must have, checked from product details: `allergens_none`, `title_contains`, `specs`, `variant_code` |
| `all_results_match` | Every product shown satisfies `search` and `result_constraints` |
| `expect_empty` | No product matches exactly; the assistant must say so rather than pass off a near miss |
| `mentions` / `mentions_any` | Text the reply must contain (all / at least one) |
| `must_not_mention` / `must_not` | Text the reply must not contain / tool actions it must not take (for example `create_return`) |
| `cite` | Policy documents the reply must cite: a document `id` from `content/policies/`, optionally with a section, such as `returns-and-refunds#rr-7-3` (section IDs are the anchors on `/returns-policy`) |
| `uses` | Tools it should call, such as `list_stores` |

Return scripts also have `order` (a scenario key from `seed/orders.py`) and an `outcome`: the
line(s) and quantity, `eligible`, `reason` (`within_window`, `outside_window`, `final_sale`,
`not_delivered`, `canceled`, `perishable_within_7_days`, `perishable_past_7_days`,
`not_owner`, `fully_returned`, `invalid_request`), `refund_timing` (`instant`, `after_inspection`,
`after_receipt`, `no_return_needed`), `refund_minor` (integer cents, including tax and, when
the whole order comes back, shipping), `shipping_refunded`, and `confirmation_required`.

A return script can also have `history`: units already returned earlier
(`returned_units`, by product slug) and that return's `return_status` and `refund_status`.
Those records are seeded by the returns milestone; the outcome accounts for them (a later
unit takes the later cent shares, and nothing left to return is `fully_returned`).

The quote card, not the model's text, is the source of the refund amount; the eval checks the
quote the server produced for the conversation.
