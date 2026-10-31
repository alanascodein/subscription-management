import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.constants import PaymentMethod
from core.money import quantize_money
from subscriptions.models import Customer
from billing.models import Invoice


class Payment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER
    )
    payment_date = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=150, blank=True)
    note = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        constraints = [
            CheckConstraint(
                condition=Q(amount__gt=0),
                name='payment_amount_gt_0'
            ),
        ]

    def __str__(self):
        return f"Payment {self.id} - Rs. {self.amount} for {self.invoice.invoice_number}"

    def clean(self):
        super().clean()
        if self.amount is not None:
            self.amount = quantize_money(self.amount)
