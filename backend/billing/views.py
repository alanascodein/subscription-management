from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from accounts.permissions import staff_required, role_required
from core.constants import UserRole, InvoiceStatus
from billing.models import Invoice, BillingRun
from billing import services as billing_services


@staff_required
def invoices_list_view(request):
    status_filter = request.GET.get('status')
    qs = Invoice.objects.select_related('customer', 'subscription').all()

    if status_filter:
        if status_filter == 'overdue':
            today = timezone.localdate()
            qs = qs.filter(status=InvoiceStatus.CONFIRMED, balance_due__gt=0, due_date__lt=today)
        elif status_filter == 'partially_paid':
            qs = qs.filter(amount_paid__gt=0, balance_due__gt=0).exclude(status=InvoiceStatus.VOID)
        else:
            qs = qs.filter(status=status_filter)

    return render(request, 'billing/invoice_list.html', {
        'invoices': qs,
        'status_filter': status_filter,
    })


@role_required(UserRole.ADMIN, UserRole.STAFF, UserRole.CUSTOMER)
def invoice_detail_view(request, uuid):
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer', 'subscription', 'subscription__plan')
        .prefetch_related('items', 'payments'),
        uuid=uuid
    )

    # Scoping check: if customer user, must match
    if request.user.role == UserRole.CUSTOMER and invoice.customer.user != request.user:
        raise Http404("Invoice not found.")

    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'items': invoice.items.all(),
        'payments': invoice.payments.all(),
    })


@staff_required
def invoice_confirm_view(request, uuid):
    invoice = get_object_or_404(Invoice, uuid=uuid)
    if request.method == 'POST':
        try:
            billing_services.confirm_invoice(invoice, actor=request.user)
            messages.success(request, f"Invoice {invoice.invoice_number} confirmed.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('invoice_detail', uuid=invoice.uuid)


@staff_required
def invoice_void_view(request, uuid):
    invoice = get_object_or_404(Invoice, uuid=uuid)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        try:
            billing_services.void_invoice(invoice, reason=reason, actor=request.user)
            messages.success(request, f"Invoice {invoice.invoice_number} voided.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('invoice_detail', uuid=invoice.uuid)


@staff_required
def trigger_billing_view(request):
    if request.method == 'POST':
        today = timezone.localdate()
        run_record = billing_services.run(run_date=today)
        messages.success(
            request,
            f"Billing run executed for {today}: {run_record.invoices_created} new invoices generated "
            f"(Total: Rs. {run_record.total_billed})."
        )
    return redirect('invoices')
