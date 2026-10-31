from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from core.constants import UserRole
from accounts.models import User
from accounts.validators import ProofBillPasswordValidator


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@company.com', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'})
    )

    def clean(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid email or password.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("This account has been deactivated.")
        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[ProofBillPasswordValidator()]
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomerRegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        label="Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jane Doe'})
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        label="Company Name (Optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Acme Corp'})
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'jane@example.com'})
    )
    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone Number (Optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'})
    )
    billing_address = forms.CharField(
        required=False,
        label="Billing Address (Optional)",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street, City, Postal Code'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'At least 9 characters'}),
        validators=[ProofBillPasswordValidator()]
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter your password'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        from subscriptions.models import Customer
        email = self.cleaned_data['email'].strip().lower()
        password = self.cleaned_data['password']
        name = self.cleaned_data['name'].strip()
        company_name = self.cleaned_data.get('company_name', '').strip()
        phone = self.cleaned_data.get('phone', '').strip()
        billing_address = self.cleaned_data.get('billing_address', '').strip()

        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.CUSTOMER,
        )

        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={
                'user': user,
                'name': name,
                'company_name': company_name,
                'phone': phone,
                'billing_address': billing_address,
            }
        )
        if not created and not customer.user:
            customer.user = user
            customer.save()

        return user

