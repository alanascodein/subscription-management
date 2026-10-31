# ProofBill: Work Division

Odoo x Make-A-Ton 9.0, Kochi Hackathon 2026
Team: 3 members (Frontend, Backend, Integration) | Build time: 5 hours

ProofBill is a subscription-management platform with a built-in Proof Engine that compares what should have been billed with what was actually billed, and raises explainable alerts. This document fixes who builds what, with which tools, and when the pieces must meet.

---

## 1. Stack (one codebase, no separate API layer)

| Layer | Choice | Why it fits a 5-hour, 3-person build |
|---|---|---|
| Language / framework | Python 3.11+, Django 5 | Auth, ORM, forms, migrations and templates in one framework |
| Database | SQLite | Zero setup; supports partial unique constraints and transactions. PostgreSQL only if time remains |
| Pages | Django templates, server-rendered | No SPA, no CORS, no API contract to maintain |
| Styling | Bootstrap 5 grid and form components, overridden by one custom stylesheet | Fast layout, but the look is ours (see section 5) |
| Charts | Chart.js, served locally | Two or three simple charts; no build step |
| Scripting | Vanilla JavaScript | Filters, confirm dialogs, live price preview. No framework |
| Money | `decimal.Decimal` only, half-up rounding per line | Correct totals; never floats |
| Dates | `dateutil.relativedelta` | Month-end clamping (31 Jan becomes 28/29 Feb) |
| Scheduling | Management commands: `run_billing`, `run_detection`, `seed_demo` | No Celery or cron needed for the demo |
| Tests | Django `TestCase` | Runs with `python manage.py test`; no extra tooling |
| Config | `python-dotenv`, `.env.example` committed, `.env` ignored | Keeps secrets out of Git |
| Version control | Git + GitHub, one branch per member | Merge on the agreed gates |

Everything works offline: no CDN links, no external fonts, no external API. Email uses Django's console backend (the password-reset link prints to the terminal).

---

## 2. Roles at a glance

| Role | Owns | Main deliverable |
|---|---|---|
| Backend | Data model and all money and lifecycle logic | Correct subscriptions, invoices and payments |
| Integration | Auth and roles, Proof Engine, alerts, dashboard queries, seed data, tests, merges | The detection layer wired to real records, and a repeatable demo |
| Frontend | Templates, styling, charts, client-side behaviour | Every screen, built to the design rules in section 5 |

Rule of ownership: a file belongs to one person. Anyone else who needs a change asks the owner, so merges stay clean.

---

## 3. Role details

### 3.1 Backend

**Stack used:** Django models and migrations, Django forms, `decimal`, `dateutil`, Django `TestCase`.

**Apps owned:** `products`, `subscriptions`, `billing`, `payments`, `core` (money, pricing, periods, constants)

**Builds**

1. All models and migrations, merged within the first 45 minutes. Models: Product, ProductVariant, Plan, TaxRule, Discount, Customer, Subscription, SubscriptionItem, SubscriptionEvent, Invoice, InvoiceItem, NumberSequence, BillingRun, Payment.
2. Views and forms for the catalogue: products, variants (extra price), plans with explicit rules (cycle, minimum quantity, availability dates, pause, early close, renewal, grace days).
3. `pricing.calculate()`: unit price = product price + variant extra, minus discount, then tax, rounded per line.
4. `lifecycle.transition()`: Draft, Quotation, Confirmed, Active, Paused, Closed with an event record for every change. Illegal moves are rejected.
5. `periods`: period end and next start for daily, weekly, monthly and yearly cycles.
6. `billing.run(run_date)`: one invoice per subscription per period, catching up any missed periods in order, safe to run twice.
7. `payments.record()`: partial and full payments, rejects overpayment, idempotency key stops a double submit; invoice becomes Paid only at zero balance.
8. Invoice confirm and void (reason required); void frees the billing period.

**Database guarantees (do not leave these to form validation)**

- Unique constraint on (subscription, period start) for invoices where status is not void.
- Check constraints: prices at least 0, quantity above 0, payment amount above 0, percent discount at most 100.
- Invoice line items are snapshots and are never rewritten.
- `amount_paid` and `balance_due` change only inside the payment transaction.

**Tests owned:** pricing example (Rs. 999 + 560, quantity 3, 10% discount, 18% tax = Rs. 4,966.97), lifecycle transitions, billing twice gives one invoice, catch-up after 3 skipped days, paused and closed are not billed, partial payment then remainder, overpayment rejected.

**Scope decisions for 5 hours**

- A quotation is a subscription in the Quotation state with a validity date. A template library is a stretch item.
- One percentage tax rule and one discount per invoice.
- No proration; full periods only.

---

### 3.2 Integration

**Stack used:** Django auth with a custom user model, decorators and mixins, Python `csv` module, Django ORM aggregation (`Sum`, `Count`, `Q`), management commands, Django test client.

**Apps owned:** `accounts`, `audit` (Proof Engine and alerts), `analytics`, `notifications`, seed and test tooling

**Builds**

1. Custom user with a role field (admin, staff, customer); unique email regardless of case; password rule (at least 9 characters, upper, lower, special); password reset by email link.
2. Permission layer: a role decorator on every view, customer querysets scoped to the owner, public UUIDs in URLs, 404 for other customers' records, admin-only staff creation.
3. `seed_demo`: five customers, mixed plans, expired and paused subscriptions, paid, overdue and partially paid invoices, payments across several months. It must exist by hour 1.5 so the Proof Engine and the dashboard can be built before billing is finished.
4. Proof Engine (`proof_engine.run(as_of)`), rules only, no AI:
   - Missed invoice: active billable subscription, expected period has no invoice after the grace days.
   - Overdue invoice: confirmed, balance above zero, past due date (partial payments handled).
   - Possible duplicate: same customer, overlapping period, matching amount; flagged, never cancelled.
   - Invoice anomaly (if time): recompute the invoice with `pricing.calculate()` and flag any mismatch.
5. Alert model: type, priority (high, medium, low by amount, days overdue and status), reason, evidence, amount, status (New, In Review, Resolved, Dismissed), review notes and history. A unique key on rule, object and period stops duplicate alerts when detection runs repeatedly.
6. Revenue at Risk: potential exposure kept separate from confirmed outstanding balance, without double-counting one invoice that triggers two alerts. Labelled "potential", never "lost revenue".
7. `analytics.summary(filters)`: active subscriptions, collected revenue, outstanding, overdue, MRR, all from database aggregates.
8. Leak Injection command and button: creates a skipped invoice, a duplicate invoice and a mispriced invoice so the demo shows live detection.
9. Guarded fix action `Generate missing invoice`, which calls `billing.create_invoice()` after staff confirmation and writes an audit entry.
10. Customer portal views (own subscriptions, invoices, payments; request cancel or renew).

**Stretch (only after the freeze check is green):** bank-statement CSV import with suggested invoice matches and unmatched-payment alerts; billing preview before a run.

**Tests owned:** duplicate email in a different case, weak passwords, customer denied on staff and admin pages, another customer's invoice returns 404, staff cannot create staff, overdue listing, alerts do not duplicate on a second run, dashboard totals equal raw sums.

**Also owns:** the shared contract file (section 4), the merge order, and the final demo run-through.

---

### 3.3 Frontend

**Stack used:** Django templates with template inheritance and partials, Bootstrap 5 (grid, forms, tables, modals), one custom CSS file, Chart.js, vanilla JavaScript.

**Folders owned:** `templates/`, `static/css/`, `static/js/`

**Builds**

1. Base layout: sidebar, top bar, role-aware navigation, flash messages. Separate navigation for admin, staff and customer.
2. Shared components: data table with pagination, filter bar, status badge, empty state, confirm dialog, form field with inline error.
3. Catalogue pages: products, variants, plans, tax and discount rules (admin).
4. Customers, quotations, subscriptions (list, detail, lifecycle action buttons with confirmation for pause, close and void).
5. Invoices: list, detail, print-friendly layout (browser print, no PDF library), payment form with partial amount.
6. Dashboard: summary cards (Revenue at Risk, overdue amount and count, outstanding, collected, active subscriptions), revenue trend, paid versus unpaid, overdue table, upcoming renewals, with a tooltip defining each metric.
7. Alert pages: table with filters (type, priority, status, customer, date range); detail page showing explanation, evidence, calculation, recommended action, notes and review history.
8. Customer portal pages and a plan browser with a live price preview.

Until real data exists, build each page against the context keys agreed in the contract, using sample dictionaries in view stubs. Remove the stubs when the owner's view lands. Do not wait for the backend.

---

## 4. Shared contract (agree in the first 30 minutes; commit as `core/constants.py` and `CONTRACT.md`)

**Constants**

```
SUBSCRIPTION_STATUS = draft, quotation, confirmed, active, paused, closed
INVOICE_STATUS      = draft, confirmed, paid, void      (partially paid and overdue are derived)
ALERT_TYPE          = missed_invoice, overdue_invoice, possible_duplicate,
                      unmatched_payment, invoice_anomaly, renewal_attention
ALERT_STATUS        = new, in_review, resolved, dismissed
PRIORITY            = high, medium, low
```

**Service signatures**

```
pricing.calculate(items, discount=None, tax_rule=None) -> PricingResult
periods.end(start_date, cycle) -> date
lifecycle.transition(subscription, action, actor, reason="") -> Subscription
billing.run(run_date) -> BillingRun
billing.create_invoice(subscription, period_start) -> Invoice | None
payments.record(invoice, amount, method, date, reference, note, actor, idempotency_key) -> Payment
proof_engine.run(as_of) -> RunSummary
alerts.apply_fix(alert, actor) -> Alert
analytics.summary(filters) -> dict
```

**URL names** are fixed in `CONTRACT.md` before anyone writes a template: `login`, `dashboard`, `customers`, `products`, `plans`, `subscriptions`, `subscription_detail`, `invoices`, `invoice_detail`, `payment_record`, `alerts`, `alert_detail`, `portal_home`.

**Dashboard context keys** (Integration provides, Frontend reads): `revenue_at_risk`, `overdue_amount`, `overdue_count`, `outstanding`, `collected_month`, `active_count`, `mrr`, `trend`, `recent_payments`, `upcoming_renewals`, `overdue_rows`.

---

## 5. Design rules (Frontend, and anyone touching a template)

The interface should look like finance software a business would trust: quiet, legible and dense where needed.

**Do**

- Neutral palette with graphite as the main colour:

  | Use | Colour |
  |---|---|
  | Page background | `#F3F4F4` |
  | Surface (tables, panels) | `#FFFFFF` |
  | Border | `#D9DBDD` |
  | Primary text and primary buttons | `#1E2124` |
  | Secondary text | `#5B6168` |
  | Paid / success | `#2E7D4F` |
  | Warning / partially paid | `#B7791F` |
  | Overdue / error / Revenue at Risk | `#B3261E` |
  | Void / inactive / Active subscription badge | `#8A8F95` / graphite outline |

- One typeface: the system UI stack (`system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`). Use `font-variant-numeric: tabular-nums` and right-align every money column.
- Sentence case everywhere. Button labels say what happens: "Record payment", "Generate invoice", "Mark as resolved".
- Status is a text badge with a colour, never colour alone.
- Links are graphite and underlined. Primary buttons are solid graphite; secondary buttons are outlined.
- Visible keyboard focus: a 2px graphite outline with offset.
- Tables are the main structure; cards only for the dashboard summary row.
- Plain explanatory errors: say what is wrong and how to fix it.

**Do not**

- No blue or purple anywhere, including Bootstrap's default blue links, focus ring and primary button. Override these variables in the custom stylesheet before building any page.
- No gradients, glow, glass effects, large soft shadows or decorative illustrations.
- No button animation: set `transition: none` on buttons, links and cards. Hover changes the background colour instantly. No lift, scale, ripple or loading shimmer.
- No entrance animations, page-load effects or hover effects on cards.
- No emoji, all-caps labels or decorative icons. Icons only where they carry meaning, in one simple monochrome set.
- No extra typefaces.

---

## 6. Timeline (5 hours)

| Time | Backend | Integration | Frontend |
|---|---|---|---|
| 0:00 to 0:30 | Together: repo, Django project, branches, `core/constants.py`, `CONTRACT.md` | (same) | (same) |
| 0:30 to 1:30 | Models and migrations (merged by 0:45), catalogue views, `pricing.calculate()` with its unit test | Custom user, roles, decorators, login and reset, `seed_demo` | Base layout, CSS tokens and Bootstrap overrides, shared components, navigation |
| 1:30 to 2:00 | `periods`, `lifecycle.transition()` | Dashboard aggregates, overdue and missed rules against seed data | Catalogue and customer pages |
| **2:00** | **Gate 1: an Active subscription can be created through the UI** | | |
| 2:00 to 3:00 | `billing.run()`, `billing.create_invoice()`, invoice numbering, subscription views | Alert model, duplicate rule, priority and Revenue at Risk, alert review flow | Subscription and invoice pages, dashboard cards |
| 3:00 to 3:30 | `payments.record()`, invoice confirm and void | Leak Injection, `Generate missing invoice` fix | Payment form, alert table and filters |
| **3:30** | **Gate 2: invoice, then payment, then dashboard update works end to end. If it fails, everyone helps Backend until it works** | | |
| 3:30 to 4:00 | Discount usage limit, tax rule, backend tests | Portal views, permission tests, anomaly rule if time | Alert detail page, portal pages, charts |
| **4:00** | **Feature freeze. Stretch items only if everything above works** | | |
| 4:00 to 4:40 | Fix bugs found in integration, final backend tests | Run the full test suite, fix permission leaks, rehearse the seed and injection flow | Empty states, error messages, print layout, responsive check |
| 4:40 to 5:00 | Whole team: demo rehearsal, fallback recording, local copy ready, `README.md` with setup steps | (same) | (same) |

**Hand-offs**

| Who waits | For what | Needed by |
|---|---|---|
| Frontend, Integration | Backend's pushed schema | 0:45 |
| Integration | `next_billing_date` and invoice fields for the Proof Engine | 1:30 |
| Frontend | Real `analytics.summary()` output (stub until then) | 2:30 |
| Frontend | Alert model and services from Integration | 3:00 |
| Everyone | Working invoice, then payment path | Gate at 3:30 |

**Merge rules**

- Merge to `main` at 0:45, 2:00, 3:30 and 4:00. `main` must always start and migrate cleanly. Integration performs the merges.
- Branches: `backend`, `integration`, `frontend`. Pull from `main` before starting each block.
- Model changes go through the Backend owner and are announced in the team chat.
- Commits are small, with `feat:`, `fix:`, `test:` or `docs:` prefixes. Stage files explicitly; never `git add .` or commit `.env`. Do not overwrite anyone's unfinished work.
- Stuck for more than 15 minutes? Say so in the chat straight away.

---

## 7. Priorities and fallbacks

**Must have (never cut):** login with three roles, products and plans, subscription creation and activation, billing run with no duplicate periods, payment recording with partial payments, financial dashboard, overdue, missed and duplicate alerts, Revenue at Risk, alert review and resolve.

**Should have:** variants, one tax rule, one discount, customer portal, invoice anomaly check, `Generate missing invoice` fix, Leak Injection.

**Stretch:** bank CSV matching, billing preview, quotation template library, renewal-attention alerts.

**Out of scope:** payment gateway, PDF library, email delivery beyond the console, proration, refunds, AI features.

| If this runs late | Fall back to |
|---|---|
| Billing engine | Seed script creates the invoices; demo the billing run on a single subscription |
| Tax and discount | One percentage tax, or skip both |
| Variants | A single extra-price field |
| Customer portal | Read-only, or skip and mention it as planned |
| Anomaly rule and one-click fix | Drop them; keep missed, overdue and duplicate |
| Charts | Keep the summary cards only |
| Email reset | Console email backend; show the link in the terminal |
| Live demo fails | Play the backup recording on the seeded database |

Cut order: stretch items, anomaly rule, portal request actions, discount usage limit.

---

## 8. Definition of done (run between 4:00 and 4:40; report only what was actually run)

- [ ] `python manage.py migrate && python manage.py seed_demo && python manage.py runserver` works from a clean clone
- [ ] Running billing twice produces one invoice per period
- [ ] Pricing example gives exactly Rs. 4,966.97
- [ ] A customer cannot open staff, admin or another customer's pages
- [ ] Dashboard totals equal raw database sums
- [ ] Leak Injection creates faults and the Proof Engine reports each one with evidence, amount and next step
- [ ] Running detection twice creates no duplicate alerts
- [ ] No blue or purple, and no button animation, anywhere in the UI
- [ ] The demo runs start to finish in five minutes without editing data by hand

## 9. Demo owners

| Step | Presenter |
|---|---|
| Create plan, activate subscription, run billing twice, show no duplicate | Backend |
| Partial payment, remainder, dashboard update | Frontend |
| Leak Injection, detection run, Revenue at Risk, alert detail, one-click fix, resolve | Integration |
| Customer portal and access-denied check | Integration |

## 10. Open points to confirm

- Whether Odoo integration is expected or scored by the organisers (not assumed here).
- Whether the team prefers PostgreSQL over SQLite; the default here is SQLite for speed.
- Whether a quotation template library matters to the judges; the default here is a quotation state only.
