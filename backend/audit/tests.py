from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from core.constants import SubscriptionStatus, InvoiceStatus, AlertType, AlertStatus
from products.models import Product, Plan
from subscriptions.models import Customer, Subscription, SubscriptionItem
from billing.models import Invoice, NumberSequence
from audit.models import Alert
from audit import proof_engine


class ProofEngineTestCase(TestCase):
    def setUp(self):
        self.today = date(2026, 5, 20)
        self.customer = Customer.objects.create(name='Acme Testing', email='acme@test.com')
        self.plan = Plan.objects.create(
            name='Monthly Standard',
            code='m-std',
            cycle='monthly',
            minimum_quantity=1,
            grace_days=3
        )
        self.product = Product.objects.create(
            name='Compute Engine',
            sales_price=Decimal('1500.00'),
            cost_price=Decimal('500.00')
        )

    def test_missed_invoice_detection_and_apply_fix(self):
        # Subscription expected to bill on May 1st. Today is May 20th. Grace days = 3.
        # Grace period ended May 4th. No invoice exists -> Should flag missed_invoice.
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 5, 1),
            next_billing_date=date(2026, 5, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('1500.00')
        )

        summary = proof_engine.run(as_of=self.today)
        self.assertEqual(summary.alerts_created, 1)

        alert = Alert.objects.filter(alert_type=AlertType.MISSED_INVOICE, subscription=sub).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.amount, Decimal('1500.00'))
        self.assertEqual(alert.status, AlertStatus.NEW)

        # Running detection second time creates NO duplicates
        summary2 = proof_engine.run(as_of=self.today)
        self.assertEqual(summary2.alerts_created, 0)
        self.assertEqual(Alert.objects.filter(alert_type=AlertType.MISSED_INVOICE, subscription=sub).count(), 1)

        # Apply guarded fix
        fixed_alert = proof_engine.apply_fix(alert)
        self.assertEqual(fixed_alert.status, AlertStatus.RESOLVED)

        # Invoice should now exist for that period
        inv = Invoice.objects.filter(subscription=sub, period_start=date(2026, 5, 1)).first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.total_amount, Decimal('1500.00'))

    def test_overdue_invoice_detection(self):
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 2, 1),
        )
        inv = Invoice.objects.create(
            invoice_number=NumberSequence.get_next(),
            subscription=sub,
            customer=self.customer,
            status=InvoiceStatus.CONFIRMED,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 15), # past due
            subtotal=Decimal('1500.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('1500.00'),
            amount_paid=Decimal('500.00'),
            balance_due=Decimal('1000.00'),
        )

        summary = proof_engine.run(as_of=self.today)
        alert = Alert.objects.filter(alert_type=AlertType.OVERDUE_INVOICE, invoice=inv).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.amount, Decimal('1000.00')) # balance due

    def test_alert_api_serializes_and_filters_alerts(self):
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 5, 1),
            next_billing_date=date(2026, 5, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('1500.00'),
        )
        proof_engine.run(as_of=self.today)
        alert = Alert.objects.get(alert_type=AlertType.MISSED_INVOICE, subscription=sub)

        list_response = self.client.get('/api/alerts/?type=missed_invoice')
        self.assertEqual(list_response.status_code, 200)
        alert_data = list_response.json()['data'][0]
        self.assertEqual(alert_data['rule_type'], AlertType.MISSED_INVOICE)
        self.assertEqual(alert_data['summary'], alert.title)
        self.assertEqual(alert_data['customer']['name'], self.customer.name)

        detail_response = self.client.get(f'/api/alerts/{alert.id}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()['data']['id'], alert.id)
