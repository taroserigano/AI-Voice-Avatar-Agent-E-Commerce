---
id: returns-and-refunds
title: Return and refund policy
version: sandbox-2026-09
effective_date: 2026-09-26
applies_to: all orders placed on the Larkspur website
status: sandbox  # fixed rules for development and tests; a policy owner replaces them before any pilot
section_prefix: rr
summary:
  - Most items can be returned within 30 days after delivery, for a refund to your original payment method.
  - "Return shipping is free: use the prepaid label or drop the package at any Larkspur store."
  - Fresh and frozen food isn't sent back. Tell us within 7 days of delivery if it arrived damaged or spoiled and we'll refund it.
  - Gift cards are final sale.
  - Items under $25 are refunded as soon as your package is scanned; electronics after we inspect them; everything else when it reaches our warehouse.
  - You always see the exact refund before you confirm, and nothing is returned until you confirm.
# Machine-readable rules. services/commerce/tests/unit/test_policy_documents.py checks them
# against the returns engine and the category data, so this text can't drift from the code.
rules:
  return_window_days: 30
  perishable_report_days: 7
  instant_refund_under_minor: 2500
  quote_valid_minutes: 15
  restocking_fee_minor: 0
  shipping_minor: 599
  free_shipping_at_minor: 3500
  refund_destination: original_payment_method
  store_credit: false
  exchanges: false
  policy_classes:
    final_sale: [gift-cards]
    inspection: [electronics]
    perishable: [dairy-eggs, produce, meat-seafood, bakery, frozen]
---

# Return and refund policy

This policy explains what you can return, how to return it, and how much you get back and when.
It applies to every order placed on the Larkspur website and shipped to you. It's the same
policy whether you return an item from **Orders & returns**, with Steph (our shopping
assistant), with Xana (our customer-support assistant), or with a member of our team.

> **Sandbox notice.** Larkspur is a demonstration store. This is a sandbox policy used to build
> and test the site. No real orders, payments, or refunds take place, and nothing here is legal
> advice.

## 1. Words we use

### 1.1 Delivery date

The day the carrier marks your order delivered. Every return window counts from the delivery
date, not the day you placed the order. The delivery date is shown on the order in
**Orders & returns**.

### 1.2 Line and unit

A **line** is one product on your order, in one size or color, in some quantity (for example
"3 × Everyday Cotton Tee, Medium"). Each item in that quantity is a **unit**. You can return
some or all units of a line.

### 1.3 Return quote

Before you confirm a return, we show a **quote**: the exact units, the exact refund in dollars
and cents, how the refund will be timed, and where it goes. A quote is valid for **15 minutes**.
If it expires, or anything about the order changes, we make a new one.

### 1.4 Item types

For returns, every product belongs to one of four groups, based on its department:

| Group | Departments | What's different |
|---|---|---|
| Standard | Pantry, Snacks, Beverages, Household, Health & Wellness, Baby, Pet, Home & Kitchen, Clothing & Shoes, Outdoor, Sports, Toys, Beauty, Office | Returnable within 30 days |
| Inspected | Electronics | Returnable within 30 days; refunded after inspection |
| Perishable | Dairy & Eggs, Fresh Produce, Meat & Seafood, Bakery & Bread, Frozen | Not sent back; refunded if reported within 7 days |
| Final sale | Gift Cards | Not returnable |

The product page shows which group an item is in, under **Returns**.

## 2. How long you have

### 2.1 Standard and inspected items

You can start a return up to **30 days after the delivery date**. Day 1 is the day after
delivery. On day 31 the item can no longer be returned.

### 2.2 Perishable items

Fresh and frozen food can't be returned for a change of mind. If it arrives damaged, spoiled,
thawed, or past its date, tell us **within 7 days after the delivery date** and we'll refund it
without asking you to send anything back.

### 2.3 Orders that haven't been delivered

An item can't be returned until its order is delivered. If your order is late or missing, see
[section 8](#rr-8).

### 2.4 No extensions in chat

Neither our assistants nor our team can extend a return window in a conversation. If you think
your situation needs an exception (for example, a recall or a delivery problem), ask for a person
and we'll open a support case ([section 16](#rr-16)).

## 3. What you can't return

### 3.1 Gift cards

Gift cards are **final sale**. They can't be returned, exchanged, or refunded, and they can't be
redeemed for cash except where the law requires it.

### 3.2 Perishables for a change of mind

See [section 2.2](#rr-2-2). Perishables are refunded only for a quality problem reported within 7
days.

### 3.3 Items already returned

You can't return more units of a line than you bought. Units that are already on their way back
to us, or already refunded, count as returned. A return we rejected or you canceled doesn't
count, so you can start it again if you're still within the window.

### 3.4 Items not bought from Larkspur online

This policy covers only items bought on the Larkspur website. Larkspur stores accept return
packages for online orders at their drop-off counters, but they can't take back items bought
somewhere else.

## 4. Condition of returned items

### 4.1 Standard items

Send items back with everything that came in the box: parts, accessories, manuals, and free gifts
that came with the purchase. Opened items are fine. Please don't send items that are dirty,
damaged by use, or have had parts removed.

### 4.2 Electronics

Electronics are inspected when they arrive ([section 11.3](#rr-11-3)). To pass inspection an item
must include its accessories and cables, show no damage beyond normal handling, and be reset to
factory settings with your accounts signed out. Please remove any personal data before sending a
device back; we erase devices we receive but can't protect data you leave on them.

### 4.3 Damaged, defective, or wrong items

If an item arrives damaged, doesn't work, or isn't what you ordered, return it the same way as any
other item and choose the matching reason. The refund is the same as for any return, the return
label is free, and a wrong or damaged item is never counted as abuse
([section 15](#rr-15)). For fresh and frozen food, see [section 2.2](#rr-2-2).

## 5. How to start a return

### 5.1 Three ways, one policy

- **Orders & returns:** open the order, choose **Start a return**, and choose the item.
- **Steph:** open **Ask Steph** at the bottom of any page and say which order and item.
- **Xana:** open **Support** and talk (or type) to Xana, our customer-support assistant.

All three use the same rules and show you the same quote. Steph and Xana are AI assistants; they
look up your order and ask the policy engine what you're owed. They never decide eligibility or
amounts themselves ([returns regulations, section 3](/returns-policy#rg-3)).

### 5.2 What we ask you

Which order, which item, how many units, and why you're returning it (for example: damaged,
doesn't work, wrong item, not as described, spoiled or past its date, missing parts, no longer
needed, found a better price, arrived too late). The reason helps us improve; for perishables it
must be a quality problem.

### 5.3 Confirming

We show the quote, and nothing is returned until **you** confirm it:

- On screen, with the **Confirm return** button.
- By voice with Xana, only after she has read the whole quote back to you and you clearly say yes
  (for example "yes, confirm the return"). A hesitant or unclear answer ("mm-hmm", "I guess",
  "yes but…") isn't a confirmation; Xana will ask again or show you the button.

Once you confirm, we send your return label (unless nothing has to be sent back) and the return
appears in **Orders & returns**.

### 5.4 Canceling a return

You can ask to cancel a return any time before the package is scanned by the carrier or a store.
After it's scanned, the return continues.

## 6. Sending it back

### 6.1 Free return label

Return shipping is free. Print the prepaid label (or show the QR code) and drop the package with
the carrier.

### 6.2 Store drop-off

You can also drop a labeled package at the return drop-off counter of any Larkspur store around
Dallas–Fort Worth ([store locator](/stores)). A store scan counts exactly like a carrier scan. Stores
send packages on to our warehouse; they can't give refunds in cash or on the spot.

### 6.3 One package per return

Pack every item from one return in one package with its label. If you're returning items from two
orders, start two returns.

### 6.4 Perishables

Perishable refunds need no package. Please dispose of spoiled food safely.

## 7. How much you get back

### 7.1 The price you paid

For each unit you return you get back what you paid for it: the unit price, **minus** that unit's
share of any discount on the line, **plus** that unit's share of the sales tax you paid.

### 7.2 Splitting discounts and tax

When a line has more than one unit, its discount and tax are split evenly in whole cents. If a
split leaves extra cents, the **last** unit returned takes them. For example, a $10.00 discount on
3 shirts is split $3.33, $3.33, and $3.34: return one shirt and $3.33 comes off its price; return
the third later and $3.34 comes off. The refunds for a line never add up to more than you paid for
that line.

### 7.3 Shipping charges

Standard shipping is $5.99 (free on orders of $35 or more after discounts, before tax). We refund
the shipping charge only when you return **every unit of every item** on the order, across one or
more returns. Returning part of an order never adds a shipping charge, even if what you keep would
have been under $35.

### 7.4 No fees

There's no restocking fee and no return shipping fee.

### 7.5 Tax-exempt items

Items that weren't taxed (for example most grocery food and gift cards in Texas) have no tax to
refund.

### 7.6 Worked example

You bought 3 tees at $15.00 each with a $10.00 discount on the line and $2.89 tax on it, plus a
$4.00 notebook with $0.33 tax. That's $39.00 after the discount, so shipping was free, and the
order total was $42.22.

The line's discount splits $3.33, $3.33, $3.34 and its tax splits $0.96, $0.96, $0.97.

| You return | Refund |
|---|---|
| 1 tee | $15.00 − $3.33 + $0.96 = **$12.63** |
| The other 2 tees, later | ($15.00 − $3.33 + $0.96) + ($15.00 − $3.34 + $0.97) = **$25.26** |
| The notebook | $4.00 + $0.33 = **$4.33** |

The three refunds add up to exactly the $42.22 you paid.

## 8. Late, missing, and canceled orders

### 8.1 Late orders

We ship most orders within 1 business day. If we can't ship by the time we promised, we'll tell
you, give you a new date, and let you cancel for a full refund instead.

### 8.2 Missing packages

If tracking hasn't moved for 7 days, or says delivered but you can't find the package, ask for a
person. We'll check with the carrier and either send a replacement or refund you in full,
including shipping.

### 8.3 Canceled orders

A canceled order can't be returned because nothing was delivered; any payment taken for it is
refunded in full to the original payment method.

## 9. Gifts

Returns can be started only by the account that placed the order, and refunds go to that
account's original payment method. If you received a gift, ask the person who sent it to start
the return.

## 10. Exchanges and price changes

### 10.1 No exchanges

We don't do direct exchanges. Return the item for a refund and place a new order for the size or
color you want.

### 10.2 No price adjustments

If an item's price drops after you buy it, we don't refund the difference. You can return it
within the window and buy it again at the new price.

## 11. When your refund is issued

### 11.1 Refund timing

| Item | Refunded |
|---|---|
| Under $25 per unit, not electronics | **Instantly**, when the carrier or a store scans your package |
| $25 or more per unit, not electronics | When the package **arrives at our warehouse** and is checked in |
| Electronics | **After inspection**, usually 3–5 business days after the package arrives |
| Fresh and frozen food | **Right away** when you report the problem; nothing is sent back |

When one return includes items with different timings, each item is refunded on its own schedule.

### 11.2 Where the refund goes

Refunds always go back to the **original payment method** (the card you paid with). We don't issue
store credit or cash, and we can't send a refund to a different card. If that card has been
closed, your bank will usually pass the refund on to your new card; if not, ask for a person.

### 11.3 Inspection outcomes

When an inspected item arrives we check it against [section 4.2](#rr-4-2):

- **Passed:** refunded in full.
- **Failed** (for example damage from use, missing accessories, a device still locked to an
  account, or a different item in the box): not refunded. We'll tell you why and offer to ship
  the item back to you at no cost, or you can ask a person to review the decision.

### 11.4 When you'll see it

After we issue a refund, your bank usually shows it within 3–10 business days. The refund appears
as a credit from Larkspur on your card statement.

### 11.5 Refund status

You can see each return's status in **Orders & returns** or by asking Steph or Xana:
**Requested → Authorized → In transit → Received → Inspected → Closed**, with **Refund:
pending → succeeded**. A return can also be **In review** (a person is checking it),
**Rejected**, or **Canceled**. If a refund fails at the bank we retry, and if it still fails a
person contacts you.

## 12. Recalls and warranties

### 12.1 Product recalls

If a product you bought from us is recalled, follow the recall's instructions. Recall refunds and
replacements aren't limited by the 30-day window; ask for a person and we'll handle it as the
recall directs.

### 12.2 Manufacturer warranties

Many products come with a manufacturer's warranty. After the return window, warranty claims go to
the manufacturer. Nothing in this policy limits your warranty rights or the rights the law gives
you.

## 13. Payment disputes

If you dispute a charge with your card issuer, we pause any return refund for the same charge
until the dispute is resolved, so you're never refunded twice. Please try a return first; it's
usually faster.

## 14. Your privacy

To handle a return we use your order details, the reason you give, and, for voice conversations,
a transcript of what you said. Audio is turned into text by our speech providers and not stored.
See the [privacy notice](/privacy).

## 15. Fair use

We may decline returns that look like abuse, for example returning used items as new, returning
a different item than the one bought, or an unusually high rate of returns with no reason given.
If we do, we'll tell you why, and a person will review the decision if you ask. Returning damaged,
defective, or wrong items is never counted against you.

## 16. Getting help

### 16.1 Ask for a person

At any point you can ask Steph or Xana for a person. We'll open a support case with your
conversation attached, so you don't have to repeat yourself, and reply within 1 business day.

### 16.2 Disagreeing with a decision

If you disagree with a return decision, ask for a review. A person who wasn't involved in the
first decision will look at it and explain the outcome.

## 17. Changes to this policy

We may change this policy. Each version has a version name and an effective date at the top of
this page. A return is handled under the policy in effect on the day the order was placed; if a
later version is better for you, we apply that one.
