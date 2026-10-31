from django.urls import path
from products import views

urlpatterns = [
    path('', views.products_list_view, name='products'),
    path('rules/', views.rules_list_view, name='rules_list'),
]

