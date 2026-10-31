from django import forms
from core.constants import PaymentMethod
from payments.models import Payment


class PaymentRecordForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_date', 'reference', 'note', 'idempotency_key']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Txn reference ID'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'idempotency_key': forms.HiddenInput(),
        }
