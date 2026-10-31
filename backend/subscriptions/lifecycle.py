from django.db import transaction
from django.utils import timezone
from core.constants import SubscriptionStatus
from subscriptions.models import Subscription, SubscriptionEvent


class LifecycleError(Exception):
    """Raised when an invalid subscription lifecycle transition is attempted."""
    pass


ALLOWED_TRANSITIONS = {
    SubscriptionStatus.DRAFT: {
        'send_quotation': SubscriptionStatus.QUOTATION,
        'confirm': SubscriptionStatus.CONFIRMED,
        'close': SubscriptionStatus.CLOSED,
    },
    SubscriptionStatus.QUOTATION: {
        'confirm': SubscriptionStatus.CONFIRMED,
        'close': SubscriptionStatus.CLOSED,
    },
    SubscriptionStatus.CONFIRMED: {
        'activate': SubscriptionStatus.ACTIVE,
        'close': SubscriptionStatus.CLOSED,
    },
    SubscriptionStatus.ACTIVE: {
        'pause': SubscriptionStatus.PAUSED,
        'close': SubscriptionStatus.CLOSED,
    },
    SubscriptionStatus.PAUSED: {
        'resume': SubscriptionStatus.ACTIVE,
        'close': SubscriptionStatus.CLOSED,
    },
    SubscriptionStatus.CLOSED: {
        'renew': SubscriptionStatus.ACTIVE,
    },
}


def transition(
    subscription: Subscription,
    action: str,
    actor=None,
    reason: str = ""
) -> Subscription:
    """
    Execute a guarded state transition on a Subscription.
    Validates business rules, records a SubscriptionEvent, and saves atomically.
    """
    current_status = subscription.status
    allowed_actions = ALLOWED_TRANSITIONS.get(current_status, {})

    if action not in allowed_actions:
        raise LifecycleError(
            f"Cannot execute '{action}' on subscription in '{current_status}' status. "
            f"Allowed actions: {list(allowed_actions.keys()) or 'None'}."
        )

    target_status = allowed_actions[action]

    # Business rule validations
    if action == 'pause' and not subscription.plan.pause_allowed:
        raise LifecycleError(f"Plan '{subscription.plan.name}' does not allow pausing.")

    if action == 'renew' and not subscription.plan.renewal_allowed:
        raise LifecycleError(f"Plan '{subscription.plan.name}' does not allow renewal.")

    if action == 'close':
        today = timezone.localdate()
        if subscription.end_date and today < subscription.end_date:
            if not subscription.plan.early_close_allowed:
                raise LifecycleError(f"Plan '{subscription.plan.name}' does not permit early closure before {subscription.end_date}.")

    if target_status == SubscriptionStatus.ACTIVE:
        # Validate items and minimum quantity
        items = list(subscription.items.all())
        if not items:
            raise LifecycleError("Cannot activate a subscription with no items.")
        total_qty = sum(item.quantity for item in items)
        if total_qty < subscription.plan.minimum_quantity:
            raise LifecycleError(
                f"Total quantity ({total_qty}) is below plan minimum ({subscription.plan.minimum_quantity})."
            )

    with transaction.atomic():
        subscription.status = target_status
        today = timezone.localdate()

        if action == 'pause':
            subscription.pause_date = today
        elif action == 'resume':
            subscription.pause_date = None
        elif action == 'close':
            subscription.close_date = today
            subscription.close_reason = reason or "Closed by user/staff"
        elif action == 'renew':
            subscription.close_date = None
            subscription.close_reason = ""
            subscription.start_date = today
            subscription.next_billing_date = today

        subscription.save()

        SubscriptionEvent.objects.create(
            subscription=subscription,
            action=action,
            from_status=current_status,
            to_status=target_status,
            actor=actor if actor and getattr(actor, 'is_authenticated', False) else None,
            reason=reason,
        )

    return subscription
