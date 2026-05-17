from django.urls import path
from . import views

urlpatterns = [
    path('', views.orders, name='orders'),
    path('create/', views.place_order, name='create_order'),
    path('razorpay-success/', views.razorpay_order_success, name='razorpay_order_success'),
    path('<uuid:pk>/', views.order_detail, name='order_detail'),
]