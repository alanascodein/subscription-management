# Team Changelog and Progress Tracker

## Instructions for the Next Coding Agent

Before making any code changes:
1. Read `AGENTS.md`, `TASKS.md`, `CONTRACT.md` (`API_CONTRACT.md`), and this `TEAM_CHANGELOG.md`.
2. Inspect `git status` to identify uncommitted changes.
3. Inspect recent commits and the current branch (`backend`).
4. Review the changelog for changes that affect your assigned task.
5. Verify whether relevant teammate branches are available locally or remotely.
6. Inspect actual code before relying on a changelog description.
7. Avoid overwriting teammates' work.
8. Follow the existing API contracts and architecture.
9. If required changes are missing, document the dependency instead of guessing.
10. Update `TEAM_CHANGELOG.md` when your task is completed.

---

## Project Information
- **Repository Name**: subscription-management
- **Current Branch**: `backend`
- **Last Updated**: 2026-10-31 11:45 UTC
- **Framework & Runtime**: Python 3.12, Django 6.1.2, SQLite

---

## Recent Teammate Changes

### Change Entry: Backend Architecture & Core Services Implementation
- **Contributor / Author**: adharsh <adharshsaju.official@gmail.com> (Backend Agent)
- **Branch**: `backend`
- **Commit Hash**: `b91166b8a84925bedd658868d9ef131c0816df0a`
- **Date & Time**: 2026-10-31 11:57 IST
- **Status**: Committed on `backend` branch (Ready for push)
- **Summary of Changes**:
  - Initialized virtual environment `.venv` and generated `requirements.txt` with Django, `python-dateutil`, and `python-dotenv`. Committed `.gitignore` and `.env.example`.
  - Defined and enforced shared contracts in `CONTRACT.md`, `API_CONTRACT.md`, and `core/constants.py`.
  - Built `core` app with half-up Decimal money quantizer (`core/money.py`), billing cycle periods calculation (`core/periods.py`), and line-item pricing engine (`core/pricing.py`).
  - Implemented custom User model in `accounts` app with case-insensitive unique email lookup, custom password policy validator (min 9 chars, upper, lower, special), role choices (`admin`, `staff`, `customer`), and role-based access decorators (`@role_required`).
  - Implemented catalogue models in `products` app: `Product`, `ProductVariant` (extra price support), `Plan` (cycle, grace days, pause/early-close/renewal rules), `TaxRule`, and `Discount` (percentage/fixed with usage limits).
  - Implemented `subscriptions` app: `Customer`, `Subscription`, `SubscriptionItem`, `SubscriptionEvent`, and guarded lifecycle state machine (`subscriptions/lifecycle.py`) enforcing transition rules and writing immutable event logs.
  - Implemented `billing` app: `NumberSequence`, `Invoice`, `InvoiceItem` (snapshotted line items), `BillingRun`, and `billing/services.py` with idempotent billing runs, catch-up of skipped periods, and voiding with mandatory reason.
  - Implemented `payments` app: `Payment` model and `payments/services.py` with atomic payments, overpayment rejection, and idempotency key deduplication.
  - Implemented `audit` app (Proof Engine): `Alert` model with deduplication keys, `AuditLog`, deterministic detection rules for missed invoices, overdue balances, duplicate billings, and pricing anomalies, Revenue at Risk calculator, and guarded one-click fixes (`generate_missing_invoice`, `rebalance`).
  - Implemented `analytics` app: `analytics/services.py` computing real database aggregations for MRR, active count, collected revenue, outstanding balance, overdue accounts, and trends.
  - Implemented four CLI management commands: `run_billing`, `run_detection`, `leak_injection`, and `seed_demo`.
  - Created offline HTML/CSS template suite following the graphite design system and typography rules.
  - Created 18 automated unit and integration tests covering pricing (Rs. 4,966.97 verification), lifecycle state machine, billing idempotency, catch-up, payment atomicity, overpayment prevention, case-insensitive email, and role scoping.

- **Files Added / Modified**:
  - `.gitignore`, `.env.example`, `requirements.txt`
  - `TASKS.md`, `CONTRACT.md`, `API_CONTRACT.md`
  - `proofbill/settings.py`, `proofbill/urls.py`
  - `core/constants.py`, `core/money.py`, `core/periods.py`, `core/pricing.py`, `core/tests.py`, `core/management/commands/seed_demo.py`
  - `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/permissions.py`, `accounts/validators.py`, `accounts/admin.py`, `accounts/tests.py`
  - `products/models.py`, `products/forms.py`, `products/views.py`, `products/urls.py`, `products/admin.py`
  - `subscriptions/models.py`, `subscriptions/forms.py`, `subscriptions/views.py`, `subscriptions/urls.py`, `subscriptions/lifecycle.py`, `subscriptions/admin.py`, `subscriptions/tests.py`
  - `billing/models.py`, `billing/services.py`, `billing/views.py`, `billing/urls.py`, `billing/admin.py`, `billing/tests.py`, `billing/management/commands/run_billing.py`
  - `payments/models.py`, `payments/services.py`, `payments/forms.py`, `payments/views.py`, `payments/urls.py`, `payments/admin.py`, `payments/tests.py`
  - `audit/models.py`, `audit/proof_engine.py`, `audit/views.py`, `audit/urls.py`, `audit/admin.py`, `audit/tests.py`, `audit/management/commands/run_detection.py`, `audit/management/commands/leak_injection.py`
  - `analytics/services.py`, `analytics/views.py`, `analytics/urls.py`, `analytics/tests.py`
  - `static/css/proofbill.css`
  - `templates/base.html`, `templates/accounts/*.html`, `templates/analytics/*.html`, `templates/audit/*.html`, `templates/billing/*.html`, `templates/payments/*.html`, `templates/subscriptions/*.html`, `templates/products/*.html`, `templates/portal/*.html`

- **Database Constraints**:
  - `unique_subscription_active_period` on `Invoice(subscription, period_start)` where `status != 'void'`.
  - Non-negative check constraints on prices, quantities, and balances.
  - Percentage checks: `0 <= rate_percent <= 100`.

- **Tests Performed & Results**:
  - Executed `python manage.py test`: 18 tests passed in 6.5s with zero errors and zero warnings.
  - Executed `python manage.py seed_demo`: Successfully populated users, catalogue, 5 customers, 5 subscriptions, and invoices.
  - Executed `python manage.py run_billing`: Idempotency confirmed.
  - Executed `python manage.py run_detection`: Detected alerts without duplicates on recurring runs.
  - Executed `python manage.py leak_injection`: Successfully injected synthetic faults and proved live detection by Proof Engine.

### Change Entry: Backend Bug Fixes, Quantization, Password Reset & Customer Registration
- **Contributor / Author**: Antigravity (Backend Agent)
- **Branch**: `backend`
- **Commit Hash**: `8af52b55b9a718704250275817c91ad9b8b05691`
- **Date & Time**: 2026-10-31 15:08 IST
- **Status**: Committed on `backend` branch (Ready for push)

- **Summary of Changes**:
  - **P0 Model Quantization**: Overrode `save()` in `Product`, `ProductVariant`, and `TaxRule` in `products/models.py` to ensure `quantize_money` runs on monetary/percentage fields even when `clean()` is bypassed (e.g. via `objects.create()`).
  - **P0 URL Routing Fixes**: Resolved routing in `proofbill/urls.py`, `products/urls.py`, and `subscriptions/urls.py` so `/plans/`, `/customers/`, and `/customers/<uuid>/` are direct top-level endpoints matching `CONTRACT.md` without duplicate mounts.
  - **P1 Password Reset Flow**: Configured Django's built-in `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, and `PasswordResetCompleteView` in `accounts/urls.py`. Created graphite-styled templates (`password_reset.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`, `password_reset_email.html`, `password_reset_subject.txt`). Added "Forgot password?" link to login page.
  - **P2 Customer Self-Registration & User Linkage**: Implemented `CustomerRegistrationForm` with `ProofBillPasswordValidator`, `register_view`, and `templates/accounts/register.html`. Added automatic customer `User` account linkage when staff creates a customer at `/customers/`.
  - **Validator Fix**: Added `__call__` method to `ProofBillPasswordValidator` so it works seamlessly as both a Django auth password validator and a form field validator.
  - **Database Migrations**: Applied unapplied migration `analytics.0001_initial`.
  - **Test Suite**: Added unit/integration tests for customer registration and password reset. Total tests increased to 43, all 43 passing.
- **Files Modified / Added**:
  - `backend/products/models.py`, `backend/products/urls.py`, `backend/subscriptions/urls.py`, `backend/subscriptions/views.py`, `backend/proofbill/urls.py`
  - `backend/accounts/validators.py`, `backend/accounts/forms.py`, `backend/accounts/views.py`, `backend/accounts/urls.py`, `backend/accounts/tests.py`
  - `backend/templates/base.html`, `backend/templates/accounts/login.html`, `backend/templates/accounts/register.html`
  - `backend/templates/accounts/password_reset*.html`, `backend/templates/accounts/password_reset_subject.txt`
  - `backend/TASKS.md`, `.gitignore`
- **Tests Performed & Results**:
  - `python manage.py test`: 43/43 tests passed (0 failures, 0 errors)
  - `python manage.py seed_demo`: Verified successfully seeding complete demo dataset
  - `python manage.py run_billing`: Confirmed idempotent recurring billing
  - `python manage.py run_detection`: Confirmed audit detection with deduplicated alerts
  - `python manage.py leak_injection`: Verified synthetic fault generation and live Proof Engine detection

### Change Entry: Impeccable Minimalist Frontend SPA & Complete Backend JSON API
- **Contributor / Author**: Antigravity (Frontend & Integration Agent)
- **Branch**: `backend`
- **Commit Hash**: `5f7822384918e76bb925e01ca209581ffba271a5`
- **Date & Time**: 2026-10-31 15:28 IST
- **Status**: Committed on `backend` branch (Ready for push)

- **Summary of Changes**:
  - **PRODUCT.md & DESIGN.md**: Initialized `PRODUCT.md` via `/impeccable init` capturing durable product truth, operating context, and core principles. Created `DESIGN.md` establishing the graphite design system (`#1E2124`, `#F3F4F4`, `#FFFFFF`, `#D9DBDD`, `#5B6168`, `#2E7D4F`, `#B7791F`, `#B3261E`).
  - **Django JSON API (`proofbill/api.py`, `proofbill/api_urls.py`)**: Built REST endpoints for auth, dashboard metrics, subscriptions, customer directory, invoices, payments, catalogue, and Proof Engine audit actions. Added `corsheaders` support in `settings.py`.
  - **Minimalist React + Vite Frontend (`frontend/`)**: Scaffolded modern SPA with zero AI slop, no blue/purple themes, no floating shadows or button animations, crisp 1px borders, and tabular numerals.
  - **Views & Components Built**:
    - `DashboardView`: Revenue at Risk headline, financial summary metrics, overdue invoices, and upcoming renewals.
    - `AlertsView`: Proof Engine detection review, JSON evidence viewer, and one-click guarded fixes (`generate_missing_invoice`, `rebalance`).
    - `SubscriptionsView`: Subscriptions table with cycle and plan metadata, lifecycle state machine transition modal, and immutable event history.
    - `InvoicesView`: Line-item snapshots, partial payment recording dialog with atomic balance deduction, void dialog with mandatory reason, and print layout.
    - `CustomersView`: Subscriber directory with active plan counts and customer creation.
    - `CatalogueView`: Products, variants with price additions, recurring plans with grace days and lifecycle flags.
    - `CustomerPortalView`: Subscriber self-service portal for active subscriptions, invoices, and renewal/cancel requests.
    - `DemoBar`: Top interactive bar for switching between Admin, Staff, and Customer accounts, and triggering billing runs, detection, and leak injection on demand.
  - **Mechanical Design Check**: Ran Impeccable detector; 0 antipatterns found (`[]`).
  - **Build Verification**: `vite build` completed in 366ms with 0 errors. Backend test suite: 43/43 tests passing.
- **Files Added / Modified**:
  - `PRODUCT.md`, `DESIGN.md`, `.impeccable/config.json`
  - `backend/proofbill/settings.py`, `backend/proofbill/urls.py`, `backend/proofbill/api.py`, `backend/proofbill/api_urls.py`
  - `backend/TASKS.md`
  - `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`
  - `frontend/src/index.css`, `frontend/src/api.js`, `frontend/src/App.jsx`
  - `frontend/src/components/Header.jsx`, `frontend/src/components/DemoBar.jsx`
  - `frontend/src/views/DashboardView.jsx`, `frontend/src/views/AlertsView.jsx`, `frontend/src/views/SubscriptionsView.jsx`, `frontend/src/views/InvoicesView.jsx`, `frontend/src/views/CustomersView.jsx`, `frontend/src/views/CatalogueView.jsx`, `frontend/src/views/CustomerPortalView.jsx`, `frontend/src/views/AuthModal.jsx`

---


## Important Changes for Other Agents

- **Custom User Model**: `AUTH_USER_MODEL = 'accounts.User'`. Always reference via `settings.AUTH_USER_MODEL` or `get_user_model()`.
- **Money Calculations**: Never use native float arithmetic. Use `from core.money import quantize_money` and `Decimal`.
- **Pricing Calculation**: Use `core.pricing.calculate(items, discount, tax_rule)`.
- **Lifecycle Changes**: Always invoke `subscriptions.lifecycle.transition(subscription, action, actor, reason)` to ensure event history and business rules are preserved.
- **Payment Processing**: Always invoke `payments.services.record(...)`. Direct modification of invoice balances outside this service is prohibited.
- **URLs and Views**: All URLs follow the names in `CONTRACT.md`. Customer scoping returns 404 for unowned records.

---

## Current Integration State
- **Current Branch**: `backend`
- **Latest Remote Commit**: Initial repository commit on `main`.
- **Working Tree**: Clean after committing backend architecture and services.
- **Database**: Migrations applied cleanly.
- **Next Recommended Action**: Push `backend` feature branch to origin and open pull request into `main`.
