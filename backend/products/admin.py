from django.contrib import admin
from products.models import Product, ProductVariant, Plan, TaxRule, Discount


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost_price', 'sales_price', 'is_active', 'created_at')
    inlines = [ProductVariantInline]
    search_fields = ('name',)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'cycle', 'minimum_quantity', 'grace_days', 'is_active')
    prepopulated_fields = {'code': ('name',)}
    list_filter = ('cycle', 'is_active')


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate_percent', 'is_active')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'discount_type', 'value', 'times_used', 'usage_limit', 'is_active')
