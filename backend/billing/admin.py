from django.contrib import admin
from billing.models import Invoice, InvoiceItem, NumberSequence, BillingRun


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'unit_price', 'line_subtotal', 'discount_amount', 'net_amount', 'tax_amount', 'line_total')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'status', 'total_amount', 'amount_paid', 'balance_due', 'period_start', 'due_date')
    list_filter = ('status', 'issue_date')
    search_fields = ('invoice_number', 'customer__name')
    inlines = [InvoiceItemInline]


@admin.register(BillingRun)
class BillingRunAdmin(admin.ModelAdmin):
    list_display = ('run_date', 'invoices_created', 'total_billed', 'status', 'created_at')


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ('sequence_type', 'prefix', 'next_number')
