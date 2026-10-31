import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator
from core.constants import SubscriptionStatus
from core.money import quantize_money
from products.models import Product, ProductVariant, Plan, TaxRule, Discount


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    billing_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company_name})" if self.company_name else self.name

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()


class Subscription(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.DRAFT
    )
    start_date = models.DateField(help_text='First period start date')
    next_billing_date = models.DateField(help_text='Date when next period should be billed')
    end_date = models.DateField(null=True, blank=True, help_text='Optional fixed end date')
    quotation_valid_until = models.DateField(null=True, blank=True)
    tax_rule = models.ForeignKey(
        TaxRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    pause_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    close_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_subscriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SUB-{self.id:04d} - {self.customer.name} - {self.plan.name} ({self.get_status_display()})"

    @property
    def is_billable(self):
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class SubscriptionItem(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='subscription_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subscription_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        ordering = ['id']
        constraints = [
            CheckConstraint(
                condition=Q(quantity__gt=0),
                name='sub_item_quantity_gt_0'
            ),
            CheckConstraint(
                condition=Q(unit_price__gte=0),
                name='sub_item_unit_price_gte_0'
            ),
        ]

    def __str__(self):
        v_str = f" ({self.variant.name})" if self.variant else ""
        return f"{self.product.name}{v_str} x {self.quantity}"

    def clean(self):
        super().clean()
        if self.unit_price is not None:
            self.unit_price = quantize_money(self.unit_price)

    @property
    def line_subtotal(self):
        return quantize_money(self.unit_price * self.quantity)


class SubscriptionEvent(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='events'
    )
    action = models.CharField(max_length=50)
    from_status = models.CharField(max_length=20, choices=SubscriptionStatus.choices)
    to_status = models.CharField(max_length=20, choices=SubscriptionStatus.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_actions'
    )
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_name = self.actor.full_name if self.actor else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action}: {self.from_status} -> {self.to_status} by {actor_name}"
