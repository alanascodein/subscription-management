from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.constants import SubscriptionStatus, InvoiceStatus
from core.money import quantize_money
from subscriptions.models import Customer, Subscription, SubscriptionItem
from products.models import Product, Plan
from billing.models import Invoice, InvoiceItem, NumberSequence
from audit import proof_engine


class Command(BaseCommand):
    help = 'Injects realistic billing faults (missed invoice, duplicate invoice, mispriced invoice) for live demo audit detection.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(self.style.WARNING("Injecting synthetic billing leaks into database..."))

        # 1. Skipped invoice: Create an active subscription with next_billing_date 12 days ago and no invoice
        plan = Plan.objects.first()
        customer = Customer.objects.first()
        product = Product.objects.first()

        if not plan or not customer or not product:
            self.stderr.write("Seed data missing. Run 'python manage.py seed_demo' first.")
            return

        skipped_start = today - timedelta(days=20)
        skipped_sub, created = Subscription.objects.get_or_create(
            customer=customer,
            plan=plan,
            start_date=skipped_start,
            defaults={
                'status': SubscriptionStatus.ACTIVE,
                'next_billing_date': today - timedelta(days=12),
            }
        )
        if created:
            SubscriptionItem.objects.create(
                subscription=skipped_sub,
                product=product,
                quantity=2,
                unit_price=product.sales_price
            )
        else:
            skipped_sub.status = SubscriptionStatus.ACTIVE
            skipped_sub.next_billing_date = today - timedelta(days=12)
            skipped_sub.save()

        # Delete any existing invoices for this period start to ensure it is missing
        Invoice.objects.filter(subscription=skipped_sub, period_start=today - timedelta(days=12)).delete()
        self.stdout.write(self.style.SUCCESS(f"  [+] Injected Skipped Invoice fault for Subscription {skipped_sub.id}"))

        # 2. Duplicate invoice: create duplicate invoice for same customer across subscriptions or overlapping period
        sub_dup, _ = Subscription.objects.get_or_create(
            customer=customer,
            plan=plan,
            start_date=today - timedelta(days=60),
            defaults={
                'status': SubscriptionStatus.ACTIVE,
                'next_billing_date': today + timedelta(days=30),
            }
        )
        dup_period = today - timedelta(days=30)
        Invoice.objects.filter(period_start=dup_period, customer=customer).delete()

        dup_inv_num = NumberSequence.get_next(prefix='INV-DUP-')
        Invoice.objects.create(
            invoice_number=dup_inv_num,
            subscription=skipped_sub,
            customer=customer,
            status=InvoiceStatus.CONFIRMED,
            period_start=dup_period,
            period_end=today - timedelta(days=1),
            issue_date=dup_period,
            due_date=dup_period + timedelta(days=15),
            subtotal=Decimal('2500.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('450.00'),
            total_amount=Decimal('2950.00'),
            amount_paid=Decimal('0.00'),
            balance_due=Decimal('2950.00'),
            notes="Injected duplicate billing fault",
        )
        # Create second invoice for same customer and period start under sub_dup
        dup_inv_num2 = NumberSequence.get_next(prefix='INV-DUP-')
        Invoice.objects.create(
            invoice_number=dup_inv_num2,
            subscription=sub_dup,
            customer=customer,
            status=InvoiceStatus.CONFIRMED,
            period_start=dup_period,
            period_end=today - timedelta(days=1),
            issue_date=dup_period,
            due_date=dup_period + timedelta(days=15),
            subtotal=Decimal('2500.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('450.00'),
            total_amount=Decimal('2950.00'),
            amount_paid=Decimal('0.00'),
            balance_due=Decimal('2950.00'),
            notes="Injected duplicate billing fault #2",
        )
        self.stdout.write(self.style.SUCCESS(f"  [+] Injected Duplicate Invoice fault ({dup_inv_num} & {dup_inv_num2})"))

        # 3. Mispriced invoice / anomaly
        anom_period = today - timedelta(days=60)
        Invoice.objects.filter(period_start=anom_period, subscription=skipped_sub).delete()
        anomaly_inv_num = NumberSequence.get_next(prefix='INV-ANOM-')
        anom_inv = Invoice.objects.create(
            invoice_number=anomaly_inv_num,
            subscription=skipped_sub,
            customer=customer,
            status=InvoiceStatus.CONFIRMED,
            period_start=anom_period,
            period_end=today - timedelta(days=31),
            issue_date=anom_period,
            due_date=anom_period + timedelta(days=15),
            subtotal=Decimal('1000.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('180.00'),
            total_amount=Decimal('9999.00'),  # Fault: total is 9999 instead of 1180
            amount_paid=Decimal('0.00'),
            balance_due=Decimal('9999.00'),
            notes="Injected pricing calculation anomaly",
        )
        InvoiceItem.objects.create(
            invoice=anom_inv,
            product=product,
            product_name=product.name,
            quantity=1,
            unit_price=Decimal('1000.00'),
            line_subtotal=Decimal('1000.00'),
            discount_amount=Decimal('0.00'),
            net_amount=Decimal('1000.00'),
            tax_amount=Decimal('180.00'),
            line_total=Decimal('1180.00'),
        )
        self.stdout.write(self.style.SUCCESS(f"  [+] Injected Pricing Anomaly fault on {anomaly_inv_num} (stored Rs. 9999 vs line sum Rs. 1180)"))

        # Run Proof Engine detection
        self.stdout.write(self.style.NOTICE("Running Proof Engine to detect newly injected leaks..."))
        summary = proof_engine.run(as_of=today)
        self.stdout.write(
            self.style.SUCCESS(
                f"Detection completed! Revenue at Risk now at: Rs. {summary.revenue_at_risk} "
                f"({summary.alerts_created} new alerts, {summary.alerts_existing} existing)"
            )
        )
