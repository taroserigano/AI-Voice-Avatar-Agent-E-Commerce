---
id: returns-regulations
title: How we handle returns and refunds
version: sandbox-2026-09
effective_date: 2026-09-26
applies_to: every return and refund, in every channel (website, Steph, Xana, staff)
status: sandbox
section_prefix: rg
summary:
  - The same rules apply everywhere, whether you use the website, Steph, Xana, or talk to a person.
  - Eligibility and refund amounts are calculated by our policy engine from your order records, never by an AI model.
  - Nothing is returned or refunded until you confirm a quote yourself, on screen or with a clear spoken yes.
  - Steph and Xana say they're AI assistants, and you can ask for a person at any time.
  - Refunds go only to the original payment method, and never twice for the same item.
---

# How we handle returns and refunds

These are the binding rules Larkspur follows for every return and refund, in every channel: the
**Orders & returns** pages, **Steph** (our shopping assistant), **Xana** (our customer-support
assistant, by text or voice), and our support team. They sit alongside the
[return and refund policy](/returns-policy#rr-1), which says what you're entitled to; this
document says how we make sure you get exactly that.

Each rule is marked **System** when our software enforces it (it can't be skipped), or
**Procedure** when our team follows it.

> **Sandbox notice.** Larkspur is a demonstration store. The legal references below describe how a
> real US retailer's policy would be designed to comply; they're not legal advice, and no real
> transactions take place.

## 1. One policy, every channel

### 1.1 Same answer everywhere

| Rule | Enforced by |
|---|---|
| The website, Steph, Xana, and staff tools all call the same policy engine and get the same eligibility, amount, and timing for the same request. | System |
| No channel can offer terms the policy doesn't allow: no extra refunds, window extensions, store credit, or payments to a different card. | System |
| Exceptions (recalls, lost packages, disputes over an inspection) are handled only through a support case reviewed by a person. | Procedure |

### 1.2 The policy version

Every order line records the policy version in effect when it was bought. Returns use that
version, unless a later version is better for the customer. **System**

## 2. Identity and ownership

| Rule | Enforced by |
|---|---|
| Every return action requires a signed-in customer. There is no guest or anonymous return. | System |
| A customer can see, quote, and return only their own orders. Asking about someone else's order gets the same answer as an order that doesn't exist. | System |
| The customer's identity comes from their signed-in session on our servers. An assistant never chooses, types, or changes whose account it's acting for. | System |
| Staff look up another customer's order only inside a support case, and every look-up is logged. | Procedure |

## 3. Who decides eligibility and amounts

### 3.1 The policy engine decides

Eligibility (window, item group, quantity already returned), the refund amount (price, discount
share, tax share, shipping), and the refund timing are calculated by the policy engine from the
amounts saved on the order at purchase time. **System**

### 3.2 AI models never decide

Steph and Xana use AI models to understand what you're asking and to explain the answer. The
models can't set or change an amount, approve an ineligible item, or override a rule. Any amount
an assistant says aloud or in text comes from the engine's quote, and the quote card on screen is
the authoritative figure. **System**

### 3.3 Understanding your request

To work out what you mean (for example which order, which item, or why you're returning it), our
assistants use language models, including a decision model (TypeSafe Jev) that chooses among a
fixed list of options and reports how sure it is. When it isn't sure enough, the assistant asks you
instead of guessing. These signals only steer the conversation; they never approve a return or set
an amount. **System**

## 4. Quotes and confirmation

### 4.1 Quote first

Before anything is returned the customer sees a quote: the units, the exact refund in cents, the
timing, and the refund destination. A quote is valid for 15 minutes and is tied to exact terms; if
anything changes, a new quote is needed. **System**

### 4.2 Only the customer confirms

| Rule | Enforced by |
|---|---|
| A return is created only when the customer confirms a specific quote, with the **Confirm return** button or a verified spoken yes (section 5). | System |
| AI assistants have no ability to confirm a return. The confirmation step uses a single-use code that never passes through an AI model or the conversation history. | System |
| Confirming the same quote twice (a double click, a retry, a dropped connection) creates one return, never two. | System |
| An expired, altered, or already-used quote can't be confirmed. | System |

### 4.3 After confirming

The customer gets the return label (unless nothing is sent back), and the return appears in
**Orders & returns** with its status. **System**

## 5. Voice conversations with Xana

### 5.1 Before the microphone turns on

Xana's page says that Xana is an AI assistant, that speech is sent to our speech-recognition and
speech-synthesis providers to be converted, that audio isn't stored, and that a text transcript
is saved with the conversation. The microphone starts only after the customer chooses to start.
**System**

### 5.2 Spoken confirmation

A spoken answer counts as confirming a return only if **all** of these are true. Otherwise Xana
asks again or shows the Confirm button. **System**

1. Xana has read the quote back in full: the item, the quantity, the refund amount, and that it
   goes to the original card. Interrupting the read-back cancels it.
2. The customer's answer is a complete, final turn (not a partial transcript).
3. The answer is a clear yes, such as "yes", "yes, confirm", or "confirm the return". Fillers and
   hedges ("mm-hmm", "uh-huh", "I guess", "maybe", "yes but…"), questions, and background speech
   don't count.
4. The answer isn't too short or too quiet to be sure of.
5. When the decision model is on, it must also judge the answer to be a clear confirmation
   (probability at least 0.90). It can only block a confirmation, never cause one.

### 5.3 Text is always available

Every voice feature has a text equivalent on the same page, and every confirmation can be made
with the on-screen button. **System**

## 6. What our AI assistants may and may not do

| Steph and Xana may | Steph and Xana may not |
|---|---|
| Look up the signed-in customer's orders, returns, and refund status | Look up any other customer's information |
| Explain the policy and cite its sections | State a policy that isn't in the approved documents; if unsure, they say so or offer a person |
| Ask which item or order the customer means | Guess between two matching items; they show both and ask |
| Prepare a quote from the policy engine | Change an amount, waive a rule, or promise an exception |
| Read back a quote and ask for confirmation | Confirm a return, issue a refund, or cancel one |
| Open a support case for a person | Ask for card numbers, passwords, or one-time codes |
| Follow the customer's instructions | Follow instructions found inside product descriptions, reviews, policy text, or tool results |

Assistants always say they're AI assistants when asked, and introduce themselves as assistants.
**System**

## 7. Escalation to a person

### 7.1 When we hand off

An assistant offers a person when the customer asks for one; when the customer seems upset or
repeats the same problem; when a case needs an exception (recall, missing package, inspection
dispute, closed card, suspected fraud); or when the assistant can't answer from the approved
documents. **System** (offer) / **Procedure** (handling)

### 7.2 Support cases

A support case includes the conversation transcript and the order, so the customer doesn't have to
repeat themselves. We reply within 1 business day. A decision the customer disagrees with is
reviewed by someone who wasn't involved in it. **Procedure**

## 8. Refunds

| Rule | Enforced by |
|---|---|
| Refunds go only to the original payment method. No cash, store credit, or other card. | System |
| Each refund has a unique operation ID, so a retry after a timeout can never refund twice. | System |
| Before retrying an uncertain refund, we check the payment provider's record first. | System |
| A refund that fails at the bank is retried; if it still fails, a person contacts the customer. | Procedure |
| While a card dispute (chargeback) is open for a charge, return refunds on that charge are paused. | Procedure |
| Refund amounts are reconciled against the payment provider daily; any mismatch is investigated the same day. | Procedure |

## 9. Records and privacy

### 9.1 What we keep

Every quote, confirmation, return, and refund is recorded with who did it, when, the policy
version, and the amounts, and kept for at least 4 years, in line with Texas sales-tax record
rules. **System**

### 9.2 What we don't collect

We never ask for or store full card numbers; payments and refunds go through our payment provider.
Assistants are given only what they need for the request (order lines, dates, amounts), not
addresses or payment details. Monitoring data is scrubbed of emails, names, addresses, and
card-like numbers. **System**

## 10. Regulatory map

How this policy is designed to meet the US consumer rules that apply to an online retailer based
in Texas that ships nationwide.

| Rule | What it requires (summary) | How we meet it |
|---|---|---|
| FTC Mail, Internet, or Telephone Order Merchandise Rule (16 CFR Part 435) | Ship within the time stated (or 30 days if none); if delayed, tell the customer and offer to cancel; refund canceled orders promptly | Stated shipping times and late-order handling ([rr-8.1](/returns-policy#rr-8-1)); delay notices with a cancel option; canceled orders refunded in full ([rr-8.3](/returns-policy#rr-8-3)) |
| Fair Credit Billing Act (15 U.S.C. §1666 and following) | Card holders may dispute billing errors, including goods not delivered as agreed | Disputes are respected; return refunds pause during a dispute so nothing is refunded twice ([rr-13](/returns-policy#rr-13)) |
| Magnuson-Moss Warranty Act (15 U.S.C. §2301 and following) and implied warranties | Written warranties must be clear; implied warranties can't be improperly disclaimed | The policy doesn't limit warranty or legal rights ([rr-12.2](/returns-policy#rr-12-2)) |
| State refund-policy disclosure laws (for example California Civil Code §1723, New York General Business Law §218-a) | Post the refund policy where customers see it before buying | The full policy is public at `/returns-policy`, linked from every product page and the site footer |
| Texas Deceptive Trade Practices Act (Tex. Bus. & Com. Code §17.41 and following) | No false or misleading statements about refunds, warranties, or rights | One approved policy text; assistants may only state what it says and must cite it |
| State sales-tax rules | Tax collected on a refunded sale is returned with the refund | Each unit's tax share is refunded ([rr-7.1](/returns-policy#rr-7-1)) |
| Consumer Product Safety Act (CPSC recalls) | Cooperate with recalls and their remedies | Recall refunds aren't limited by the return window ([rr-12.1](/returns-policy#rr-12-1)) |
| Bot disclosure (for example California Business and Professions Code §17940–17943) | Disclose when an automated bot communicates with a customer to encourage a sale | Steph and Xana introduce themselves as AI assistants ([section 6](#rg-6)) |
| Call-recording and eavesdropping laws (federal one-party consent; all-party consent states such as California Penal Code §632) | Consent before recording a conversation | Notice and an explicit start before the microphone turns on; audio isn't stored ([section 5.1](#rg-5-1)) |
| Americans with Disabilities Act and WCAG 2.2 AA | Accessible service | Every voice feature has a text path; pages target WCAG 2.2 AA ([section 5.3](#rg-5-3)) |
| Card network rules | Refunds go to the card that was charged | Original payment method only ([section 8](#rg-8)) |
| Texas Data Privacy and Security Act and similar state laws | Collect and share only the personal data needed | Data minimization for assistants and monitoring ([section 9.2](#rg-9-2)) |

## 11. Changes

Changes to these rules or to the return policy are reviewed by the policy owner, get a new version
and effective date, and are checked by automated tests against the policy engine before release.
**Procedure**
