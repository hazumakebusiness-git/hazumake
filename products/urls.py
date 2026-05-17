# products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop, name='shop'),                          # /shop/ — all games
    path('<slug:game_slug>/', views.game_shop, name='game_shop'),  # /shop/mobile-legends/
    path('product/<uuid:pk>/', views.product_detail, name='product_detail'),
    path('verify-player/', views.verify_player_view, name='verify_player'),
]

