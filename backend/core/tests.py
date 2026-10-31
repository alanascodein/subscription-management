from datetime import date
from decimal import Decimal
from django.test import TestCase
from core.money import quantize_money
from core.constants import BillingCycle, DiscountType
from core import periods, pricing
from products.models import Product, ProductVariant, TaxRule, Discount


class CoreServicesTestCase(TestCase):
    def test_pricing_calculation_specification(self):
        """
        Verify exact pricing test case from brief:
        Rs. 999 + 560, quantity 3, 10% discount, 18% tax = Rs. 4,966.97
        """
        items = [{
            'name': 'Cloud Hosting Pro',
            'quantity': 3,
            'base_price': Decimal('999.00'),
            'variant_extra': Decimal('560.00'),
        }]
        discount = {
            'discount_type': DiscountType.PERCENT,
            'value': Decimal('10.00'),
        }
        tax_rule = {
            'rate_percent': Decimal('18.00'),
        }

        result = pricing.calculate(items=items, discount=discount, tax_rule=tax_rule)

        # Expected:
        # Unit price = 999 + 560 = 1559.00
        # Subtotal = 1559 * 3 = 4677.00
        # 10% discount = 467.70
        # Net = 4209.30
        # 18% tax on 4209.30 = 757.67
        # Total = 4966.97
        self.assertEqual(result.subtotal, Decimal('4677.00'))
        self.assertEqual(result.discount_amount, Decimal('467.70'))
        self.assertEqual(result.net_amount, Decimal('4209.30'))
        self.assertEqual(result.tax_amount, Decimal('757.67'))
        self.assertEqual(result.total_amount, Decimal('4966.97'))

        # Check line breakdown
        self.assertEqual(len(result.items), 1)
        line = result.items[0]
        self.assertEqual(line.unit_price, Decimal('1559.00'))
        self.assertEqual(line.subtotal, Decimal('4677.00'))
        self.assertEqual(line.total_amount, Decimal('4966.97'))

    def test_period_calculations(self):
        # Daily
        d = date(2026, 1, 15)
        self.assertEqual(periods.end(d, BillingCycle.DAILY), date(2026, 1, 15))
        self.assertEqual(periods.next_start(d, BillingCycle.DAILY), date(2026, 1, 16))

        # Weekly
        self.assertEqual(periods.end(d, BillingCycle.WEEKLY), date(2026, 1, 21))
        self.assertEqual(periods.next_start(d, BillingCycle.WEEKLY), date(2026, 1, 22))

        # Monthly standard
        m_start = date(2026, 1, 1)
        self.assertEqual(periods.end(m_start, BillingCycle.MONTHLY), date(2026, 1, 31))
        self.assertEqual(periods.next_start(m_start, BillingCycle.MONTHLY), date(2026, 2, 1))

        # Monthly with 31st Jan clamping
        m_31 = date(2026, 1, 31)
        self.assertEqual(periods.end(m_31, BillingCycle.MONTHLY), date(2026, 2, 27))
        self.assertEqual(periods.next_start(m_31, BillingCycle.MONTHLY), date(2026, 2, 28))

        # Yearly
        y_start = date(2026, 1, 1)
        self.assertEqual(periods.end(y_start, BillingCycle.YEARLY), date(2026, 12, 31))
        self.assertEqual(periods.next_start(y_start, BillingCycle.YEARLY), date(2027, 1, 1))
