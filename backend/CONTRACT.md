# ProofBill Shared Contract

This document fixes constants, service signatures, URL names, and money rules across Backend, Integration, and Frontend.

## 1. Constants

### Subscription Status
- `draft`: Initial draft being configured.
- `quotation`: Sent to customer with validity deadline.
- `confirmed`: Customer accepted; awaiting activation.
- `active`: In active recurring billing lifecycle.
- `paused`: Temporarily suspended; excluded from recurring billing.
- `closed`: Terminated; never billed again.

### Invoice Status
- `draft`: Editable invoice draft.
- `confirmed`: Issued to customer; balance due.
- `paid`: Balance due is exactly 0.00.
- `void`: Cancelled/annulled with reason; frees the billing period.

*Note: `partially_paid` and `overdue` are derived states based on `amount_paid > 0 and balance_due > 0`, and `due_date < today and balance_due > 0`.*

### Alert Types
- `missed_invoice`: Active billable subscription without invoice past grace days.
- `overdue_invoice`: Confirmed invoice with balance > 0 past due date.
- `possible_duplicate`: Overlapping periods or matching amounts for same customer.
- `unmatched_payment`: Payment without confident invoice link.
- `invoice_anomaly`: Stored line totals / tax / discount mismatch recalculated values.
- `renewal_attention`: Subscription nearing expiration without renewal action.

### Alert Status & Priority
- `ALERT_STATUS`: `new`, `in_review`, `resolved`, `dismissed`
- `PRIORITY`: `high`, `medium`, `low`

### User Roles
- `admin`: Full system access, staff management, settings.
- `staff`: Operations, catalogue, billing runs, payments, alert review.
- `customer`: Scoped to own subscriptions, invoices, and payments.

---

## 2. Service Signatures

```python
# Pricing
pricing.calculate(items: list[dict], discount=None, tax_rule=None) -> PricingResult

# Periods
periods.end(start_date: date, cycle: str) -> date
periods.next_start(start_date: date, cycle: str) -> date

# Subscription Lifecycle
lifecycle.transition(subscription: Subscription, action: str, actor, reason: str = "") -> Subscription

# Billing Engine
billing.run(run_date: date) -> BillingRun
billing.create_invoice(subscription: Subscription, period_start: date) -> Invoice | None
billing.confirm_invoice(invoice: Invoice, actor) -> Invoice
billing.void_invoice(invoice: Invoice, reason: str, actor) -> Invoice

# Payment Recording
payments.record(
    invoice: Invoice,
    amount: Decimal,
    method: str,
    date: date,
    reference: str = "",
    note: str = "",
    actor = None,
    idempotency_key: str = ""
) -> Payment

# Proof Engine
proof_engine.run(as_of: date) -> RunSummary
alerts.apply_fix(alert: Alert, actor) -> Alert

# Analytics Aggregates
analytics.summary(filters: dict = None) -> dict
```

---

## 3. URL Names

- `login`: `/accounts/login/`
- `logout`: `/accounts/logout/`
- `dashboard`: `/dashboard/`
- `customers`: `/customers/`
- `customer_detail`: `/customers/<uuid:uuid>/`
- `products`: `/products/`
- `plans`: `/plans/`
- `subscriptions`: `/subscriptions/`
- `subscription_detail`: `/subscriptions/<uuid:uuid>/`
- `invoices`: `/invoices/`
- `invoice_detail`: `/invoices/<uuid:uuid>/`
- `payment_record`: `/invoices/<uuid:uuid>/pay/`
- `alerts`: `/alerts/`
- `alert_detail`: `/alerts/<int:pk>/`
- `portal_home`: `/portal/`

---

## 4. Money & Calculation Rules

- All monetary figures use `decimal.Decimal` with 2 decimal places.
- Rounding mode: `ROUND_HALF_UP`.
- Calculations are performed line-by-line before computing invoice totals.
- Tax is calculated on the discounted net amount.
- Checking constraints ensure positive quantities, non-negative prices, and valid percentages (0-100).
