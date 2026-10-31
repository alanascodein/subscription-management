# ProofBill API & Internal Contract

Refer to [CONTRACT.md](file:///C:/Users/adhar/subscription-management/CONTRACT.md) for full service signatures, lifecycle constraints, and data definitions.

## Key Backend Guarantees:
1. **Financial Precision**: All calculations use `Decimal` with `ROUND_HALF_UP`.
2. **Billing Idempotency**: Billing runs check existing confirmed/draft invoices before creating new ones; partial database constraints prevent duplicate active periods.
3. **Auditability**: Every lifecycle shift generates an immutable `SubscriptionEvent`.
4. **Guarded State**: Transitions outside allowable state machines fail with an explicit `LifecycleError`.
5. **No Overpayments**: Payment recording enforces `amount <= invoice.balance_due` within an atomic transaction.
