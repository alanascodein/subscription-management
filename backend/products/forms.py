from django import forms
from products.models import Product, ProductVariant, Plan, TaxRule, Discount


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'cost_price', 'sales_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sales_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'name', 'sku', 'extra_price', 'is_active']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'extra_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            'name', 'code', 'description', 'cycle', 'minimum_quantity',
            'availability_start', 'availability_end', 'grace_days',
            'auto_close', 'early_close_allowed', 'pause_allowed', 'renewal_allowed', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cycle': forms.Select(attrs={'class': 'form-select'}),
            'minimum_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'availability_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'availability_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grace_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_close': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'early_close_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pause_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'renewal_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxRuleForm(forms.ModelForm):
    class Meta:
        model = TaxRule
        fields = ['name', 'rate_percent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rate_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['code', 'name', 'discount_type', 'value', 'usage_limit', 'valid_from', 'valid_to', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
