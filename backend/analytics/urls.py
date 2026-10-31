from django.urls import path
from analytics import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('portal/', views.portal_home_view, name='portal_home'),
    path('portal/subscription/<uuid:uuid>/cancel/', views.portal_subscription_cancel_view, name='portal_sub_cancel'),
    path('portal/subscription/<uuid:uuid>/renew/', views.portal_subscription_renew_view, name='portal_sub_renew'),
]
