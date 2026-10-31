from datetime import date
from decimal import Decimal
from django.test import TestCase
from core.constants import SubscriptionStatus, BillingCycle
from accounts.models import User
from products.models import Product, Plan
from subscriptions.models import Customer, Subscription, SubscriptionItem
from subscriptions import lifecycle


class SubscriptionLifecycleTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('billing@test.com', 'Pass12345!', role='staff')
        self.customer = Customer.objects.create(name='Test Corp', email='billing@test.com')
        self.plan = Plan.objects.create(
            name='Monthly Standard',
            code='m-std',
            cycle=BillingCycle.MONTHLY,
            minimum_quantity=2,
            pause_allowed=True,
            renewal_allowed=True,
        )
        self.product = Product.objects.create(
            name='API Server',
            sales_price=Decimal('100.00'),
            cost_price=Decimal('40.00')
        )
        self.subscription = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status=SubscriptionStatus.DRAFT,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 1, 1),
        )

    def test_lifecycle_transitions_and_event_history(self):
        sub = self.subscription

        # Cannot activate draft directly
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.transition(sub, 'activate', actor=self.user)

        # Transition: draft -> quotation
        lifecycle.transition(sub, 'send_quotation', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.QUOTATION)
        self.assertEqual(sub.events.count(), 1)
        self.assertEqual(sub.events.first().action, 'send_quotation')

        # Transition: quotation -> confirmed
        lifecycle.transition(sub, 'confirm', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.CONFIRMED)

        # Cannot activate without items
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.transition(sub, 'activate', actor=self.user)

        # Add item below plan minimum (minimum is 2)
        item = SubscriptionItem.objects.create(
            subscription=sub,
            product=self.product,
            quantity=1,
            unit_price=Decimal('100.00')
        )
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.transition(sub, 'activate', actor=self.user)

        # Update item quantity to meet minimum
        item.quantity = 2
        item.save()

        # Transition: confirmed -> active
        lifecycle.transition(sub, 'activate', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

        # Transition: active -> paused
        lifecycle.transition(sub, 'pause', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.PAUSED)
        self.assertIsNotNone(sub.pause_date)

        # Transition: paused -> active (resume)
        lifecycle.transition(sub, 'resume', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertIsNone(sub.pause_date)

        # Transition: active -> closed
        lifecycle.transition(sub, 'close', actor=self.user, reason='Customer request')
        self.assertEqual(sub.status, SubscriptionStatus.CLOSED)
        self.assertEqual(sub.close_reason, 'Customer request')

        # Transition: closed -> renew
        lifecycle.transition(sub, 'renew', actor=self.user)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)
        self.assertEqual(sub.events.count(), 7)

    def test_disallowed_pause_rule(self):
        self.plan.pause_allowed = False
        self.plan.save()

        # Activate sub first
        SubscriptionItem.objects.create(
            subscription=self.subscription,
            product=self.product,
            quantity=2,
            unit_price=Decimal('100.00')
        )
        self.subscription.status = SubscriptionStatus.ACTIVE
        self.subscription.save()

        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.transition(self.subscription, 'pause', actor=self.user)
