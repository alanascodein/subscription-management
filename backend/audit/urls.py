from django.urls import path
from audit import views

urlpatterns = [
    path('', views.alerts_list_view, name='alerts'),
    path('detect/', views.trigger_detection_view, name='trigger_detection'),
    path('inject-leak/', views.trigger_leak_injection_view, name='trigger_leak_injection'),
    path('<int:pk>/', views.alert_detail_view, name='alert_detail'),
    path('<int:pk>/fix/', views.alert_fix_view, name='alert_fix'),
]
