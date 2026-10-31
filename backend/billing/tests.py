from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.db.utils import IntegrityError
from core.constants import SubscriptionStatus, InvoiceStatus, BillingCycle
from products.models import Product, Plan
from subscriptions.models import Customer, Subscription, SubscriptionItem
from billing.models import Invoice, BillingRun
from billing import services as billing_services


class BillingServicesTestCase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name='Acme Testing', email='acme@test.com')
        self.daily_plan = Plan.objects.create(
            name='Daily Compute',
            code='daily-comp',
            cycle=BillingCycle.DAILY,
            minimum_quantity=1,
            is_active=True
        )
        self.monthly_plan = Plan.objects.create(
            name='Monthly Cloud',
            code='month-cloud',
            cycle=BillingCycle.MONTHLY,
            minimum_quantity=1,
            is_active=True
        )
        self.product = Product.objects.create(
            name='VM Instance',
            sales_price=Decimal('50.00'),
            cost_price=Decimal('20.00')
        )

    def test_billing_run_idempotency(self):
        """
        Running billing twice produces one invoice per period.
        """
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.monthly_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )

        # Run 1
        run1 = billing_services.run(run_date=date(2026, 1, 1))
        self.assertEqual(run1.invoices_created, 1)
        self.assertEqual(Invoice.objects.filter(subscription=sub).count(), 1)

        # Reload subscription
        sub.refresh_from_db()
        self.assertEqual(sub.next_billing_date, date(2026, 2, 1))

        # Run 2 on same date
        run2 = billing_services.run(run_date=date(2026, 1, 1))
        self.assertEqual(run2.invoices_created, 0)
        self.assertEqual(Invoice.objects.filter(subscription=sub).count(), 1)

    def test_catch_up_after_3_skipped_days(self):
        """
        Daily plan with 3 skipped days: run_billing generates 3 sequential invoices.
        """
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.daily_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 3, 1),
            next_billing_date=date(2026, 3, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )

        # Run as of March 3 (3 days to bill: March 1, March 2, March 3)
        run_res = billing_services.run(run_date=date(2026, 3, 3))
        self.assertEqual(run_res.invoices_created, 3)
        self.assertEqual(Invoice.objects.filter(subscription=sub).count(), 3)

        sub.refresh_from_db()
        self.assertEqual(sub.next_billing_date, date(2026, 3, 4))

    def test_paused_and_closed_are_not_billed(self):
        sub_paused = Subscription.objects.create(
            customer=self.customer,
            plan=self.monthly_plan,
            status=SubscriptionStatus.PAUSED,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub_paused,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )

        sub_closed = Subscription.objects.create(
            customer=self.customer,
            plan=self.monthly_plan,
            status=SubscriptionStatus.CLOSED,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub_closed,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )

        run_res = billing_services.run(run_date=date(2026, 1, 15))
        self.assertEqual(run_res.invoices_created, 0)
        self.assertEqual(Invoice.objects.filter(subscription__in=[sub_paused, sub_closed]).count(), 0)

    def test_void_invoice_and_reason_requirement(self):
        sub = Subscription.objects.create(
            customer=self.customer,
            plan=self.monthly_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )
        SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )
        inv = billing_services.create_invoice(sub, period_start=date(2026, 1, 1))

        # Reason is required
        with self.assertRaises(ValueError):
            billing_services.void_invoice(inv, reason="")

        # Voiding with valid reason
        billing_services.void_invoice(inv, reason="Incorrect client configuration")
        self.assertEqual(inv.status, InvoiceStatus.VOID)
        self.assertEqual(inv.void_reason, "Incorrect client configuration")

        # Now creating another invoice for the same period succeeds because void freed the period!
        inv2 = billing_services.create_invoice(sub, period_start=date(2026, 1, 1))
        self.assertEqual(inv2.status, InvoiceStatus.CONFIRMED)
