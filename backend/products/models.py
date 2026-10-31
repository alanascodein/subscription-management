from decimal import Decimal
from django.db import models
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator, MaxValueValidator
from core.constants import BillingCycle, DiscountType
from core.money import quantize_money


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    sales_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(
                condition=Q(cost_price__gte=0),
                name='product_cost_price_gte_0'
            ),
            CheckConstraint(
                condition=Q(sales_price__gte=0),
                name='product_sales_price_gte_0'
            ),
        ]

    def __str__(self):
        return f"{self.name} (Rs. {self.sales_price})"

    def clean(self):
        super().clean()
        if self.cost_price is not None:
            self.cost_price = quantize_money(self.cost_price)
        if self.sales_price is not None:
            self.sales_price = quantize_money(self.sales_price)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=100, blank=True)
    extra_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['product', 'name']
        unique_together = ('product', 'name')
        constraints = [
            CheckConstraint(
                condition=Q(extra_price__gte=0),
                name='variant_extra_price_gte_0'
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name} (+Rs. {self.extra_price})"

    def clean(self):
        super().clean()
        if self.extra_price is not None:
            self.extra_price = quantize_money(self.extra_price)

    @property
    def total_unit_price(self):
        return self.product.sales_price + self.extra_price


class Plan(models.Model):
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY
    )
    minimum_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    availability_start = models.DateField(null=True, blank=True)
    availability_end = models.DateField(null=True, blank=True)
    auto_close = models.BooleanField(
        default=False,
        help_text='Automatically close subscription when availability ends'
    )
    early_close_allowed = models.BooleanField(
        default=True,
        help_text='Allow customer or staff to close subscription early'
    )
    pause_allowed = models.BooleanField(
        default=True,
        help_text='Allow pausing subscription lifecycle'
    )
    renewal_allowed = models.BooleanField(
        default=True,
        help_text='Allow renewal after end date'
    )
    grace_days = models.PositiveIntegerField(
        default=3,
        help_text='Number of days after period start before flagging missing invoice'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(
                condition=Q(minimum_quantity__gt=0),
                name='plan_min_qty_gt_0'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_cycle_display()})"


class TaxRule(models.Model):
    name = models.CharField(max_length=100)
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(
                condition=Q(rate_percent__gte=0) & Q(rate_percent__lte=100),
                name='tax_rate_percent_range'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"

    def clean(self):
        super().clean()
        if self.rate_percent is not None:
            self.rate_percent = quantize_money(self.rate_percent)


class Discount(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum number of times this discount can be applied'
    )
    times_used = models.PositiveIntegerField(default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        constraints = [
            CheckConstraint(
                condition=Q(value__gte=0),
                name='discount_value_gte_0'
            ),
        ]

    def __str__(self):
        unit = '%' if self.discount_type == DiscountType.PERCENT else ' Rs'
        return f"{self.code} - {self.name} ({self.value}{unit})"

    def clean(self):
        super().clean()
        if self.value is not None:
            self.value = quantize_money(self.value)
        if self.discount_type == DiscountType.PERCENT and self.value > Decimal('100.00'):
            from django.core.exceptions import ValidationError
            raise ValidationError({'value': 'Percentage discount cannot exceed 100%'})

    @property
    def is_usable(self):
        if not self.is_active:
            return False
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False
        return True
