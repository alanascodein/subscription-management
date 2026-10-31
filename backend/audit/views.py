from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.permissions import staff_required
from audit.models import Alert
from audit import proof_engine
from django.core.management import call_command


@staff_required
def alerts_list_view(request):
    type_filter = request.GET.get('type')
    priority_filter = request.GET.get('priority')
    status_filter = request.GET.get('status')

    qs = Alert.objects.select_related('subscription', 'invoice', 'reviewed_by').all()

    if type_filter:
        qs = qs.filter(alert_type=type_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)

    revenue_at_risk = proof_engine.compute_revenue_at_risk()

    return render(request, 'audit/alert_list.html', {
        'alerts': qs,
        'revenue_at_risk': revenue_at_risk,
        'type_filter': type_filter,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
    })


@staff_required
def alert_detail_view(request, pk):
    alert = get_object_or_404(
        Alert.objects.select_related('subscription', 'subscription__customer', 'invoice', 'reviewed_by'),
        pk=pk
    )
    return render(request, 'audit/alert_detail.html', {
        'alert': alert,
    })


@staff_required
def alert_fix_view(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        if action == 'apply_fix':
            try:
                proof_engine.apply_fix(alert, actor=request.user)
                messages.success(request, f"Fix applied successfully for alert '{alert.title}'.")
            except Exception as e:
                messages.error(request, f"Error applying fix: {e}")
        elif action == 'dismiss':
            alert.status = 'dismissed'
            alert.review_notes = notes or "Dismissed by reviewer."
            alert.reviewed_by = request.user
            alert.reviewed_at = timezone.now()
            alert.save()
            messages.info(request, f"Alert #{alert.id} dismissed.")
    return redirect('alert_detail', pk=alert.id)


@staff_required
def trigger_detection_view(request):
    if request.method == 'POST':
        today = timezone.localdate()
        summary = proof_engine.run(as_of=today)
        messages.success(
            request,
            f"Proof Engine detection finished: {summary.alerts_created} new alerts created, "
            f"{summary.alerts_existing} existing. Revenue at Risk: Rs. {summary.revenue_at_risk}."
        )
    return redirect('alerts')


@staff_required
def trigger_leak_injection_view(request):
    if request.method == 'POST':
        call_command('leak_injection')
        messages.warning(
            request,
            "Demo Mode: Synthetic billing leaks (missing invoice, duplicate billing, pricing anomaly) injected! "
            "Proof Engine has refreshed the Revenue at Risk."
        )
    return redirect('alerts')
