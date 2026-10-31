"""
Shared constants across ProofBill.
"""

from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    STAFF = 'staff', 'Staff'
    CUSTOMER = 'customer', 'Customer'


class BillingCycle(models.TextChoices):
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class SubscriptionStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    QUOTATION = 'quotation', 'Quotation'
    CONFIRMED = 'confirmed', 'Confirmed'
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    CLOSED = 'closed', 'Closed'


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    CONFIRMED = 'confirmed', 'Confirmed'
    PAID = 'paid', 'Paid'
    VOID = 'void', 'Void'


class AlertType(models.TextChoices):
    MISSED_INVOICE = 'missed_invoice', 'Missed Invoice'
    OVERDUE_INVOICE = 'overdue_invoice', 'Overdue Invoice'
    POSSIBLE_DUPLICATE = 'possible_duplicate', 'Possible Duplicate'
    UNMATCHED_PAYMENT = 'unmatched_payment', 'Unmatched Payment'
    INVOICE_ANOMALY = 'invoice_anomaly', 'Invoice Anomaly'
    RENEWAL_ATTENTION = 'renewal_attention', 'Renewal Attention'


class AlertStatus(models.TextChoices):
    NEW = 'new', 'New'
    IN_REVIEW = 'in_review', 'In Review'
    RESOLVED = 'resolved', 'Resolved'
    DISMISSED = 'dismissed', 'Dismissed'


class Priority(models.TextChoices):
    HIGH = 'high', 'High'
    MEDIUM = 'medium', 'Medium'
    LOW = 'low', 'Low'


class DiscountType(models.TextChoices):
    PERCENT = 'percent', 'Percentage'
    FIXED = 'fixed', 'Fixed Amount'


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    CARD = 'card', 'Credit/Debit Card'
    CASH = 'cash', 'Cash'
    MANUAL = 'manual', 'Manual'
