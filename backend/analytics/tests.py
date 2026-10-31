from datetime import date
from decimal import Decimal
from django.test import TestCase
from core.constants import SubscriptionStatus, InvoiceStatus, PaymentMethod
from products.models import Product, Plan
from subscriptions.models import Customer, Subscription, SubscriptionItem
from billing.models import Invoice, NumberSequence
from payments.models import Payment
from analytics import services as analytics_services


class AnalyticsTestCase(TestCase):
    def test_dashboard_aggregates_equal_raw_database_sums(self):
        customer = Customer.objects.create(name='Acme Testing', email='acme@test.com')
        plan = Plan.objects.create(name='Monthly Plan', code='m-plan', cycle='monthly')
        product = Product.objects.create(name='Hosting', sales_price=Decimal('200.00'), cost_price=Decimal('50.00'))

        sub1 = Subscription.objects.create(
            customer=customer,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 2, 1),
        )
        SubscriptionItem.objects.create(subscription=sub1, product=product, quantity=1, unit_price=Decimal('200.00'))

        inv1 = Invoice.objects.create(
            invoice_number=NumberSequence.get_next(),
            subscription=sub1,
            customer=customer,
            status=InvoiceStatus.CONFIRMED,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 15),
            subtotal=Decimal('200.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('200.00'),
            amount_paid=Decimal('50.00'),
            balance_due=Decimal('150.00'),
        )

        Payment.objects.create(
            invoice=inv1,
            customer=customer,
            amount=Decimal('50.00'),
            payment_method=PaymentMethod.BANK_TRANSFER,
            payment_date=date(2026, 1, 10),
        )

        data = analytics_services.summary()

        self.assertEqual(data['active_count'], 1)
        self.assertEqual(data['outstanding'], Decimal('150.00'))
        self.assertEqual(data['total_collected'], Decimal('50.00'))
