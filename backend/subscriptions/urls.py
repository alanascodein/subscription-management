from django.urls import path
from subscriptions import views

urlpatterns = [
    path('', views.subscriptions_list_view, name='subscriptions'),
    path('<uuid:uuid>/', views.subscription_detail_view, name='subscription_detail'),
    path('<uuid:uuid>/transition/', views.subscription_transition_view, name='subscription_transition'),
]

