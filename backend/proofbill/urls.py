from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from core.constants import UserRole
from products.views import plans_list_view
from subscriptions.views import customers_list_view, customer_detail_view


def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == UserRole.CUSTOMER:
        return redirect('portal_home')
    return redirect('dashboard')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
    path('api/', include('proofbill.api_urls')),
    path('accounts/', include('accounts.urls')),

    path('products/', include('products.urls')),
    path('plans/', plans_list_view, name='plans'),
    path('customers/', customers_list_view, name='customers'),
    path('customers/<uuid:uuid>/', customer_detail_view, name='customer_detail'),
    path('subscriptions/', include('subscriptions.urls')),
    path('invoices/', include('billing.urls')),
    path('', include('payments.urls')),
    path('alerts/', include('audit.urls')),
    path('', include('analytics.urls')),
]

