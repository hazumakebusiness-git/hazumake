from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_topup, name='wallet'),
    path('create-order/', views.razorpay_create_order, name='razorpay_create_order'),
]