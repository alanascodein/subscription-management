from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from core.constants import SubscriptionStatus, InvoiceStatus, BillingCycle
from core.money import quantize_money
from subscriptions.models import Subscription
from billing.models import Invoice
from payments.models import Payment
from audit.proof_engine import compute_revenue_at_risk


def summary(filters: dict = None) -> dict:
    """
    Compute database-aggregated financial metrics for the ProofBill dashboard.
    All figures are derived directly from real database records.
    """
    today = timezone.localdate()
    month_start = today.replace(day=1)

    # 1. Active subscriptions count
    active_subs_qs = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE)
    active_count = active_subs_qs.count()

    # 2. Collected revenue this month
    collected_month_val = Payment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    collected_month = quantize_money(collected_month_val)

    # Total collected all-time
    total_collected_val = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_collected = quantize_money(total_collected_val)

    # 3. Outstanding balance (confirmed non-void invoices with balance > 0)
    outstanding_val = Invoice.objects.filter(
        status=InvoiceStatus.CONFIRMED,
        balance_due__gt=Decimal('0.00')
    ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00')
    outstanding = quantize_money(outstanding_val)

    # 4. Overdue amount and count
    overdue_qs = Invoice.objects.filter(
        status=InvoiceStatus.CONFIRMED,
        balance_due__gt=Decimal('0.00'),
        due_date__lt=today
    ).select_related('customer', 'subscription')

    overdue_stats = overdue_qs.aggregate(
        total=Sum('balance_due'),
        count=Count('id')
    )
    overdue_amount = quantize_money(overdue_stats['total'] or Decimal('0.00'))
    overdue_count = overdue_stats['count']

    overdue_rows = []
    for inv in overdue_qs.order_by('due_date')[:10]:
        days_late = (today - inv.due_date).days
        overdue_rows.append({
            'invoice_id': inv.id,
            'uuid': str(inv.uuid),
            'invoice_number': inv.invoice_number,
            'customer_name': inv.customer.name,
            'due_date': inv.due_date,
            'days_overdue': days_late,
            'total_amount': inv.total_amount,
            'balance_due': inv.balance_due,
        })

    # 5. MRR (Monthly Recurring Revenue)
    # Calculated on active subscriptions
    mrr_val = Decimal('0.00')
    for sub in active_subs_qs.prefetch_related('items__product', 'items__variant').select_related('plan', 'discount', 'tax_rule'):
        # Base monthly value per cycle
        sub_total = sum((item.line_subtotal for item in sub.items.all()), Decimal('0.00'))
        if sub.plan.cycle == BillingCycle.MONTHLY:
            monthly_equiv = sub_total
        elif sub.plan.cycle == BillingCycle.YEARLY:
            monthly_equiv = sub_total / Decimal('12.00')
        elif sub.plan.cycle == BillingCycle.WEEKLY:
            monthly_equiv = (sub_total * Decimal('52.00')) / Decimal('12.00')
        elif sub.plan.cycle == BillingCycle.DAILY:
            monthly_equiv = sub_total * Decimal('30.00')
        else:
            monthly_equiv = sub_total
        mrr_val += monthly_equiv

    mrr = quantize_money(mrr_val)

    # 6. Revenue at Risk (Proof Engine alert total)
    revenue_at_risk = compute_revenue_at_risk()

    # 7. Recent payments
    recent_payments_qs = Payment.objects.select_related('invoice', 'customer').order_by('-payment_date', '-id')[:5]
    recent_payments = []
    for p in recent_payments_qs:
        recent_payments.append({
            'id': p.id,
            'invoice_number': p.invoice.invoice_number,
            'customer_name': p.customer.name,
            'amount': p.amount,
            'method': p.get_payment_method_display(),
            'date': p.payment_date,
            'reference': p.reference,
        })

    # 8. Upcoming renewals
    upcoming_renewals_qs = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30)
    ).select_related('customer', 'plan')[:5]

    upcoming_renewals = []
    for r in upcoming_renewals_qs:
        upcoming_renewals.append({
            'id': r.id,
            'uuid': str(r.uuid),
            'customer_name': r.customer.name,
            'plan_name': r.plan.name,
            'end_date': r.end_date,
            'days_remaining': (r.end_date - today).days,
        })

    # 9. Simple 6-month Trend
    trend = []
    for i in range(5, -1, -1):
        m_date = today - timedelta(days=i * 30)
        m_start = m_date.replace(day=1)
        next_month = (m_start + timedelta(days=32)).replace(day=1)
        collected = Payment.objects.filter(
            payment_date__gte=m_start,
            payment_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        trend.append({
            'month': m_start.strftime('%b %Y'),
            'collected': str(quantize_money(collected)),
        })

    return {
        'revenue_at_risk': revenue_at_risk,
        'overdue_amount': overdue_amount,
        'overdue_count': overdue_count,
        'outstanding': outstanding,
        'collected_month': collected_month,
        'total_collected': total_collected,
        'active_count': active_count,
        'mrr': mrr,
        'trend': trend,
        'recent_payments': recent_payments,
        'upcoming_renewals': upcoming_renewals,
        'overdue_rows': overdue_rows,
    }
