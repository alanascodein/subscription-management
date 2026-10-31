from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone
from core.constants import SubscriptionStatus, InvoiceStatus, BillingCycle
from core.money import quantize_money
from core.pricing import monthly_equivalent
from subscriptions.models import Subscription
from billing.models import Invoice
from payments.models import Payment
from audit.proof_engine import compute_revenue_at_risk
from analytics.models import DashboardSnapshot


def summary(filters: dict = None) -> dict:
    """
    Compute database-aggregated financial metrics for the ProofBill dashboard.

    All figures are derived directly from real database records, then cached
    into a DashboardSnapshot row so the template layer has a stable object to
    render.
    """
    snapshot = DashboardSnapshot.refresh_current(label='current')

    today = timezone.localdate()
    overdue_rows = []
    overdue_qs = Invoice.objects.filter(
        status=InvoiceStatus.CONFIRMED,
        balance_due__gt=Decimal('0.00'),
        due_date__lt=today,
    ).select_related('customer', 'subscription')

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

    upcoming_renewals_qs = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30),
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

    trend = []
    for i in range(5, -1, -1):
        m_date = today - timedelta(days=i * 30)
        m_start = m_date.replace(day=1)
        next_month = (m_start + timedelta(days=32)).replace(day=1)
        collected = Payment.objects.filter(
            payment_date__gte=m_start,
            payment_date__lt=next_month,
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        trend.append({
            'month': m_start.strftime('%b %Y'),
            'collected': str(quantize_money(collected)),
        })

    return {
        'snapshot': snapshot,
        'revenue_at_risk': snapshot.revenue_at_risk,
        'overdue_amount': snapshot.overdue_amount,
        'overdue_count': snapshot.overdue_count,
        'outstanding': snapshot.outstanding,
        'collected_month': snapshot.collected_month,
        'total_collected': snapshot.total_collected,
        'active_count': snapshot.active_count,
        'mrr': snapshot.mrr,
        'trend': trend,
        'recent_payments': recent_payments,
        'upcoming_renewals': upcoming_renewals,
        'overdue_rows': overdue_rows,
    }
