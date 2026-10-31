from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Any
from core.money import quantize_money
from core.constants import BillingCycle, DiscountType


def monthly_equivalent(cycle: str, amount: Decimal) -> Decimal:
    """
    Convert a billing cycle amount to its monthly equivalent.

    Used for MRR (Monthly Recurring Revenue) calculations:
    - MONTHLY: amount as-is
    - YEARLY: amount / 12
    - WEEKLY: amount * 52 / 12 (≈ amount * 4.33)
    - DAILY: amount * 365 / 12 (≈ amount * 30.42)
    """
    if cycle == BillingCycle.MONTHLY:
        return amount
    elif cycle == BillingCycle.YEARLY:
        return amount / Decimal('12')
    elif cycle == BillingCycle.WEEKLY:
        return amount * Decimal('52') / Decimal('12')
    elif cycle == BillingCycle.DAILY:
        return amount * Decimal('365') / Decimal('12')
    else:
        raise ValueError(f"Unsupported billing cycle: {cycle}")


@dataclass
class PricingLineResult:
    product_id: Optional[int]
    variant_id: Optional[int]
    name: str
    description: str
    quantity: int
    base_price: Decimal
    variant_extra: Decimal
    unit_price: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    net_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal


@dataclass
class PricingResult:
    items: List[PricingLineResult] = field(default_factory=list)
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    net_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')


def calculate(
    items: List[Any],
    discount: Optional[Any] = None,
    tax_rule: Optional[Any] = None,
) -> PricingResult:
    """
    Calculate pricing for invoice or subscription line items.
    
    Formula per line:
      unit_price = product_price + variant_extra
      line_subtotal = unit_price * quantity
    
    Total subtotal is the sum of all line subtotals.
    Discount applies to subtotal:
      - percentage discount: subtotal * (percent / 100)
      - fixed discount: min(subtotal, fixed_amount)
    
    Net amount = max(0, subtotal - discount_amount)
    Tax is calculated on the net amount:
      tax_amount = net_amount * (rate_percent / 100)
    
    Total amount = net_amount + tax_amount.
    All calculations rounded half-up to 2 decimal places.
    """
    line_results: List[PricingLineResult] = []
    total_subtotal = Decimal('0.00')

    for item in items:
        # Support dicts or objects (SubscriptionItem / InvoiceItem)
        if isinstance(item, dict):
            product_id = item.get('product_id')
            variant_id = item.get('variant_id')
            name = item.get('name', '')
            desc = item.get('description', '')
            qty = int(item.get('quantity', 1))
            base_price = quantize_money(item.get('price', item.get('base_price', '0.00')))
            variant_extra = quantize_money(item.get('extra_price', item.get('variant_extra', '0.00')))
        else:
            product = getattr(item, 'product', None)
            variant = getattr(item, 'variant', None)
            product_id = getattr(product, 'id', None)
            variant_id = getattr(variant, 'id', None)
            name = getattr(product, 'name', '')
            desc = getattr(product, 'description', '')
            qty = int(getattr(item, 'quantity', 1))
            base_price = quantize_money(getattr(product, 'sales_price', '0.00'))
            variant_extra = quantize_money(getattr(variant, 'extra_price', '0.00')) if variant else Decimal('0.00')

        unit_price = base_price + variant_extra
        line_subtotal = quantize_money(unit_price * qty)
        total_subtotal += line_subtotal

        line_results.append(
            PricingLineResult(
                product_id=product_id,
                variant_id=variant_id,
                name=name,
                description=desc,
                quantity=qty,
                base_price=base_price,
                variant_extra=variant_extra,
                unit_price=unit_price,
                subtotal=line_subtotal,
                discount_amount=Decimal('0.00'),
                net_amount=line_subtotal,
                tax_amount=Decimal('0.00'),
                total_amount=line_subtotal,
            )
        )

    # Calculate discount
    discount_amount = Decimal('0.00')
    if discount and total_subtotal > Decimal('0.00'):
        d_type = getattr(discount, 'discount_type', None) or (discount.get('discount_type') if isinstance(discount, dict) else None)
        d_val = getattr(discount, 'value', None) or (discount.get('value') if isinstance(discount, dict) else None)
        if d_val is not None:
            d_val = quantize_money(d_val)
            if d_type == DiscountType.PERCENT or d_type == 'percent':
                discount_amount = quantize_money((total_subtotal * d_val) / Decimal('100.00'))
            else:
                discount_amount = min(total_subtotal, d_val)

    net_amount = max(Decimal('0.00'), total_subtotal - discount_amount)

    # Calculate tax
    tax_amount = Decimal('0.00')
    if tax_rule and net_amount > Decimal('0.00'):
        t_rate = getattr(tax_rule, 'rate_percent', None) or (tax_rule.get('rate_percent') if isinstance(tax_rule, dict) else None)
        if t_rate is not None:
            t_rate = quantize_money(t_rate)
            tax_amount = quantize_money((net_amount * t_rate) / Decimal('100.00'))

    total_amount = quantize_money(net_amount + tax_amount)

    # Allocate discounts and taxes proportionally to line items
    if total_subtotal > Decimal('0.00') and line_results:
        running_discount = Decimal('0.00')
        running_tax = Decimal('0.00')
        for i, lr in enumerate(line_results):
            if i == len(line_results) - 1:
                # Last line takes remainder to avoid rounding mismatch
                line_disc = discount_amount - running_discount
                line_tax_val = tax_amount - running_tax
            else:
                proportion = lr.subtotal / total_subtotal
                line_disc = quantize_money(discount_amount * proportion)
                running_discount += line_disc
                line_tax_val = quantize_money(tax_amount * proportion)
                running_tax += line_tax_val

            lr.discount_amount = line_disc
            lr.net_amount = max(Decimal('0.00'), lr.subtotal - line_disc)
            lr.tax_amount = line_tax_val
            lr.total_amount = quantize_money(lr.net_amount + line_tax_val)

    return PricingResult(
        items=line_results,
        subtotal=total_subtotal,
        discount_amount=discount_amount,
        net_amount=net_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
