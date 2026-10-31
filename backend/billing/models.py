import uuid
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.constants import InvoiceStatus
from core.money import quantize_money
from products.models import Product, ProductVariant
from subscriptions.models import Customer, Subscription


class NumberSequence(models.Model):
    sequence_type = models.CharField(max_length=50, unique=True)
    prefix = models.CharField(max_length=20, default='INV-')
    next_number = models.PositiveIntegerField(default=1)

    @classmethod
    def get_next(cls, sequence_type='invoice', prefix='INV-') -> str:
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(
                sequence_type=sequence_type,
                defaults={'prefix': prefix, 'next_number': 1}
            )
            current_num = seq.next_number
            seq.next_number = current_num + 1
            seq.save()
            return f"{seq.prefix}{current_num:05d}"


class Invoice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.CONFIRMED
    )
    period_start = models.DateField()
    period_end = models.DateField()
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    balance_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    void_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-id']
        constraints = [
            # Guarantees no two non-void invoices exist for the same subscription and period start
            UniqueConstraint(
                fields=['subscription', 'period_start'],
                condition=~Q(status=InvoiceStatus.VOID),
                name='unique_subscription_active_period'
            ),
            CheckConstraint(
                condition=Q(subtotal__gte=0),
                name='invoice_subtotal_gte_0'
            ),
            CheckConstraint(
                condition=Q(discount_amount__gte=0),
                name='invoice_discount_amount_gte_0'
            ),
            CheckConstraint(
                condition=Q(tax_amount__gte=0),
                name='invoice_tax_amount_gte_0'
            ),
            CheckConstraint(
                condition=Q(total_amount__gte=0),
                name='invoice_total_amount_gte_0'
            ),
            CheckConstraint(
                condition=Q(amount_paid__gte=0),
                name='invoice_amount_paid_gte_0'
            ),
            CheckConstraint(
                condition=Q(balance_due__gte=0),
                name='invoice_balance_due_gte_0'
            ),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name} (Rs. {self.total_amount})"

    def clean(self):
        super().clean()
        for field in ['subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'amount_paid', 'balance_due']:
            val = getattr(self, field, None)
            if val is not None:
                setattr(self, field, quantize_money(val))

    @property
    def is_partially_paid(self) -> bool:
        return self.amount_paid > Decimal('0.00') and self.balance_due > Decimal('0.00') and self.status != InvoiceStatus.VOID

    @property
    def is_overdue(self) -> bool:
        today = timezone.localdate()
        return (
            self.status == InvoiceStatus.CONFIRMED and
            self.balance_due > Decimal('0.00') and
            self.due_date < today
        )

    @property
    def display_status(self) -> str:
        if self.status == InvoiceStatus.VOID:
            return 'Void'
        if self.status == InvoiceStatus.PAID or self.balance_due == Decimal('0.00'):
            return 'Paid'
        if self.status == InvoiceStatus.DRAFT:
            return 'Draft'
        if self.is_overdue:
            return 'Overdue'
        if self.is_partially_paid:
            return 'Partially Paid'
        return 'Confirmed'


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items'
    )
    # Snapshots
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    line_subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        ordering = ['id']
        constraints = [
            CheckConstraint(
                condition=Q(quantity__gt=0),
                name='invoice_item_quantity_gt_0'
            ),
            CheckConstraint(
                condition=Q(unit_price__gte=0),
                name='invoice_item_unit_price_gte_0'
            ),
        ]

    def __str__(self):
        v = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.product_name}{v} x {self.quantity} = Rs. {self.line_total}"


class BillingRun(models.Model):
    run_date = models.DateField()
    invoices_created = models.PositiveIntegerField(default=0)
    total_billed = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00')
    )
    status = models.CharField(max_length=20, default='success')
    log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Billing Run {self.run_date} ({self.invoices_created} invoices, Rs. {self.total_billed})"
