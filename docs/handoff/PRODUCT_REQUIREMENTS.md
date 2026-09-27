# Product requirements

## Product

Build an original US retail storefront with catalog, search, cart, checkout, account orders, returns, and a voice/text support assistant. Use original branding and licensed/sample product assets. The purpose is a realistic portfolio-quality application and a path to a limited production pilot, not an immediate nationwide retailer.

## People and permissions

There is no guest access. Every visitor must sign in (or create an account) before browsing, searching, using a cart, reading help, or using the assistant. There is no guest cart, no cart merge on sign-in, and no guest order lookup.

The only public pages are: sign-in, create account, privacy, terms, and the accessibility statement.

- Customer: own cart, checkout, order history/status, return quote and confirmation, support chat/voice.
- Staff: review exceptional returns and support cases; inspect audit trail under a separate role.
- Administrator: manage catalog and approved policy versions in a later milestone.

Enforce ownership and role checks on the server for every sensitive endpoint. A client-supplied customer ID is never authorization.

## Core journeys

### Sign-in

The sign-in screen is the first thing a visitor sees. After sign-in, the visitor returns to the page they asked for; the return path must be on our own site. The form works with password managers and allows pasting (WCAG 2.2 3.3.8), and shows the same "wrong email or password" message whether or not the account exists. Sign-in is deliberately simple: the server checks the email and password, then sets a session cookie. There is no rate limiting, CAPTCHA, password reset, or external identity provider.

### Shopping

Filter/search products by title, brand, category, product type, diet and feature tags (for example organic, fat free, sugar free, lactose free, gluten free, vegan), price, and in-stock status; tags can also be excluded. Product page shows variant, images, description, current price and availability, and, for food, nutrition facts, ingredients, and allergens. Tags have fixed meanings (`content/policies/product-labels.md`) that the seed data is tested against. Cart survives refresh and sign-out. At checkout, the server recalculates price, discounts, and stock, and reserves inventory for the payment window. Tax is calculated by Stripe Tax at payment; the checkout quote shows "tax calculated at payment". Redirect to Stripe Checkout for payment collection (cards only). After a verified payment event, show an order with line items and fulfillment status. Handle failed or expired payment without creating a false paid order.

### Returns

The customer can start from the order page or say, "I want to return the headphones from last week." If several items match, show cards and clarify. The backend checks owner, policy version, delivered date, category, quantity, previous returns, condition, and review flags. Present a structured quote with item, quantity, refund amount/currency, any deductions, destination (the original payment method), inspection requirement and expiry. Require explicit confirmation bound to that quote, given by the customer's click or an app-checked spoken "yes"; the assistant never confirms on its own. Create one return and a durable operation ID. Show label/drop-off information only after authorization. Track refund separately and use accurate PENDING/SUCCEEDED/FAILED language. Manual review handles disputed or exceptional cases.

### Sandbox return policy

These fixed rules apply in development and tests. A responsible owner sets real rules before any live pilot.

| Rule | Sandbox value |
|---|---|
| Return window | 30 days after delivery |
| Not returnable | "Final sale" category (for example, gift cards) |
| Needs inspection | "Electronics" category |
| Perishable | Fresh and frozen food (Dairy & Eggs, Fresh Produce, Meat & Seafood, Bakery & Bread, Frozen) isn't sent back: a damaged or spoiled item reported within 7 days of delivery is refunded without a return shipment; after 7 days it isn't refundable |
| Instant refund | Items under $25 that don't need inspection: refund when the carrier scans the package, or a Serigan Mart store scans it at return drop-off |
| Other refunds | Refund after warehouse inspection |
| Restocking fee | None |
| Shipping refund | Only when the whole order is returned |
| Partial returns | Refund = the line's saved price − saved discount + saved tax, per unit |
| Rounding | Split cents evenly across units; the **last** unit returned takes any remainder. For example, a $10.00 discount over 3 units is 333, 333, 334 cents. Refunds for a line can never add up to more than that line's saved total. |
| Refund destination | The original payment method only; no store credit |
| Shipping charge (for reference) | $5.99, free at $35 or more after discounts and before tax |

The customer-facing wording lives in `content/policies/` (versioned, with effective dates, and citable section IDs such as `rr-7-3`); it's what the assistant retrieves and cites. The return policy's front matter carries these rules in machine-readable form, and a unit test checks them against the code. `returns-regulations.md` holds the operating rules every channel follows (AI limits, voice confirmation, escalation) and a map of the US consumer rules the policy is designed around.

### Stores

A store locator lists the Serigan Mart stores around Dallas-Fort Worth (demo locations) on a Google map, with address, phone, hours, open-now status, services, and directions. Any store accepts packaged returns at its return drop-off. Stores don't sell online inventory or hold orders for pickup; online orders ship from one warehouse.

### Help and voice

Public policy questions use approved versioned content and show citations. Current price/availability, tracking, and refund status use authorized live APIs. Voice UI has mic permission, start/stop/mute, captions, interruption, connection status, and text fallback. When the user corrects "the other headphones," stop speech and ask/select the intended item. A dropped voice session can resume the conversation and read the latest return status. Background speech or an uncertain transcript must never trigger confirmation.

## Pages

Sign-in, create account, privacy, terms, accessibility statement, return and refund policy (`/returns-policy`, rendered from `content/policies/returns-and-refunds.md` and `returns-regulations.md`) (all public); and, behind sign-in: home/category, search results, product detail, store locator, cart, checkout/status, account orders, order detail/returns, support panel, basic staff support queue, and accessible error/empty/loading states. The support panel stays usable on mobile. Show a clear indication when sandbox payments, development sign-in, or simulated shipping is in use.

## Accessibility

Target WCAG 2.2 AA.

## Pilot scope

First-party US products, English, USD, one stock location and one shipping/label adapter, responsive web. Seed a large original catalog (about 2,000 products, mostly grocery, with detailed diet, nutrition, and allergen data so the assistant can answer detailed product questions), the policy set, and, for development accounts, an order history that covers every return case. Do not build guest access, store credit, marketplace payouts, real-time store pickup, international taxes, loyalty, personalization, native mobile apps, or nationwide fulfillment in this release.

## Product outcomes

Measure completed purchase rate, return completion without staff, correct item selection, policy answer accuracy, duplicate/unauthorized financial action rate, voice task completion, handoff rate, accessibility, latency, and cost per resolved conversation. See ACCEPTANCE_AND_EVALS.md for proposed engineering targets.
