from django.urls import path
from proofbill import api

urlpatterns = [
    # Auth
    path('auth/me/', api.auth_me, name='api_auth_me'),
    path('auth/login/', api.auth_login, name='api_auth_login'),
    path('auth/logout/', api.auth_logout, name='api_auth_logout'),
    path('auth/register/', api.auth_register, name='api_auth_register'),

    # Dashboard & Analytics
    path('dashboard/', api.dashboard_summary, name='api_dashboard'),

    # Subscriptions
    path('subscriptions/', api.subscriptions_list, name='api_subscriptions_list'),
    path('subscriptions/create/', api.subscription_create, name='api_subscription_create'),
    path('subscriptions/<uuid:uuid>/', api.subscription_detail, name='api_subscription_detail'),
    path('subscriptions/<uuid:uuid>/transition/', api.subscription_transition, name='api_subscription_transition'),

    # Invoices & Billing
    path('invoices/', api.invoices_list, name='api_invoices_list'),
    path('invoices/<uuid:uuid>/', api.invoice_detail, name='api_invoice_detail'),
    path('invoices/<uuid:uuid>/pay/', api.invoice_record_payment, name='api_invoice_pay'),
    path('invoices/<uuid:uuid>/confirm/', api.invoice_confirm, name='api_invoice_confirm'),
    path('invoices/<uuid:uuid>/void/', api.invoice_void, name='api_invoice_void'),
    path('billing/run/', api.billing_run_now, name='api_billing_run'),

    # Customers
    path('customers/', api.customers_list, name='api_customers_list'),
    path('customers/create/', api.customer_create, name='api_customer_create'),
    path('customers/<uuid:uuid>/', api.customer_detail, name='api_customer_detail'),

    # Catalogue (Products, Plans, Taxes, Discounts)
    path('catalogue/', api.catalogue_list, name='api_catalogue_list'),
    path('plans/create/', api.plan_create, name='api_plan_create'),

    # Proof Engine & Alerts
    path('alerts/', api.alerts_list, name='api_alerts_list'),
    path('alerts/<int:pk>/', api.alert_detail, name='api_alert_detail'),
    path('alerts/<int:pk>/fix/', api.alert_apply_fix, name='api_alert_fix'),
    path('alerts/<int:pk>/review/', api.alert_review, name='api_alert_review'),
    path('audit/run-detection/', api.audit_run_detection, name='api_audit_run_detection'),
    path('audit/leak-injection/', api.audit_leak_injection, name='api_audit_leak_injection'),

    # Customer Portal
    path('portal/', api.portal_data, name='api_portal_data'),
]
