# ProofBill: Work Division (3 People, 5 Hours)

**Event:** Odoo × Make-A-Ton 9.0, Kochi Hackathon 2026
**Idea:** ProofBill, a subscription platform that audits its own billing (Subscript v2 base + Revenue Leak Detective engine)
**Team:** Frontend · Backend · Integration
**Stack:** Python + Django, server-rendered templates + Bootstrap 5, Chart.js, SQLite (PostgreSQL optional)
**Build window:** 5 hours. Feature freeze at **4:15**; the last 45 minutes are for integration and rehearsal.

---

## 1. Scope for 5 hours / 3 people

That is about 15 person-hours, less than half of the earlier 4-person, 8-hour plan. The goal is **one flawless end-to-end story**, not feature count.

| Must have (never cut) | Cut or stretch |
|---|---|
| Login, 3 roles, password rules, unique email | PDF invoices |
| Customers, products, variants, plans | Bank-statement CSV matching |
| Subscription lifecycle (create, activate, pause, close) | Billing dry-run preview |
| Idempotent billing run and invoices | Quotation templates (basic quotation only if time remains) |
| Payments, partial and full | Email reminders (console backend only) |
| Dashboard from real records | Gateway integration (payments are manual and labelled) |
| Proof Engine: overdue, missed, duplicate | Refunds, proration, discount stacking |
| Revenue at Risk, alert review workflow | Load test (keep indexes and aggregation, skip the 5,000-row run) |
| Seed data and Leak Injection | |

**Stretch, in this order:** one percentage tax and one discount, read-only customer portal, invoice anomaly rule, one-click "generate missing invoice" fix, unmatched-payment rule.

---

## 2. Roles at a glance

| | **Backend** | **Frontend** | **Integration** |
|---|---|---|---|
| Owns | Data model and money logic | Every screen the user sees | Auth, Proof Engine, dashboard numbers, seed data, tests, merges |
| Core deliverable | A correct billing run | A clean, demo-ready UI | A working detection layer and a stable `main` |
| Done when | Invoice then payment works with correct totals and no duplicates | All screens show real data with filters and badges | Leaks are detected, alerts reviewed, dashboard matches raw data |
| Demo role | Billing and payment moments | Dashboard, portal, UI flow | Detection and Revenue at Risk |

---

## 3. Person A: Backend

**Goal:** the shared schema, pricing and billing logic that everything else depends on. This is the critical path.

**Owns (folders):** `catalog/`, `subscriptions/`, `billing/`, `payments/`, `core/` (money, periods, constants)

**Tasks**
1. **Schema first (push by 0:45):** Product, ProductVariant, Plan, Customer link, Subscription, SubscriptionItem, SubscriptionEvent, Invoice, InvoiceItem, Payment, NumberSequence, BillingRun. Money as `DecimalField(12, 2)`. Invoice unique on `(subscription, billing_period_start)` excluding void.
2. `core/periods.py`: next period for daily, weekly, monthly (clamp month ends), yearly (29 Feb clamp).
3. `pricing.calculate()`: base price + variant extra, line subtotal, half-up rounding, discount, tax. Must pass: Rs. 999 + 560 variant, qty 3, 10% discount, 18% tax gives subtotal 4,677.00, discount 467.70, tax 757.67, **total Rs. 4,966.97**.
4. `lifecycle.transition()`: guarded moves, writes a SubscriptionEvent. Closed subscriptions are never billed.
5. `billing.run(run_date)`: loop due active subscriptions, create one invoice per period, advance `next_billing_date`, catch up missed periods, log a BillingRun. Running it twice changes nothing.
6. `payments.record()`: validates amount and invoice state, updates `amount_paid` and `balance_due`, sets Paid at zero, rejects overpayment, uses an idempotency key.
7. After the gate: one percentage tax rule and a fixed or percent discount.

**Hand-offs:** schema to both teammates by 0:45; stable service functions to Frontend and Integration by 2:30.

---

## 4. Person B: Frontend

**Goal:** a consistent, demo-ready interface on Django templates.

**Owns (folders):** `templates/`, `static/`, form classes, display-only view code

**Tasks**
1. Base layout: sidebar, top bar, role-aware navigation, status badges (green Paid, amber Partially paid, red Overdue, grey Void, blue Active).
2. Login, logout, register and password-reset pages (wired to Integration's auth views).
3. Admin and staff screens: customers, products with variants, plans, subscriptions list and detail with lifecycle buttons and confirmation dialogs (pause, close, void).
4. Invoice list and detail, record-payment form.
5. **Dashboard:** cards for active subscriptions, collected, outstanding, overdue count and amount, Revenue at Risk; one revenue chart; upcoming renewals and overdue tables; tooltips that define each metric.
6. **Alert screens:** table with filters (type, priority, status, customer, date); detail page with explanation, evidence, calculation, recommended action, notes and history; actions Open, In Review, Resolved, Dismiss.
7. Read-only customer portal: own subscriptions, invoices, payments (stretch: request cancel or renew).
8. Empty states, validation messages, mobile-friendly layout.

**Working rule:** build against the shared contract (section 7) with stub data first, then swap in real services as they land. Do not wait for the backend.

---

## 5. Person C: Integration

**Goal:** make the pieces work together, and own the feature that sets the project apart.

**Owns (folders):** `accounts/`, `proofengine/`, `analytics/`, `tests/`, `seed/`, plus the `main` branch

**Tasks**
1. Repo, Django project, settings, `.env.example`, README setup steps, branch rules (hour 0).
2. Custom user model with role, role decorators, scoped querysets, 404 for other customers' records, UUIDs in URLs, password validators (9+ characters, upper, lower, special), admin-only staff creation.
3. **Proof Engine** (deterministic, idempotent, no AI):
   - **Overdue:** confirmed, balance above zero, due date passed; partial payments handled
   - **Missed invoice:** active subscription past `next_billing_date` plus grace days with no invoice for that period
   - **Possible duplicate:** same customer, overlapping period, same amount or lines; flag only, never cancel
   - Stretch: invoice anomaly (recompute with `pricing.calculate()` and compare), unmatched payment
4. Alert and AlertReview models; unique key (rule + object + period) so reruns do not duplicate; statuses New, In Review, Resolved, Dismissed.
5. **Revenue at Risk:** potential exposure from open missed, duplicate and anomaly alerts, each invoice or period counted once. Overdue stays a separate card (confirmed outstanding). Label it "potential", never "lost revenue".
6. `reports.summary()` dashboard aggregates using database `Sum` and `Count`, not Python loops.
7. **Seed script and Leak Injection** command or button: skip one invoice, duplicate one, backdate a due date, leave a partial payment.
8. Tests: pricing total, billing twice, partial payments, overdue, customer cannot open another customer's invoice or any staff page.
9. Merge owner: review and merge pull requests, keep `main` running, run the full demo path at each gate.

---

## 6. Hour-by-hour plan

| Time | Backend | Frontend | Integration |
|---|---|---|---|
| **0:00–0:30** | Agree contract (section 7), start models | Agree contract, scaffold templates | Repo, project, settings, branches, README |
| **0:30–1:30** | Models and migrations (push by 0:45); `periods` and `pricing` | Base layout, nav, badges, login and register pages | Custom user, roles, decorators, password rules, reset flow |
| **1:30–2:30** | `lifecycle`; subscription create and activate; catalog and customer CRUD views | Product, plan, customer, subscription forms and lists | Alert models, Proof Engine overdue and missed rules |
| **2:30–3:30** | `billing.run`, invoices, `payments.record` | Invoice pages, payment form, dashboard cards | Duplicate rule, Revenue at Risk, dashboard aggregates |
| **GATE 3:30** | Customer, active subscription, invoice, payment, dashboard works end to end. If it fails, everyone helps Backend until it works. | | |
| **3:30–4:15** | Tax, discount, variants; fix action for missing invoice | Alert table, filters, detail and review page; portal | Seed data, Leak Injection, permission tests |
| **FREEZE 4:15** | No new features after this point | | |
| **4:15–4:45** | Bug fixes, rerun billing and payment tests | UI polish, empty states, display bugs | Full-path run, integration bugs, final tests |
| **4:45–5:00** | Rehearse twice, record a backup video, reset demo DB from seed | | |

---

## 7. Shared contract (agree in the first 30 minutes; change only after telling everyone)

**Status constants**
- Roles: `admin`, `staff`, `customer`
- Subscription: `draft`, `quotation`, `confirmed`, `active`, `paused`, `closed`
- Invoice stored: `draft`, `confirmed`, `paid`, `void` (Partially paid and Overdue are **derived**, never stored)
- Alert status: `new`, `in_review`, `resolved`, `dismissed`
- Alert type: `missed_invoice`, `overdue_invoice`, `possible_duplicate`, `invoice_anomaly`, `unmatched_payment`
- Priority: `high`, `medium`, `low`

**Service signatures**

```python
pricing.calculate(items, discount=None, tax_rule=None) -> dict   # lines, subtotal, discount_total, tax_total, total
lifecycle.transition(subscription, action, actor, reason="")
billing.run(run_date=None) -> BillingRun                         # idempotent
payments.record(invoice, amount, method, payment_date, reference="", note="", actor=None, idempotency_key=None)
proofengine.run(today=None) -> list[Alert]                       # idempotent, never duplicates alerts
proofengine.revenue_at_risk() -> Decimal
alerts.update_status(alert, status, actor, note="")
reports.summary(filters=None) -> dict                            # what the dashboard cards show
```

**Minimum URL names:** `login`, `dashboard`, `customers`, `products`, `plans`, `subscriptions`, `subscription_detail`, `invoices`, `invoice_detail`, `payment_record`, `alerts`, `alert_detail`, `portal_home`

**Ownership rule:** only Backend edits models in `catalog`, `subscriptions`, `billing`, `payments`. Only Integration edits `accounts` and `proofengine`. Everyone else asks first.

---

## 8. Dependencies and hand-offs

| Who waits | For what | Needed by |
|---|---|---|
| Frontend, Integration | Backend's pushed schema | 0:45 |
| Integration | `next_billing_date` and Invoice fields for the Proof Engine | 1:30 |
| Frontend | Real `reports.summary()` output (stub until then) | 2:30 |
| Everyone | Working invoice then payment path | Gate at 3:30 |
| Frontend | Alert model and services from Integration | 3:30 |

---

## 9. Team rules

- One feature branch per person (`backend/billing`, `frontend/dashboard`, `integration/proofengine`); never work directly on `main`.
- Merge to `main` at least **every 45 minutes**; `main` must always run. Only Integration merges to `main`.
- Commit messages: `feat:`, `fix:`, `test:`, `docs:`.
- Stage explicit files (`git add path/file`), never `git add .`; never commit `.env`; do not overwrite anyone's unfinished work.
- **Stuck for more than 15 minutes?** Say so in chat immediately.

---

## 10. Cut order and fallbacks

| If this runs late | Fall back to |
|---|---|
| Billing engine | Seed script creates invoices except the one the demo needs; show the billing run for a single subscription |
| Tax and discount | One percentage tax, or skip both |
| Variants | A single extra-price field |
| Customer portal | Read-only, or skip and mention it as planned |
| Anomaly and one-click fix | Drop them; keep missed, overdue and duplicate |
| Charts | Keep the summary cards only |
| Email reset | Console email backend; show the link in the terminal |
| Live demo fails | Play the backup recording on the seeded database |

**Never cut:** subscription creation, invoice generation, payment recording, dashboard, overdue / missed / duplicate alerts, Revenue at Risk, alert review.

---

## 11. Acceptance checklist (run at 4:15–4:45; only report what was actually run)

| # | Check | Owner |
|---|---|---|
| 1 | Duplicate email in a different case is rejected; weak password rejected | Integration |
| 2 | Customer cannot open staff or admin pages; another customer's invoice returns 404; staff cannot create staff | Integration |
| 3 | Pricing example gives exactly Rs. 4,966.97 | Backend |
| 4 | Running billing twice on one date creates one invoice per period | Backend |
| 5 | Paused and closed subscriptions are not billed | Backend |
| 6 | Partial payment then remainder: balance correct, Paid only at zero; overpayment rejected | Backend |
| 7 | Leak Injection creates the faults and the Proof Engine finds each one | Integration |
| 8 | Running detection twice creates no duplicate alerts | Integration |
| 9 | Dashboard numbers equal raw database sums | Integration |
| 10 | Alert can be opened, noted, marked In Review and Resolved; Revenue at Risk updates | Frontend + Integration |

---

## 12. Demo script (5 minutes)

| Time | Presenter | Content |
|---|---|---|
| 0:00–1:30 | Backend | Create plan and customer, activate subscription, run billing twice (no duplicate), record partial then full payment |
| 1:30–3:30 | Integration | Press Leak Injection, run the Proof Engine, show Revenue at Risk, open missed and duplicate alerts, resolve one |
| 3:30–4:30 | Frontend | Live dashboard change, customer portal, access-denied check |
| 4:30–5:00 | Any | Close: "Bill it right. Prove it. Fix it." |

---

## 13. Assumptions

- "5 hours" is total build time, including integration and rehearsal.
- Odoo integration is **not** assumed; confirm with the organisers whether it is expected or scored.
- Payments are manual or simulated and labelled as such. Prices, dates and sample records are illustrative.
