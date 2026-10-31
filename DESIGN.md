# Design System: ProofBill Graphite

## 1. Visual World & Direction

ProofBill is a financial subscription-management platform built around deterministic mathematical verification. The visual world is categorized under **Operate** mode: utilitarian, calm, dense, trustworthy, and completely free of AI-generated tropes or decorative spectacle.

- **Primary Metaphor**: Financial ledger and audit proof statement.
- **Tone**: Restrained, authoritative, exact.
- **Forbidden Elements (Anti-References)**:
  - NO blue or purple color themes.
  - NO button animations, scale, lift, ripple, or pulse effects (`transition: none`).
  - NO gradients, glowing halos, floating soft shadows, or glassmorphism.
  - NO decorative emojis, AI sparklines, or nested cards.

---

## 2. Color Palette (Neutral Graphite)

| Token | Hex | Semantic Use |
|---|---|---|
| `--color-canvas` | `#F3F4F4` | Clean light gray canvas |
| `--color-surface` | `#FFFFFF` | Tables, modals, and panel surfaces |
| `--color-surface-muted` | `#F8F9FA` | Column headers, table row hover, code blocks |
| `--color-border` | `#D9DBDD` | Structural table borders and component dividers |
| `--color-border-subtle` | `#EAECEE` | Row dividers |
| `--color-text-primary` | `#1E2124` | Primary high-contrast text and solid buttons |
| `--color-text-secondary`| `#5B6168` | Secondary labels, timestamps, metadata |
| `--color-text-muted` | `#8A8F95` | Tertiary hints and helper descriptions |
| `--color-success` | `#2E7D4F` | Paid status, successful transitions |
| `--color-warning` | `#B7791F` | In review, quotations, partial payments |
| `--color-danger` | `#B3261E` | Revenue at risk, overdue balances, errors |

---

## 3. Typography & Numerals

- **Font Family**: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- **Monospace Family**: `ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace` (strictly for invoice numbers, codes, and JSON evidence)
- **Tabular Figures**: `font-variant-numeric: tabular-nums` enabled on all financial tables, metrics, and badges.
- **Alignment**: Strict right-alignment on all monetary figures.
- **Scale**: Fixed typographic hierarchy (11px, 12px, 13px, 14px, 15px, 18px, 20px, 24px) without fluid scaling.

---

## 4. Components & Affordances

### Buttons
- **Primary**: Solid graphite (`#1E2124`), white text, 1px border.
- **Secondary**: Crisp white background, 1px graphite border (`#D9DBDD`).
- **Danger**: Crimson (`#B3261E`), white text.
- **Focus Ring**: `outline: 2px solid #1E2124; outline-offset: 2px;` for WCAG AA compliance.
- **Motion**: `transition: none !important;` instant hover feedback.

### Tables
- Dense, highly readable financial tables.
- Sticky, uppercase 11px/12px headers with subtle background (`#F8F9FA`).
- Alternating subtle hover states (`#FAFBFC`).

### Status Badges
- Lowercase sentence case badges with 1px border and tinted background.
- Green for `active` / `paid`.
- Amber for `quotation` / `in_review` / `paused`.
- Red for `overdue` / `high priority alert` / `closed`.
