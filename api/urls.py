from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='api_register'),
    path('auth/login/', views.login, name='api_login'),
    path('auth/google/', views.google_auth, name='api_google_auth'),
    path('auth/otp/request/', views.otp_request, name='api_otp_request'),
    path('auth/otp/verify/', views.otp_verify, name='api_otp_verify'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),

    # Games
    path('games/', views.game_list, name='api_game_list'),

    # Products
    path('products/', views.product_list, name='api_product_list'),
    path('products/<uuid:pk>/', views.product_detail, name='api_product_detail'),

    # Wallet
    path('wallet/', views.wallet_detail, name='api_wallet_detail'),
    path('wallet/topup/', views.wallet_topup_initiate, name='api_wallet_topup'),
    path('wallet/verify/', views.wallet_topup_verify, name='api_wallet_verify'),

    # Orders
    # BUG 2: Move razorpay-verify BEFORE <uuid:pk> to prevent shadowing
    path('orders/razorpay-verify/', views.order_razorpay_verify, name='api_order_razorpay_verify'),
    path('orders/', views.order_list_create, name='api_orders'),
    path('orders/<uuid:pk>/', views.order_detail, name='api_order_detail'),
]