from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from accounts.forms import EmailAuthenticationForm, StaffCreationForm
from accounts.permissions import admin_required
from core.constants import UserRole


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == UserRole.CUSTOMER:
            return redirect('portal_home')
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.email}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.role == UserRole.CUSTOMER:
                return redirect('portal_home')
            return redirect('dashboard')
    else:
        form = EmailAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@admin_required
def create_staff_view(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff account {user.email} created successfully.")
            return redirect('dashboard')
    else:
        form = StaffCreationForm()

    return render(request, 'accounts/create_staff.html', {'form': form})
