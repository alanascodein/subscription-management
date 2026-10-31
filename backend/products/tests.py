from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from core.constants import BillingCycle, DiscountType
from products.models import Product, ProductVariant, Plan, TaxRule, Discount


class ProductModelTestCase(TestCase):
    def test_str_representation(self):
        product = Product.objects.create(
            name='VM Instance',
            sales_price=Decimal('50.00'),
            cost_price=Decimal('20.00'),
        )
        self.assertEqual(str(product), 'VM Instance (Rs. 50.00)')

    def test_cost_price_defaults_to_zero(self):
        product = Product.objects.create(
            name='Free Trial',
            sales_price=Decimal('0.00'),
        )
        self.assertEqual(product.cost_price, Decimal('0.00'))

    def test_negative_cost_price_rejected(self):
        product = Product(name='Bad', sales_price=Decimal('10.00'), cost_price=Decimal('-1.00'))
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_negative_sales_price_rejected(self):
        product = Product(name='Bad', sales_price=Decimal('-5.00'), cost_price=Decimal('0.00'))
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_money_quantization_on_save(self):
        product = Product.objects.create(
            name='Quantized',
            sales_price=Decimal('10.005'),
            cost_price=Decimal('3.335'),
        )
        self.assertEqual(product.sales_price, Decimal('10.01'))
        self.assertEqual(product.cost_price, Decimal('3.34'))


class ProductVariantModelTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Base Box',
            sales_price=Decimal('100.00'),
            cost_price=Decimal('60.00'),
        )

    def test_str_representation(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Large',
            extra_price=Decimal('25.00'),
        )
        self.assertEqual(str(variant), 'Base Box - Large (+Rs. 25.00)')

    def test_total_unit_price(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Add-on',
            extra_price=Decimal('15.00'),
        )
        self.assertEqual(variant.total_unit_price, Decimal('115.00'))

    def test_unique_variant_per_product(self):
        ProductVariant.objects.create(product=self.product, name='Std', extra_price=Decimal('0.00'))
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(product=self.product, name='Std', extra_price=Decimal('0.00'))

    def test_negative_extra_price_rejected(self):
        variant = ProductVariant(product=self.product, name='Bad', extra_price=Decimal('-1.00'))
        with self.assertRaises(ValidationError):
            variant.full_clean()


class PlanModelTestCase(TestCase):
    def test_str_representation(self):
        plan = Plan.objects.create(name='Monthly Pro', code='monthly-pro', cycle=BillingCycle.MONTHLY)
        self.assertEqual(str(plan), 'Monthly Pro (Monthly)')

    def test_code_uniqueness(self):
        Plan.objects.create(name='A', code='shared', cycle=BillingCycle.MONTHLY)
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name='B', code='shared', cycle=BillingCycle.DAILY)

    def test_invalid_cycle_rejected(self):
        plan = Plan(name='Bad', code='bad-cycle', cycle='never')
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test_minimum_quantity_constraint(self):
        plan = Plan(name='Bad', code='bad-min', cycle=BillingCycle.MONTHLY, minimum_quantity=0)
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test Availability_window(self):
        plan = Plan.objects.create(
            name='Limited',
            code='limited',
            cycle=BillingCycle.MONTHLY,
            availability_start=date(2026, 1, 1),
            availability_end=date(2026, 12, 31),
        )
        self.assertTrue(plan.is_active)
        self.assertEqual(plan.availability_start, date(2026, 1, 1))


class TaxRuleModelTestCase(TestCase):
    def test_str_representation(self):
        rule = TaxRule.objects.create(name='VAT', rate_percent=Decimal('18.00'))
        self.assertEqual(str(rule), 'VAT (18.00%)')

    def test_rate_percent_bounds(self):
        rule = TaxRule(name='Bad', rate_percent=Decimal('101.00'))
        with self.assertRaises(ValidationError):
            rule.full_clean()

        rule = TaxRule(name='Bad', rate_percent=Decimal('-1.00'))
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_rate_quantization(self):
        rule = TaxRule.objects.create(name='Rounded', rate_percent=Decimal('12.345'))
        self.assertEqual(rule.rate_percent, Decimal('12.35'))


class DiscountModelTestCase(TestCase):
    def test_str_representation_percent(self):
        discount = Discount.objects.create(
            code='SUMMER25',
            name='Summer Sale',
            discount_type=DiscountType.PERCENT,
            value=Decimal('25.00'),
        )
        self.assertEqual(str(discount), 'SUMMER25 - Summer Sale (25.00%)')

    def test_str_representation_fixed(self):
        discount = Discount.objects.create(
            code='FLAT10',
            name='Flat Discount',
            discount_type=DiscountType.FIXED,
            value=Decimal('10.00'),
        )
        self.assertEqual(str(discount), 'FLAT10 - Flat Discount (10.00 Rs)')

    def test_percent_above_100_rejected(self):
        discount = Discount(
            code='ALL',
            name='All',
            discount_type=DiscountType.PERCENT,
            value=Decimal('101.00'),
        )
        with self.assertRaises(ValidationError):
            discount.full_clean()

    def test_is_usable(self):
        discount = Discount.objects.create(
            code='GOOD',
            name='Good',
            discount_type=DiscountType.PERCENT,
            value=Decimal('10.00'),
            usage_limit=3,
        )
        self.assertTrue(discount.is_usable)

        discount.times_used = 2
        discount.save()
        self.assertTrue(discount.is_usable)

        discount.times_used = 3
        discount.save()
        self.assertFalse(discount.is_usable)

    def test_inactive_discount_not_usable(self):
        discount = Discount.objects.create(
            code='OFF',
            name='Off',
            discount_type=DiscountType.PERCENT,
            value=Decimal('10.00'),
            is_active=False,
        )
        self.assertFalse(discount.is_usable)

    def test_code_uniqueness(self):
        Discount.objects.create(code='CODE', name='A', discount_type=DiscountType.PERCENT, value=Decimal('5.00'))
        with self.assertRaises(IntegrityError):
            Discount.objects.create(code='CODE', name='B', discount_type=DiscountType.FIXED, value=Decimal('5.00'))
