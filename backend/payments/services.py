from datetime import date
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.constants import InvoiceStatus, PaymentMethod
from core.money import quantize_money
from billing.models import Invoice
from payments.models import Payment


class PaymentError(Exception):
    """Base exception for payment operations."""
    pass


class OverpaymentError(PaymentError):
    """Raised when payment exceeds the invoice balance due."""
    pass


def record(
    invoice: Invoice,
    amount: Decimal,
    method: str = PaymentMethod.BANK_TRANSFER,
    payment_date: date = None,
    reference: str = "",
    note: str = "",
    actor = None,
    idempotency_key: str = ""
) -> Payment:
    """
    Record a partial or full payment against an invoice.
    Enforces atomic updates with select_for_update, idempotency, and overpayment prevention.
    """
    amount = quantize_money(amount)
    if amount <= Decimal('0.00'):
        raise PaymentError("Payment amount must be greater than zero.")

    if payment_date is None:
        payment_date = timezone.localdate()

    cleaned_idempotency_key = idempotency_key.strip() if idempotency_key else None

    with transaction.atomic():
        # Check idempotency
        if cleaned_idempotency_key:
            existing = Payment.objects.filter(idempotency_key=cleaned_idempotency_key).first()
            if existing:
                return existing

        # Lock invoice for update
        locked_invoice = Invoice.objects.select_for_update().get(id=invoice.id)

        if locked_invoice.status == InvoiceStatus.VOID:
            raise PaymentError(f"Cannot record payment against void invoice {locked_invoice.invoice_number}.")

        if amount > locked_invoice.balance_due:
            raise OverpaymentError(
                f"Payment amount (Rs. {amount}) exceeds remaining balance due (Rs. {locked_invoice.balance_due}) "
                f"for invoice {locked_invoice.invoice_number}."
            )

        # Update invoice balances
        locked_invoice.amount_paid = quantize_money(locked_invoice.amount_paid + amount)
        locked_invoice.balance_due = quantize_money(locked_invoice.balance_due - amount)

        if locked_invoice.balance_due == Decimal('0.00'):
            locked_invoice.status = InvoiceStatus.PAID

        locked_invoice.save(update_fields=['amount_paid', 'balance_due', 'status', 'updated_at'])

        # Create payment record
        payment = Payment.objects.create(
            invoice=locked_invoice,
            customer=locked_invoice.customer,
            amount=amount,
            payment_method=method,
            payment_date=payment_date,
            reference=reference.strip(),
            note=note.strip(),
            idempotency_key=cleaned_idempotency_key,
            recorded_by=actor if actor and getattr(actor, 'is_authenticated', False) else None
        )

    return payment
