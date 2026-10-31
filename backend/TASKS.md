# ProofBill: Tasks and Work Status

| Task ID | Task Description | Owner | Status | Notes |
|---------|------------------|-------|--------|-------|
| TASK-01 | Project setup, virtual environment, and dependency management | Backend | Completed | `.venv` created, `requirements.txt` generated, `.gitignore` and `.env.example` committed. |
| TASK-02 | Shared contract and constants (`core/constants.py`, `CONTRACT.md`, `API_CONTRACT.md`) | Backend | Completed | Enums, signatures, URL names, and money rules defined. |
| TASK-03 | Core app: Money calculation rules, `periods` service, `pricing` service | Backend | Completed | Half-up Decimal rounding, cycle dates, line-item pricing engine implemented. |
| TASK-04 | Custom User model (`accounts`), roles (admin, staff, customer), password policy, auth views | Backend | Completed | Email as username (case-insensitive), password validator (9+ chars, upper, lower, special), role decorators. |
| TASK-05 | Catalogue models (`products`): Product, ProductVariant, Plan, TaxRule, Discount | Backend | Completed | Check constraints, variants with extra prices, plan cycles and rules implemented. |
| TASK-06 | Subscriptions app: Customer, Subscription, SubscriptionItem, SubscriptionEvent, `lifecycle` service | Backend | Completed | Lifecycle state machine with strict transition guards and event logging. |
| TASK-07 | Billing app: NumberSequence, Invoice, InvoiceItem, BillingRun, `billing` service | Backend | Completed | Idempotent billing runs, partial unique constraints, catch-up missed periods, void/confirm. |
| TASK-08 | Payments app: Payment model, `payments` service, overpayment rejection, idempotency key | Backend | Completed | Atomic payment recording, zero-balance check, balance deduction. |
| TASK-09 | Proof Engine & Alerts (`audit`): Detection rules, Revenue at Risk, one-click fixes | Backend | Completed | Missed, overdue, duplicate, anomaly, renewal rules; deduplication; guarded fixes. |
| TASK-10 | Analytics service: `analytics.summary()` database aggregations | Backend | Completed | Real SQL/ORM aggregation for MRR, active count, collected, overdue, revenue at risk. |
| TASK-11 | Management commands: `run_billing`, `run_detection`, `seed_demo`, `leak_injection` | Backend | Completed | CLI tools for batch billing, audit detection, demo dataset seeding, and fault injection. |
| TASK-12 | Backend test suite: unit and integration tests | Backend | Completed | 18 automated tests passing: pricing test (Rs. 4,966.97), lifecycle, billing idempotency, catch-up, payments, overpayments, roles, scoping. |
| TASK-13 | UI Templates and Offline Stylesheet | Backend / Fullstack | Completed | Server-rendered templates following graphite palette and typographic design system without CDN dependencies. |
