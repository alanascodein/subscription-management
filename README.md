# ProofBill — Subscription Management & Revenue Leakage Prevention Engine

> A high-precision subscription and billing engine equipped with an active "immune system"—detecting, auditing, and healing revenue leaks before money is lost.

[![Tests](https://img.shields.io/badge/tests-43%2F43%20passing-2e7d4f?style=flat-square)](backend/accounts/tests.py)
[![Backend](https://img.shields.io/badge/backend-Django%205-1e2124?style=flat-square)](backend/)
[![Frontend](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite-1e2124?style=flat-square)](frontend/)
[![Design](https://img.shields.io/badge/design-Graphite%20Code--First-5b6168?style=flat-square)](DESIGN.md)

---

## ⚡ What is ProofBill?

Most billing systems operate like blind conveyor belts—charging credit cards without verifying whether the underlying math, tax rules, or billing intervals are intact. In software and SaaS, **3% to 5% of total revenue is silently lost every year** to orphaned subscriptions, skipped renewals, and rounding errors.

**ProofBill** pairs deterministic subscription billing with the **Proof Engine**:
1. **Active Immune System**: Automatically detects unbilled cycles, orphaned active subscriptions, missing tax rates, and duplicate invoices.
2. **One-Click Autonomous Remediation**: Resolves identified leaks into compliant, snapshotted invoices without manual database tinkering.
3. **Immutable Line-Item Snapshots**: Invoices freeze product prices, discounts, and tax rates at issuance—catalog updates never corrupt historical books.
4. **Half-Up Decimal Precision**: Zero floating-point rounding errors (`0.1 + 0.2 = 0.30000000000000004` never touches financial ledgers).
5. **Graphite Design System**: Code-first, high-density financial UI using tabular figures and clear visual hierarchy with zero AI slop.

---

## 🛠️ Architecture

```
subscription-management/
├── backend/                  # Django 5 REST / JSON Engine
│   ├── accounts/             # Role-based auth (Admin, Staff, Customer)
│   ├── products/             # Catalogue, variants, plans, tax rules, discounts
│   ├── subscriptions/        # Lifecycle state machine & event audit trails
│   ├── billing/              # Idempotent billing runner & invoice generation
│   ├── payments/             # Atomic partial payments & overpayment protection
│   ├── audit/                # Proof Engine detector & leak remediation
│   ├── analytics/            # Real-time MRR, churn, and leakage metrics
│   └── proofbill/            # Main configuration, CORS, and REST API (/api/)
├── frontend/                 # React 18 + Vite SPA
│   ├── src/views/            # Dashboard, Alerts, Subscriptions, Invoices, Portal
│   ├── src/components/       # DemoBar (role switcher & leak simulator), Header
│   └── src/index.css         # Graphite design tokens & tabular typography
├── script.md                 # 5-minute presentation & demo walkthrough script
└── PRODUCT.md / DESIGN.md    # Product thesis and design token specifications
```

---

## 🚀 Quickstart & Local Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed database with realistic demo data (customers, products, invoices)
python manage.py seed_demo

# Start Django development server
python manage.py runserver 127.0.0.1:8000
```
Backend API and Admin will be running at `http://127.0.0.1:8000/`.

### 2. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend SPA will be live at `http://localhost:5173/` (pre-configured to proxy `/api/` to backend).

---

## 🔑 Demo Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Finance Admin** | `admin@proofbill.io` | `ProofBill@Admin2026` | Full platform control, billing runner, leak injection, one-click fixes |
| **Staff Member** | `staff@proofbill.io` | `ProofBill@Staff2026` | Subscriptions, customer management, invoice issuance |
| **Customer (Acme Corp)** | `customer@acme.corp` | `Customer@2026!` | Customer self-service portal, view & pay invoices, plan changes |

*(You can also use the interactive **Demo Bar** at the top of the frontend to switch roles instantly with one click.)*

---

## 🧪 Testing & Verification

Run the comprehensive automated test suite (43 tests covering pricing models, lifecycle transitions, payment atomicity, idempotency, and auth):

```bash
cd backend
python manage.py test
```

Build the frontend production bundle:

```bash
cd frontend
npm run build
```

---

## 🚢 Production Deployment

### Production Backend (Gunicorn / Waitress + WhiteNoise)

```bash
cd backend
pip install gunicorn whitenoise
# Set production environment variables
export DEBUG=False
export SECRET_KEY="your-production-secret-key"
export ALLOWED_HOSTS="yourdomain.com,127.0.0.1"

# Run with Gunicorn (Linux)
gunicorn proofbill.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Or with Waitress (Windows)
# waitress-serve --listen=0.0.0.0:8000 proofbill.wsgi:application
```

### Production Frontend (Static Hosting / Nginx)

```bash
cd frontend
npm run build
# Deploy the generated dist/ folder to Nginx, Vercel, Netlify, or Cloudflare Pages
```

---

## 📜 Key CLI Commands

| Command | Action |
| :--- | :--- |
| `python manage.py run_billing` | Executes billing runner across all eligible active subscriptions |
| `python manage.py run_detection` | Scans database for missing invoices, orphaned subscriptions, and tax anomalies |
| `python manage.py leak_injection` | Injects a simulated unbilled subscription to demonstrate real-time detection |
| `python manage.py seed_demo` | Wipes and resets the database to a clean, populated demonstration state |

---

## 📄 License & Credits
Developed for Odoo x Make-A-Ton 9.0 by team ProofBill.
Distributed under the MIT License.
