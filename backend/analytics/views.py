from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.permissions import staff_required, role_required
from core.constants import UserRole, SubscriptionStatus
from subscriptions.models import Customer, Subscription
from subscriptions import lifecycle
from billing.models import Invoice
from payments.models import Payment
from analytics import services as analytics_services


@staff_required
def dashboard_view(request):
    summary_data = analytics_services.summary()
    return render(request, 'analytics/dashboard.html', summary_data)


@role_required(UserRole.CUSTOMER, UserRole.ADMIN, UserRole.STAFF)
def portal_home_view(request):
    if request.user.role in [UserRole.ADMIN, UserRole.STAFF] and not hasattr(request.user, 'customer_profile'):
        # For staff testing portal without customer profile
        customer = Customer.objects.first()
    else:
        customer = getattr(request.user, 'customer_profile', None)

    if not customer:
        messages.warning(request, "No customer profile is linked to this account.")
        return render(request, 'portal/portal_home.html', {
            'customer': None,
            'subscriptions': [],
            'invoices': [],
            'payments': [],
        })

    subscriptions = customer.subscriptions.select_related('plan').prefetch_related('items').all()
    invoices = customer.invoices.all()
    payments = customer.payments.select_related('invoice').all()

    return render(request, 'portal/portal_home.html', {
        'customer': customer,
        'subscriptions': subscriptions,
        'invoices': invoices,
        'payments': payments,
    })


@role_required(UserRole.CUSTOMER)
def portal_subscription_cancel_view(request, uuid):
    sub = get_object_or_404(Subscription, uuid=uuid, customer__user=request.user)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Customer requested cancellation from portal.')
        try:
            lifecycle.transition(sub, action='close', actor=request.user, reason=reason)
            messages.success(request, f"Subscription #{sub.id} closed as requested.")
        except lifecycle.LifecycleError as e:
            messages.error(request, str(e))
    return redirect('portal_home')


@role_required(UserRole.CUSTOMER)
def portal_subscription_renew_view(request, uuid):
    sub = get_object_or_404(Subscription, uuid=uuid, customer__user=request.user)
    if request.method == 'POST':
        try:
            lifecycle.transition(sub, action='renew', actor=request.user, reason="Renewed via customer portal")
            messages.success(request, f"Subscription #{sub.id} successfully renewed.")
        except lifecycle.LifecycleError as e:
            messages.error(request, str(e))
    return redirect('portal_home')
