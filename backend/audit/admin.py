from django.contrib import admin
from audit.models import Alert, AuditLog


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'priority', 'status', 'amount', 'created_at')
    list_filter = ('alert_type', 'priority', 'status')
    search_fields = ('title', 'reason', 'deduplication_key')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target_model', 'target_id', 'timestamp')
    readonly_fields = ('action', 'actor', 'target_model', 'target_id', 'details', 'timestamp')
