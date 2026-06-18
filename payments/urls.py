"""
payments/urls.py
ExPay webhook URL routing.
"""

from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("wallet/webhook/", views.ExPayWebhookView.as_view(), name="expay_webhook"),
]
