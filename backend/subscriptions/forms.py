from django import forms
from subscriptions.models import Customer, Subscription, SubscriptionItem
from products.models import Product, ProductVariant, Plan, TaxRule, Discount


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'company_name', 'billing_address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['customer', 'plan', 'start_date', 'tax_rule', 'discount', 'end_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rule': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.Select(attrs={'class': 'form-select'}),
        }


class SubscriptionItemForm(forms.ModelForm):
    class Meta:
        model = SubscriptionItem
        fields = ['product', 'variant', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
