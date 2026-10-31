from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.constants import SubscriptionStatus, InvoiceStatus
from core.money import quantize_money
from core import periods, pricing
from subscriptions.models import Subscription
from billing.models import Invoice, InvoiceItem, NumberSequence, BillingRun


def create_invoice(
    subscription: Subscription,
    period_start: date,
    status: str = InvoiceStatus.CONFIRMED,
    issue_date: date = None,
    due_date: date = None,
    actor = None
) -> Invoice:
    """
    Generate an invoice for a specific subscription and billing period start.
    Performs pricing calculation, snapshots lines, and updates discount usage atomically.
    """
    if issue_date is None:
        issue_date = timezone.localdate()

    period_end = periods.end(period_start, subscription.plan.cycle)

    if due_date is None:
        # Default 15 days payment term from period start (or issue date if later)
        due_date = max(period_start, issue_date) + timedelta(days=15)

    # Check for discount validity
    discount = subscription.discount
    if discount and not discount.is_usable:
        discount = None

    tax_rule = subscription.tax_rule if (subscription.tax_rule and subscription.tax_rule.is_active) else None

    # Calculate pricing
    items = list(subscription.items.all())
    pricing_result = pricing.calculate(items, discount=discount, tax_rule=tax_rule)

    with transaction.atomic():
        invoice_number = NumberSequence.get_next(sequence_type='invoice', prefix='INV-')

        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            subscription=subscription,
            customer=subscription.customer,
            status=status,
            period_start=period_start,
            period_end=period_end,
            issue_date=issue_date,
            due_date=due_date,
            subtotal=pricing_result.subtotal,
            discount_amount=pricing_result.discount_amount,
            tax_amount=pricing_result.tax_amount,
            total_amount=pricing_result.total_amount,
            amount_paid=Decimal('0.00'),
            balance_due=pricing_result.total_amount,
        )

        # Snapshot invoice items
        for lr in pricing_result.items:
            InvoiceItem.objects.create(
                invoice=invoice,
                product_id=lr.product_id,
                variant_id=lr.variant_id,
                product_name=lr.name,
                variant_name="",
                description=lr.description,
                quantity=lr.quantity,
                unit_price=lr.unit_price,
                line_subtotal=lr.subtotal,
                discount_amount=lr.discount_amount,
                net_amount=lr.net_amount,
                tax_amount=lr.tax_amount,
                line_total=lr.total_amount,
            )

        if discount and pricing_result.discount_amount > Decimal('0.00'):
            discount.times_used += 1
            discount.save(update_fields=['times_used'])

    return invoice


def run(run_date: date = None) -> BillingRun:
    """
    Execute billing run as of run_date.
    Finds active subscriptions whose next_billing_date <= run_date.
    Catches up any missed periods in sequence and guarantees no duplicate periods.
    """
    if run_date is None:
        run_date = timezone.localdate()

    invoices_created_count = 0
    total_billed_amount = Decimal('0.00')
    log_lines = []

    log_lines.append(f"Starting billing run for date: {run_date}")

    with transaction.atomic():
        # Lock subscriptions to avoid concurrent billing runs
        subscriptions = Subscription.objects.select_for_update().filter(
            status=SubscriptionStatus.ACTIVE,
            next_billing_date__lte=run_date
        ).select_related('customer', 'plan', 'tax_rule', 'discount')

        for sub in subscriptions:
            # Handle possible auto-close if past end_date
            if sub.end_date and sub.next_billing_date > sub.end_date:
                if sub.plan.auto_close:
                    sub.status = SubscriptionStatus.CLOSED
                    sub.close_date = run_date
                    sub.close_reason = "Auto-closed on reaching end date."
                    sub.save()
                    log_lines.append(f"Subscription {sub.id} reached end date {sub.end_date} and was auto-closed.")
                continue

            # Catch up missed periods sequentially
            while sub.next_billing_date <= run_date:
                period_start = sub.next_billing_date

                # Check if non-void invoice already exists for this period
                existing_invoice = Invoice.objects.filter(
                    subscription=sub,
                    period_start=period_start
                ).exclude(status=InvoiceStatus.VOID).first()

                if not existing_invoice:
                    invoice = create_invoice(subscription=sub, period_start=period_start, issue_date=run_date)
                    invoices_created_count += 1
                    total_billed_amount += invoice.total_amount
                    log_lines.append(f"Created invoice {invoice.invoice_number} for Sub {sub.id} (Period: {period_start})")
                else:
                    log_lines.append(f"Invoice {existing_invoice.invoice_number} already exists for Sub {sub.id} (Period: {period_start})")

                # Advance next billing date
                next_date = periods.next_start(period_start, sub.plan.cycle)
                sub.next_billing_date = next_date

                # Stop catch-up if past end date
                if sub.end_date and next_date > sub.end_date:
                    if sub.plan.auto_close:
                        sub.status = SubscriptionStatus.CLOSED
                        sub.close_date = run_date
                        sub.close_reason = "Auto-closed upon completing final period."
                    break

            sub.save()

        billing_run = BillingRun.objects.create(
            run_date=run_date,
            invoices_created=invoices_created_count,
            total_billed=total_billed_amount,
            status='success',
            log="\n".join(log_lines),
        )

    return billing_run


def confirm_invoice(invoice: Invoice, actor=None) -> Invoice:
    """
    Confirm a draft invoice.
    """
    if invoice.status != InvoiceStatus.DRAFT:
        raise ValueError(f"Only draft invoices can be confirmed. Current status: {invoice.status}")
    invoice.status = InvoiceStatus.CONFIRMED
    invoice.save(update_fields=['status', 'updated_at'])
    return invoice


def void_invoice(invoice: Invoice, reason: str, actor=None) -> Invoice:
    """
    Void an invoice. Requires an explicit reason.
    Voiding frees the billing period so a correct invoice can be created.
    """
    if not reason or not reason.strip():
        raise ValueError("A reason is strictly required to void an invoice.")
    if invoice.status == InvoiceStatus.VOID:
        return invoice
    if invoice.amount_paid > Decimal('0.00'):
        raise ValueError("Cannot void an invoice that has recorded payments. Reverse payments first.")

    invoice.status = InvoiceStatus.VOID
    invoice.void_reason = reason.strip()
    invoice.save(update_fields=['status', 'void_reason', 'updated_at'])
    return invoice
