from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from accounts.permissions import staff_required, role_required
from core.constants import UserRole, SubscriptionStatus
from core.money import quantize_money
from subscriptions.models import Customer, Subscription, SubscriptionItem
from subscriptions.forms import CustomerForm, SubscriptionForm, SubscriptionItemForm
from subscriptions import lifecycle


@staff_required
def customers_list_view(request):
    customers = Customer.objects.all()
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f"Customer '{c.name}' registered.")
            return redirect('customers')

    return render(request, 'subscriptions/customer_list.html', {
        'customers': customers,
        'form': form,
    })


@role_required(UserRole.ADMIN, UserRole.STAFF, UserRole.CUSTOMER)
def customer_detail_view(request, uuid):
    customer = get_object_or_404(Customer, uuid=uuid)

    # Scoping check: if customer user, must match
    if request.user.role == UserRole.CUSTOMER and customer.user != request.user:
        raise Http404("Customer not found.")

    subscriptions = customer.subscriptions.all()
    invoices = customer.invoices.all()

    return render(request, 'subscriptions/customer_detail.html', {
        'customer': customer,
        'subscriptions': subscriptions,
        'invoices': invoices,
    })


@staff_required
def subscriptions_list_view(request):
    status_filter = request.GET.get('status')
    qs = Subscription.objects.select_related('customer', 'plan').prefetch_related('items')

    if status_filter:
        qs = qs.filter(status=status_filter)

    form = SubscriptionForm()
    item_form = SubscriptionItemForm()

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        item_form = SubscriptionItemForm(request.POST)
        if form.is_valid() and item_form.is_valid():
            sub = form.save(commit=False)
            sub.next_billing_date = sub.start_date
            sub.created_by = request.user
            sub.save()

            item = item_form.save(commit=False)
            item.subscription = sub
            item.unit_price = item.product.sales_price + (item.variant.extra_price if item.variant else 0)
            item.save()

            messages.success(request, f"Subscription #{sub.id} created in Draft status.")
            return redirect('subscription_detail', uuid=sub.uuid)

    return render(request, 'subscriptions/subscription_list.html', {
        'subscriptions': qs,
        'form': form,
        'item_form': item_form,
        'status_filter': status_filter,
    })


@role_required(UserRole.ADMIN, UserRole.STAFF, UserRole.CUSTOMER)
def subscription_detail_view(request, uuid):
    sub = get_object_or_404(
        Subscription.objects.select_related('customer', 'plan', 'tax_rule', 'discount')
        .prefetch_related('items__product', 'items__variant', 'events', 'invoices'),
        uuid=uuid
    )

    # Scoping check
    if request.user.role == UserRole.CUSTOMER and sub.customer.user != request.user:
        raise Http404("Subscription not found.")

    return render(request, 'subscriptions/subscription_detail.html', {
        'subscription': sub,
        'events': sub.events.all()[:20],
        'invoices': sub.invoices.all(),
    })


@staff_required
def subscription_transition_view(request, uuid):
    sub = get_object_or_404(Subscription, uuid=uuid)

    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        try:
            lifecycle.transition(sub, action=action, actor=request.user, reason=reason)
            messages.success(request, f"Subscription successfully updated to {sub.get_status_display()}.")
        except lifecycle.LifecycleError as e:
            messages.error(request, str(e))

    return redirect('subscription_detail', uuid=sub.uuid)
