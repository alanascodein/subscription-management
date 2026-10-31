from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from core.constants import BillingCycle


def end(start_date: date, cycle: str) -> date:
    """
    Returns the inclusive end date for a billing period starting on start_date.
    e.g. for monthly starting 2026-01-01 -> 2026-01-31
    for monthly starting 2026-01-31 -> 2026-02-27 (or 2026-02-28 depending on leap year)
    """
    if cycle == BillingCycle.DAILY:
        return start_date
    elif cycle == BillingCycle.WEEKLY:
        return start_date + timedelta(days=6)
    elif cycle == BillingCycle.MONTHLY:
        next_period_start = start_date + relativedelta(months=1)
        return next_period_start - timedelta(days=1)
    elif cycle == BillingCycle.YEARLY:
        next_period_start = start_date + relativedelta(years=1)
        return next_period_start - timedelta(days=1)
    else:
        raise ValueError(f"Unsupported billing cycle: {cycle}")


def next_start(start_date: date, cycle: str) -> date:
    """
    Returns the start date for the subsequent billing period.
    """
    if cycle == BillingCycle.DAILY:
        return start_date + timedelta(days=1)
    elif cycle == BillingCycle.WEEKLY:
        return start_date + timedelta(days=7)
    elif cycle == BillingCycle.MONTHLY:
        return start_date + relativedelta(months=1)
    elif cycle == BillingCycle.YEARLY:
        return start_date + relativedelta(years=1)
    else:
        raise ValueError(f"Unsupported billing cycle: {cycle}")
