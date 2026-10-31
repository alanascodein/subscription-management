from django.urls import path
from payments import views

urlpatterns = [
    path('invoices/<uuid:uuid>/pay/', views.payment_record_view, name='payment_record'),
]
