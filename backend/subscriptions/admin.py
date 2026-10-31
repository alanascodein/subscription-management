from django.contrib import admin
from subscriptions.models import Customer, Subscription, SubscriptionItem, SubscriptionEvent


class SubscriptionItemInline(admin.TabularInline):
    model = SubscriptionItem
    extra = 1


class SubscriptionEventInline(admin.TabularInline):
    model = SubscriptionEvent
    extra = 0
    readonly_fields = ('action', 'from_status', 'to_status', 'actor', 'reason', 'timestamp')
    can_delete = False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'company_name', 'email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'plan', 'status', 'start_date', 'next_billing_date', 'created_at')
    list_filter = ('status', 'plan')
    inlines = [SubscriptionItemInline, SubscriptionEventInline]
