from datetime import date
from decimal import Decimal
from django.test import TestCase
from core.constants import InvoiceStatus, PaymentMethod
from products.models import Product, Plan
from subscriptions.models import Customer, Subscription, SubscriptionItem
from billing.models import Invoice
from billing import services as billing_services
from payments import services as payment_services


class PaymentServicesTestCase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name='Global Media', email='global@media.com')
        self.plan = Plan.objects.create(name='Standard Plan', code='std', cycle='monthly')
        self.sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status='active',
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )
        self.product = Product.objects.create(
            name='Standard Tier',
            sales_price=Decimal('1000.00'),
            cost_price=Decimal('200.00')
        )
        SubscriptionItem.objects.create(
            subscription=self.sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('1000.00')
        )
        self.invoice = billing_services.create_invoice(self.sub, period_start=date(2026, 1, 1))

    def test_partial_payment_then_remainder(self):
        inv = self.invoice
        self.assertEqual(inv.total_amount, Decimal('1000.00'))
        self.assertEqual(inv.balance_due, Decimal('1000.00'))
        self.assertEqual(inv.amount_paid, Decimal('0.00'))
        self.assertEqual(inv.status, InvoiceStatus.CONFIRMED)

        # 1. Partial payment of 400
        p1 = payment_services.record(inv, amount=Decimal('400.00'), method=PaymentMethod.BANK_TRANSFER)
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('400.00'))
        self.assertEqual(inv.balance_due, Decimal('600.00'))
        self.assertEqual(inv.status, InvoiceStatus.CONFIRMED)
        self.assertTrue(inv.is_partially_paid)

        # 2. Remainder payment of 600
        p2 = payment_services.record(inv, amount=Decimal('600.00'), method=PaymentMethod.CARD)
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('1000.00'))
        self.assertEqual(inv.balance_due, Decimal('0.00'))
        self.assertEqual(inv.status, InvoiceStatus.PAID)
        self.assertFalse(inv.is_partially_paid)

    def test_overpayment_rejected(self):
        inv = self.invoice
        # Trying to pay 1000.01 on 1000.00 invoice
        with self.assertRaises(payment_services.OverpaymentError):
            payment_services.record(inv, amount=Decimal('1000.01'))

        # Balance remains untouched
        inv.refresh_from_db()
        self.assertEqual(inv.balance_due, Decimal('1000.00'))
        self.assertEqual(inv.amount_paid, Decimal('0.00'))

    def test_idempotency_prevents_duplicate_charge(self):
        inv = self.invoice
        key = 'txn-unique-idemp-12345'

        # First submit
        p1 = payment_services.record(inv, amount=Decimal('300.00'), idempotency_key=key)
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('300.00'))
        self.assertEqual(inv.balance_due, Decimal('700.00'))

        # Second submit with same key (e.g. user double-clicks button)
        p2 = payment_services.record(inv, amount=Decimal('300.00'), idempotency_key=key)
        self.assertEqual(p1.id, p2.id)

        # Invoice balance is NOT charged twice!
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal('300.00'))
        self.assertEqual(inv.balance_due, Decimal('700.00'))
