# ProofBill: Subscription Billing That Audits Itself

*Odoo × Make-A-Ton 9.0, Kochi Hackathon 2026 · Challenge: Subscription Management System · 4 members, 8 hours*

**Tagline: Bill it right. Prove it. Fix it.**

## 1. The problem

Brightloop Software runs subscriptions on spreadsheets: renewals are remembered by hand, invoices are typed by hand, payments are matched by scrolling bank statements, and revenue reports arrive quarterly. The result is missed renewals, wrong or missing invoices, late payments and no live view of recurring revenue.

A conventional subscription system fixes the manual work but still asks the business to trust that its billing engine did everything correctly. When an invoice is skipped, duplicated or mispriced, nobody finds out until the money is already missing.

## 2. Our idea

ProofBill is a complete subscription-management platform (customers, products and variants, plans, quotations, subscriptions, recurring invoices, taxes, discounts, payments, dashboard and customer portal) built around one new principle: **every billing outcome is independently verified against what should have happened.**

The platform keeps two views of the truth for every subscription:

- **Expected:** a billing calendar computed from the plan, start date, frequency and lifecycle state: which periods should be invoiced, for how much, and by when.
- **Actual:** the invoices and payments that really exist.

A deterministic **Proof Engine** continuously reconciles the two. Any gap becomes an explainable alert with evidence, a financial amount and a one-click, human-approved fix. The business moves from *"we think billing is right"* to *"we can show it is right, and we are told when it is not."*

## 3. What makes it different

1. **Detect → Explain → Fix in one flow.** Most leak tools stop at a report. Each ProofBill alert shows what happened, why it was flagged, the amount affected and a guarded action button (for example: *Generate the missing invoice for 1–31 Oct*, *Void duplicate (reason required)*, *Link payment to INV-0042*). Every fix runs through the same service layer as normal operations and is written to the audit log.
2. **Preview before you bill.** A billing dry run shows exactly which invoices will be created, with tax and discount breakdowns, and flags anything suspicious (zero total, missing customer data, large change from last period) *before* the run is committed. Prevention first, detection as the safety net.
3. **Revenue at Risk, defined honestly.** One headline figure of potential exposure, kept separate from confirmed outstanding balances, with no double-counting when several alerts concern the same invoice. Estimates are never labelled as lost revenue.
4. **Bank-statement reconciliation.** Upload a bank CSV; the engine suggests matches between statement lines and open invoices (customer, amount, date, reference) and flags unmatched payments for staff confirmation. This replaces the "scrolling bank statements" pain directly.
5. **Self-checking invoices.** Every invoice total is recomputed by the single pricing calculator and compared with the stored figures, so tax, discount and rounding errors are caught by verifiable rules rather than guesses.
6. **Explainable prioritisation.** Alerts are ranked by amount, days overdue, subscription status and renewal urgency using transparent rules (High, Medium, Low), not an opaque score.
7. **Leak Injection demo mode.** A built-in control creates realistic faults (skip an invoice, duplicate one, mis-price one, add an unmatched payment) so judges can watch the engine catch them live on real database records.

## 4. Functional scope (covering the official brief)

| Brief requirement | ProofBill coverage |
| --- | --- |
| Admin, Staff, Customer roles; unique email; strong password; email reset; only admin adds staff | Custom user model with role, per-view role checks, customer data scoped to the owner, 404 on others' records |
| Products with cost and sales price; variants with extra price | Product and ProductVariant models; pricing calculator adds the variant extra |
| Plans: daily, weekly, monthly, yearly; minimum quantity; availability dates; close, pause and renew rules | Plan model with explicit auto-close, early-close, pause and renewal flags |
| Quotation templates, subscription lifecycle Draft → Quotation → Confirmed → Active → Closed | Quotation converts to subscription; all changes through one lifecycle service with event history |
| Automatic recurring invoices; no duplicate or skipped periods | Idempotent billing run with a uniqueness rule on subscription and period start, catch-up of missed periods |
| Taxes and discounts (fixed or percent, limits, dates, scope) | Admin-configured tax rule; fixed and percentage discounts with usage limits |
| Payments against invoices; paid, outstanding, overdue | Payment service with partial payments; Overdue derived from due date and balance |
| Dashboard and reports; pages under 2 seconds | Database-aggregated metrics, indexes and pagination, timed on a seeded dataset |
| Customer portal | View own plans, invoices and payments; request cancel or renew |

## 5. Proof Engine rules (all deterministic)

- **Missed invoice:** active, billable subscription whose expected period has no invoice after the grace days.
- **Overdue invoice:** confirmed, balance above zero, due date passed; partial payments handled.
- **Possible duplicate:** same customer, overlapping period, matching amount or lines; flagged for human review, never auto-cancelled.
- **Unmatched payment:** payment or bank line with no confident invoice link; match suggestions shown.
- **Invoice anomaly:** stored totals differ from the recomputed totals, zero or negative totals, missing customer or lines.
- **Renewal attention:** expiry approaching with no renewal action or next invoice.

Alerts are de-duplicated across repeated runs, carry review notes and a status (New, In Review, Resolved, Dismissed), and never change financial records without a confirmed human action.

## 6. Technical approach

- **One codebase:** Python + Django, server-rendered templates with Bootstrap 5, Chart.js for charts. No separate React and API layer, which removes the largest integration risk in eight hours.
- **Database:** SQLite for the build (partial unique constraints are supported); PostgreSQL if time allows.
- **Service layer:** views stay thin; `pricing`, `lifecycle`, `billing`, `payments` and `proof_engine` services are shared by every screen, so money is never calculated two ways.
- **Money rules:** Decimal arithmetic only, half-up rounding per line, invoice lines snapshotted so later price changes never rewrite history.
- **Billing trigger:** a management command (`run_billing`) plus a button; no task queue.
- **AI is optional:** it may rephrase an alert or draft a payment follow-up for staff approval, using only verified fields. The engine works fully without it.

## 7. Eight-hour plan for four members

| Member | Ownership |
| --- | --- |
| 1 | Project setup, custom user and roles, products, variants, plans, customers, audit log |
| 2 | Subscriptions and lifecycle service, pricing, billing run, invoices, payment service |
| 3 | Proof Engine, alerts and review flow, Revenue at Risk, bank CSV matching, one-click fixes |
| 4 | Templates and dashboard, customer portal, seed data, Leak Injection mode, demo rehearsal |

| Hours | Milestone |
| --- | --- |
| 0–1 | Repo, shared models, status constants and service signatures agreed |
| 1–3 | Auth, roles, catalogue, plans, customers, subscription lifecycle |
| 3–5 | Pricing, billing run, invoices, payments (gate: invoice then payment works end to end) |
| 5–6.5 | Proof Engine: overdue, missed, duplicate, anomaly; alert review; Revenue at Risk |
| 6.5–7.5 | Dashboard, seed data, Leak Injection, bank CSV import if time allows |
| 7.5–8 | Rehearsal, backup recording, local fallback |

**Priorities.** *Must have:* auth and roles, products and plans, subscriptions, billing run, payments, dashboard, overdue, missed and duplicate alerts, Revenue at Risk, alert review. *Should have:* tax, discounts, variants, portal, anomaly check, one-click fixes. *If time remains:* bank CSV matching, billing dry run, PDF invoice, quotation templates, email reminders. Never cut subscription creation, invoice generation, payment recording or the dashboard.

## 8. Demo story (5 minutes)

1. Create a plan, register a customer and activate a subscription.
2. Run billing; show tax and discount; run it again to show **no duplicate**.
3. Record a partial payment, then the remainder; the dashboard updates live.
4. Press **Leak Injection**: a skipped invoice, a duplicate and an unmatched payment appear.
5. Run the Proof Engine: the dashboard shows **Revenue at Risk**; open each alert to see evidence, calculation and recommended action.
6. Apply a one-click fix, mark an alert Resolved, and watch the figures change.
7. Show the customer portal and an access-denied check.

## 9. Impact

The business gets a single system that runs subscriptions and watches its own billing. Staff spend time on exceptions instead of spreadsheets, finance sees a trustworthy live revenue picture, and customers get accurate invoices. Because every figure comes from real records and deterministic rules, the results are explainable, auditable and safe to act on.

## 10. Assumptions and open points

- Odoo integration is not assumed; confirm with the organisers whether it is expected or scored.
- Payments are recorded manually or simulated and labelled as such; no live gateway.
- One percentage tax and one discount per invoice in the first build; no proration; full periods only.
- Bank CSV matching and the billing dry run are stretch goals if the core slips.
