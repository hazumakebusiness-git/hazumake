from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_topup, name='wallet'),
    path('create-order/', views.expay_create_order, name='expay_create_order'),
]