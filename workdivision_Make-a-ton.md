# ProofBill: Work Division (3 People, 5 Hours)

**Event:** Odoo × Make-A-Ton 9.0, Kochi Hackathon 2026
**Project:** ProofBill, a subscription billing platform that audits itself
**Stack:** Python + Django, server-rendered templates + Bootstrap 5, Chart.js, SQLite (PostgreSQL optional)

---

## 1. Scope for 5 hours / 3 people

That is about 15 person-hours, less than half of the original 4-person, 8-hour plan. The scope below is cut to fit. The goal is **one flawless end-to-end story**, not feature count.

### Must have (never cut)
- Login with 3 roles (Admin, Staff, Customer), strong-password rule, unique email
- Customers, products, variants, plans (daily / weekly / monthly / yearly)
- Subscription lifecycle: Draft → Quotation → Confirmed → Active → Closed (plus Pause / Resume)
- Idempotent recurring billing run (no duplicate or skipped periods)
- Invoices with variant price, one tax rule, one discount
- Payment recording (partial and full)
- Financial dashboard from real database records
- Proof Engine: **missed**, **overdue**, **duplicate** alerts
- Revenue at Risk, alert details, review workflow (New, In Review, Resolved, Dismissed)
- Seed data + Leak Injection demo button

### Should have (only if the gates are met on time)
- Invoice anomaly check (recompute total and compare)
- One-click fix for a missed invoice
- Read-only customer portal (own subscriptions, invoices, payments)
- Password reset by email (console backend)

### Cut / out of scope
Bank CSV matching, billing dry run, PDF invoices, Razorpay, email reminders, quotation templates beyond a basic quotation, proration, refunds, discount stacking, AI features, performance load test (keep indexes and aggregation, skip the 5,000-row run).

---

## 2. Roles at a glance

| | Person A: Foundation & Catalog | Person B: Subscriptions & Billing | Person C: Proof Engine & Dashboard |
|---|---|---|---|
| Owns | Users, roles, auth, customers, products, variants, plans, tax and discount rules, audit log, base layout | Lifecycle, pricing, billing run, invoices, payments | Alerts, detection rules, Revenue at Risk, dashboard, seed data, Leak Injection |
| Apps | `accounts`, `products`, `discounts` | `subscriptions`, `billing`, `payments`, `core` (pricing, periods, money) | `audit` (proof engine), `analytics`, `templates/dashboard` |
| Critical path? | Early (everyone needs login and catalog) | **Yes, heaviest** (everything downstream needs invoices) | Starts on contracts, then depends on B's data |
| Demo role | Setup and access-control moments | Billing and payment moments | Detection, Revenue at Risk, dashboard |

**Load balancing:** Person B has the hardest logic, so tax and discount models and CRUD sit with A, and B only *consumes* them in the pricing calculator. Person C builds against a seed script from minute one, so the engine is not blocked waiting for B.

---

## 3. Hour-by-hour plan

### Hour 0:00–0:30 — Together: contracts and setup (everyone, same screen)
- Create the repo, Django project, `.gitignore`, `.env.example`, branches: `feat/foundation`, `feat/billing`, `feat/proof-engine`.
- Agree and commit `core/constants.py` (statuses, roles, cycles) and the **service signatures** in section 5.
- Agree the models in section 4. **Person A merges the shared models to `main` by 0:30.** Others branch from that.
- Rule: only A edits shared models after that; ask in chat first.

### Hour 0:30–2:00 — Build the foundation

| Person | Tasks |
|---|---|
| **A** | Custom user (role field), login / logout / register, password validator (9+ chars, upper, lower, special), role decorator, scoped customer queryset. Base template + sidebar. Product, variant, plan CRUD (admin only). |
| **B** | `core/money.py` (Decimal, half-up), `core/periods.py` (daily, weekly, monthly with end-of-month clamp, yearly with 29 Feb clamp), `pricing.calculate()` with the unit test below. Subscription + SubscriptionItem models, `lifecycle.transition()` with events. |
| **C** | Alert + AlertReview models, `dedup_key` unique constraint. Write `seed_demo` (customers, plans, subscriptions, invoices, payments, including deliberately broken ones). Write the 3 detection rules against seed data using the agreed field names. |

**Pricing unit test (B must pass this):** ₹999 + ₹560 variant, qty 3, 10% discount, 18% tax → subtotal 4,677.00, discount 467.70, tax 757.67, **total 4,966.97**.

### 🚦 Gate 1 at 2:00
Everyone can run the project from `main`, log in as each role, and see products and plans. Seed script runs.

### Hour 2:00–3:30 — Billing, payments, first alerts

| Person | Tasks |
|---|---|
| **A** | Tax rule + discount CRUD (admin). Customer and subscription creation screens (staff). Admin-only staff creation. AuditLog writes for staff creation, price changes, voids. |
| **B** | `billing.run(date)`: for each Active subscription due, create one Confirmed invoice per missed period, a unique constraint on (subscription, period start) excluding void, catch-up loop, `BillingRun` log, `run_billing` command. `payments.record()` with partial payments, overpayment rejection, idempotency key, `balance_due` update. |
| **C** | Run the three rules for real: **overdue** (derived from due date and balance), **missed invoice** (Active, past grace days, no invoice for the period), **possible duplicate** (same customer + overlapping period + same amount). Priority rules and Revenue at Risk calculation. `POST /detections/run` as a button. |

### 🚦 Gate 2 at 3:30
Create a customer → subscription Active → run billing → invoice exists → record payment → balance and status are right. **If this fails, A and C stop their tasks and help B until it works.**

### Hour 3:30–4:30 — Screens and integration

| Person | Tasks |
|---|---|
| **A** | Invoice list/detail and subscription list/detail screens with lifecycle buttons (pause, resume, close with reason). Permission checks: customer gets 404 on another customer's invoice. Read-only portal if time allows. |
| **B** | Fix integration bugs. Quotation → subscription conversion (basic). Billing edge cases: paused or closed not billed, rerun twice gives one invoice. Anomaly check (recompute vs stored total) if P0 is solid. |
| **C** | Dashboard: cards (Revenue at Risk, overdue amount and count, missed, duplicates, unresolved alerts, active subscriptions, collected, outstanding), alert table with filters (type, priority, status), alert detail page (what, why, amount, next step, evidence, notes, history), status changes. Leak Injection button. |

**🧊 Feature freeze at 4:30.** No new features after this. Only bug fixes.

### Hour 4:30–5:00 — Test and rehearse (everyone)
- Run the checklist in section 7.
- Rehearse the demo twice with the roles in section 8.
- Reset the demo database from `seed_demo` and keep it as the starting state.
- Keep a screen recording as a backup in case something fails live.

---

## 4. Shared data contract (agreed at 0:00, owned by A)

**Constants:** roles `admin | staff | customer`; cycles `daily | weekly | monthly | yearly`; subscription `draft | quotation | confirmed | active | paused | closed`; invoice stored `draft | confirmed | paid | void` (Overdue and Partially paid are **derived**, never stored); alert status `new | in_review | resolved | dismissed`; priority `high | medium | low`.

**Key models and fields**

| Model | Fields that others depend on |
|---|---|
| User / Customer | `role`, `email`, `company_name` |
| Product / Variant | `sales_price`, `cost_price`, `extra_price` |
| Plan | `billing_cycle`, `price`, `minimum_quantity`, `available_from/to`, `allow_pause`, `allow_early_close`, `allow_renewal`, `grace_days` |
| Subscription | `number`, `customer`, `plan`, `start_date`, `expiry_date`, `payment_terms_days`, `status`, `next_billing_date` |
| SubscriptionItem | `product`, `variant`, `quantity`, `unit_price` (snapshot) |
| Invoice | `number`, `public_id`, `customer`, `subscription` (nullable), `billing_period_start/end`, `issue_date`, `due_date`, `subtotal`, `discount_total`, `tax_total`, `total`, `amount_paid`, `balance_due`, `status` |
| InvoiceItem | `description`, `quantity`, `unit_price`, `discount_amount`, `tax_rate`, `tax_amount`, `line_total` (all snapshots) |
| Payment | `invoice`, `amount`, `method`, `payment_date`, `reference`, `idempotency_key` (unique) |
| Alert | `rule`, `dedup_key` (unique), `customer`, `subscription`, `invoice`, `amount`, `priority`, `status`, `explanation`, `evidence` (JSON), `recommended_action`, `detected_at` |
| AlertReview | `alert`, `actor`, `from_status`, `to_status`, `note`, `created_at` |

All money is `DecimalField(max_digits=12, decimal_places=2)`. Never floats.

---

## 5. Service signatures (agreed at 0:00)

```python
# core/pricing.py (B)
pricing.calculate(items, discount=None, tax_rule=None) -> dict
# {"lines": [...], "subtotal", "discount_total", "tax_total", "total"}

# core/periods.py (B)
periods.end(start_date, cycle) -> date
periods.next_start(start_date, cycle, anchor_day) -> date

# subscriptions/lifecycle.py (B)
lifecycle.transition(subscription, action, actor, reason="") -> Subscription

# billing/services.py (B)
billing.run(run_date) -> BillingRun          # idempotent
invoices.create_for_period(subscription, period_start) -> Invoice | None

# payments/services.py (B)
payments.record(invoice, amount, method, payment_date,
                reference="", idempotency_key=None, actor=None) -> Payment

# audit/engine.py (C)
proof_engine.run(today) -> list[Alert]       # creates alerts, never duplicates
alerts.update_status(alert, new_status, actor, note="") -> Alert
alerts.apply_fix(alert, actor) -> Invoice | None   # human-confirmed, goes through billing services

# analytics/queries.py (C)
analytics.summary(filters) -> dict           # aggregates in the DB, no Python loops
```

---

## 6. Detection and Revenue at Risk rules (owned by C)

| Rule | Trigger | Priority |
|---|---|---|
| Missed invoice | Active subscription, expected period past `grace_days`, no non-void invoice for that period | High |
| Overdue invoice | Confirmed, `balance_due > 0`, `due_date < today` | High if large or 30+ days, else Medium |
| Possible duplicate | Same customer, overlapping period, same total (or lines), both non-void | Medium |
| Invoice anomaly (stretch) | Stored total ≠ recomputed total; zero/negative total | Medium |

**Rules of the engine**
- Alert `dedup_key` = `rule + object id + period`, so reruns never create duplicates.
- Never auto-delete, cancel or edit. Any fix needs a human click, goes through B's services, and is written to the audit log.
- **Revenue at Risk** = potential exposure from *open* alerts of missed, duplicate and anomaly types, each invoice or period counted once. **Overdue is shown as its own card** (confirmed outstanding) and is not mixed into Revenue at Risk. Label it "potential", never "lost revenue".

---

## 7. Integration and acceptance checklist (hour 4:30)

| # | Check | Owner |
|---|---|---|
| 1 | Duplicate email in different case is rejected | A |
| 2 | 8-char or no-special password is rejected | A |
| 3 | Customer cannot open `/staff/` or `/admin-panel/`; other customer's invoice returns 404; staff cannot create staff | A |
| 4 | Pricing test gives exactly ₹4,966.97 | B |
| 5 | `run_billing` twice on the same date creates one invoice per period | B |
| 6 | Job skipped 3 days then run: each missed period created exactly once | B |
| 7 | Paused and closed subscriptions are not billed | B |
| 8 | Partial payment then remainder: balance correct, Paid only at zero; overpayment rejected | B |
| 9 | Leak Injection creates the faults; Proof Engine finds each one | C |
| 10 | Running detection twice does not duplicate alerts | C |
| 11 | Dashboard numbers equal raw database sums | C |
| 12 | Alert: open, add a note, mark In Review, Resolved; Revenue at Risk updates | C |

Never say a test passed unless it was actually run.

---

## 8. Demo script (5 minutes) and who presents

| Min | Step | Presenter |
|---|---|---|
| 0:00–1:00 | Admin creates a product, variant, plan, tax rule; customer registers; show access-denied check | A |
| 1:00–2:30 | Activate a subscription, run billing (tax + discount shown), run it again: no duplicate, record partial then full payment, dashboard updates live | B |
| 2:30–4:30 | Press Leak Injection; run the Proof Engine; open a missed-invoice alert with evidence and expected amount; show Revenue at Risk vs overdue; explain the duplicate; mark one Resolved and show the dashboard change | C |
| 4:30–5:00 | Wrap-up: how the system proves its own billing; limitations and next steps | All |

---

## 9. Team rules

- **One branch per person**, merge to `main` at every gate and at least once an hour. `main` must always run.
- **Contract first.** Do not rename fields, statuses or function signatures without telling the others.
- Stage files explicitly (`git add path/file`), not `git add .`. Never commit `.env`.
- Commit messages: `feat:`, `fix:`, `test:`, `docs:`.
- Do not overwrite or discard another person's unfinished work.
- **Stuck for more than 15 minutes?** Say it in chat immediately.
- If Gate 2 is late, stop building new features and help the critical path.

---

## 10. Fallbacks if time runs short

| Problem | Fallback |
|---|---|
| Billing engine late | Seed script creates invoices for everything except the one the demo needs; show the billing run for a single subscription |
| Tax and discount late | One percentage tax, one discount type, no usage limit |
| Quotation flow late | Create subscriptions directly (Draft → Confirmed) |
| Portal late | Skip it; mention it as planned |
| Anomaly check or one-click fix late | Drop them; keep missed, overdue and duplicate |
| Email not working | Console email backend; show the reset link in the terminal |
| Live demo fails | Play the backup screen recording and use the seeded database |

---

## 11. Assumptions

- "5 hours" is total build time, including integration and rehearsal.
- Odoo integration is **not** assumed. Confirm with the organisers whether it is expected or scored.
- Payments are manual or simulated and labelled as such.
- Dates, prices and sample records are illustrative.
