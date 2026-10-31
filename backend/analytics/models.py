from django.db import models
from django.utils import timezone
from decimal import Decimal

from core.money import quantize_money
from core.constants import SubscriptionStatus, InvoiceStatus
from subscriptions.models import Subscription
from billing.models import Invoice
from payments.models import Payment
from audit.proof_engine import compute_revenue_at_risk


class DashboardSnapshot(models.Model):
    """
    Cached read of the current dashboard aggregates.

    Kept intentionally simple: one row that analytics services can refresh
    when the seed/demo data changes, so the dashboard template always has
    something definite to render instead of an empty frame.
    """
    label = models.CharField(max_length=64, unique=True)
    captured_at = models.DateTimeField(default=timezone.now)

    active_count = models.PositiveIntegerField(default=0)
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    collected_month = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    outstanding = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    overdue_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    overdue_count = models.PositiveIntegerField(default=0)
    revenue_at_risk = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ('-captured_at',)

    def __str__(self):
        return f"{self.label} @ {self.captured_at:%Y-%m-%d %H:%M}"

    @classmethod
    def refresh_current(cls, label='current'):
        today = timezone.localdate()
        month_start = today.replace(day=1)

        active_subs_qs = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE)
        active_count = active_subs_qs.count()

        total_collected_val = Payment.objects.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        total_collected = quantize_money(total_collected_val)

        collected_month_val = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=today,
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        collected_month = quantize_money(collected_month_val)

        outstanding_val = Invoice.objects.filter(
            status=InvoiceStatus.CONFIRMED,
            balance_due__gt=Decimal('0.00'),
        ).aggregate(total=models.Sum('balance_due'))['total'] or Decimal('0.00')
        outstanding = quantize_money(outstanding_val)

        overdue_qs = Invoice.objects.filter(
            status=InvoiceStatus.CONFIRMED,
            balance_due__gt=Decimal('0.00'),
            due_date__lt=today,
        )
        overdue_stats = overdue_qs.aggregate(
            total=models.Sum('balance_due'),
            count=models.Count('id'),
        )
        overdue_amount = quantize_money(overdue_stats['total'] or Decimal('0.00'))
        overdue_count = overdue_stats['count'] or 0

        mrr_val = Decimal('0.00')
        from core.pricing import monthly_equivalent
        for sub in active_subs_qs.prefetch_related('items'):
            sub_total = sum((item.line_subtotal for item in sub.items.all()), Decimal('0.00'))
            mrr_val += monthly_equivalent(sub.plan.cycle, sub_total)

        mrr = quantize_money(mrr_val)
        revenue_at_risk = compute_revenue_at_risk()

        snapshot, _ = cls.objects.update_or_create(
            label=label,
            defaults={
                'captured_at': timezone.now(),
                'active_count': active_count,
                'mrr': mrr,
                'total_collected': total_collected,
                'collected_month': collected_month,
                'outstanding': outstanding,
                'overdue_amount': overdue_amount,
                'overdue_count': overdue_count,
                'revenue_at_risk': revenue_at_risk,
            },
        )
        return snapshot
