import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.permissions import staff_required
from billing.models import Invoice
from payments.forms import PaymentRecordForm
from payments import services as payment_services


@staff_required
def payment_record_view(request, uuid):
    invoice = get_object_or_404(Invoice, uuid=uuid)

    if request.method == 'POST':
        form = PaymentRecordForm(request.POST)
        if form.is_valid():
            try:
                payment = payment_services.record(
                    invoice=invoice,
                    amount=form.cleaned_data['amount'],
                    method=form.cleaned_data['payment_method'],
                    payment_date=form.cleaned_data['payment_date'],
                    reference=form.cleaned_data['reference'],
                    note=form.cleaned_data['note'],
                    actor=request.user,
                    idempotency_key=form.cleaned_data.get('idempotency_key') or str(uuid.uuid4())
                )
                messages.success(
                    request,
                    f"Payment of Rs. {payment.amount} recorded successfully. "
                    f"Remaining balance due: Rs. {invoice.balance_due}."
                )
                return redirect('invoice_detail', uuid=invoice.uuid)
            except payment_services.OverpaymentError as e:
                messages.error(request, str(e))
            except payment_services.PaymentError as e:
                messages.error(request, str(e))
    else:
        initial_data = {
            'amount': invoice.balance_due,
            'idempotency_key': str(uuid.uuid4()),
        }
        form = PaymentRecordForm(initial=initial_data)

    return render(request, 'payments/payment_form.html', {
        'invoice': invoice,
        'form': form,
    })
