from django.contrib import admin
from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'customer', 'amount', 'payment_method', 'payment_date', 'reference')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('invoice__invoice_number', 'customer__name', 'reference')
