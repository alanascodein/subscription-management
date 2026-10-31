from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal('0.01')


def quantize_money(amount) -> Decimal:
    """
    Quantize any monetary value to 2 decimal places using half-up rounding.
    Never uses floating-point approximations.
    """
    if amount is None:
        return Decimal('0.00')
    if isinstance(amount, float):
        amount = str(amount)
    dec = Decimal(amount)
    return dec.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
