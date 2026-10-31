from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.constants import AlertType, AlertStatus, Priority
from core.money import quantize_money
from subscriptions.models import Subscription
from billing.models import Invoice


class Alert(models.Model):
    deduplication_key = models.CharField(
        max_length=255,
        unique=True,
        help_text='Unique hash/key stopping duplicate alerts across recurring runs'
    )
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    title = models.CharField(max_length=255)
    reason = models.TextField(help_text='Explanation of why this was flagged')
    evidence = models.JSONField(
        default=dict,
        help_text='Structured evidence details supporting the detection'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Financial exposure amount'
    )
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.NEW
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    period_start = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_alerts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(
                condition=Q(amount__gte=0),
                name='alert_amount_gte_0'
            ),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()} | {self.get_alert_type_display()}] {self.title} - Rs. {self.amount}"

    def clean(self):
        super().clean()
        if self.amount is not None:
            self.amount = quantize_money(self.amount)

    @property
    def is_open(self):
        return self.status in [AlertStatus.NEW, AlertStatus.IN_REVIEW]


class AuditLog(models.Model):
    action = models.CharField(max_length=100)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_entries'
    )
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_email = self.actor.email if self.actor else "System"
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {actor_email}: {self.action} on {self.target_model} #{self.target_id}"
