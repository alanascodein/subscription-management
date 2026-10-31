from django.contrib import admin

from analytics.models import DashboardSnapshot


@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('label', 'captured_at', 'active_count', 'mrr', 'total_collected', 'outstanding', 'overdue_amount', 'revenue_at_risk')
    readonly_fields = ('captured_at',)
    search_fields = ('label',)
