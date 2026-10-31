# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite SPA (in `frontend/`) communicating with Django JSON API (in `backend/`) over HTTP with CORS & Session credentials.

## Users

- **Finance & System Administrators**: Manage catalogue, tax rules, discounts, staff access, and high-level financial health.
- **Operations Staff**: Handle customer registrations, subscription lifecycle transitions, recurring billing runs, payment reconciliation, and audit alert reviews with one-click fixes.
- **Customers**: Self-service portal to view active plans, invoices, balances, payment history, and request renewal or cancellation.

## Product Purpose

ProofBill is a subscription-management platform featuring a built-in deterministic Proof Engine. It computes what should have been billed based on subscription contracts and compares it continuously with actual invoices and payments, highlighting explainable discrepancies with one-click remediations.

## Positioning

"Bill it right. Prove it. Fix it." Rather than hoping automated billing worked correctly, ProofBill provides an independent mathematical proof of every billing outcome, turning revenue leakage into traceable, fixable alerts.

## Operating Context

Professional B2B financial accounting and operations. The interface must be calm, dense, highly scannable, and completely free of gimmicks or distractions.

## Capabilities and Constraints

- **Catalogue**: Products, variants with price additions, recurring plans (daily, weekly, monthly, yearly), tax rules, discounts with usage limits.
- **Subscriptions**: State machine (Draft, Quotation, Confirmed, Active, Paused, Closed) with transition guards and immutable event history.
- **Billing**: Idempotent billing runs, partial unique constraints, catch-up of skipped periods, sequential invoice numbering.
- **Payments**: Partial & full payments, atomic updates, overpayment rejection, idempotency key deduplication.
- **Proof Engine**: Deterministic rules for missed invoices, overdue balances, duplicate billings, and pricing anomalies; de-duplicated Revenue at Risk calculations; one-click fixes (`generate_missing_invoice`, `rebalance`).
- **Design Constraints**:
  - Absolute ban on "AI slop": NO blue/purple themes, NO button animations, NO glassmorphism, NO glow/shimmer/floating effects, NO decorative emojis.
  - Neutral graphite palette: `#1E2124` text/primary, `#FFFFFF` surfaces, `#F3F4F4` canvas, `#D9DBDD` borders, `#5B6168` secondary text, semantic status badges (green `#2E7D4F`, amber `#B7791F`, red `#B3261E`).
  - Strict typographic scale, monospace/tabular numbers for monetary figures (`tabular-nums`), right-aligned amounts.
  - Sentence case buttons and titles with explicit verbs ("Record payment", "Generate invoice").

## Brand Commitments

- **Name**: ProofBill
- **Tagline**: Bill it right. Prove it. Fix it.
- **Voice**: Factual, authoritative, transparent.
- **Mode**: Operate (task completion, fast scanning, predictable layouts).

## Evidence on Hand

- Complete Django backend with 43 automated passing tests.
- Seeding pipeline (`seed_demo`) with realistic test customers, plans, invoices, and alerts.
- Live Leak Injection engine (`leak_injection`) for verifying detection.

## Product Principles

1. **Deterministic Truth**: All metrics and alerts stem from exact decimal arithmetic; no probabilistic guesses.
2. **Utilitarian Minimalism**: The interface recedes so the financial data and decisions take center stage.
3. **Actionable Transparency**: When an alert is raised, show the expected calculation vs. actual data, the monetary exposure, and the direct remedy.
4. **Resilient Idempotency**: Billing runs and payment recordings can be repeated safely without side effects or duplicates.

## Accessibility & Inclusion

- WCAG AA contrast compliance across all text and border tokens.
- Visible high-contrast focus rings for full keyboard navigation.
- Native semantic HTML elements (tables, forms, buttons) for accessibility tools.
