from django.urls import path
from billing import views

urlpatterns = [
    path('', views.invoices_list_view, name='invoices'),
    path('run/', views.trigger_billing_view, name='trigger_billing'),
    path('<uuid:uuid>/', views.invoice_detail_view, name='invoice_detail'),
    path('<uuid:uuid>/confirm/', views.invoice_confirm_view, name='invoice_confirm'),
    path('<uuid:uuid>/void/', views.invoice_void_view, name='invoice_void'),
]
