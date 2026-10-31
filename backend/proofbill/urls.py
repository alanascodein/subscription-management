from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from core.constants import UserRole


def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == UserRole.CUSTOMER:
        return redirect('portal_home')
    return redirect('dashboard')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('plans/', include([
        path('', include('products.urls')),
    ])),
    path('subscriptions/', include('subscriptions.urls')),
    path('customers/', include('subscriptions.urls')),
    path('invoices/', include('billing.urls')),
    path('', include('payments.urls')),
    path('alerts/', include('audit.urls')),
    path('', include('analytics.urls')),
]
