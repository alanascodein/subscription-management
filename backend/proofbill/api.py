import json
import uuid
from decimal import Decimal
from datetime import datetime, date
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction

from core.constants import UserRole, SubscriptionStatus, InvoiceStatus, AlertStatus, AlertType, BillingCycle
from core.money import quantize_money
from core import pricing, periods
from accounts.models import User
from products.models import Product, ProductVariant, Plan, TaxRule, Discount
from subscriptions.models import Customer, Subscription, SubscriptionItem, SubscriptionEvent
from subscriptions import lifecycle
from billing.models import Invoice, InvoiceItem
from billing import services as billing_services
from payments.models import Payment
from payments import services as payment_services
from audit.models import Alert, AuditLog
from audit import proof_engine
from analytics import services as analytics_services


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def json_ok(data=None, **kwargs):
    payload = {'status': 'ok'}
    if data is not None:
        payload['data'] = data
    payload.update(kwargs)
    return JsonResponse(payload, json_dumps_params={'default': decimal_default})


def json_error(message, status=400, **kwargs):
    payload = {'status': 'error', 'message': str(message)}
    payload.update(kwargs)
    return JsonResponse(payload, status=status)


def serialize_alert(alert):
    customer = (
        alert.subscription.customer if alert.subscription_id
        else alert.invoice.customer if alert.invoice_id
        else None
    )
    fix_actions = {
        AlertType.MISSED_INVOICE: ('generate_missing_invoice', 'Generate missing invoice'),
        AlertType.POSSIBLE_DUPLICATE: ('review', 'Mark for review'),
        AlertType.INVOICE_ANOMALY: ('rebalance', 'Rebalance invoice'),
    }
    fix_action, fix_action_display = fix_actions.get(
        alert.alert_type,
        ('none', 'No automatic fix available'),
    )

    return {
        'id': alert.id,
        'rule_type': alert.alert_type,
        'rule_type_display': alert.get_alert_type_display(),
        'priority': alert.priority,
        'status': alert.status,
        'status_display': alert.get_status_display(),
        'amount_at_risk': alert.amount,
        'summary': alert.title,
        'explanation': alert.reason,
        'evidence': alert.evidence,
        'customer': {
            'uuid': str(customer.uuid),
            'name': customer.name,
            'email': customer.email,
        } if customer else None,
        'subscription_id': alert.subscription_id,
        'subscription': {
            'id': alert.subscription.id,
            'uuid': str(alert.subscription.uuid),
            'plan_name': alert.subscription.plan.name,
        } if alert.subscription_id else None,
        'invoice_number': alert.invoice.invoice_number if alert.invoice_id else None,
        'invoice': {
            'uuid': str(alert.invoice.uuid),
            'invoice_number': alert.invoice.invoice_number,
            'total': alert.invoice.total_amount,
            'balance_due': alert.invoice.balance_due,
        } if alert.invoice_id else None,
        'fix_action': fix_action,
        'fix_action_display': fix_action_display,
        'review_notes': alert.review_notes,
        'reviewed_by': alert.reviewed_by.email if alert.reviewed_by else None,
        'reviewed_at': alert.reviewed_at,
        'created_at': alert.created_at,
    }


def parse_json_body(request):
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return {}


# --------------------------------------------------------------------------
# Auth Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def auth_me(request):
    if not request.user.is_authenticated:
        return json_ok(authenticated=False, user=None)

    customer = getattr(request.user, 'customer_profile', None)
    return json_ok(
        authenticated=True,
        user={
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'full_name': request.user.full_name,
            'role': request.user.role,
            'is_staff': request.user.is_staff_user,
            'is_admin': request.user.is_admin_user,
            'is_customer': request.user.is_customer_user,
            'customer_uuid': str(customer.uuid) if customer else None,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def auth_login(request):
    body = parse_json_body(request)
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')

    if not email or not password:
        return json_error("Email and password are required.", status=400)

    user = authenticate(username=email, password=password)
    if not user:
        return json_error("Invalid email or password.", status=401)
    if not user.is_active:
        return json_error("Account is deactivated.", status=403)

    login(request, user)
    customer = getattr(user, 'customer_profile', None)
    return json_ok(
        message="Sign in successful.",
        user={
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'role': user.role,
            'is_staff': user.is_staff_user,
            'is_admin': user.is_admin_user,
            'is_customer': user.is_customer_user,
            'customer_uuid': str(customer.uuid) if customer else None,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def auth_logout(request):
    logout(request)
    return json_ok(message="Signed out successfully.")


@csrf_exempt
@require_http_methods(["POST"])
def auth_register(request):
    body = parse_json_body(request)
    email = body.get('email', '').strip().lower()
    name = body.get('name', '').strip()
    password = body.get('password', '')
    company_name = body.get('company_name', '').strip()
    phone = body.get('phone', '').strip()
    billing_address = body.get('billing_address', '').strip()

    if not email or not password or not name:
        return json_error("Name, email, and password are required.")

    if User.objects.filter(email=email).exists():
        return json_error("An account with this email already exists.")

    from accounts.validators import ProofBillPasswordValidator
    validator = ProofBillPasswordValidator()
    try:
        validator.validate(password)
    except Exception as e:
        return json_error(str(e))

    name_parts = name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.CUSTOMER,
        )
        customer = Customer.objects.create(
            user=user,
            name=name,
            email=email,
            company_name=company_name,
            phone=phone,
            billing_address=billing_address,
        )

    login(request, user)
    return json_ok(
        message="Customer registration successful.",
        user={
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'role': user.role,
            'is_staff': False,
            'is_admin': False,
            'is_customer': True,
            'customer_uuid': str(customer.uuid),
        }
    )


# --------------------------------------------------------------------------
# Dashboard & Analytics Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET", "HEAD"])
def dashboard_summary(request):
    summary_data = analytics_services.summary()

    # High priority alerts count
    high_priority_count = Alert.objects.filter(priority='high', status__in=['new', 'in_review']).count()

    return json_ok({
        'revenue_at_risk': summary_data.get('revenue_at_risk', Decimal('0.00')),
        'overdue_amount': summary_data.get('overdue_amount', Decimal('0.00')),
        'overdue_count': summary_data.get('overdue_count', 0),
        'outstanding': summary_data.get('outstanding', Decimal('0.00')),
        'collected_month': summary_data.get('collected_month', Decimal('0.00')),
        'active_count': summary_data.get('active_count', 0),
        'mrr': summary_data.get('mrr', Decimal('0.00')),
        'trend': summary_data.get('trend', []),
        'overdue_rows': summary_data.get('overdue_rows', []),
        'upcoming_renewals': summary_data.get('upcoming_renewals', []),
        'recent_payments': summary_data.get('recent_payments', []),
        'high_priority_alerts_count': high_priority_count,
        'total_open_alerts_count': Alert.objects.filter(status__in=['new', 'in_review']).count(),
    })



# --------------------------------------------------------------------------
# Subscriptions Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def subscriptions_list(request):
    status_filter = request.GET.get('status')
    qs = Subscription.objects.select_related('customer', 'plan').prefetch_related('items').order_by('-created_at')

    if status_filter:
        qs = qs.filter(status=status_filter)

    results = []
    for s in qs:
        # Calculate subtotal estimate
        total_estimate = Decimal('0.00')
        for it in s.items.all():
            p_price = it.product.sales_price
            v_extra = it.variant.extra_price if it.variant else Decimal('0.00')
            total_estimate += (p_price + v_extra) * it.quantity

        results.append({
            'id': s.id,
            'uuid': str(s.uuid),
            'customer': {
                'uuid': str(s.customer.uuid),
                'name': s.customer.name,
                'email': s.customer.email,
                'company_name': s.customer.company_name,
            },
            'plan': {
                'id': s.plan.id,
                'name': s.plan.name,
                'cycle': s.plan.cycle,
                'cycle_display': s.plan.get_cycle_display(),
            },
            'status': s.status,
            'status_display': s.get_status_display(),
            'start_date': s.start_date,
            'next_billing_date': s.next_billing_date,
            'end_date': s.end_date,
            'items_count': s.items.count(),
            'estimated_period_total': quantize_money(total_estimate),
            'created_at': s.created_at,
        })
    return json_ok(results)


@require_http_methods(["GET"])
def subscription_detail(request, uuid):
    sub = get_object_or_404(
        Subscription.objects.select_related('customer', 'plan', 'tax_rule', 'discount')
        .prefetch_related('items__product', 'items__variant', 'events', 'invoices'),
        uuid=uuid
    )

    items_data = []
    for it in sub.items.all():
        unit_price = it.product.sales_price + (it.variant.extra_price if it.variant else Decimal('0.00'))
        line_total = unit_price * it.quantity
        items_data.append({
            'id': it.id,
            'product_name': it.product.name,
            'variant_name': it.variant.name if it.variant else None,
            'unit_price': quantize_money(unit_price),
            'quantity': it.quantity,
            'line_total': quantize_money(line_total),
        })

    events_data = []
    for ev in sub.events.all()[:30]:
        events_data.append({
            'id': ev.id,
            'from_status': ev.from_status,
            'to_status': ev.to_status,
            'actor_email': ev.actor.email if ev.actor else 'System',
            'reason': ev.reason,
            'created_at': ev.created_at,
        })

    invoices_data = []
    for inv in sub.invoices.all().order_by('-issue_date'):
        invoices_data.append({
            'uuid': str(inv.uuid),
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'total': inv.total_amount,
            'amount_paid': inv.amount_paid,
            'balance_due': inv.balance_due,
            'issue_date': inv.issue_date,
            'due_date': inv.due_date,
        })

    return json_ok({
        'id': sub.id,
        'uuid': str(sub.uuid),
        'customer': {
            'uuid': str(sub.customer.uuid),
            'name': sub.customer.name,
            'email': sub.customer.email,
            'company_name': sub.customer.company_name,
            'phone': sub.customer.phone,
            'billing_address': sub.customer.billing_address,
        },
        'plan': {
            'id': sub.plan.id,
            'name': sub.plan.name,
            'code': sub.plan.code,
            'cycle': sub.plan.cycle,
            'cycle_display': sub.plan.get_cycle_display(),
            'grace_days': sub.plan.grace_days,
            'pause_allowed': sub.plan.pause_allowed,
            'early_close_allowed': sub.plan.early_close_allowed,
            'renewal_allowed': sub.plan.renewal_allowed,
        },
        'status': sub.status,
        'status_display': sub.get_status_display(),
        'start_date': sub.start_date,
        'next_billing_date': sub.next_billing_date,
        'end_date': sub.end_date,
        'tax_rule': {
            'id': sub.tax_rule.id,
            'name': sub.tax_rule.name,
            'rate_percent': sub.tax_rule.rate_percent,
        } if sub.tax_rule else None,
        'discount': {
            'id': sub.discount.id,
            'name': sub.discount.name,
            'code': sub.discount.code,
            'discount_type': sub.discount.discount_type,
            'value': sub.discount.value,
        } if sub.discount else None,
        'items': items_data,
        'events': events_data,
        'invoices': invoices_data,
        'created_at': sub.created_at,
    })


@csrf_exempt
@require_http_methods(["POST"])
def subscription_create(request):
    body = parse_json_body(request)
    customer_uuid = body.get('customer_uuid')
    customer_id = body.get('customer_id')
    plan_id = body.get('plan_id')
    start_date_str = body.get('start_date')
    tax_rule_id = body.get('tax_rule_id')
    discount_id = body.get('discount_id')
    items_input = body.get('items', [])

    if customer_uuid:
        customer = get_object_or_404(Customer, uuid=customer_uuid)
    elif customer_id:
        customer = get_object_or_404(Customer, id=customer_id)
    else:
        return json_error("Customer identifier required.")

    plan = get_object_or_404(Plan, id=plan_id)
    start_date_val = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else timezone.localdate()
    tax_rule = TaxRule.objects.filter(id=tax_rule_id).first() if tax_rule_id else None
    discount = Discount.objects.filter(id=discount_id).first() if discount_id else None

    with transaction.atomic():
        sub = Subscription.objects.create(
            customer=customer,
            plan=plan,
            start_date=start_date_val,
            next_billing_date=start_date_val,
            tax_rule=tax_rule,
            discount=discount,
            status=SubscriptionStatus.DRAFT,
        )

        for item_data in items_input:
            prod = get_object_or_404(Product, id=item_data.get('product_id'))
            variant = None
            if item_data.get('variant_id'):
                variant = ProductVariant.objects.filter(id=item_data.get('variant_id'), product=prod).first()
            qty = int(item_data.get('quantity', 1))
            SubscriptionItem.objects.create(
                subscription=sub,
                product=prod,
                variant=variant,
                quantity=max(1, qty)
            )

        # Log creation
        actor = request.user if request.user.is_authenticated else None
        SubscriptionEvent.objects.create(
            subscription=sub,
            from_status='',
            to_status=SubscriptionStatus.DRAFT,
            actor=actor,
            reason="Subscription created via API"
        )

    return json_ok(
        message="Subscription created successfully.",
        subscription={'uuid': str(sub.uuid), 'id': sub.id, 'status': sub.status}
    )


@csrf_exempt
@require_http_methods(["POST"])
def subscription_transition(request, uuid):
    sub = get_object_or_404(Subscription, uuid=uuid)
    body = parse_json_body(request)
    action = body.get('action')
    reason = body.get('reason', '')

    if not action:
        return json_error("Transition action required.")

    actor = request.user if request.user.is_authenticated else None
    try:
        updated_sub = lifecycle.transition(sub, action=action, actor=actor, reason=reason)
        return json_ok(
            message=f"Subscription moved to {updated_sub.get_status_display()}.",
            subscription={'uuid': str(updated_sub.uuid), 'status': updated_sub.status, 'status_display': updated_sub.get_status_display()}
        )
    except lifecycle.LifecycleError as e:
        return json_error(str(e))


# --------------------------------------------------------------------------
# Invoices & Billing Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def invoices_list(request):
    status_filter = request.GET.get('status')
    customer_uuid = request.GET.get('customer')

    qs = Invoice.objects.select_related('customer', 'subscription').order_by('-issue_date')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if customer_uuid:
        qs = qs.filter(customer__uuid=customer_uuid)

    results = []
    for inv in qs:
        results.append({
            'uuid': str(inv.uuid),
            'invoice_number': inv.invoice_number,
            'customer': {
                'uuid': str(inv.customer.uuid),
                'name': inv.customer.name,
                'email': inv.customer.email,
            },
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'period_start': inv.period_start,
            'period_end': inv.period_end,
            'issue_date': inv.issue_date,
            'due_date': inv.due_date,
            'subtotal': inv.subtotal,
            'tax_amount': inv.tax_amount,
            'discount_amount': inv.discount_amount,
            'total': inv.total_amount,
            'amount_paid': inv.amount_paid,
            'balance_due': inv.balance_due,
            'is_overdue': inv.is_overdue,
            'is_partially_paid': inv.is_partially_paid,
        })
    return json_ok(results)


@require_http_methods(["GET"])
def invoice_detail(request, uuid):
    inv = get_object_or_404(
        Invoice.objects.select_related('customer', 'subscription__plan')
        .prefetch_related('items', 'payments'),
        uuid=uuid
    )

    items_data = []
    for it in inv.items.all():
        items_data.append({
            'id': it.id,
            'description': it.description,
            'unit_price': it.unit_price,
            'quantity': it.quantity,
            'line_subtotal': it.line_subtotal,
            'discount_amount': it.discount_amount,
            'tax_amount': it.tax_amount,
            'line_total': it.line_total,
        })

    payments_data = []
    for p in inv.payments.all().order_by('-payment_date'):
        payments_data.append({
            'uuid': str(p.uuid),
            'amount': p.amount,
            'date': p.payment_date,
            'method': p.payment_method,
            'method_display': p.get_payment_method_display(),
            'reference': p.reference,
            'note': p.note,
        })

    return json_ok({
        'uuid': str(inv.uuid),
        'invoice_number': inv.invoice_number,
        'customer': {
            'uuid': str(inv.customer.uuid),
            'name': inv.customer.name,
            'email': inv.customer.email,
            'company_name': inv.customer.company_name,
            'billing_address': inv.customer.billing_address,
        },
        'subscription': {
            'uuid': str(inv.subscription.uuid) if inv.subscription else None,
            'plan_name': inv.subscription.plan.name if inv.subscription and inv.subscription.plan else 'Custom',
        } if inv.subscription else None,
        'status': inv.status,
        'status_display': inv.get_status_display(),
        'period_start': inv.period_start,
        'period_end': inv.period_end,
        'issue_date': inv.issue_date,
        'due_date': inv.due_date,
        'subtotal': inv.subtotal,
        'tax_amount': inv.tax_amount,
        'discount_amount': inv.discount_amount,
        'total': inv.total_amount,
        'amount_paid': inv.amount_paid,
        'balance_due': inv.balance_due,
        'is_overdue': inv.is_overdue,
        'is_partially_paid': inv.is_partially_paid,
        'void_reason': inv.void_reason,
        'items': items_data,
        'payments': payments_data,
    })


@csrf_exempt
@require_http_methods(["POST"])
def invoice_record_payment(request, uuid):
    inv = get_object_or_404(Invoice, uuid=uuid)
    body = parse_json_body(request)
    amount_str = body.get('amount')
    method = body.get('method', 'bank_transfer')
    date_str = body.get('date')
    reference = body.get('reference', '')
    note = body.get('note', '')

    if not amount_str:
        return json_error("Payment amount is required.")

    try:
        amount = Decimal(str(amount_str))
    except Exception:
        return json_error("Invalid monetary amount.")

    p_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.localdate()
    actor = request.user if request.user.is_authenticated else None

    try:
        payment = payment_services.record(
            invoice=inv,
            amount=amount,
            method=method,
            payment_date=p_date,
            reference=reference,
            note=note,
            actor=actor
        )
        return json_ok(
            message=f"Payment of Rs. {payment.amount} recorded successfully.",
            payment={
                'uuid': str(payment.uuid),
                'amount': payment.amount,
                'invoice_balance_due': inv.balance_due,
                'invoice_status': inv.status,
            }
        )
    except Exception as e:
        return json_error(str(e))


@csrf_exempt
@require_http_methods(["POST"])
def invoice_confirm(request, uuid):
    inv = get_object_or_404(Invoice, uuid=uuid)
    actor = request.user if request.user.is_authenticated else None
    try:
        billing_services.confirm_invoice(inv, actor=actor)
        return json_ok(message=f"Invoice {inv.invoice_number} confirmed.")
    except Exception as e:
        return json_error(str(e))


@csrf_exempt
@require_http_methods(["POST"])
def invoice_void(request, uuid):
    inv = get_object_or_404(Invoice, uuid=uuid)
    body = parse_json_body(request)
    reason = body.get('reason', '').strip()
    if not reason:
        return json_error("A void reason is required.")

    actor = request.user if request.user.is_authenticated else None
    try:
        billing_services.void_invoice(inv, reason=reason, actor=actor)
        return json_ok(message=f"Invoice {inv.invoice_number} has been voided.")
    except Exception as e:
        return json_error(str(e))


@csrf_exempt
@require_http_methods(["POST"])
def billing_run_now(request):
    body = parse_json_body(request)
    run_date_str = body.get('run_date')
    run_date = datetime.strptime(run_date_str, "%Y-%m-%d").date() if run_date_str else timezone.localdate()

    try:
        billing_run = billing_services.run(run_date=run_date)
        return json_ok(
            message=f"Billing run completed. {billing_run.invoices_created} invoices generated.",
            billing_run={
                'id': billing_run.id,
                'run_date': billing_run.run_date,
                'invoices_created': billing_run.invoices_created,
                'total_billed': billing_run.total_billed,
                'created_at': billing_run.created_at,
            }
        )
    except Exception as e:
        return json_error(str(e))


# --------------------------------------------------------------------------
# Customers Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def customers_list(request):
    customers = Customer.objects.prefetch_related('subscriptions', 'invoices').order_by('name')
    results = []
    for c in customers:
        unpaid = Decimal('0.00')
        for inv in c.invoices.filter(status='confirmed'):
            unpaid += inv.balance_due

        results.append({
            'uuid': str(c.uuid),
            'name': c.name,
            'email': c.email,
            'company_name': c.company_name,
            'phone': c.phone,
            'billing_address': c.billing_address,
            'active_subscriptions_count': c.subscriptions.filter(status=SubscriptionStatus.ACTIVE).count(),
            'total_subscriptions_count': c.subscriptions.count(),
            'unpaid_balance': quantize_money(unpaid),
            'created_at': c.created_at,
        })
    return json_ok(results)


@require_http_methods(["GET"])
def customer_detail(request, uuid):
    c = get_object_or_404(Customer.objects.prefetch_related('subscriptions__plan', 'invoices', 'payments'), uuid=uuid)

    subscriptions_data = []
    for s in c.subscriptions.all():
        subscriptions_data.append({
            'uuid': str(s.uuid),
            'id': s.id,
            'plan_name': s.plan.name,
            'cycle': s.plan.cycle,
            'status': s.status,
            'status_display': s.get_status_display(),
            'next_billing_date': s.next_billing_date,
        })

    invoices_data = []
    for inv in c.invoices.all().order_by('-issue_date'):
        invoices_data.append({
            'uuid': str(inv.uuid),
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'total': inv.total_amount,
            'balance_due': inv.balance_due,
            'issue_date': inv.issue_date,
            'due_date': inv.due_date,
            'is_overdue': inv.is_overdue,
        })

    payments_data = []
    for p in c.payments.select_related('invoice').order_by('-payment_date'):
        payments_data.append({
            'uuid': str(p.uuid),
            'amount': p.amount,
            'date': p.payment_date,
            'method': p.get_payment_method_display(),
            'invoice_number': p.invoice.invoice_number,
        })

    return json_ok({
        'uuid': str(c.uuid),
        'name': c.name,
        'email': c.email,
        'company_name': c.company_name,
        'phone': c.phone,
        'billing_address': c.billing_address,
        'subscriptions': subscriptions_data,
        'invoices': invoices_data,
        'payments': payments_data,
        'created_at': c.created_at,
    })


@csrf_exempt
@require_http_methods(["POST"])
def customer_create(request):
    body = parse_json_body(request)
    name = body.get('name', '').strip()
    email = body.get('email', '').strip().lower()
    company_name = body.get('company_name', '').strip()
    phone = body.get('phone', '').strip()
    billing_address = body.get('billing_address', '').strip()

    if not name or not email:
        return json_error("Customer name and email are required.")

    with transaction.atomic():
        # Ensure a customer user account is linked
        user = User.objects.filter(email=email).first()
        if not user:
            name_parts = name.split(maxsplit=1)
            first = name_parts[0]
            last = name_parts[1] if len(name_parts) > 1 else ''
            user = User.objects.create_user(
                email=email,
                first_name=first,
                last_name=last,
                role=UserRole.CUSTOMER
            )

        customer = Customer.objects.create(
            user=user,
            name=name,
            email=email,
            company_name=company_name,
            phone=phone,
            billing_address=billing_address,
        )

    return json_ok(
        message=f"Customer '{customer.name}' registered successfully.",
        customer={'uuid': str(customer.uuid), 'name': customer.name, 'email': customer.email}
    )


# --------------------------------------------------------------------------
# Catalogue Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def catalogue_list(request):
    products = Product.objects.prefetch_related('variants').all()
    plans = Plan.objects.all()
    taxes = TaxRule.objects.all()
    discounts = Discount.objects.all()

    products_data = []
    for p in products:
        variants_data = [{
            'id': v.id,
            'name': v.name,
            'extra_price': v.extra_price,
            'is_active': v.is_active,
        } for v in p.variants.all()]

        products_data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'cost_price': p.cost_price,
            'sales_price': p.sales_price,
            'is_active': p.is_active,
            'variants': variants_data,
        })

    plans_data = [{
        'id': pl.id,
        'code': pl.code,
        'name': pl.name,
        'cycle': pl.cycle,
        'cycle_display': pl.get_cycle_display(),
        'minimum_quantity': pl.minimum_quantity,
        'grace_days': pl.grace_days,
        'auto_close': pl.auto_close,
        'early_close_allowed': pl.early_close_allowed,
        'pause_allowed': pl.pause_allowed,
        'renewal_allowed': pl.renewal_allowed,
        'is_active': pl.is_active,
    } for pl in plans]

    taxes_data = [{
        'id': t.id,
        'name': t.name,
        'rate_percent': t.rate_percent,
        'is_active': t.is_active,
    } for t in taxes]

    discounts_data = [{
        'id': d.id,
        'name': d.name,
        'code': d.code,
        'discount_type': d.discount_type,
        'value': d.value,
        'usage_limit': d.usage_limit,
        'times_used': d.times_used,
        'is_active': d.is_active,
    } for d in discounts]

    return json_ok({
        'products': products_data,
        'plans': plans_data,
        'tax_rules': taxes_data,
        'discounts': discounts_data,
    })


@csrf_exempt
@require_http_methods(["POST"])
def plan_create(request):
    body = parse_json_body(request)
    code = body.get('code', '').strip()
    name = body.get('name', '').strip()
    cycle = body.get('cycle', 'monthly')
    grace_days = int(body.get('grace_days', 3))
    minimum_quantity = int(body.get('minimum_quantity', 1))

    if not code or not name:
        return json_error("Plan code and name are required.")

    if Plan.objects.filter(code=code).exists():
        return json_error("A plan with this code already exists.")

    plan = Plan.objects.create(
        code=code,
        name=name,
        cycle=cycle,
        grace_days=grace_days,
        minimum_quantity=minimum_quantity,
        pause_allowed=body.get('pause_allowed', True),
        early_close_allowed=body.get('early_close_allowed', True),
        renewal_allowed=body.get('renewal_allowed', True),
    )
    return json_ok(message=f"Plan '{plan.name}' created.", plan={'id': plan.id, 'name': plan.name})


# --------------------------------------------------------------------------
# Proof Engine & Audit Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def alerts_list(request):
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    rule_type_filter = request.GET.get('type')

    qs = Alert.objects.select_related(
        'subscription__customer',
        'subscription__plan',
        'invoice__customer',
        'reviewed_by',
    ).order_by('-created_at')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)
    if rule_type_filter:
        qs = qs.filter(alert_type=rule_type_filter)

    return json_ok([serialize_alert(alert) for alert in qs])


@require_http_methods(["GET"])
def alert_detail(request, pk):
    alert = get_object_or_404(
        Alert.objects.select_related(
            'subscription__customer',
            'subscription__plan',
            'invoice__customer',
            'reviewed_by',
        ),
        pk=pk,
    )
    return json_ok(serialize_alert(alert))


@csrf_exempt
@require_http_methods(["POST"])
def alert_apply_fix(request, pk):
    a = get_object_or_404(Alert, pk=pk)
    actor = request.user if request.user.is_authenticated else None

    if a.status == AlertStatus.RESOLVED:
        return json_error("This alert is already marked as resolved.")

    try:
        updated_alert = proof_engine.apply_fix(a, actor=actor)
        return json_ok(
            message=f"One-click fix applied successfully. Alert status updated to {updated_alert.get_status_display()}.",
            alert={'id': updated_alert.id, 'status': updated_alert.status, 'status_display': updated_alert.get_status_display()}
        )
    except Exception as e:
        return json_error(str(e))


@csrf_exempt
@require_http_methods(["POST"])
def alert_review(request, pk):
    a = get_object_or_404(Alert, pk=pk)
    body = parse_json_body(request)
    new_status = body.get('status')
    notes = body.get('notes', '')

    if new_status not in [c[0] for c in AlertStatus.choices]:
        return json_error("Invalid alert status.")

    a.status = new_status
    a.review_notes = notes
    a.reviewed_by = request.user if request.user.is_authenticated else None
    a.reviewed_at = timezone.now()
    a.save()

    return json_ok(
        message=f"Alert status updated to {a.get_status_display()}.",
        alert={'id': a.id, 'status': a.status, 'status_display': a.get_status_display()}
    )


@csrf_exempt
@require_http_methods(["POST"])
def audit_run_detection(request):
    body = parse_json_body(request)
    as_of_str = body.get('as_of')
    as_of = datetime.strptime(as_of_str, "%Y-%m-%d").date() if as_of_str else timezone.localdate()

    try:
        summary = proof_engine.run(as_of=as_of)
        return json_ok(
            message=f"Proof Engine detection finished. {summary.new_alerts_count} new alerts, {summary.existing_alerts_count} active.",
            summary={
                'new_alerts_count': summary.new_alerts_count,
                'existing_alerts_count': summary.existing_alerts_count,
                'total_alerts_count': summary.total_alerts_count,
                'revenue_at_risk': summary.revenue_at_risk,
            }
        )
    except Exception as e:
        return json_error(str(e))


@csrf_exempt
@require_http_methods(["POST"])
def audit_leak_injection(request):
    try:
        from core.management.commands.leak_injection import Command as LeakCommand
        cmd = LeakCommand()
        cmd.handle()
        summary = proof_engine.run(as_of=timezone.localdate())
        return json_ok(
            message="Synthetic billing leaks successfully injected into database! Proof Engine audit refreshed.",
            revenue_at_risk=summary.revenue_at_risk,
            total_alerts=summary.total_alerts_count,
        )
    except Exception as e:
        return json_error(str(e))


# --------------------------------------------------------------------------
# Customer Portal Endpoints
# --------------------------------------------------------------------------

@require_http_methods(["GET"])
def portal_data(request):
    customer = None
    if request.user.is_authenticated:
        customer = getattr(request.user, 'customer_profile', None)

    # Fallback to first customer for preview if staff or unassigned
    if not customer:
        customer = Customer.objects.first()

    if not customer:
        return json_ok({
            'customer': None,
            'subscriptions': [],
            'invoices': [],
            'payments': [],
        })

    subs_data = []
    for s in customer.subscriptions.select_related('plan').prefetch_related('items__product').all():
        subs_data.append({
            'uuid': str(s.uuid),
            'id': s.id,
            'plan_name': s.plan.name,
            'cycle': s.plan.cycle,
            'cycle_display': s.plan.get_cycle_display(),
            'status': s.status,
            'status_display': s.get_status_display(),
            'start_date': s.start_date,
            'next_billing_date': s.next_billing_date,
            'can_pause': s.plan.pause_allowed and s.status == SubscriptionStatus.ACTIVE,
            'can_cancel': s.plan.early_close_allowed and s.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED],
            'can_renew': s.plan.renewal_allowed,
        })

    invoices_data = []
    for inv in customer.invoices.all().order_by('-issue_date'):
        invoices_data.append({
            'uuid': str(inv.uuid),
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'total': inv.total_amount,
            'amount_paid': inv.amount_paid,
            'balance_due': inv.balance_due,
            'issue_date': inv.issue_date,
            'due_date': inv.due_date,
            'is_overdue': inv.is_overdue,
        })

    payments_data = []
    for p in customer.payments.select_related('invoice').all().order_by('-payment_date'):
        payments_data.append({
            'uuid': str(p.uuid),
            'amount': p.amount,
            'date': p.payment_date,
            'method': p.get_payment_method_display(),
            'invoice_number': p.invoice.invoice_number,
            'reference': p.reference,
        })

    return json_ok({
        'customer': {
            'uuid': str(customer.uuid),
            'name': customer.name,
            'email': customer.email,
            'company_name': customer.company_name,
            'phone': customer.phone,
            'billing_address': customer.billing_address,
        },
        'subscriptions': subs_data,
        'invoices': invoices_data,
        'payments': payments_data,
    })
