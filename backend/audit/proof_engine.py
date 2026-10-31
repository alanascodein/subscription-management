from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from core.constants import AlertType, AlertStatus, Priority, SubscriptionStatus, InvoiceStatus
from core.money import quantize_money
from core import pricing
from subscriptions.models import Subscription
from billing.models import Invoice
from billing import services as billing_services
from audit.models import Alert, AuditLog


@dataclass
class RunSummary:
    as_of: date
    alerts_created: int
    alerts_existing: int
    revenue_at_risk: Decimal
    details: List[str]


def compute_revenue_at_risk() -> Decimal:
    """
    Calculate the total Revenue at Risk across all active, unresolved alerts.
    De-duplicates exposure so the same financial record isn't double-counted.
    """
    open_alerts = Alert.objects.filter(status__in=[AlertStatus.NEW, AlertStatus.IN_REVIEW])
    seen_invoices = set()
    seen_subscriptions_periods = set()
    total_risk = Decimal('0.00')

    for alert in open_alerts:
        if alert.invoice_id:
            if alert.invoice_id not in seen_invoices:
                seen_invoices.add(alert.invoice_id)
                total_risk += alert.amount
        elif alert.subscription_id and alert.period_start:
            key = (alert.subscription_id, alert.period_start)
            if key not in seen_subscriptions_periods:
                seen_subscriptions_periods.add(key)
                total_risk += alert.amount
        else:
            total_risk += alert.amount

    return quantize_money(total_risk)


def run(as_of: date = None) -> RunSummary:
    """
    Deterministic Proof Engine execution.
    Inspects expected billing state vs actual invoices/payments and raises deduplicated alerts.
    """
    if as_of is None:
        as_of = timezone.localdate()

    created_count = 0
    existing_count = 0
    log_messages = []

    # 1. Detect Missed Invoices
    active_subs = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE).select_related('customer', 'plan', 'discount', 'tax_rule').prefetch_related('items__product', 'items__variant')
    for sub in active_subs:
        cutoff = sub.next_billing_date + timedelta(days=sub.plan.grace_days)
        if as_of > cutoff:
            # Check if invoice exists for this period
            has_invoice = Invoice.objects.filter(
                subscription=sub,
                period_start=sub.next_billing_date
            ).exclude(status=InvoiceStatus.VOID).exists()

            if not has_invoice:
                calc = pricing.calculate(sub.items.all(), discount=sub.discount, tax_rule=sub.tax_rule)
                expected_amt = calc.total_amount
                days_overdue = (as_of - sub.next_billing_date).days
                prio = Priority.HIGH if (expected_amt >= Decimal('5000.00') or days_overdue > 14) else Priority.MEDIUM

                dedup_key = f"missed_invoice:{sub.id}:{sub.next_billing_date}"
                alert, created = Alert.objects.get_or_create(
                    deduplication_key=dedup_key,
                    defaults={
                        'alert_type': AlertType.MISSED_INVOICE,
                        'priority': prio,
                        'title': f"Missing invoice for {sub.customer.name} ({sub.plan.name})",
                        'reason': (
                            f"Subscription was expected to be billed on {sub.next_billing_date}. "
                            f"Grace period of {sub.plan.grace_days} days expired on {cutoff} without an invoice."
                        ),
                        'evidence': {
                            'subscription_id': sub.id,
                            'customer_name': sub.customer.name,
                            'period_start': str(sub.next_billing_date),
                            'grace_days': sub.plan.grace_days,
                            'days_overdue': days_overdue,
                            'expected_amount': str(expected_amt),
                        },
                        'amount': expected_amt,
                        'subscription': sub,
                        'period_start': sub.next_billing_date,
                        'status': AlertStatus.NEW,
                    }
                )
                if created:
                    created_count += 1
                    log_messages.append(f"Created missed_invoice alert for Sub {sub.id}")
                else:
                    existing_count += 1

    # 2. Detect Overdue Invoices
    overdue_invoices = Invoice.objects.filter(
        status=InvoiceStatus.CONFIRMED,
        balance_due__gt=Decimal('0.00'),
        due_date__lt=as_of
    ).select_related('customer', 'subscription')

    for inv in overdue_invoices:
        days_past_due = (as_of - inv.due_date).days
        if days_past_due > 30 or inv.balance_due >= Decimal('10000.00'):
            prio = Priority.HIGH
        elif days_past_due > 7:
            prio = Priority.MEDIUM
        else:
            prio = Priority.LOW

        dedup_key = f"overdue_invoice:{inv.id}:{inv.due_date}"
        alert, created = Alert.objects.get_or_create(
            deduplication_key=dedup_key,
            defaults={
                'alert_type': AlertType.OVERDUE_INVOICE,
                'priority': prio,
                'title': f"Overdue invoice {inv.invoice_number} ({days_past_due} days late)",
                'reason': (
                    f"Invoice {inv.invoice_number} of Rs. {inv.total_amount} was due on {inv.due_date}. "
                    f"Outstanding balance of Rs. {inv.balance_due} remains unpaid."
                ),
                'evidence': {
                    'invoice_id': inv.id,
                    'invoice_number': inv.invoice_number,
                    'customer_name': inv.customer.name,
                    'due_date': str(inv.due_date),
                    'days_past_due': days_past_due,
                    'total_amount': str(inv.total_amount),
                    'amount_paid': str(inv.amount_paid),
                    'balance_due': str(inv.balance_due),
                },
                'amount': inv.balance_due,
                'invoice': inv,
                'subscription': inv.subscription,
                'period_start': inv.period_start,
                'status': AlertStatus.NEW,
            }
        )
        if created:
            created_count += 1
            log_messages.append(f"Created overdue_invoice alert for Invoice {inv.invoice_number}")
        else:
            existing_count += 1

    # 3. Detect Duplicate Invoices
    # Find active non-void invoices with same customer and period_start
    all_active_invoices = Invoice.objects.exclude(status=InvoiceStatus.VOID).values('customer_id', 'period_start').distinct()
    for entry in all_active_invoices:
        cust_id = entry['customer_id']
        p_start = entry['period_start']
        matches = list(Invoice.objects.filter(customer_id=cust_id, period_start=p_start).exclude(status=InvoiceStatus.VOID))
        if len(matches) > 1:
            # Duplicate found
            dup_numbers = [m.invoice_number for m in matches]
            extra_amount = sum((m.total_amount for m in matches[1:]), Decimal('0.00'))
            dedup_key = f"possible_duplicate:{cust_id}:{p_start}"

            alert, created = Alert.objects.get_or_create(
                deduplication_key=dedup_key,
                defaults={
                    'alert_type': AlertType.POSSIBLE_DUPLICATE,
                    'priority': Priority.HIGH,
                    'title': f"Duplicate billing detected for period {p_start}",
                    'reason': (
                        f"Customer has {len(matches)} overlapping invoices ({', '.join(dup_numbers)}) "
                        f"for billing period starting {p_start}."
                    ),
                    'evidence': {
                        'customer_id': cust_id,
                        'period_start': str(p_start),
                        'invoice_count': len(matches),
                        'invoices': [{'number': m.invoice_number, 'amount': str(m.total_amount)} for m in matches],
                    },
                    'amount': extra_amount,
                    'subscription': matches[0].subscription,
                    'period_start': p_start,
                    'status': AlertStatus.NEW,
                }
            )
            if created:
                created_count += 1
                log_messages.append(f"Created possible_duplicate alert for Customer {cust_id} period {p_start}")
            else:
                existing_count += 1

    # 4. Detect Invoice Anomalies (stored amounts mismatch recomputed line items)
    confirmed_invoices = Invoice.objects.exclude(status=InvoiceStatus.VOID).prefetch_related('items')
    for inv in confirmed_invoices:
        lines = list(inv.items.all())
        sum_lines = sum((l.line_total for l in lines), Decimal('0.00'))
        if sum_lines != inv.total_amount or inv.total_amount < Decimal('0.00'):
            diff = abs(inv.total_amount - sum_lines)
            dedup_key = f"invoice_anomaly:{inv.id}:{diff}"
            alert, created = Alert.objects.get_or_create(
                deduplication_key=dedup_key,
                defaults={
                    'alert_type': AlertType.INVOICE_ANOMALY,
                    'priority': Priority.HIGH,
                    'title': f"Total mismatch on invoice {inv.invoice_number}",
                    'reason': (
                        f"Invoice total stored is Rs. {inv.total_amount}, but calculated sum of lines is Rs. {sum_lines}."
                    ),
                    'evidence': {
                        'invoice_id': inv.id,
                        'invoice_number': inv.invoice_number,
                        'stored_total': str(inv.total_amount),
                        'calculated_sum': str(sum_lines),
                        'difference': str(diff),
                    },
                    'amount': diff,
                    'invoice': inv,
                    'subscription': inv.subscription,
                    'period_start': inv.period_start,
                    'status': AlertStatus.NEW,
                }
            )
            if created:
                created_count += 1
            else:
                existing_count += 1

    # 5. Detect Renewal Attention
    nearing_subs = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__isnull=False,
        end_date__lte=as_of + timedelta(days=14),
        end_date__gte=as_of
    ).select_related('customer', 'plan')

    for sub in nearing_subs:
        days_left = (sub.end_date - as_of).days
        dedup_key = f"renewal_attention:{sub.id}:{sub.end_date}"
        alert, created = Alert.objects.get_or_create(
            deduplication_key=dedup_key,
            defaults={
                'alert_type': AlertType.RENEWAL_ATTENTION,
                'priority': Priority.LOW if days_left > 7 else Priority.MEDIUM,
                'title': f"Subscription {sub.id} expiring in {days_left} days",
                'reason': f"Customer {sub.customer.name} subscription reaches end date on {sub.end_date}.",
                'evidence': {
                    'subscription_id': sub.id,
                    'customer_name': sub.customer.name,
                    'end_date': str(sub.end_date),
                    'days_remaining': days_left,
                },
                'amount': Decimal('0.00'),
                'subscription': sub,
                'status': AlertStatus.NEW,
            }
        )
        if created:
            created_count += 1
        else:
            existing_count += 1

    current_risk = compute_revenue_at_risk()

    return RunSummary(
        as_of=as_of,
        alerts_created=created_count,
        alerts_existing=existing_count,
        revenue_at_risk=current_risk,
        details=log_messages,
    )


def apply_fix(alert: Alert, actor=None) -> Alert:
    """
    Apply guarded one-click fix for an alert.
    Writes an audit entry and updates alert status to Resolved.
    """
    with transaction.atomic():
        if alert.alert_type == AlertType.MISSED_INVOICE:
            if not alert.subscription or not alert.period_start:
                raise ValueError("Alert lacks subscription or period start required to generate invoice.")
            
            # Check if invoice already exists
            existing = Invoice.objects.filter(
                subscription=alert.subscription,
                period_start=alert.period_start
            ).exclude(status=InvoiceStatus.VOID).first()

            if not existing:
                new_inv = billing_services.create_invoice(
                    subscription=alert.subscription,
                    period_start=alert.period_start,
                    actor=actor
                )
                fix_note = f"Generated missing invoice {new_inv.invoice_number} for period {alert.period_start}."
            else:
                fix_note = f"Verified existing invoice {existing.invoice_number}."

            alert.status = AlertStatus.RESOLVED
            alert.review_notes = (alert.review_notes + "\n" + fix_note).strip()
            alert.reviewed_by = actor if actor and getattr(actor, 'is_authenticated', False) else None
            alert.reviewed_at = timezone.now()
            alert.save()

            AuditLog.objects.create(
                action='apply_fix_missed_invoice',
                actor=alert.reviewed_by,
                target_model='Alert',
                target_id=str(alert.id),
                details={'fix_note': fix_note, 'alert_id': alert.id}
            )

        elif alert.alert_type == AlertType.POSSIBLE_DUPLICATE:
            alert.status = AlertStatus.IN_REVIEW
            alert.review_notes = "Marked for review. Inspect duplicate invoices before voiding."
            alert.reviewed_by = actor if actor and getattr(actor, 'is_authenticated', False) else None
            alert.reviewed_at = timezone.now()
            alert.save()

        elif alert.alert_type == AlertType.INVOICE_ANOMALY:
            # Rebalance stored total to sum of line items if invoice exists
            if alert.invoice:
                sum_lines = sum((l.line_total for l in alert.invoice.items.all()), Decimal('0.00'))
                alert.invoice.total_amount = sum_lines
                alert.invoice.balance_due = quantize_money(max(Decimal('0.00'), sum_lines - alert.invoice.amount_paid))
                alert.invoice.save()
                alert.status = AlertStatus.RESOLVED
                alert.review_notes = f"Fixed stored total on invoice {alert.invoice.invoice_number} to Rs. {sum_lines}."
                alert.reviewed_by = actor if actor and getattr(actor, 'is_authenticated', False) else None
                alert.reviewed_at = timezone.now()
                alert.save()

                AuditLog.objects.create(
                    action='apply_fix_invoice_anomaly',
                    actor=alert.reviewed_by,
                    target_model='Invoice',
                    target_id=str(alert.invoice.id),
                    details={'new_total': str(sum_lines)}
                )

        else:
            alert.status = AlertStatus.RESOLVED
            alert.reviewed_by = actor if actor and getattr(actor, 'is_authenticated', False) else None
            alert.reviewed_at = timezone.now()
            alert.save()

    return alert
