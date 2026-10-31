from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from core.constants import UserRole, BillingCycle, SubscriptionStatus, InvoiceStatus, PaymentMethod
from products.models import Product, ProductVariant, Plan, TaxRule, Discount
from subscriptions.models import Customer, Subscription, SubscriptionItem, SubscriptionEvent
from billing.models import Invoice, InvoiceItem, NumberSequence
from payments.models import Payment
from audit import proof_engine


class Command(BaseCommand):
    help = 'Populates the database with rich demo data: users, catalogue, customers, subscriptions, invoices, and payments.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding ProofBill demonstration dataset..."))
        today = timezone.localdate()

        # 1. Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@proofbill.io',
            defaults={
                'first_name': 'Dev',
                'last_name': 'Admin',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('AdminPass123!')
        admin_user.save()

        staff_user, _ = User.objects.get_or_create(
            email='staff@proofbill.io',
            defaults={
                'first_name': 'Billing',
                'last_name': 'Staff',
                'role': UserRole.STAFF,
                'is_staff': True,
            }
        )
        staff_user.set_password('StaffPass123!')
        staff_user.save()

        # 2. Tax Rules & Discounts
        gst18, _ = TaxRule.objects.get_or_create(
            name='GST 18%',
            defaults={'rate_percent': Decimal('18.00'), 'is_active': True}
        )
        vat5, _ = TaxRule.objects.get_or_create(
            name='VAT 5%',
            defaults={'rate_percent': Decimal('5.00'), 'is_active': True}
        )

        disc_welcome, _ = Discount.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'name': '10% Welcome Partner Discount',
                'discount_type': 'percent',
                'value': Decimal('10.00'),
                'usage_limit': 100,
                'is_active': True,
            }
        )
        disc_flat, _ = Discount.objects.get_or_create(
            code='FLAT500',
            defaults={
                'name': 'Flat Rs. 500 Promo',
                'discount_type': 'fixed',
                'value': Decimal('500.00'),
                'usage_limit': 50,
                'is_active': True,
            }
        )

        # 3. Products and Variants
        prod_saas, _ = Product.objects.get_or_create(
            name='ProofBill SaaS Core',
            defaults={
                'description': 'Core billing and subscription engine platform licence.',
                'cost_price': Decimal('300.00'),
                'sales_price': Decimal('999.00'),
                'is_active': True,
            }
        )
        var_pro, _ = ProductVariant.objects.get_or_create(
            product=prod_saas,
            name='Pro Edition',
            defaults={'extra_price': Decimal('560.00'), 'is_active': True}
        )
        var_ent, _ = ProductVariant.objects.get_or_create(
            product=prod_saas,
            name='Enterprise Edition',
            defaults={'extra_price': Decimal('1500.00'), 'is_active': True}
        )

        prod_db, _ = Product.objects.get_or_create(
            name='High-Availability DB Node',
            defaults={
                'description': 'Managed PostgreSQL cluster with automated replication.',
                'cost_price': Decimal('400.00'),
                'sales_price': Decimal('1200.00'),
                'is_active': True,
            }
        )

        prod_sla, _ = Product.objects.get_or_create(
            name='24/7 Dedicated Support SLA',
            defaults={
                'description': 'Priority escalation and dedicated financial systems engineer.',
                'cost_price': Decimal('200.00'),
                'sales_price': Decimal('750.00'),
                'is_active': True,
            }
        )

        # 4. Plans
        plan_monthly, _ = Plan.objects.get_or_create(
            code='monthly-growth',
            defaults={
                'name': 'Monthly Growth Plan',
                'cycle': BillingCycle.MONTHLY,
                'minimum_quantity': 1,
                'grace_days': 3,
                'auto_close': False,
                'early_close_allowed': True,
                'pause_allowed': True,
                'renewal_allowed': True,
                'is_active': True,
            }
        )
        plan_annual, _ = Plan.objects.get_or_create(
            code='annual-scale',
            defaults={
                'name': 'Annual Scale Plan',
                'cycle': BillingCycle.YEARLY,
                'minimum_quantity': 1,
                'grace_days': 7,
                'auto_close': False,
                'early_close_allowed': True,
                'pause_allowed': True,
                'renewal_allowed': True,
                'is_active': True,
            }
        )
        plan_weekly, _ = Plan.objects.get_or_create(
            code='weekly-starter',
            defaults={
                'name': 'Weekly Flex Plan',
                'cycle': BillingCycle.WEEKLY,
                'minimum_quantity': 1,
                'grace_days': 2,
                'auto_close': False,
                'early_close_allowed': True,
                'pause_allowed': True,
                'renewal_allowed': True,
                'is_active': True,
            }
        )

        # 5. Customers
        customer_data = [
            ('Acme Corp', 'billing@acme.com', '+91 98765 43210', 'Acme Corp Pvt Ltd', 'Tech Park, Bangalore'),
            ('Brightloop Tech', 'finance@brightloop.com', '+91 98450 11223', 'Brightloop Software', 'Infopark, Kochi'),
            ('CloudScale Labs', 'admin@cloudscale.io', '+91 99100 88776', 'CloudScale Inc', 'Cyber City, Hyderabad'),
            ('Delta Dynamics', 'accounts@deltadynamics.com', '+91 97230 44556', 'Delta Dynamics LLP', 'BKC, Mumbai'),
            ('Echo Media Works', 'contact@echomedia.net', '+91 96540 33221', 'Echo Media Network', 'Sector 62, Noida'),
        ]

        customers = []
        for name, email, phone, company, address in customer_data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': name.split()[0],
                    'last_name': 'Admin',
                    'role': UserRole.CUSTOMER,
                }
            )
            user.set_password('CustomerPass123!')
            user.save()

            cust, _ = Customer.objects.get_or_create(
                email=email,
                defaults={
                    'user': user,
                    'name': name,
                    'phone': phone,
                    'company_name': company,
                    'billing_address': address,
                }
            )
            customers.append(cust)

        # 6. Subscriptions across various states
        # Customer 1: Active Monthly subscription
        sub1, _ = Subscription.objects.get_or_create(
            customer=customers[0],
            plan=plan_monthly,
            defaults={
                'status': SubscriptionStatus.ACTIVE,
                'start_date': today - timedelta(days=90),
                'next_billing_date': today + timedelta(days=10),
                'tax_rule': gst18,
                'discount': disc_welcome,
            }
        )
        if not sub1.items.exists():
            SubscriptionItem.objects.create(
                subscription=sub1,
                product=prod_saas,
                variant=var_pro,
                quantity=3,
                unit_price=Decimal('1559.00')
            )
            SubscriptionEvent.objects.create(
                subscription=sub1,
                action='activate',
                from_status=SubscriptionStatus.CONFIRMED,
                to_status=SubscriptionStatus.ACTIVE,
                actor=staff_user,
                reason='Activated subscription upon approval'
            )

        # Customer 2: Paused Subscription
        sub2, _ = Subscription.objects.get_or_create(
            customer=customers[1],
            plan=plan_monthly,
            defaults={
                'status': SubscriptionStatus.PAUSED,
                'start_date': today - timedelta(days=120),
                'next_billing_date': today + timedelta(days=20),
                'pause_date': today - timedelta(days=10),
                'tax_rule': gst18,
            }
        )
        if not sub2.items.exists():
            SubscriptionItem.objects.create(
                subscription=sub2,
                product=prod_db,
                quantity=2,
                unit_price=Decimal('1200.00')
            )

        # Customer 3: Closed / Expired Subscription
        sub3, _ = Subscription.objects.get_or_create(
            customer=customers[2],
            plan=plan_weekly,
            defaults={
                'status': SubscriptionStatus.CLOSED,
                'start_date': today - timedelta(days=150),
                'next_billing_date': today - timedelta(days=30),
                'end_date': today - timedelta(days=30),
                'close_date': today - timedelta(days=30),
                'close_reason': 'Customer requested cancellation at end of term',
                'tax_rule': vat5,
            }
        )
        if not sub3.items.exists():
            SubscriptionItem.objects.create(
                subscription=sub3,
                product=prod_saas,
                quantity=1,
                unit_price=Decimal('999.00')
            )

        # Customer 4: Active Annual with Upcoming Renewal
        sub4, _ = Subscription.objects.get_or_create(
            customer=customers[3],
            plan=plan_annual,
            defaults={
                'status': SubscriptionStatus.ACTIVE,
                'start_date': today - timedelta(days=355),
                'next_billing_date': today + timedelta(days=10),
                'end_date': today + timedelta(days=10),
                'tax_rule': gst18,
                'discount': disc_flat,
            }
        )
        if not sub4.items.exists():
            SubscriptionItem.objects.create(
                subscription=sub4,
                product=prod_saas,
                variant=var_ent,
                quantity=2,
                unit_price=Decimal('2499.00')
            )
            SubscriptionItem.objects.create(
                subscription=sub4,
                product=prod_sla,
                quantity=1,
                unit_price=Decimal('750.00')
            )

        # Customer 5: Quotation stage
        sub5, _ = Subscription.objects.get_or_create(
            customer=customers[4],
            plan=plan_monthly,
            defaults={
                'status': SubscriptionStatus.QUOTATION,
                'start_date': today,
                'next_billing_date': today,
                'quotation_valid_until': today + timedelta(days=14),
                'tax_rule': gst18,
            }
        )
        if not sub5.items.exists():
            SubscriptionItem.objects.create(
                subscription=sub5,
                product=prod_saas,
                variant=var_pro,
                quantity=1,
                unit_price=Decimal('1559.00')
            )

        # 7. Invoices: Paid, Partially Paid, Overdue
        # Paid Invoice
        inv_paid, _ = Invoice.objects.get_or_create(
            invoice_number='INV-00101',
            defaults={
                'subscription': sub1,
                'customer': customers[0],
                'status': InvoiceStatus.PAID,
                'period_start': today - timedelta(days=90),
                'period_end': today - timedelta(days=61),
                'issue_date': today - timedelta(days=90),
                'due_date': today - timedelta(days=75),
                'subtotal': Decimal('4677.00'),
                'discount_amount': Decimal('467.70'),
                'tax_amount': Decimal('757.67'),
                'total_amount': Decimal('4966.97'),
                'amount_paid': Decimal('4966.97'),
                'balance_due': Decimal('0.00'),
            }
        )
        Payment.objects.get_or_create(
            invoice=inv_paid,
            defaults={
                'customer': customers[0],
                'amount': Decimal('4966.97'),
                'payment_method': PaymentMethod.BANK_TRANSFER,
                'payment_date': today - timedelta(days=78),
                'reference': 'HDFC-TXN-88190',
                'recorded_by': staff_user,
            }
        )

        # Partially Paid Invoice
        inv_partial, _ = Invoice.objects.get_or_create(
            invoice_number='INV-00102',
            defaults={
                'subscription': sub1,
                'customer': customers[0],
                'status': InvoiceStatus.CONFIRMED,
                'period_start': today - timedelta(days=60),
                'period_end': today - timedelta(days=31),
                'issue_date': today - timedelta(days=60),
                'due_date': today - timedelta(days=45),
                'subtotal': Decimal('4677.00'),
                'discount_amount': Decimal('467.70'),
                'tax_amount': Decimal('757.67'),
                'total_amount': Decimal('4966.97'),
                'amount_paid': Decimal('2000.00'),
                'balance_due': Decimal('2966.97'),
            }
        )
        Payment.objects.get_or_create(
            invoice=inv_partial,
            defaults={
                'customer': customers[0],
                'amount': Decimal('2000.00'),
                'payment_method': PaymentMethod.CARD,
                'payment_date': today - timedelta(days=40),
                'reference': 'CARD-AUTH-9901',
                'recorded_by': staff_user,
            }
        )

        # Overdue Invoice (Confirmed, balance > 0, due_date < today)
        inv_overdue, _ = Invoice.objects.get_or_create(
            invoice_number='INV-00103',
            defaults={
                'subscription': sub2,
                'customer': customers[1],
                'status': InvoiceStatus.CONFIRMED,
                'period_start': today - timedelta(days=50),
                'period_end': today - timedelta(days=21),
                'issue_date': today - timedelta(days=50),
                'due_date': today - timedelta(days=35),
                'subtotal': Decimal('2400.00'),
                'discount_amount': Decimal('0.00'),
                'tax_amount': Decimal('432.00'),
                'total_amount': Decimal('2832.00'),
                'amount_paid': Decimal('0.00'),
                'balance_due': Decimal('2832.00'),
            }
        )

        # Ensure line items exist for audit recomputation
        if not inv_paid.items.exists():
            InvoiceItem.objects.create(
                invoice=inv_paid,
                product=prod_saas,
                variant=var_pro,
                product_name=prod_saas.name,
                variant_name=var_pro.name,
                quantity=3,
                unit_price=Decimal('1559.00'),
                line_subtotal=Decimal('4677.00'),
                discount_amount=Decimal('467.70'),
                net_amount=Decimal('4209.30'),
                tax_amount=Decimal('757.67'),
                line_total=Decimal('4966.97')
            )

        if not inv_overdue.items.exists():
            InvoiceItem.objects.create(
                invoice=inv_overdue,
                product=prod_db,
                product_name=prod_db.name,
                quantity=2,
                unit_price=Decimal('1200.00'),
                line_subtotal=Decimal('2400.00'),
                discount_amount=Decimal('0.00'),
                net_amount=Decimal('2400.00'),
                tax_amount=Decimal('432.00'),
                line_total=Decimal('2832.00')
            )

        # Run Proof Engine audit
        self.stdout.write(self.style.NOTICE("Running Proof Engine initial audit on seed data..."))
        proof_engine.run(as_of=today)

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully seeded ProofBill demo dataset!\n"
                "  Admin user: admin@proofbill.io (AdminPass123!)\n"
                "  Staff user: staff@proofbill.io (StaffPass123!)\n"
                "  Customer:   billing@acme.com (CustomerPass123!)\n"
                "  5 Customers, 5 Subscriptions, Invoices (Paid, Partial, Overdue), and Alerts loaded."
            )
        )
